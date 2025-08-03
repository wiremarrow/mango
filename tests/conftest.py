"""
Pytest configuration and shared fixtures.
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, MagicMock

from polymarket.models.models import Market, Event, PriceHistory, PricePoint
from polymarket.models.orderbook import OrderBook, OrderLevel


@pytest.fixture
def sample_market():
    """Create a sample market for testing."""
    return Market(
        id="market-123",
        slug="will-btc-hit-100k-2024",
        condition_id="0x123abc",
        question="Will Bitcoin hit $100k in 2024?",
        outcomes=["Yes", "No"],
        token_ids=["0xtoken1", "0xtoken2"],
        active=True,
        volume=1000000.0,
        liquidity=500000.0,
        neg_risk=False
    )


@pytest.fixture
def sample_negrisk_market():
    """Create a sample negRisk market for testing."""
    return Market(
        id="negrisk-123",
        slug="person-n-win-2028",
        condition_id="0x456def",
        question="Will Person N win the 2028 election?",
        outcomes=["Yes", "No"],
        token_ids=["", ""],  # Empty token IDs for inactive option
        active=False,
        neg_risk=True,
        neg_risk_market_id="election-2028",
        group_item_title="Person N"
    )


@pytest.fixture
def sample_event():
    """Create a sample event for testing."""
    return Event(
        id="event-123",
        slug="presidential-election-2028",
        title="2028 US Presidential Election",
        description="Who will win the 2028 US Presidential Election?",
        markets=[],
        liquidity=10000000.0,
        volume=50000000.0,
        active=True
    )


@pytest.fixture
def sample_price_history():
    """Create sample price history data."""
    price_points = [
        PricePoint(
            timestamp=datetime(2024, 1, 1, 0, 0),
            price=0.45
        ),
        PricePoint(
            timestamp=datetime(2024, 1, 1, 1, 0),
            price=0.46
        ),
        PricePoint(
            timestamp=datetime(2024, 1, 1, 2, 0),
            price=0.44
        ),
    ]
    
    return PriceHistory(
        market_id="market-123",
        token_id="0xtoken1",
        outcome="Yes",
        interval="1h",
        price_points=price_points
    )


@pytest.fixture
def sample_order_book():
    """Create a sample order book."""
    bids = [
        OrderLevel(price=0.45, size=1000),
        OrderLevel(price=0.44, size=2000),
        OrderLevel(price=0.43, size=3000),
    ]
    
    asks = [
        OrderLevel(price=0.46, size=1500),
        OrderLevel(price=0.47, size=2500),
        OrderLevel(price=0.48, size=3500),
    ]
    
    return OrderBook(
        market_id="market-123",
        outcome="Yes",
        bids=bids,
        asks=asks,
        timestamp=datetime.now()
    )


@pytest.fixture
def mock_api_response():
    """Create a mock API response."""
    return {
        "id": "market-123",
        "slug": "will-btc-hit-100k-2024",
        "conditionId": "0x123abc",
        "question": "Will Bitcoin hit $100k in 2024?",
        "outcomes": ["Yes", "No"],
        "tokenIds": ["0xtoken1", "0xtoken2"],
        "active": True,
        "volume": "1000000.0",
        "liquidity": "500000.0"
    }


@pytest.fixture
def mock_httpx_client():
    """Create a mock httpx client."""
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {}
    mock_response.raise_for_status = MagicMock()
    mock_client.get.return_value = mock_response
    mock_client.post.return_value = mock_response
    return mock_client


@pytest.fixture
def valid_market_urls():
    """Valid Polymarket URLs for testing."""
    return [
        "https://polymarket.com/event/presidential-election-2028/will-jd-vance-win",
        "https://polymarket.com/market/will-btc-hit-100k",
        "https://polymarket.com/will-btc-hit-100k",
    ]


@pytest.fixture
def valid_event_urls():
    """Valid event URLs for testing."""
    return [
        "https://polymarket.com/event/presidential-election-2028",
        "https://polymarket.com/event/english-premier-league-winner",
    ]


@pytest.fixture
def invalid_urls():
    """Invalid URLs for testing."""
    return [
        "https://example.com/market",
        "not-a-url",
        "https://polymarket.com/",
        "",
    ]