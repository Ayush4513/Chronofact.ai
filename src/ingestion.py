"""
Chronofact.ai - Data Ingestion Module
Handles X data scraping using Selenium and mock data loading.
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


class XDataIngestor:
    """Ingests X data via Selenium or mock data."""
    
    def __init__(self, use_mock: bool = False):
        """Initialize ingestor.
        
        Args:
            use_mock: If True, use mock data instead of scraping
        """
        self.config = get_config()
        self.use_mock = use_mock
        self.driver = None
    
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
