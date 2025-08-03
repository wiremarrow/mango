"""
Unit tests for data models.
"""

import pytest
from datetime import datetime
from polymarket.models.models import (
    Market, Event, PriceHistory, PricePoint, 
    MarketHistoricalData, EventHistoricalData, TimeInterval
)
from polymarket.models.orderbook import OrderBook, OrderLevel, MarketOrderBooks


class TestPricePoint:
    """Test PricePoint model."""
    
    def test_initialization(self):
        """Test PricePoint initialization."""
        timestamp = datetime(2024, 1, 1, 12, 0)
        pp = PricePoint(timestamp=timestamp, price=0.45)
        
        assert pp.timestamp == timestamp
        assert pp.price == 0.45
    
    def test_from_api_data(self):
        """Test creating PricePoint from API data."""
        data = {"t": 1704110400, "p": 0.45}
        pp = PricePoint.from_api_data(data)
        
        assert pp.price == 0.45
        assert isinstance(pp.timestamp, datetime)


class TestPriceHistory:
    """Test PriceHistory model."""
    
    def test_initialization(self):
        """Test PriceHistory initialization."""
        price_points = [
            PricePoint(timestamp=datetime(2024, 1, 1, i), price=0.45 + i * 0.01)
            for i in range(5)
        ]
        
        history = PriceHistory(
            market_id="market-123",
            token_id="0xtoken1",
            outcome="Yes",
            interval="1h",
            price_points=price_points
        )
        
        assert history.market_id == "market-123"
        assert history.token_id == "0xtoken1"
        assert history.outcome == "Yes"
        assert history.interval == "1h"
        assert len(history.price_points) == 5
    
    def test_properties(self):
        """Test computed properties."""
        price_points = [
            PricePoint(timestamp=datetime(2024, 1, 1, 0), price=0.40),
            PricePoint(timestamp=datetime(2024, 1, 1, 1), price=0.45),
            PricePoint(timestamp=datetime(2024, 1, 1, 2), price=0.50),
        ]
        
        history = PriceHistory(
            market_id="1",
            token_id="0x1",
            outcome="Yes",
            interval="1h",
            price_points=price_points
        )
        
        assert history.data_points_count == 3
        assert history.latest_price == 0.50
        assert history.oldest_price == 0.40
        assert history.price_change == 0.10
        assert history.price_change_percent == 25.0
    
    def test_empty_history(self):
        """Test properties with empty history."""
        history = PriceHistory(
            market_id="1",
            token_id="0x1",
            outcome="Yes",
            interval="1h",
            price_points=[]
        )
        
        assert history.data_points_count == 0
        assert history.latest_price == 0.0
        assert history.oldest_price == 0.0
        assert history.price_change is None
        assert history.price_change_percent == 0.0


class TestMarket:
    """Test Market model."""
    
    def test_basic_initialization(self):
        """Test basic Market initialization."""
        market = Market(
            id="market-123",
            slug="will-btc-hit-100k",
            condition_id="0x123abc",
            question="Will Bitcoin hit $100k?",
            outcomes=["Yes", "No"],
            token_ids=["0xtoken1", "0xtoken2"]
        )
        
        assert market.id == "market-123"
        assert market.slug == "will-btc-hit-100k"
        assert market.condition_id == "0x123abc"
        assert market.question == "Will Bitcoin hit $100k?"
        assert market.outcomes == ["Yes", "No"]
        assert market.token_ids == ["0xtoken1", "0xtoken2"]
    
    def test_is_inactive_negrisk_option(self):
        """Test inactive negRisk option detection."""
        # Active regular market
        market1 = Market(
            id="1",
            slug="test",
            condition_id="0x1",
            question="Test?",
            outcomes=["Yes", "No"],
            token_ids=["0x1", "0x2"],
            neg_risk=False
        )
        assert market1.is_inactive_negrisk_option() is False
        
        # Inactive negRisk option
        market2 = Market(
            id="2",
            slug="test",
            condition_id="0x2",
            question="Test?",
            outcomes=["Yes", "No"],
            token_ids=["", ""],  # Empty token IDs
            neg_risk=True,
            neg_risk_market_id="group-123"
        )
        assert market2.is_inactive_negrisk_option() is True
        
        # Active negRisk option
        market3 = Market(
            id="3",
            slug="test",
            condition_id="0x3",
            question="Test?",
            outcomes=["Yes", "No"],
            token_ids=["0x1", "0x2"],  # Has token IDs
            neg_risk=True,
            neg_risk_market_id="group-123"
        )
        assert market3.is_inactive_negrisk_option() is False
    
    def test_from_gamma_api(self):
        """Test creating Market from Gamma API data."""
        data = {
            "id": "market-123",
            "slug": "will-btc-hit-100k",
            "conditionId": "0x123abc",
            "question": "Will Bitcoin hit $100k?",
            "outcomes": ["Yes", "No"],
            "outcomePrices": ["0.45", "0.55"],
            "volume": "1000000.0",
            "liquidity": "500000.0",
            "active": True,
            "closed": False,
            "marketType": "binary"
        }
        
        market = Market.from_gamma_api(data)
        
        assert market.id == "market-123"
        assert market.slug == "will-btc-hit-100k"
        assert market.condition_id == "0x123abc"
        assert market.volume == 1000000.0
        assert market.active is True
        assert market.closed is False


class TestOrderBook:
    """Test OrderBook model."""
    
    def test_initialization(self):
        """Test OrderBook initialization."""
        bids = [
            OrderLevel(price=0.45, size=1000),
            OrderLevel(price=0.44, size=2000),
        ]
        asks = [
            OrderLevel(price=0.46, size=1500),
            OrderLevel(price=0.47, size=2500),
        ]
        
        book = OrderBook(
            market_id="market-123",
            outcome="Yes",
            bids=bids,
            asks=asks,
            timestamp=datetime.now()
        )
        
        assert book.market_id == "market-123"
        assert book.outcome == "Yes"
        assert len(book.bids) == 2
        assert len(book.asks) == 2
    
    def test_properties(self):
        """Test computed properties."""
        bids = [
            OrderLevel(price=0.45, size=1000),
            OrderLevel(price=0.44, size=2000),
        ]
        asks = [
            OrderLevel(price=0.46, size=1500),
            OrderLevel(price=0.47, size=2500),
        ]
        
        book = OrderBook(
            market_id="1",
            outcome="Yes",
            bids=bids,
            asks=asks
        )
        
        assert book.best_bid.price == 0.45
        assert book.best_ask.price == 0.46
        assert book.mid_price == 0.455
        assert book.spread == 0.01
        assert abs(book.spread_percent - 2.198) < 0.01
    
    def test_empty_book(self):
        """Test properties with empty book."""
        book = OrderBook(
            market_id="1",
            outcome="Yes",
            bids=[],
            asks=[]
        )
        
        assert book.best_bid is None
        assert book.best_ask is None
        assert book.mid_price == 0.0
        assert book.spread == 0.0
        assert book.spread_percent == 0.0


class TestTimeInterval:
    """Test TimeInterval enum."""
    
    def test_string_values(self):
        """Test enum string values."""
        assert TimeInterval.ONE_MINUTE.value == "1m"
        assert TimeInterval.ONE_HOUR.value == "1h"
        assert TimeInterval.SIX_HOURS.value == "6h"
        assert TimeInterval.ONE_DAY.value == "1d"
        assert TimeInterval.ONE_WEEK.value == "1w"
        assert TimeInterval.MAX.value == "max"
    
    def test_from_string(self):
        """Test creating from string."""
        assert TimeInterval.from_string("1m") == TimeInterval.ONE_MINUTE
        assert TimeInterval.from_string("1h") == TimeInterval.ONE_HOUR
        assert TimeInterval.from_string("max") == TimeInterval.MAX
        
        # Invalid string returns the string itself
        assert TimeInterval.from_string("invalid") == "invalid"