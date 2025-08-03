"""
Unified data models for Polymarket data extraction.

This module contains all the data models used across the Polymarket library,
providing a consistent interface regardless of the underlying API.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any, Union
from enum import Enum


class TimeInterval(Enum):
    """Supported time intervals for historical data."""
    ONE_MINUTE = "1m"
    ONE_HOUR = "1h"
    SIX_HOURS = "6h"
    ONE_DAY = "1d"
    ONE_WEEK = "1w"
    MAX = "max"
    
    @classmethod
    def from_string(cls, value: str) -> 'TimeInterval':
        """Convert string to TimeInterval enum."""
        for interval in cls:
            if interval.value == value:
                return interval
        raise ValueError(f"Invalid interval: {value}")


@dataclass
class PricePoint:
    """Represents a single price point in time."""
    timestamp: datetime
    price: float
    
    @classmethod
    def from_api_response(cls, data: Dict[str, Any]) -> 'PricePoint':
        """Create a PricePoint from API response data."""
        return cls(
            timestamp=datetime.fromtimestamp(data['t']),
            price=float(data['p'])
        )


@dataclass
class PriceHistory:
    """Represents the complete price history for a market outcome."""
    market_id: str
    token_id: str
    outcome: str
    interval: TimeInterval
    start_time: Optional[datetime]
    end_time: Optional[datetime]
    price_points: List[PricePoint] = field(default_factory=list)
    
    @property
    def latest_price(self) -> Optional[float]:
        """Get the most recent price."""
        return self.price_points[-1].price if self.price_points else None
    
    @property
    def oldest_price(self) -> Optional[float]:
        """Get the oldest price."""
        return self.price_points[0].price if self.price_points else None
    
    @property
    def price_change(self) -> Optional[float]:
        """Calculate the price change from oldest to newest."""
        if len(self.price_points) >= 2:
            return self.latest_price - self.oldest_price
        return None
    
    @property
    def price_change_percent(self) -> Optional[float]:
        """Calculate the percentage price change."""
        if self.oldest_price and self.oldest_price != 0 and self.price_change is not None:
            return (self.price_change / self.oldest_price) * 100
        return None
    
    @property
    def data_points_count(self) -> int:
        """Get the number of data points."""
        return len(self.price_points)


@dataclass
class Market:
    """
    Unified market representation across all Polymarket APIs.
    
    This class provides a consistent interface for market data regardless
    of whether it comes from CLOB, Gamma, or other APIs.
    """
    # Core identifiers
    slug: str
    condition_id: str
    question: str
    
    # Market details
    outcomes: List[str]
    token_ids: List[str]
    active: bool
    closed: bool
    
    # Optional metadata
    id: Optional[Union[int, str]] = None
    question_id: Optional[str] = None
    volume: float = 0.0
    liquidity: float = 0.0
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    archived: bool = False
    enable_order_book: bool = True
    
    # negRisk market fields
    neg_risk: bool = False
    neg_risk_market_id: Optional[str] = None
    group_item_title: Optional[str] = None
    
    # Additional fields for flexibility
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def is_inactive_negrisk_option(self) -> bool:
        """Check if this is an inactive option in a negRisk market."""
        return (
            self.neg_risk and 
            self.neg_risk_market_id and
            (not self.token_ids or all(not tid for tid in self.token_ids))
        )
    
    @classmethod
    def from_gamma_response(cls, data: Dict[str, Any]) -> 'Market':
        """Create a Market from Gamma API response."""
        # Parse dates
        start_date = None
        end_date = None
        if data.get('startDate'):
            try:
                start_date = datetime.fromisoformat(data['startDate'].replace('Z', '+00:00'))
            except:
                pass
        if data.get('endDate'):
            try:
                end_date = datetime.fromisoformat(data['endDate'].replace('Z', '+00:00'))
            except:
                pass
        
        # Parse token IDs from string representation
        token_ids = []
        if data.get('clobTokenIds'):
            import json
            try:
                token_ids = json.loads(data['clobTokenIds'])
            except:
                token_ids = data.get('clobTokenIds', [])
        
        # Parse outcomes
        outcomes = []
        if data.get('outcomes'):
            import json
            try:
                outcomes = json.loads(data['outcomes'])
            except:
                outcomes = data.get('outcomes', [])
        
        return cls(
            id=data.get('id'),
            slug=data.get('slug', ''),
            question=data.get('question', ''),
            condition_id=data.get('conditionId', ''),
            token_ids=token_ids,
            outcomes=outcomes,
            active=data.get('active', False),
            closed=data.get('closed', False),
            archived=data.get('archived', False),
            liquidity=float(data.get('liquidity', 0) or 0),
            volume=float(data.get('volume', 0) or 0),
            start_date=start_date,
            end_date=end_date,
            enable_order_book=data.get('enableOrderBook', True),
            neg_risk=data.get('negRisk', False),
            neg_risk_market_id=data.get('negRiskMarketID'),
            group_item_title=data.get('groupItemTitle'),
            metadata=data
        )
    
    @classmethod
    def from_clob_response(cls, data: Dict[str, Any]) -> 'Market':
        """Create a Market from CLOB API response."""
        import logging
        logger = logging.getLogger(__name__)
        
        # Debug log for negRisk markets
        if data.get('neg_risk'):
            logger.debug(f"Processing negRisk market: {data.get('market_slug')}")
            logger.debug(f"neg_risk_market_id: {data.get('neg_risk_market_id')}")
            logger.debug(f"tokens: {data.get('tokens', [])}")
        
        # Extract token IDs and outcomes from tokens array
        token_ids = []
        outcomes = []
        for token in data.get('tokens', []):
            token_id = token.get('token_id', '')
            outcome = token.get('outcome', '')
            # Only add non-empty token IDs
            if token_id and outcome:
                token_ids.append(token_id)
                outcomes.append(outcome)
        
        # Parse end date
        end_date = None
        if data.get('end_date_iso'):
            try:
                end_date = datetime.fromisoformat(data['end_date_iso'].replace('Z', '+00:00'))
            except:
                pass
        
        return cls(
            slug=data.get('market_slug', ''),
            condition_id=data.get('condition_id', ''),
            question_id=data.get('question_id'),
            question=data.get('question', ''),
            token_ids=token_ids,
            outcomes=outcomes,
            active=data.get('active', False),
            closed=data.get('closed', False),
            archived=data.get('archived', False),
            end_date=end_date,
            enable_order_book=data.get('enable_order_book', True),
            neg_risk=data.get('neg_risk', False),
            neg_risk_market_id=data.get('neg_risk_market_id'),
            group_item_title=data.get('group_item_title'),
            metadata=data
        )


@dataclass
class Event:
    """Represents a Polymarket event containing multiple markets."""
    id: str
    ticker: str
    slug: str
    title: str
    description: str
    markets: List[Market] = field(default_factory=list)
    active: bool = True
    closed: bool = False
    archived: bool = False
    featured: bool = False
    liquidity: float = 0.0
    volume: float = 0.0
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    neg_risk: bool = False
    neg_risk_market_id: Optional[str] = None
    
    @classmethod
    def from_gamma_response(cls, data: Dict[str, Any]) -> 'Event':
        """Create an Event from Gamma API response."""
        # Parse dates
        start_date = None
        end_date = None
        if data.get('startDate'):
            try:
                start_date = datetime.fromisoformat(data['startDate'].replace('Z', '+00:00'))
            except:
                pass
        if data.get('endDate'):
            try:
                end_date = datetime.fromisoformat(data['endDate'].replace('Z', '+00:00'))
            except:
                pass
        
        # Parse markets if present
        markets = []
        for market_data in data.get('markets', []):
            try:
                markets.append(Market.from_gamma_response(market_data))
            except:
                pass
        
        return cls(
            id=str(data.get('id', '')),
            ticker=data.get('ticker', ''),
            slug=data.get('slug', ''),
            title=data.get('title', ''),
            description=data.get('description', ''),
            markets=markets,
            active=data.get('active', True),
            closed=data.get('closed', False),
            archived=data.get('archived', False),
            featured=data.get('featured', False),
            liquidity=float(data.get('liquidity', 0) or 0),
            volume=float(data.get('volume', 0) or 0),
            start_date=start_date,
            end_date=end_date,
            neg_risk=data.get('negRisk', False),
            neg_risk_market_id=data.get('negRiskMarketID')
        )


@dataclass
class MarketHistoricalData:
    """Complete historical data for a market including all outcomes."""
    market: Market
    price_histories: Dict[str, PriceHistory]
    extracted_at: datetime = field(default_factory=datetime.now)
    
    @property
    def has_data(self) -> bool:
        """Check if any price history data is available."""
        return any(history.price_points for history in self.price_histories.values())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format for serialization."""
        return {
            'market': {
                'id': self.market.id,
                'slug': self.market.slug,
                'question': self.market.question,
                'condition_id': self.market.condition_id,
                'outcomes': self.market.outcomes,
                'active': self.market.active,
                'volume': self.market.volume,
                'liquidity': self.market.liquidity,
            },
            'price_data': {
                outcome: {
                    'token_id': history.token_id,
                    'latest_price': history.latest_price,
                    'oldest_price': history.oldest_price,
                    'price_change': history.price_change,
                    'price_change_percent': history.price_change_percent,
                    'data_points': history.data_points_count,
                    'prices': [
                        {
                            'timestamp': point.timestamp.isoformat(),
                            'price': point.price
                        }
                        for point in history.price_points
                    ]
                }
                for outcome, history in self.price_histories.items()
            },
            'extracted_at': self.extracted_at.isoformat()
        }


@dataclass
class EventHistoricalData:
    """Complete historical data for all markets in an event."""
    event: Event
    market_data: Dict[str, MarketHistoricalData] = field(default_factory=dict)
    extracted_at: datetime = field(default_factory=datetime.now)
    
    @property
    def total_markets(self) -> int:
        """Total number of markets with data."""
        return len(self.market_data)
    
    @property
    def has_data(self) -> bool:
        """Check if any market has data."""
        return any(data.has_data for data in self.market_data.values())
    
    def get_aligned_timestamps(self) -> List[datetime]:
        """Get all unique timestamps across all markets, sorted."""
        all_timestamps = set()
        for market_data in self.market_data.values():
            for history in market_data.price_histories.values():
                for point in history.price_points:
                    all_timestamps.add(point.timestamp)
        return sorted(all_timestamps)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'event': {
                'id': self.event.id,
                'title': self.event.title,
                'slug': self.event.slug,
                'description': self.event.description,
                'neg_risk': self.event.neg_risk,
                'total_markets': self.total_markets
            },
            'market_data': {
                market_slug: data.to_dict()
                for market_slug, data in self.market_data.items()
            },
            'extracted_at': self.extracted_at.isoformat()
        }