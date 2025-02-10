from dataclasses import dataclass
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from ..utils.config import Config

@dataclass
class ItemOrder:
    platinum: float
    quantity: int
    order_type: str
    user_status: str
    
    @classmethod
    def from_api(cls, order_data: Dict):
        return cls(
            platinum=float(order_data['platinum']),
            quantity=int(order_data['quantity']),
            order_type=order_data['order_type'],
            user_status=order_data['user']['status']
        )

@dataclass
class ItemAnalysis:
    url_name: str
    name: str
    lowest_sell: float
    highest_buy: float
    potential_profit: float
    roi_percentage: float
    daily_volume: float
    buy_orders_count: int
    sell_orders_count: int
    
    @property
    def is_profitable(self) -> bool:
        return (
            self.potential_profit >= Config.MIN_PROFIT_MARGIN and
            self.roi_percentage >= Config.MIN_ROI_PERCENTAGE and
            self.daily_volume >= Config.MIN_DAILY_VOLUME
        )

class Item:
    def __init__(self, url_name: str, name: str = None, max_price: float = None):
        self.url_name = url_name
        self.name = name or url_name
        self.max_price = max_price
        self.orders_cache = None
        self.stats_cache = None
        self.cache_time = None
        self.cache_duration = timedelta(seconds=Config.CACHE_DURATION_SECONDS)
    
    def update_data(self, api) -> None:
        """Update item data from API if cache is expired"""
        current_time = datetime.now()
        
        if (not self.cache_time or 
            current_time - self.cache_time > self.cache_duration):
            self.orders_cache = api.get_orders(self.url_name)
            self.stats_cache = api.get_statistics(self.url_name)
            self.cache_time = current_time
    
    def analyze(self) -> Optional['ItemAnalysis']:
        """Analyze current market data for trading opportunities"""
        if not self.orders_cache or not self.stats_cache:
            return None
            
        # Filter active buy/sell orders
        buy_orders = [
            order for order in self.orders_cache
            if (order['order_type'] == 'buy' and 
                order['user']['status'] == 'ingame' and
                not order['user']['id'].startswith('bot'))
        ]
        
        sell_orders = [
            order for order in self.orders_cache
            if (order['order_type'] == 'sell' and
                order['user']['status'] == 'ingame' and
                not order['user']['id'].startswith('bot'))
        ]
        
        if not buy_orders or not sell_orders:
            return None
            
        # Get highest buy and lowest sell prices
        highest_buy = max(float(order['platinum']) for order in buy_orders)
        
        # Skip if buy price is above budget
        if self.max_price and highest_buy > self.max_price:
            return None
            
        lowest_sell = min(float(order['platinum']) for order in sell_orders)
        
        # Calculate potential profit
        potential_profit = lowest_sell - highest_buy
        
        # Calculate ROI percentage
        roi_percentage = (potential_profit / highest_buy) * 100 if highest_buy > 0 else 0
        
        # Calculate daily volume from statistics
        try:
            # Get the 48h statistics
            if isinstance(self.stats_cache, dict):
                daily_stats = self.stats_cache.get('48hours', [])
            else:
                daily_stats = self.stats_cache

            if daily_stats:
                total_volume = sum(stat.get('volume', 0) for stat in daily_stats)
                daily_volume = total_volume / 2  # Convert 48h to daily average
            else:
                daily_volume = 0
            
        except Exception as e:
            print(f"Error calculating volume for {self.name}: {self.stats_cache}")
            daily_volume = 0
        
        return ItemAnalysis(
            url_name=self.url_name,
            name=self.name,
            lowest_sell=lowest_sell,
            highest_buy=highest_buy,
            potential_profit=potential_profit,
            roi_percentage=roi_percentage,
            daily_volume=daily_volume,
            buy_orders_count=len(buy_orders),
            sell_orders_count=len(sell_orders)
        )