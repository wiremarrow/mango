"""
Polymarket Data Extraction Library

A Python library for extracting historical price data from Polymarket prediction markets.
"""

__version__ = "1.0.0"
__author__ = "Polymarket Data Team"

from .models import Market, Event, PriceHistory, PricePoint, MarketHistoricalData, TimeInterval
from .api import PolymarketAPI
from .parser import PolymarketURLParser
from .processor import DataProcessor

__all__ = [
    "Market",
    "Event",
    "PriceHistory", 
    "PricePoint",
    "MarketHistoricalData",
    "TimeInterval",
    "PolymarketAPI",
    "PolymarketURLParser",
    "DataProcessor",
]