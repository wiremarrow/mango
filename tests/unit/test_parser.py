"""
Unit tests for URL parser.
"""

import pytest
from polymarket.utils.parser import PolymarketURLParser
from polymarket.utils.exceptions import InvalidURLError


class TestPolymarketURLParser:
    """Test PolymarketURLParser class."""
    
    def setup_method(self):
        """Set up test instance."""
        self.parser = PolymarketURLParser()
    
    def test_parse_event_market_url(self):
        """Test parsing event/market URLs."""
        url = "https://polymarket.com/event/presidential-election-2028/will-jd-vance-win"
        result = self.parser.parse(url)
        
        assert result['url'] == url
        assert result['event_slug'] == "presidential-election-2028"
        assert result['market_slug'] == "will-jd-vance-win"
        assert result['is_event'] is False
        assert result['is_market'] is True
    
    def test_parse_event_only_url(self):
        """Test parsing event-only URLs."""
        url = "https://polymarket.com/event/presidential-election-2028"
        result = self.parser.parse(url)
        
        assert result['url'] == url
        assert result['event_slug'] == "presidential-election-2028"
        assert result['market_slug'] is None
        assert result['is_event'] is True
        assert result['is_market'] is False
    
    def test_parse_direct_market_url(self):
        """Test parsing direct market URLs."""
        url = "https://polymarket.com/market/will-btc-hit-100k"
        result = self.parser.parse(url)
        
        assert result['url'] == url
        assert result['event_slug'] is None
        assert result['market_slug'] == "will-btc-hit-100k"
        assert result['is_event'] is False
        assert result['is_market'] is True
    
    def test_parse_short_market_url(self):
        """Test parsing short market URLs."""
        url = "https://polymarket.com/will-btc-hit-100k"
        result = self.parser.parse(url)
        
        assert result['url'] == url
        assert result['event_slug'] is None
        assert result['market_slug'] == "will-btc-hit-100k"
        assert result['is_event'] is False
        assert result['is_market'] is True
    
    def test_invalid_domain(self):
        """Test invalid domain raises error."""
        with pytest.raises(InvalidURLError):
            self.parser.parse("https://example.com/market/test")
    
    def test_invalid_format(self):
        """Test invalid URL format raises error."""
        with pytest.raises(InvalidURLError):
            self.parser.parse("not-a-url")
    
    def test_empty_url(self):
        """Test empty URL raises error."""
        with pytest.raises(InvalidURLError):
            self.parser.parse("")
    
    def test_common_non_market_paths(self):
        """Test common non-market paths are rejected."""
        non_market_urls = [
            "https://polymarket.com/",
            "https://polymarket.com/markets",
            "https://polymarket.com/leaderboard",
            "https://polymarket.com/portfolio",
        ]
        
        for url in non_market_urls:
            with pytest.raises(InvalidURLError):
                self.parser.parse(url)
    
    def test_is_event_url(self):
        """Test is_event_url method."""
        assert self.parser.is_event_url("https://polymarket.com/event/test") is True
        assert self.parser.is_event_url("https://polymarket.com/event/test/market") is False
        assert self.parser.is_event_url("https://polymarket.com/market/test") is False
    
    def test_is_market_url(self):
        """Test is_market_url method."""
        assert self.parser.is_market_url("https://polymarket.com/event/test/market") is True
        assert self.parser.is_market_url("https://polymarket.com/market/test") is True
        assert self.parser.is_market_url("https://polymarket.com/test") is True
        assert self.parser.is_market_url("https://polymarket.com/event/test") is False
    
    def test_extract_slug(self):
        """Test extract_slug method."""
        # Event slug
        assert self.parser.extract_slug("https://polymarket.com/event/test") == "test"
        
        # Market slug from event/market URL
        assert self.parser.extract_slug("https://polymarket.com/event/e/m") == "m"
        
        # Direct market slug
        assert self.parser.extract_slug("https://polymarket.com/market/test") == "test"
        
        # Short URL slug
        assert self.parser.extract_slug("https://polymarket.com/test") == "test"
    
    def test_get_api_slug(self):
        """Test get_api_slug method."""
        # Same behavior as extract_slug in current implementation
        assert self.parser.get_api_slug("https://polymarket.com/event/test/market") == "market"
        assert self.parser.get_api_slug("https://polymarket.com/market/test") == "test"
    
    def test_build_market_url(self):
        """Test build_market_url method."""
        url = self.parser.build_market_url("event-slug", "market-slug")
        assert url == "https://polymarket.com/event/event-slug/market-slug"