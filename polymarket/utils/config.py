"""
Configuration constants and settings for the Polymarket library.

This module contains all configuration values used throughout the library,
making it easy to adjust settings in one place.
"""

import os
from typing import Optional


# API Endpoints
CLOB_BASE_URL = os.getenv("POLYMARKET_CLOB_URL", "https://clob.polymarket.com")
GAMMA_BASE_URL = os.getenv("POLYMARKET_GAMMA_URL", "https://gamma-api.polymarket.com")
DATA_API_URL = os.getenv("POLYMARKET_DATA_API_URL", "https://data-api.polymarket.com")

# HTTP Client Settings
DEFAULT_TIMEOUT = float(os.getenv("POLYMARKET_TIMEOUT", "30.0"))
MAX_RETRIES = int(os.getenv("POLYMARKET_MAX_RETRIES", "3"))
RETRY_DELAY = float(os.getenv("POLYMARKET_RETRY_DELAY", "1.0"))
USER_AGENT = os.getenv("POLYMARKET_USER_AGENT", "PolymarketDataExtractor/1.0")

# API Keys
DEFAULT_API_KEY: Optional[str] = os.getenv("POLYMARKET_API_KEY")

# Data Processing Settings
DEFAULT_DAYS_BACK = int(os.getenv("POLYMARKET_DEFAULT_DAYS", "30"))
DEFAULT_INTERVAL = os.getenv("POLYMARKET_DEFAULT_INTERVAL", "1d")
MAX_PRICE_POINTS = int(os.getenv("POLYMARKET_MAX_POINTS", "10000"))

# Export Settings removed - CSV is the only format

# Logging Configuration
LOG_LEVEL = os.getenv("POLYMARKET_LOG_LEVEL", "INFO")
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Market Discovery Settings
MARKET_SEARCH_LIMIT = int(os.getenv("POLYMARKET_SEARCH_LIMIT", "20"))
EVENT_MARKETS_LIMIT = int(os.getenv("POLYMARKET_EVENT_MARKETS_LIMIT", "100"))

# Polygon Chain Configuration
POLYGON_CHAIN_ID = 137
POLYGON_RPC_URL = os.getenv("POLYGON_RPC_URL", "https://polygon-rpc.com")

# File Size Limits
MAX_CSV_SIZE_MB = int(os.getenv("POLYMARKET_MAX_CSV_MB", "100"))

# Rate Limiting
RATE_LIMIT_CALLS_PER_MINUTE = int(os.getenv("POLYMARKET_RATE_LIMIT", "60"))

# Cache Settings
ENABLE_CACHE = os.getenv("POLYMARKET_ENABLE_CACHE", "false").lower() == "true"
CACHE_TTL_SECONDS = int(os.getenv("POLYMARKET_CACHE_TTL", "300"))

# Validation Settings
MIN_PRICE = 0.0
MAX_PRICE = 1.0
PRICE_PRECISION = 4