"""
Integration tests for PolymarketExtractor.
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime

from polymarket.cli.extractor import PolymarketExtractor
from polymarket.models.models import Market, Event, PriceHistory, PricePoint
from polymarket.utils.exceptions import InvalidURLError, MarketNotFoundError


class TestPolymarketExtractor:
    """Test PolymarketExtractor class."""
    
    def setup_method(self):
        """Set up test instance."""
        self.extractor = PolymarketExtractor(api_key="test-key", verbose=True)
    
    @patch('polymarket.api.api.CLOBAPIClient.get_market')
    @patch('polymarket.api.api.CLOBAPIClient.get_price_history')
    def test_extract_from_market_url_success(self, mock_get_history, mock_get_market):
        """Test successful extraction from market URL."""
        # Mock market
        mock_market = Market(
            id="market-123",
            slug="will-btc-hit-100k",
            condition_id="0x123",
            question="Will Bitcoin hit $100k?",
            outcomes=["Yes", "No"],
            token_ids=["0xtoken1", "0xtoken2"],
            active=True,
            volume=1000000.0
        )
        mock_get_market.return_value = mock_market
        
        # Mock price history
        price_points = [
            PricePoint(timestamp=datetime(2024, 1, 1, i), price=0.45 + i * 0.01)
            for i in range(3)
        ]
        
        mock_get_history.return_value = {
            "Yes": PriceHistory(
                market_id="market-123",
                token_id="0xtoken1",
                outcome="Yes",
                interval="1h",
                price_points=price_points
            ),
            "No": PriceHistory(
                market_id="market-123",
                token_id="0xtoken2",
                outcome="No",
                interval="1h",
                price_points=price_points
            )
        }
        
        # Extract data
        result = self.extractor.extract_from_url(
            "https://polymarket.com/will-btc-hit-100k",
            interval="1h",
            days_back=1
        )
        
        assert result is not None
        assert result.market.slug == "will-btc-hit-100k"
        assert len(result.price_histories) == 2
        assert result.has_data is True
    
    @patch('polymarket.api.api.GammaAPIClient.get_event')
    def test_extract_from_event_url_shows_markets(self, mock_get_event):
        """Test that event URLs show available markets."""
        # Mock event with markets
        mock_event = Event(
            id="event-123",
            slug="presidential-election-2028",
            title="2028 US Presidential Election",
            description="Who will win?",
            markets=[
                Market(
                    id="1",
                    slug="candidate-a-win",
                    condition_id="0x1",
                    question="Will Candidate A win?",
                    outcomes=["Yes", "No"],
                    token_ids=["0x1", "0x2"]
                ),
                Market(
                    id="2",
                    slug="candidate-b-win",
                    condition_id="0x2",
                    question="Will Candidate B win?",
                    outcomes=["Yes", "No"],
                    token_ids=["0x3", "0x4"]
                )
            ]
        )
        mock_get_event.return_value = mock_event
        
        # Should return None but display markets
        result = self.extractor.extract_from_url(
            "https://polymarket.com/event/presidential-election-2028"
        )
        
        assert result is None  # Event URLs don't extract data
    
    def test_extract_from_invalid_url(self):
        """Test extraction with invalid URL."""
        result = self.extractor.extract_from_url("https://example.com/market")
        assert result is None
    
    @patch('polymarket.api.api.CLOBAPIClient.get_market')
    def test_extract_market_not_found(self, mock_get_market):
        """Test extraction when market not found."""
        mock_get_market.return_value = None
        
        result = self.extractor.extract_from_url(
            "https://polymarket.com/non-existent-market"
        )
        
        assert result is None
    
    @patch('polymarket.api.api.CLOBAPIClient.get_market')
    def test_extract_inactive_negrisk_market(self, mock_get_market):
        """Test extraction of inactive negRisk market."""
        # Mock inactive negRisk market
        mock_market = Market(
            id="market-123",
            slug="person-n-win",
            condition_id="0x123",
            question="Will Person N win?",
            outcomes=["Yes", "No"],
            token_ids=["", ""],  # Empty token IDs
            active=False,
            neg_risk=True,
            neg_risk_market_id="election-2028"
        )
        mock_get_market.return_value = mock_market
        
        result = self.extractor.extract_from_url(
            "https://polymarket.com/event/election-2028/person-n-win"
        )
        
        assert result is None  # Should fail validation
    
    @patch('polymarket.api.api.GammaAPIClient.get_event')
    @patch('polymarket.api.api.CLOBAPIClient.get_price_history')
    def test_extract_all_event_markets(self, mock_get_history, mock_get_event):
        """Test extracting all markets from an event."""
        # Mock event with multiple markets
        mock_event = Event(
            id="event-123",
            slug="premier-league",
            title="Premier League Winner",
            description="Who will win?",
            markets=[
                Market(
                    id="1",
                    slug="liverpool-win",
                    condition_id="0x1",
                    question="Will Liverpool win?",
                    outcomes=["Yes", "No"],
                    token_ids=["0x1", "0x2"],
                    group_item_title="Liverpool"
                ),
                Market(
                    id="2",
                    slug="chelsea-win",
                    condition_id="0x2",
                    question="Will Chelsea win?",
                    outcomes=["Yes", "No"],
                    token_ids=["0x3", "0x4"],
                    group_item_title="Chelsea"
                ),
                Market(
                    id="3",
                    slug="placeholder-team",
                    condition_id="0x3",
                    question="Will Placeholder win?",
                    outcomes=["Yes", "No"],
                    token_ids=["", ""],  # Inactive
                    neg_risk=True,
                    neg_risk_market_id="premier-league"
                )
            ]
        )
        mock_get_event.return_value = mock_event
        
        # Mock price histories
        price_points = [
            PricePoint(timestamp=datetime(2024, 1, 1, 0), price=0.30),
            PricePoint(timestamp=datetime(2024, 1, 1, 1), price=0.31),
        ]
        
        mock_get_history.return_value = {
            "Yes": PriceHistory(
                market_id="",
                token_id="",
                outcome="Yes",
                interval="1h",
                price_points=price_points
            )
        }
        
        # Extract all markets
        result = self.extractor.extract_all_event_markets(
            "premier-league",
            interval="1h",
            days_back=1,
            enable_gc=True
        )
        
        assert result is not None
        assert result.event.slug == "premier-league"
        assert result.total_markets == 2  # Only active markets
        assert "liverpool-win" in result.market_data
        assert "chelsea-win" in result.market_data
        assert "placeholder-team" not in result.market_data  # Skipped
    
    @patch('polymarket.api.api.CLOBAPIClient.get_price_history')
    def test_retry_logic_on_interval_too_long(self, mock_get_history):
        """Test retry logic when interval is too long."""
        # First call fails, second succeeds
        mock_get_history.side_effect = [
            Exception("invalid filters: 'startTs' and 'endTs' interval is too long"),
            {
                "Yes": PriceHistory(
                    market_id="1",
                    token_id="0x1",
                    outcome="Yes",
                    interval="1h",
                    price_points=[
                        PricePoint(timestamp=datetime(2024, 1, 1), price=0.5)
                    ]
                )
            }
        ]
        
        market = Market(
            id="1",
            slug="test",
            condition_id="0x1",
            question="Test?",
            outcomes=["Yes", "No"],
            token_ids=["0x1", "0x2"]
        )
        
        # Should retry with reduced time range
        histories = self.extractor._fetch_price_history_with_retry(
            market, "1h", 
            int(datetime(2024, 1, 1).timestamp()),
            int(datetime(2024, 1, 31).timestamp())
        )
        
        assert histories is not None
        assert "Yes" in histories
    
    def test_close(self):
        """Test closing the extractor."""
        self.extractor.close()
        # Should not raise any errors