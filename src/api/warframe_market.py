import requests
import time
import json
import os
from typing import Dict, List, Optional
from ..utils.config import Config
from datetime import datetime, timedelta
import random

class WarframeMarketAPI:
    def __init__(self):
        self.base_url = "https://api.warframe.market/v1"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'WarframeTrader/1.0',
            'Platform': 'pc',
            'Language': 'en'
        })
        self.cache = {}
        self.cache_duration = timedelta(seconds=Config.CACHE_DURATION_SECONDS)
        self.last_request_time = 0
        self.base_delay = Config.API_RATE_LIMIT_SECONDS
        self.jitter = 1.0
        self.retry_delay = 10
        self.max_retries = 3
        self._recent_failures = 0
        
        # Create cache directory if it doesn't exist
        self.cache_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'cache')
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # Clear old cache files
        self._cleanup_cache()
    
    def _cleanup_cache(self):
        """Clean up old cache files"""
        try:
            for file in os.listdir(self.cache_dir):
                if file.endswith('.cache'):
                    file_path = os.path.join(self.cache_dir, file)
                    try:
                        # Remove files older than 1 hour
                        if time.time() - os.path.getmtime(file_path) > 3600:
                            os.remove(file_path)
                    except:
                        pass
        except Exception as e:
            print(f"Error cleaning cache: {str(e)}")
    
    def _get_cache_file(self, item_url: str) -> str:
        """Get cache file path for an item"""
        return os.path.join(self.cache_dir, f"{item_url}.cache")
    
    def _load_cached_orders(self, item_url: str) -> Optional[tuple]:
        """Load cached orders for a specific item"""
        cache_file = self._get_cache_file(item_url)
        try:
            if os.path.exists(cache_file):
                with open(cache_file, 'r') as f:
                    data = json.load(f)
                    if time.time() - data['timestamp'] < 3600:  # 1 hour cache
                        return (data['orders'], datetime.fromtimestamp(data['timestamp']))
        except Exception as e:
            # Silently fail and return None
            pass
        return None
    
    def _save_cached_orders(self, item_url: str, orders: dict):
        """Save cached orders for a specific item"""
        cache_file = self._get_cache_file(item_url)
        try:
            with open(cache_file, 'w') as f:
                json.dump({
                    'timestamp': time.time(),
                    'orders': orders
                }, f)
        except Exception as e:
            # Silently fail
            pass
    
    def _rate_limit(self):
        """Implement rate limiting"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        # Add progressive delay based on recent failures
        extra_delay = min(self._recent_failures * 0.5, 5.0)
        delay = self.base_delay + random.random() * self.jitter + extra_delay
        
        if time_since_last < delay:
            time.sleep(delay - time_since_last)
        self.last_request_time = time.time()
    
    def _get_from_cache(self, cache_key: str) -> Optional[Dict]:
        """Get data from cache if valid"""
        if cache_key in self.cache:
            data, timestamp = self.cache[cache_key]
            if datetime.now() - timestamp < self.cache_duration:
                return data
            del self.cache[cache_key]
        return None
    
    def _store_in_cache(self, cache_key: str, data: Dict):
        """Store data in cache"""
        self.cache[cache_key] = (data, datetime.now())
    
    def _make_request(self, endpoint: str, retries: int = 0) -> Optional[Dict]:
        """Make API request with retry logic"""
        try:
            self._rate_limit()
            url = f"{self.base_url}/{endpoint}"
            response = self.session.get(url)
            
            if response.status_code == 200:
                self._recent_failures = max(0, self._recent_failures - 1)
                return response.json()
            elif response.status_code == 429 and retries < self.max_retries:
                self._recent_failures += 1
                wait_time = self.retry_delay * (retries + 1)
                print(f"Rate limited, adjusting delay and waiting {wait_time} seconds...")
                time.sleep(wait_time)
                return self._make_request(endpoint, retries + 1)
            else:
                print(f"HTTP error {response.status_code} for {url}")
                return None
                
        except Exception as e:
            print(f"Error accessing {url}: {str(e)}")
            return None
    
    def get_items_list(self) -> list:
        """Get list of all items with persistent caching"""
        cache_file = os.path.join(self.cache_dir, 'items_list.json')
        
        # Try to load from persistent cache first
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'r') as f:
                    cached_data = json.load(f)
                    cache_time = datetime.fromtimestamp(cached_data['timestamp'])
                    
                    # Check if cache is still valid (24 hours for items list)
                    if datetime.now() - cache_time < timedelta(hours=24):
                        return cached_data['items']
            except Exception as e:
                print(f"Error reading cache file: {str(e)}")
        
        # If no cache or expired, fetch from API
        response = self._make_request("items")
        
        if response and 'items' in response['payload']:
            items = response['payload']['items']
            
            # Save to persistent cache
            try:
                with open(cache_file, 'w') as f:
                    json.dump({
                        'timestamp': datetime.now().timestamp(),
                        'items': items
                    }, f)
            except Exception as e:
                print(f"Error writing cache file: {str(e)}")
            
            return items
        return []
    
    def get_item_orders(self, item_url_name: str) -> List[Dict]:
        """Get current orders for an item with filtering"""
        response = self._make_request(f"items/{item_url_name}/orders")
        if response and 'payload' in response:
            orders = response['payload']['orders']
            # Filter out inactive orders
            return [order for order in orders if order.get('user', {}).get('status') == 'ingame']
        return []
    
    def get_item_statistics(self, item_url_name: str) -> Dict:
        """Get 90-day statistics for an item with validation"""
        response = self._make_request(f"items/{item_url_name}/statistics")
        if response and 'payload' in response:
            stats = response['payload']['statistics_closed'].get('90days', {})
            # Validate statistics
            if isinstance(stats, list) and stats:
                return stats
        return []

    def get_item_details(self, item_url_name: str) -> Optional[Dict]:
        """Get detailed information about an item with validation"""
        response = self._make_request(f"items/{item_url_name}")
        if response and 'payload' in response and 'item' in response['payload']:
            return response['payload']['item']
        return None

    def get_orders(self, item_url: str) -> Optional[Dict]:
        """Get orders with per-item caching"""
        # Check memory cache first
        if item_url in self.cache:
            cached_data, cache_time = self.cache[item_url]
            if datetime.now() - cache_time < self.cache_duration:
                return cached_data
        
        # Check file cache
        cached_result = self._load_cached_orders(item_url)
        if cached_result:
            orders, cache_time = cached_result
            self.cache[item_url] = (orders, cache_time)
            return orders
        
        # Make API request
        response = self._make_request(f"items/{item_url}/orders")
        
        if response and 'orders' in response['payload']:
            orders = response['payload']['orders']
            self.cache[item_url] = (orders, datetime.now())
            self._save_cached_orders(item_url, orders)
            return orders
        return None
    
    def get_statistics(self, item_url: str) -> Optional[Dict]:
        """Get statistics for an item"""
        cache_key = f"stats_{item_url}"
        if cache_key in self.cache:
            cached_data, cache_time = self.cache[cache_key]
            if datetime.now() - cache_time < self.cache_duration:
                return cached_data
        
        response = self._make_request(f"items/{item_url}/statistics")
        
        if response and 'statistics_closed' in response['payload']:
            stats = response['payload']['statistics_closed']
            self.cache[cache_key] = (stats, datetime.now())
            return stats
        return None
    
    def cleanup(self):
        """Clean up resources"""
        if hasattr(self, 'session'):
            self.session.close()
        self.cache.clear()