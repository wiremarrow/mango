"""
Unit tests for API clients.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime
import httpx

from polymarket.api.api import BaseAPIClient, CLOBAPIClient, GammaAPIClient, PolymarketAPI
from polymarket.api.data_api import DataAPIClient
from polymarket.models.models import Market, Event, PriceHistory, TimeInterval
from polymarket.models.orderbook import OrderBook
from polymarket.utils.exceptions import APIError, RateLimitError, MarketNotFoundError


class TestBaseAPIClient:
    """Test BaseAPIClient class."""
    
    def test_initialization(self):
        """Test client initialization."""
        client = BaseAPIClient("https://api.example.com", api_key="test-key")
        
        assert client.base_url == "https://api.example.com"
        assert client.api_key == "test-key"
        assert isinstance(client.client, httpx.Client)
    
    @patch('httpx.Client.get')
    def test_get_request(self, mock_get):
        """Test GET request."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"result": "success"}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        client = BaseAPIClient("https://api.example.com")
        result = client._get("/test")
        
        assert result == {"result": "success"}
        mock_get.assert_called_once()
    
    @patch('httpx.Client.get')
    def test_rate_limit_error(self, mock_get):
        """Test rate limit error handling."""
        mock_response = Mock()
        mock_response.status_code = 429
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "429 Too Many Requests",
            request=Mock(),
            response=mock_response
        )
        mock_get.return_value = mock_response
        
        client = BaseAPIClient("https://api.example.com")
        
        with pytest.raises(RateLimitError):
            client._get("/test")
    
    def test_close(self):
        """Test client closure."""
        client = BaseAPIClient("https://api.example.com")
        client.close()
        # Should not raise any errors


class TestCLOBAPIClient:
    """Test CLOBAPIClient class."""
    
    @patch('polymarket.api.api.BaseAPIClient._get')
    def test_search_markets(self, mock_get):
        """Test market search."""
        mock_get.return_value = {
            "markets": [
                {
                    "condition_id": "0x123",
                    "question": "Test market?",
                    "outcomes": ["Yes", "No"],
                    "tokens": [{"token_id": "0x1"}, {"token_id": "0x2"}],
                    "active": True
                }
            ]
        }
        
        client = CLOBAPIClient()
        markets = client.search_markets("test", limit=10)
        
        assert len(markets) == 1
        assert markets[0].question == "Test market?"
        assert markets[0].condition_id == "0x123"
    
    @patch('polymarket.api.api.BaseAPIClient._get')
    def test_get_price_history_individual_requests(self, mock_get):
        """Test price history with individual token requests."""
        # Mock responses for individual token price requests
        mock_get.side_effect = [
            {
                "history": [
                    {"t": 1704110400, "p": 0.45},
                    {"t": 1704114000, "p": 0.46}
                ]
            },
            {
                "history": [
                    {"t": 1704110400, "p": 0.55},
                    {"t": 1704114000, "p": 0.54}
                ]
            }
        ]
        
        market = Market(
            id="1",
            slug="test",
            condition_id="0x123",
            question="Test?",
            outcomes=["Yes", "No"],
            token_ids=["0xtoken1", "0xtoken2"]
        )
        
        client = CLOBAPIClient()
        histories = client.get_price_history(
            market,
            interval=TimeInterval.ONE_HOUR,
            start_ts=1704110400,
            end_ts=1704117600
        )
        
        assert len(histories) == 2
        assert "Yes" in histories
        assert "No" in histories
        assert len(histories["Yes"].price_points) == 2
        assert histories["Yes"].price_points[0].price == 0.45
    
    @patch('polymarket.api.api.BaseAPIClient._get')
    def test_get_order_books(self, mock_get):
        """Test getting order books."""
        mock_get.return_value = {
            "0xtoken1": {
                "bids": [{"price": "0.45", "size": "1000"}],
                "asks": [{"price": "0.46", "size": "1500"}]
            },
            "0xtoken2": {
                "bids": [{"price": "0.54", "size": "2000"}],
                "asks": [{"price": "0.55", "size": "2500"}]
            }
        }
        
        market = Market(
            id="1",
            slug="test",
            condition_id="0x123",
            question="Test?",
            outcomes=["Yes", "No"],
            token_ids=["0xtoken1", "0xtoken2"]
        )
        
        client = CLOBAPIClient()
        order_books = client.get_order_books(market)
        
        assert "Yes" in order_books.books
        assert "No" in order_books.books
        assert order_books.books["Yes"].best_bid.price == 0.45
        assert order_books.books["No"].best_ask.price == 0.55


class TestGammaAPIClient:
    """Test GammaAPIClient class."""
    
    @patch('polymarket.api.api.BaseAPIClient._get')
    def test_get_market(self, mock_get):
        """Test getting market by slug."""
        mock_get.return_value = {
            "id": "market-123",
            "slug": "test-market",
            "conditionId": "0x123",
            "question": "Test market?",
            "outcomes": ["Yes", "No"],
            "active": True,
            "volume": "1000000"
        }
        
        client = GammaAPIClient()
        market = client.get_market("test-market")
        
        assert market.id == "market-123"
        assert market.slug == "test-market"
        assert market.question == "Test market?"
        assert market.volume == 1000000.0
    
    @patch('polymarket.api.api.BaseAPIClient._get')
    def test_get_event(self, mock_get):
        """Test getting event by slug."""
        mock_get.return_value = {
            "id": "event-123",
            "slug": "test-event",
            "title": "Test Event",
            "description": "Test description",
            "markets": [
                {
                    "id": "market-1",
                    "slug": "market-1",
                    "conditionId": "0x1",
                    "question": "Market 1?",
                    "outcomes": ["Yes", "No"]
                }
            ],
            "liquidity": "10000000",
            "volume": "50000000"
        }
        
        client = GammaAPIClient()
        event = client.get_event("test-event")
        
        assert event.id == "event-123"
        assert event.slug == "test-event"
        assert event.title == "Test Event"
        assert len(event.markets) == 1
        assert event.liquidity == 10000000.0


class TestDataAPIClient:
    """Test DataAPIClient class."""
    
    @patch('polymarket.api.data_api.BaseAPIClient._get')
    def test_get_user_positions(self, mock_get):
        """Test getting user positions."""
        mock_get.return_value = {
            "positions": [
                {
                    "market": {
                        "condition_id": "0x123",
                        "question": "Test market?",
                        "slug": "test-market"
                    },
                    "outcome": "Yes",
                    "size": "1000",
                    "average_price": "0.45",
                    "current_price": "0.50",
                    "value": "500",
                    "pnl": "50"
                }
            ]
        }
        
        client = DataAPIClient()
        positions = client.get_user_positions("0xuser123")
        
        assert len(positions) == 1
        assert positions[0]["size"] == 1000.0
        assert positions[0]["current_value"] == 500.0
        assert positions[0]["pnl"] == 50.0
    
    @patch('polymarket.api.data_api.BaseAPIClient._get')
    def test_get_market_holders(self, mock_get):
        """Test getting market holders."""
        mock_get.return_value = {
            "holders": [
                {
                    "user": "0xholder1",
                    "outcome": "Yes",
                    "size": "10000",
                    "value": "5000"
                },
                {
                    "user": "0xholder2",
                    "outcome": "Yes",
                    "size": "5000",
                    "value": "2500"
                }
            ]
        }
        
        client = DataAPIClient()
        holders = client.get_market_holders("0x123", outcome="Yes")
        
        assert len(holders) == 2
        assert holders[0]["size"] == 10000.0
        assert holders[1]["size"] == 5000.0


class TestPolymarketAPI:
    """Test unified PolymarketAPI class."""
    
    @patch('polymarket.api.api.CLOBAPIClient.get_market')
    def test_get_market_clob_success(self, mock_clob_get):
        """Test getting market with CLOB success."""
        mock_market = Market(
            id="1",
            slug="test",
            condition_id="0x123",
            question="Test?",
            outcomes=["Yes", "No"],
            token_ids=["0x1", "0x2"]
        )
        mock_clob_get.return_value = mock_market
        
        api = PolymarketAPI()
        market = api.get_market("test")
        
        assert market.slug == "test"
        mock_clob_get.assert_called_once_with("test")
    
    @patch('polymarket.api.api.CLOBAPIClient.get_market')
    @patch('polymarket.api.api.GammaAPIClient.get_market')
    def test_get_market_fallback_to_gamma(self, mock_gamma_get, mock_clob_get):
        """Test fallback to Gamma API when CLOB fails."""
        mock_clob_get.return_value = None
        
        mock_market = Market(
            id="1",
            slug="test",
            condition_id="0x123",
            question="Test?",
            outcomes=["Yes", "No"]
        )
        mock_gamma_get.return_value = mock_market
        
        api = PolymarketAPI()
        market = api.get_market("test")
        
        assert market.slug == "test"
        mock_clob_get.assert_called_once()
        mock_gamma_get.assert_called_once()