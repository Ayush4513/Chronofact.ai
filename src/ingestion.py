"""
Chronofact.ai - Data Ingestion Module
Handles X data ingestion using multiple sources:
1. Legal data pipeline (academic datasets + synthetic generation) - RECOMMENDED
2. Mock data from CSV files
3. Selenium scraping (NOT RECOMMENDED - may violate ToS)
"""

import time
from typing import List, Dict, Optional
import pandas as pd

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

from .config import get_config

logger = None


def get_logger():
    global logger
    if logger is None:
        import logging
        logger = logging.getLogger(__name__)
    return logger


class LegalDataIngestor:
    """
    Ingests data using 100% legal sources.
    
    This is the RECOMMENDED approach for hackathon demos:
    - Uses academic datasets from HuggingFace
    - Generates synthetic data with LLM
    - Event-focused timelines for realistic demos
    """
    
    def __init__(self):
        """Initialize legal data ingestor."""
        self.config = get_config()
        self._pipeline = None
    
    @property
    def pipeline(self):
        """Lazy load the pipeline."""
        if self._pipeline is None:
            from .data import LegalDataPipeline
            self._pipeline = LegalDataPipeline(
                google_api_key=self.config.google_ai.api_key
            )
        return self._pipeline
    
    def collect(
        self,
        query: str,
        max_results: int = 100,
        strategy: str = "auto"
    ) -> pd.DataFrame:
        """
        Collect data for a query using legal sources.
        
        Args:
            query: Search query (e.g., "Mumbai floods", "Indian elections 2024")
            max_results: Maximum number of results to return
            strategy: Collection strategy
                - "auto": Automatically select best source
                - "academic": Use academic datasets only
                - "synthetic": Generate synthetic data
                - "event": Use event-focused generation
                - "hybrid": Mix all sources
        
        Returns:
            DataFrame of collected data
        """
        get_logger().info(f"Collecting legal data for: {query}")
        
        try:
            tweets = self.pipeline.collect_data(
                query=query,
                num_results=max_results,
                strategy=strategy
            )
            
            # Convert to DataFrame
            df = pd.DataFrame(tweets)
            
            # Ensure required columns exist
            required_cols = [
                "tweet_id", "text", "author", "timestamp",
                "fave_count", "retweet_count", "is_verified",
                "media_urls", "location", "credibility_score"
            ]
            for col in required_cols:
                if col not in df.columns:
                    df[col] = None
            
            get_logger().info(f"Collected {len(df)} legal data points")
            return df
            
        except Exception as e:
            get_logger().error(f"Failed to collect legal data: {e}")
            return self._create_empty_dataframe()
    
    def get_data_summary(self, df: pd.DataFrame) -> Dict:
        """Get summary of collected data."""
        if df.empty:
            return {"total": 0}
        
        return {
            "total": len(df),
            "with_images": len(df[df["media_urls"].apply(lambda x: bool(x) if x else False)]),
            "verified": len(df[df["is_verified"] == True]),
            "avg_credibility": df["credibility_score"].mean() if "credibility_score" in df else 0,
            "date_range": {
                "start": df["timestamp"].min() if "timestamp" in df else None,
                "end": df["timestamp"].max() if "timestamp" in df else None,
            }
        }
    
    def _create_empty_dataframe(self) -> pd.DataFrame:
        """Create empty DataFrame with required columns."""
        return pd.DataFrame(columns=[
            "tweet_id", "text", "author", "timestamp",
            "fave_count", "retweet_count", "is_verified",
            "media_urls", "location", "credibility_score"
        ])


class XDataIngestor:
    """
    Ingests X data via multiple methods (in order of preference):
    1. Legal data pipeline (academic + synthetic)
    2. Mock data from CSV
    3. Selenium scraping (NOT RECOMMENDED)
    """
    
    def __init__(self, use_mock: bool = False, use_legal: bool = True):
        """Initialize ingestor.
        
        Args:
            use_mock: If True, use mock data instead of scraping
            use_legal: If True, prefer legal data pipeline (RECOMMENDED)
        """
        self.config = get_config()
        self.use_mock = use_mock
        self.use_legal = use_legal
        self.driver = None
        self._legal_ingestor = None
    
    @property
    def legal_ingestor(self):
        """Lazy load legal ingestor."""
        if self._legal_ingestor is None:
            self._legal_ingestor = LegalDataIngestor()
        return self._legal_ingestor
    
    def ingest(
        self,
        query: str,
        max_results: int = 100,
        strategy: str = "auto"
    ) -> pd.DataFrame:
        """
        Main entry point for data ingestion.
        
        Automatically selects the best data source:
        1. Legal data pipeline (if use_legal=True)
        2. Mock data (if use_mock=True)
        3. Selenium scraping (fallback, not recommended)
        
        Args:
            query: Search query
            max_results: Maximum results
            strategy: Strategy for legal pipeline
        
        Returns:
            DataFrame of ingested data
        """
        if self.use_legal:
            get_logger().info("Using legal data pipeline (RECOMMENDED)")
            return self.legal_ingestor.collect(query, max_results, strategy)
        
        if self.use_mock:
            get_logger().info("Using mock data")
            return self.load_mock_data()
        
        # Fallback to scraping (NOT RECOMMENDED)
        get_logger().warning("Using Selenium scraping - NOT RECOMMENDED for production")
        try:
            return self.scrape_topic(query, max_results)
        except Exception as e:
            get_logger().error(f"Scraping failed: {e}. Falling back to legal data.")
            return self.legal_ingestor.collect(query, max_results, strategy)
    
    def scrape_topic(
        self,
        topic: str,
        max_posts: Optional[int] = None,
        headless: Optional[bool] = None
    ) -> pd.DataFrame:
        """
        Scrape X posts for a topic using Selenium.
        
        Args:
            topic: Search topic or hashtag
            max_posts: Maximum number of posts to scrape
            headless: Whether to run browser in headless mode
        
        Returns:
            DataFrame of scraped posts
        """
        if max_posts is None:
            max_posts = self.config.selenium.max_posts
        
        if headless is None:
            headless = self.config.selenium.headless
        
        get_logger().info(f"Scraping X for topic: {topic}")
        
        try:
            self._setup_driver(headless)
            posts = self._scrape_posts(topic, max_posts)
            
            get_logger().info(f"Scraped {len(posts)} posts")
            return pd.DataFrame(posts)
            
        finally:
            if self.driver:
                self.driver.quit()
    
    def load_mock_data(
        self,
        filepath: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Load mock X data from CSV.
        
        Args:
            filepath: Path to CSV file
        
        Returns:
            DataFrame of mock posts
        """
        if filepath is None:
            filepath = str(self.config.mock_data_path)
        
        get_logger().info(f"Loading mock data from: {filepath}")
        
        try:
            df = pd.read_csv(filepath)
            get_logger().info(f"Loaded {len(df)} mock posts")
            return df
        except FileNotFoundError:
            get_logger().warning(f"Mock data file not found: {filepath}")
            get_logger().info("Creating empty DataFrame with required columns")
            return self._create_empty_dataframe()
    
    def _setup_driver(self, headless: bool) -> None:
        """Setup Selenium Chrome driver."""
        chrome_options = Options()
        
        if headless:
            chrome_options.add_argument("--headless")
        
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument(
            "user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        
        service = Service(ChromeDriverManager().install())
        
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.driver.set_page_load_timeout(self.config.selenium.timeout)
    
    def _scrape_posts(
        self,
        topic: str,
        max_posts: int
    ) -> List[Dict]:
        """Scrape posts from X search page."""
        search_url = f"https://x.com/search?q={topic}&src=typed_query&f=live"
        
        self.driver.get(search_url)
        time.sleep(3)
        
        posts = []
        scroll_count = 0
        
        while len(posts) < max_posts:
            tweet_elements = self.driver.find_elements(
                By.CSS_SELECTOR, 
                '[data-testid="tweet"]'
            )
            
            get_logger().debug(f"Found {len(tweet_elements)} tweets on page")
            
            for tweet in tweet_elements:
                if len(posts) >= max_posts:
                    break
                
                try:
                    post_data = self._extract_tweet_data(tweet)
                    if post_data:
                        posts.append(post_data)
                except Exception as e:
                    get_logger().warning(f"Error extracting tweet: {e}")
                    continue
            
            if len(posts) >= max_posts:
                break
            
            scroll_count += 1
            if scroll_count > 10:
                break
            
            get_logger().debug(f"Scrolling... ({len(posts)} posts so far)")
            self.driver.execute_script(
                "window.scrollTo(0, document.body.scrollHeight);"
            )
            time.sleep(2)
        
        return posts[:max_posts]
    
    def _extract_tweet_data(self, tweet_element) -> Optional[Dict]:
        """Extract data from a tweet element."""
        try:
            tweet_id = tweet_element.get_attribute("data-tweet-id") or "unknown"
            
            text_elem = tweet_element.find_element(By.CSS_SELECTOR, '[data-testid="tweetText"]')
            text = text_elem.text if text_elem else ""
            
            author_elem = tweet_element.find_element(By.CSS_SELECTOR, '[data-testid="User-Name"]')
            author = author_elem.text if author_elem else "unknown"
            
            verified_elem = tweet_element.find_elements(By.CSS_SELECTOR, '[data-testid="icon-verified"]')
            is_verified = len(verified_elem) > 0
            
            timestamp_elem = tweet_element.find_element(By.TIME)
            timestamp = timestamp_elem.get_attribute("datetime") if timestamp_elem else ""
            
            fave_count = self._extract_count(tweet_element, "favorite")
            retweet_count = self._extract_count(tweet_element, "retweet")
            
            media_urls = self._extract_media_urls(tweet_element)
            
            return {
                "tweet_id": tweet_id,
                "text": text,
                "author": author,
                "timestamp": timestamp,
                "fave_count": fave_count,
                "retweet_count": retweet_count,
                "is_verified": is_verified,
                "media_urls": media_urls,
                "location": None,
                "credibility_score": 0.0
            }
            
        except Exception as e:
            get_logger().debug(f"Failed to extract tweet data: {e}")
            return None
    
    def _extract_count(self, tweet_element, count_type: str) -> int:
        """Extract like/retweet count."""
        try:
            elem = tweet_element.find_element(
                By.CSS_SELECTOR, 
                f'[data-testid="{count_type}"]'
            )
            count_str = elem.get_attribute("aria-label") or "0"
            return self._parse_count(count_str)
        except Exception:
            return 0
    
    def _parse_count(self, count_str: str) -> int:
        """Parse count string to integer."""
        try:
            count_str = count_str.lower().replace(",", "").replace("k", "000")
            if "m" in count_str:
                count_str = count_str.replace("m", "") + "000000"
            return int(float(count_str))
        except Exception:
            return 0
    
    def _extract_media_urls(self, tweet_element) -> List[str]:
        """Extract image/video URLs."""
        urls = []
        try:
            media_elems = tweet_element.find_elements(
                By.CSS_SELECTOR,
                '[data-testid="tweetPhoto"] img, [data-testid="videoPlayer"] img'
            )
            for elem in media_elems[:4]:
                src = elem.get_attribute("src")
                if src:
                    urls.append(src)
        except Exception:
            pass
        return urls
    
    def _create_empty_dataframe(self) -> pd.DataFrame:
        """Create empty DataFrame with required columns."""
        return pd.DataFrame(columns=[
            "tweet_id", "text", "author", "timestamp",
            "fave_count", "retweet_count", "is_verified",
            "media_urls", "location", "credibility_score"
        ])


def create_sample_mock_data(filepath: str = "./data/sample_x_data.csv") -> None:
    """
    Create a sample CSV file with mock X data.
    
    Args:
        filepath: Path to save the CSV file
    """
    import os
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    
    data = [
        {
            "tweet_id": "1234567890",
            "text": "Breaking: Heavy rainfall expected in Mumbai over the next 48 hours. #MumbaiRains",
            "author": "MumbaiWeather",
            "timestamp": "2026-01-21T10:30:00Z",
            "fave_count": 1250,
            "retweet_count": 450,
            "is_verified": True,
            "media_urls": "[]",
            "location": "Mumbai",
            "credibility_score": 0.85
        },
        {
            "tweet_id": "1234567891",
            "text": "Flood warning issued for low-lying areas. Citizens advised to stay indoors. #Mumbai",
            "author": "BMC_Official",
            "timestamp": "2026-01-21T11:15:00Z",
            "fave_count": 3400,
            "retweet_count": 890,
            "is_verified": True,
            "media_urls": "['https://example.com/flood-map.jpg']",
            "location": "Mumbai",
            "credibility_score": 0.92
        },
        {
            "tweet_id": "1234567892",
            "text": "I just heard schools are closing tomorrow due to heavy rains! #Breaking",
            "author": "randomuser123",
            "timestamp": "2026-01-21T11:30:00Z",
            "fave_count": 45,
            "retweet_count": 12,
            "is_verified": False,
            "media_urls": "[]",
            "location": None,
            "credibility_score": 0.35
        },
        {
            "tweet_id": "1234567893",
            "text": "Indian Meteorological Department forecasts 200mm rainfall in 24 hours #WeatherAlert",
            "author": "IMD_Updates",
            "timestamp": "2026-01-21T09:00:00Z",
            "fave_count": 8900,
            "retweet_count": 2100,
            "is_verified": True,
            "media_urls": "[]",
            "location": "Mumbai",
            "credibility_score": 0.95
        }
    ]
    
    df = pd.DataFrame(data)
    df.to_csv(filepath, index=False)
    print(f"Created sample mock data: {filepath}")


# Convenience functions for easy access

def collect_legal_data(
    query: str,
    num_results: int = 100,
    strategy: str = "auto"
) -> pd.DataFrame:
    """
    Convenience function to collect legal data.
    
    Args:
        query: Search query (e.g., "Mumbai floods", "Indian elections")
        num_results: Number of results
        strategy: Collection strategy (auto, academic, synthetic, event, hybrid)
    
    Returns:
        DataFrame of collected data
    """
    ingestor = LegalDataIngestor()
    return ingestor.collect(query, num_results, strategy)


def get_available_events() -> List[str]:
    """Get list of available pre-defined events for demo."""
    from .data import EventDataGenerator
    generator = EventDataGenerator()
    return generator.get_available_events()


def get_available_datasets() -> List[str]:
    """Get list of available academic datasets."""
    from .data import AcademicTwitterData
    return AcademicTwitterData().get_available_datasets()
