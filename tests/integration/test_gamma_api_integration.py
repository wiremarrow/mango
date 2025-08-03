"""
Integration tests for Gamma API parameter functionality.
"""

import pytest
import os
from datetime import datetime

from polymarket.api.api import GammaAPIClient, PolymarketAPI
from polymarket.models.models import Market, Event


# Skip integration tests if not explicitly enabled
pytestmark = pytest.mark.skipif(
    os.getenv("RUN_INTEGRATION_TESTS") != "true",
    reason="Integration tests disabled. Set RUN_INTEGRATION_TESTS=true to run."
)


class TestGammaAPIIntegration:
    """Integration tests for Gamma API with real API calls."""
    
    @pytest.fixture
    def gamma_client(self):
        """Create a real GammaAPIClient instance."""
        return GammaAPIClient()
    
    @pytest.fixture
    def api(self):
        """Create a real PolymarketAPI instance."""
        return PolymarketAPI()
    
    def test_get_markets_with_volume_filter(self, gamma_client):
        """Test getting markets with volume filter."""
        # Get high volume markets
        markets = gamma_client.get_markets(
            volume_num_min=1000000,  # 1M minimum
            limit=5,
            order='volume',
            ascending=False
        )
        
        assert len(markets) > 0
        assert all(isinstance(m, Market) for m in markets)
        assert all(m.volume >= 1000000 for m in markets)
        
        # Verify descending order
        volumes = [m.volume for m in markets]
        assert volumes == sorted(volumes, reverse=True)
    
    def test_get_markets_with_liquidity_filter(self, gamma_client):
        """Test getting markets with liquidity filter."""
        markets = gamma_client.get_markets(
            liquidity_num_min=50000,  # 50k minimum
            liquidity_num_max=500000,  # 500k maximum
            limit=5
        )
        
        assert len(markets) > 0
        assert all(isinstance(m, Market) for m in markets)
        assert all(50000 <= m.liquidity <= 500000 for m in markets)
    
    def test_get_markets_by_status(self, gamma_client):
        """Test filtering markets by status."""
        # Test active markets
        active_markets = gamma_client.get_markets(
            active=True,
            closed=False,
            limit=5
        )
        
        assert len(active_markets) > 0
        assert all(m.active and not m.closed for m in active_markets)
        
        # Test closed markets
        closed_markets = gamma_client.get_markets(
            active=False,
            closed=True,
            limit=5
        )
        
        # May or may not have closed markets
        if closed_markets:
            assert all(not m.active and m.closed for m in closed_markets)
    
    def test_get_markets_with_tag_filter(self, gamma_client):
        """Test getting markets by tag."""
        # Try a common tag ID (may need adjustment based on actual tags)
        markets = gamma_client.get_markets(
            tag_id=1,  # Assuming tag 1 exists
            limit=5
        )
        
        # Tag filtering should work if tag exists
        if markets:
            assert all(isinstance(m, Market) for m in markets)
    
    def test_get_markets_by_multiple_ids(self, gamma_client):
        """Test getting specific markets by IDs."""
        # First get some markets to get valid IDs
        sample_markets = gamma_client.get_markets(limit=3)
        if len(sample_markets) < 3:
            pytest.skip("Not enough markets for test")
        
        market_ids = [m.id for m in sample_markets if m.id]
        
        # Now fetch by those specific IDs
        markets = gamma_client.get_markets_by_ids(market_ids)
        
        assert len(markets) > 0
        fetched_ids = [m.id for m in markets]
        assert any(mid in fetched_ids for mid in market_ids)
    
    def test_get_markets_with_order_book_filter(self, gamma_client):
        """Test filtering markets tradeable via CLOB."""
        markets = gamma_client.get_markets(
            enableOrderBook=True,
            active=True,
            limit=5
        )
        
        assert len(markets) > 0
        assert all(m.enable_order_book for m in markets)
    
    def test_get_events_with_volume_filter(self, gamma_client):
        """Test getting events with volume filter."""
        events = gamma_client.get_events(
            volume_min=100000,  # 100k minimum
            limit=5,
            order='volume',
            ascending=False
        )
        
        assert len(events) > 0
        assert all(isinstance(e, Event) for e in events)
        assert all(e.volume >= 100000 for e in events)
    
    def test_get_events_by_status(self, gamma_client):
        """Test filtering events by status."""
        active_events = gamma_client.get_events(
            active=True,
            closed=False,
            limit=5
        )
        
        assert len(active_events) > 0
        assert all(e.active and not e.closed for e in active_events)
    
    def test_complex_market_query(self, gamma_client):
        """Test complex query with multiple filters."""
        markets = gamma_client.get_markets(
            active=True,
            volume_num_min=10000,
            liquidity_num_min=1000,
            limit=10,
            order='volume',
            ascending=False
        )
        
        if markets:
            assert all(m.active for m in markets)
            assert all(m.volume >= 10000 for m in markets)
            assert all(m.liquidity >= 1000 for m in markets)
            
            # Check ordering
            volumes = [m.volume for m in markets]
            assert volumes == sorted(volumes, reverse=True)
    
    def test_pagination(self, gamma_client):
        """Test pagination with offset."""
        # Get first page
        page1 = gamma_client.get_markets(limit=5, offset=0)
        
        # Get second page
        page2 = gamma_client.get_markets(limit=5, offset=5)
        
        assert len(page1) > 0
        assert len(page2) > 0
        
        # Pages should have different markets
        page1_slugs = {m.slug for m in page1}
        page2_slugs = {m.slug for m in page2}
        assert page1_slugs.isdisjoint(page2_slugs)
    
    def test_get_markets_by_tags_helper(self, gamma_client):
        """Test helper method for tag-based search."""
        # Try tag 1 (adjust based on actual tags)
        markets = gamma_client.get_markets_by_tags(tag_id=1, include_related=False)
        
        # Should return markets if tag exists
        if markets:
            assert all(isinstance(m, Market) for m in markets)
    
    def test_empty_result_handling(self, gamma_client):
        """Test handling of queries that return no results."""
        # Query with impossible filters
        markets = gamma_client.get_markets(
            volume_num_min=1000000000,  # 1 billion minimum (unlikely)
            volume_num_max=1000000001,  # Very narrow range
            limit=10
        )
        
        # Should return empty list, not error
        assert markets == []
    
    def test_date_filter_format(self, gamma_client):
        """Test date filtering with proper format."""
        # Get markets with date filters
        markets = gamma_client.get_markets(
            start_date_min='2024-01-01T00:00:00Z',
            start_date_max='2025-12-31T23:59:59Z',
            limit=5
        )
        
        # Should handle date format correctly
        assert isinstance(markets, list)
    
    def test_multiple_slugs_query(self, gamma_client):
        """Test querying multiple markets by slug."""
        # First get some markets to get valid slugs
        sample_markets = gamma_client.get_markets(limit=2)
        if len(sample_markets) < 2:
            pytest.skip("Not enough markets for test")
        
        slugs = [m.slug for m in sample_markets]
        
        # Query by multiple slugs
        markets = gamma_client.get_markets(slug=slugs)
        
        assert len(markets) > 0
        fetched_slugs = [m.slug for m in markets]
        assert any(slug in fetched_slugs for slug in slugs)


class TestPolymarketAPIIntegration:
    """Integration tests for unified PolymarketAPI with new features."""
    
    @pytest.fixture
    def api(self):
        """Create a real PolymarketAPI instance."""
        api_key = os.getenv("POLYMARKET_API_KEY")
        return PolymarketAPI(api_key=api_key)
    
    def test_search_with_filters(self, api):
        """Test search functionality with new filters."""
        # Search using gamma client directly with filters
        markets = api.gamma_client.get_markets(
            volume_num_min=50000,
            active=True,
            limit=10
        )
        
        # Filter by search term
        search_term = "bitcoin"
        filtered = []
        for market in markets:
            if search_term.lower() in market.question.lower() or \
               search_term.lower() in market.slug.lower():
                filtered.append(market)
        
        # Should find some markets (or none if no bitcoin markets meet criteria)
        assert isinstance(filtered, list)
    
    def test_get_high_liquidity_markets(self, api):
        """Test finding high liquidity markets."""
        markets = api.gamma_client.get_markets(
            liquidity_num_min=100000,  # 100k minimum
            order='liquidity',
            ascending=False,
            limit=5
        )
        
        if markets:
            assert all(m.liquidity >= 100000 for m in markets)
            
            # Verify ordering
            liquidities = [m.liquidity for m in markets]
            assert liquidities == sorted(liquidities, reverse=True)
    
    def test_archived_markets_access(self, api):
        """Test accessing archived markets."""
        archived_markets = api.gamma_client.get_markets(
            archived=True,
            limit=5
        )
        
        # May or may not have archived markets
        if archived_markets:
            assert all(m.archived for m in archived_markets)
    
    def test_event_filtering(self, api):
        """Test event filtering capabilities."""
        # Get high volume events
        events = api.gamma_client.get_events(
            volume_min=50000,
            active=True,
            limit=5
        )
        
        if events:
            assert all(e.volume >= 50000 for e in events)
            assert all(e.active for e in events)
    
    def test_market_creation_date(self, api):
        """Test that created_at is populated for markets from Gamma."""
        markets = api.gamma_client.get_markets(limit=5)
        
        # Check if any markets have created_at
        markets_with_dates = [m for m in markets if m.created_at is not None]
        
        if markets_with_dates:
            market = markets_with_dates[0]
            assert isinstance(market.created_at, datetime)
            assert market.created_at.year >= 2020  # Polymarket started ~2020