"""
Polymarket Data Extraction Library

A Python library for extracting historical price data from Polymarket prediction markets.
"""

__version__ = "1.0.0"
__author__ = "Polymarket Data Team"

from .models import Market, Event, PriceHistory, PricePoint, MarketHistoricalData, TimeInterval, EventHistoricalData
from .models.orderbook import OrderBook, OrderLevel, MarketOrderBooks
from .api import PolymarketAPI
from .api.data_api import DataAPIClient
from .utils.parser import PolymarketURLParser
from .utils.processor import DataProcessor
from .utils import get_column_prefix, format_price, format_volume
from .cli.extractor import PolymarketExtractor
from .cli.cli_output import CLIReporter

__all__ = [
    "Market",
    "Event",
    "PriceHistory", 
    "PricePoint",
    "MarketHistoricalData",
    "EventHistoricalData",
    "TimeInterval",
    "PolymarketAPI",
    "PolymarketURLParser",
    "DataProcessor",
    "OrderBook",
    "OrderLevel",
    "MarketOrderBooks",
    "DataAPIClient",
    "PolymarketExtractor",
    "CLIReporter",
    "get_column_prefix",
    "format_price",
    "format_volume",
]