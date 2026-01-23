"""
Chronofact.ai - Image Processing Utilities
Handles image downloading, analysis, and preprocessing for multimodal embeddings.
"""

import os
import hashlib
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from io import BytesIO
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
from PIL import Image, ImageStat, ImageFilter
import numpy as np

logger = logging.getLogger(__name__)

# Default cache directory
DEFAULT_CACHE_DIR = "./data/image_cache"

# Supported image formats
SUPPORTED_FORMATS = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp'}

# Max image size for processing (to avoid memory issues)
MAX_IMAGE_SIZE = (1920, 1920)
THUMBNAIL_SIZE = (224, 224)  # CLIP input size


class ImageProcessor:
    """
    Image processing utility for multimodal tweet analysis.
    Handles downloading, caching, resizing, and basic analysis.
    """
    
    def __init__(
        self,
        cache_dir: str = DEFAULT_CACHE_DIR,
        max_workers: int = 4,
        timeout: int = 15
    ):
        """
        Initialize image processor.
        
        Args:
            cache_dir: Directory to cache downloaded images
            max_workers: Max parallel downloads
            timeout: Request timeout in seconds
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.max_workers = max_workers
        self.timeout = timeout
        
        # Stats
        self.stats = {
            "downloaded": 0,
            "cached": 0,
            "failed": 0,
        }
    
    def download_image(
        self,
        url: str,
        save_local: bool = True
    ) -> Optional[Image.Image]:
        """
        Download image from URL.
        
        Args:
            url: Image URL
            save_local: Whether to cache locally
        
        Returns:
            PIL Image or None if failed
        """
        try:
            # Check cache first
            cache_path = self._get_cache_path(url)
            if cache_path.exists():
                self.stats["cached"] += 1
                return Image.open(cache_path).convert("RGB")
            
            # Download
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            response = requests.get(url, headers=headers, timeout=self.timeout, stream=True)
            response.raise_for_status()
            
            # Verify content type
            content_type = response.headers.get("Content-Type", "")
            if not content_type.startswith("image/"):
                logger.warning(f"Non-image content type: {content_type}")
                return None
            
            # Load image
            image_data = BytesIO(response.content)
            image = Image.open(image_data).convert("RGB")
            
            # Resize if too large
            if image.size[0] > MAX_IMAGE_SIZE[0] or image.size[1] > MAX_IMAGE_SIZE[1]:
                image.thumbnail(MAX_IMAGE_SIZE, Image.Resampling.LANCZOS)
            
            # Cache locally
            if save_local:
                self._save_to_cache(image, cache_path)
            
            self.stats["downloaded"] += 1
            return image
            
        except requests.RequestException as e:
            logger.warning(f"Failed to download image {url}: {e}")
            self.stats["failed"] += 1
            return None
        except Exception as e:
            logger.error(f"Error processing image {url}: {e}")
            self.stats["failed"] += 1
            return None
    
    def download_batch(
        self,
        urls: List[str],
        save_local: bool = True
    ) -> Dict[str, Optional[Image.Image]]:
        """
        Download multiple images in parallel.
        
        Args:
            urls: List of image URLs
            save_local: Whether to cache locally
        
        Returns:
            Dict mapping URL to PIL Image (or None if failed)
        """
        results = {}
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_url = {
                executor.submit(self.download_image, url, save_local): url
                for url in urls
            }
            
            for future in as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    results[url] = future.result()
                except Exception as e:
                    logger.error(f"Error downloading {url}: {e}")
                    results[url] = None
        
        return results
    
    def analyze_image(
        self,
        image: Image.Image
    ) -> Dict[str, Any]:
        """
        Analyze image for various features.
        
        Args:
            image: PIL Image
        
        Returns:
            Dict with analysis results
        """
        analysis = {
            "width": image.width,
            "height": image.height,
            "format": image.format,
            "mode": image.mode,
            "aspect_ratio": round(image.width / image.height, 2),
        }
        
        # Get dominant colors
        try:
            analysis["dominant_colors"] = self._get_dominant_colors(image)
        except Exception:
            analysis["dominant_colors"] = []
        
        # Check for text presence (simple heuristic)
        try:
            analysis["likely_contains_text"] = self._check_text_presence(image)
        except Exception:
            analysis["likely_contains_text"] = None
        
        # Image statistics
        try:
            stat = ImageStat.Stat(image)
            analysis["brightness"] = round(sum(stat.mean) / 3, 2)
            analysis["contrast"] = round(sum(stat.stddev) / 3, 2)
        except Exception:
            pass
        
        # Detect if likely screenshot/meme
        try:
            analysis["image_type"] = self._detect_image_type(image, analysis)
        except Exception:
            analysis["image_type"] = "unknown"
        
        return analysis
    
    def prepare_for_clip(
        self,
        image: Image.Image
    ) -> Image.Image:
        """
        Prepare image for CLIP encoding.
        
        Args:
            image: PIL Image
        
        Returns:
            Resized RGB image ready for CLIP
        """
        # Ensure RGB
        if image.mode != "RGB":
            image = image.convert("RGB")
        
        # Resize to CLIP input size
        image = image.resize(THUMBNAIL_SIZE, Image.Resampling.LANCZOS)
        
        return image
    
    def get_image_hash(self, image: Image.Image) -> str:
        """Generate unique hash for an image."""
        return hashlib.md5(image.tobytes()).hexdigest()
    
    def _get_cache_path(self, url: str) -> Path:
        """Generate cache file path for URL."""
        url_hash = hashlib.md5(url.encode()).hexdigest()
        # Get extension from URL
        ext = Path(url.split("?")[0]).suffix.lower()
        if ext not in SUPPORTED_FORMATS:
            ext = ".jpg"
        return self.cache_dir / f"{url_hash}{ext}"
    
    def _save_to_cache(self, image: Image.Image, path: Path) -> None:
        """Save image to cache."""
        try:
            image.save(path, quality=90)
        except Exception as e:
            logger.warning(f"Failed to cache image: {e}")
    
    def _get_dominant_colors(
        self,
        image: Image.Image,
        num_colors: int = 3
    ) -> List[str]:
        """Extract dominant colors as hex strings."""
        # Resize for faster processing
        small = image.copy()
        small.thumbnail((100, 100))
        
        # Quantize to get palette
        quantized = small.quantize(colors=num_colors)
        palette = quantized.getpalette()
        
        # Extract top colors
        colors = []
        for i in range(num_colors):
            r, g, b = palette[i*3:(i+1)*3]
            colors.append(f"#{r:02x}{g:02x}{b:02x}")
        
        return colors
    
    def _check_text_presence(self, image: Image.Image) -> bool:
        """
        Simple heuristic to detect if image likely contains text.
        Uses edge detection - text-heavy images have more edges.
        """
        # Convert to grayscale
        gray = image.convert("L")
        
        # Apply edge detection
        edges = gray.filter(ImageFilter.FIND_EDGES)
        
        # Calculate edge density
        edge_array = np.array(edges)
        edge_density = np.mean(edge_array > 50)  # Threshold for edge pixels
        
        # Text-heavy images typically have edge density > 0.1
        return edge_density > 0.1
    
    def _detect_image_type(
        self,
        image: Image.Image,
        analysis: Dict[str, Any]
    ) -> str:
        """Detect type of image (photo, screenshot, meme, etc.)."""
        width, height = image.size
        aspect = analysis.get("aspect_ratio", 1.0)
        
        # Screenshot detection: usually specific aspect ratios
        if aspect in [1.78, 2.17, 2.16]:  # 16:9, phone ratios
            if analysis.get("likely_contains_text", False):
                return "screenshot"
        
        # Infographic: tall images with lots of text
        if height > width * 2 and analysis.get("likely_contains_text", False):
            return "infographic"
        
        # Meme: square-ish with text
        if 0.8 < aspect < 1.3 and analysis.get("likely_contains_text", False):
            return "meme"
        
        # Default to photo
        return "photo"
    
    def clear_cache(self) -> int:
        """Clear image cache. Returns number of files deleted."""
        count = 0
        for f in self.cache_dir.iterdir():
            if f.is_file():
                f.unlink()
                count += 1
        return count
    
    def get_stats(self) -> Dict[str, int]:
        """Get download statistics."""
        return self.stats.copy()


# Convenience functions

def download_image(url: str, cache: bool = True) -> Optional[Image.Image]:
    """Download a single image."""
    processor = ImageProcessor()
    return processor.download_image(url, save_local=cache)


def analyze_image(image: Image.Image) -> Dict[str, Any]:
    """Analyze a single image."""
    processor = ImageProcessor()
    return processor.analyze_image(image)


def process_tweet_images(
    image_urls: List[str],
    cache_dir: str = DEFAULT_CACHE_DIR
) -> List[Dict[str, Any]]:
    """
    Process all images from a tweet.
    
    Args:
        image_urls: List of image URLs from tweet
        cache_dir: Cache directory
    
    Returns:
        List of processed image data dicts
    """
    processor = ImageProcessor(cache_dir=cache_dir)
    results = []
    
    # Download all images
    images = processor.download_batch(image_urls)
    
    for url, image in images.items():
        if image is None:
            results.append({
                "url": url,
                "success": False,
                "error": "Download failed"
            })
            continue
        
        # Analyze image
        analysis = processor.analyze_image(image)
        
        # Prepare for CLIP
        clip_ready = processor.prepare_for_clip(image)
        
        results.append({
            "url": url,
            "success": True,
            "image": clip_ready,
            "analysis": analysis,
            "local_path": str(processor._get_cache_path(url)),
        })
    
    return results

