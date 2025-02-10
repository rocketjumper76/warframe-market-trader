import os
from dataclasses import dataclass, field
from typing import Dict
import json
from pathlib import Path
import sys
from datetime import timedelta

@dataclass
class Config:
    # API Configuration
    BASE_URL: str = "https://api.warframe.market/v1"
    PLATFORM: str = "pc"
    LANGUAGE: str = "en"
    
    # Rate Limiting
    MAX_REQUESTS_PER_MINUTE: int = 180
    REQUEST_TIMEOUT: int = 10  # seconds
    
    # Trading Configuration
    MIN_PROFIT_MARGIN: float = 5.0  # platinum
    MIN_ROI_PERCENTAGE: float = 15.0  # %
    MIN_DAILY_VOLUME: float = 3.0  # trades
    MIN_BUY_ORDERS: int = 3
    MIN_SELL_ORDERS: int = 3
    MAX_VOLATILITY: float = 0.2
    MAX_BUDGET: float = 100.0  # Default budget
    
    # Cache Configuration
    CACHE_DURATION_SECONDS: int = 300  # 5 minutes
    CACHE_DIR: str = ".cache"
    API_RATE_LIMIT_SECONDS: float = 2.0
    
    # UI Configuration
    REFRESH_INTERVAL: int = 60  # seconds
    DARK_MODE_COLORS: Dict = field(default_factory=lambda: {
        'background': '#1E1E1E',
        'foreground': '#FFFFFF',
        'accent': '#007ACC',
        'secondary': '#252526',
        'hover': '#2D2D2D',
        'success': '#00C853',
        'warning': '#FFD700',
        'error': '#FF3D00'
    })
    
    LIGHT_MODE_COLORS: Dict = field(default_factory=lambda: {
        'background': '#FFFFFF',
        'foreground': '#2C2C2C',
        'accent': '#0078D4',
        'secondary': '#F5F5F5',
        'hover': '#E5E5E5',
        'success': '#00C853',
        'warning': '#FFA000',
        'error': '#D32F2F'
    })
    
    # Add performance settings
    WORKER_THREADS: int = 3
    BATCH_UPDATE_SIZE: int = 10
    BATCH_UPDATE_INTERVAL: float = 0.1
    
    # Add memory management
    MAX_CACHE_ITEMS: int = 1000
    CLEANUP_INTERVAL_SECONDS: int = 1800  # 30 minutes
    
    @classmethod
    def get_headers(cls) -> Dict[str, str]:
        """Get headers for API requests"""
        return {
            "Platform": cls.PLATFORM,
            "Language": cls.LANGUAGE,
            "accept": "application/json",
            "User-Agent": "WarframeTrader/1.0"
        }
    
    @classmethod
    def load_user_config(cls) -> None:
        """Load user configuration from file"""
        config_path = Path.home() / '.warframe_trader' / 'config.json'
        
        if config_path.exists():
            try:
                with open(config_path, 'r') as f:
                    user_config = json.load(f)
                
                # Update configuration with user values
                for key, value in user_config.items():
                    if hasattr(cls, key):
                        setattr(cls, key, value)
            except Exception as e:
                print(f"Error loading user config: {str(e)}")
    
    @classmethod
    def save_user_config(cls) -> None:
        """Save current configuration to file"""
        config_path = Path.home() / '.warframe_trader' / 'config.json'
        
        # Create directory if it doesn't exist
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            # Get all non-private attributes
            config_dict = {
                key: value for key, value in cls.__dict__.items()
                if not key.startswith('_') and not callable(value)
            }
            
            with open(config_path, 'w') as f:
                json.dump(config_dict, f, indent=4)
        except Exception as e:
            print(f"Error saving user config: {str(e)}")
    
    @classmethod
    def ensure_cache_dir(cls) -> None:
        """Ensure cache directory exists"""
        cache_path = Path(cls.CACHE_DIR)
        cache_path.mkdir(parents=True, exist_ok=True)
    
    @classmethod
    def clear_cache(cls) -> None:
        """Clear the cache directory"""
        cache_path = Path(cls.CACHE_DIR)
        if cache_path.exists():
            for file in cache_path.glob('*'):
                try:
                    file.unlink()
                except Exception as e:
                    print(f"Error deleting cache file {file}: {str(e)}")
    
    @classmethod
    def validate_config(cls) -> bool:
        """Validate configuration values"""
        try:
            assert cls.MIN_PROFIT_MARGIN > 0, "Minimum profit margin must be positive"
            assert cls.MIN_ROI_PERCENTAGE > 0, "Minimum ROI percentage must be positive"
            assert cls.MIN_DAILY_VOLUME >= 0, "Minimum daily volume cannot be negative"
            assert cls.MIN_BUY_ORDERS > 0, "Minimum buy orders must be positive"
            assert cls.MIN_SELL_ORDERS > 0, "Minimum sell orders must be positive"
            assert 0 <= cls.MAX_VOLATILITY <= 1, "Volatility must be between 0 and 1"
            assert cls.CACHE_DURATION_SECONDS > 0, "Cache duration must be positive"
            assert cls.MAX_REQUESTS_PER_MINUTE > 0, "Max requests per minute must be positive"
            return True
        except AssertionError as e:
            print(f"Configuration validation failed: {str(e)}")
            return False
    
    @classmethod
    def update_budget(cls, new_budget: float):
        """Update the maximum budget"""
        cls.MAX_BUDGET = float(new_budget)

def get_asset_path(filename: str) -> str:
    """Get correct path for assets in both script and exe modes"""
    if hasattr(sys, '_MEIPASS'):
        # Running as exe
        return os.path.join(sys._MEIPASS, 'assets', filename)
    else:
        # Running as script
        return os.path.join(os.path.dirname(__file__), '..', '..', 'assets', filename)