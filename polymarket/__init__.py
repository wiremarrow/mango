"""
Polymarket Data Extraction Library

A Python library for extracting historical price data from Polymarket prediction markets.
"""

__version__ = "1.0.0"
__author__ = "Polymarket Data Team"

from .models import Market, Event, PriceHistory, PricePoint, MarketHistoricalData, TimeInterval, EventHistoricalData
from .api import PolymarketAPI
from .parser import PolymarketURLParser
from .processor import DataProcessor
from .orderbook import OrderBook, OrderLevel, MarketOrderBooks
from .data_api import DataAPIClient

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
]