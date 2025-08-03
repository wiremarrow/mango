"""
Tests to ensure backward compatibility with existing code.
"""

import pytest
from unittest.mock import Mock, patch
from polymarket.api.api import GammaAPIClient, PolymarketAPI
from polymarket.models.models import Market, Event


class TestBackwardCompatibility:
    """Ensure new parameters don't break existing functionality."""
    
    @pytest.fixture
    def gamma_client(self):
        """Create a GammaAPIClient instance."""
        return GammaAPIClient()
    
    def test_get_markets_old_signature_still_works(self, gamma_client):
        """Test that old get_markets calls still work."""
        with patch.object(gamma_client, '_request_with_retry') as mock_request:
            mock_request.return_value.json.return_value = []
            
            # Old style call with only basic parameters
            result = gamma_client.get_markets(
                limit=100,
                offset=0,
                active=True,
                closed=False,
                order='volume',
                ascending=False
            )
            
            # Should work without issues
            assert result == []
            
            # Verify only expected params were sent
            params = dict(mock_request.call_args[1]['params'])
            assert params['limit'] == 100
            assert params['offset'] == 0
            assert params['active'] == True
            assert params['closed'] == False
            assert params['order'] == 'volume'
            assert params['ascending'] == False
    
    def test_get_markets_minimal_call(self, gamma_client):
        """Test get_markets with no parameters."""
        with patch.object(gamma_client, '_request_with_retry') as mock_request:
            mock_request.return_value.json.return_value = []
            
            # Minimal call
            result = gamma_client.get_markets()
            
            # Should use defaults
            params = dict(mock_request.call_args[1]['params'])
            assert params['limit'] == 100
            assert params['offset'] == 0
            assert params['order'] == 'volume'
            assert params['ascending'] == False
    
    def test_get_events_old_signature_still_works(self, gamma_client):
        """Test that old get_events calls still work."""
        with patch.object(gamma_client, '_request_with_retry') as mock_request:
            mock_request.return_value.json.return_value = []
            
            # Old style call
            result = gamma_client.get_events(
                limit=50,
                offset=10,
                active=False,
                closed=True,
                order='liquidity',
                ascending=True
            )
            
            # Should work without issues
            assert result == []
            
            params = dict(mock_request.call_args[1]['params'])
            assert params['limit'] == 50
            assert params['offset'] == 10
            assert params['active'] == False
            assert params['closed'] == True
            assert params['order'] == 'liquidity'
            assert params['ascending'] == True
    
    def test_search_markets_still_works(self, gamma_client):
        """Test that search_markets method still works."""
        with patch.object(gamma_client, 'get_markets') as mock_get:
            # Create test markets
            markets = []
            for i in range(5):
                market = Mock()
                market.question = f"Will Bitcoin hit {i}0k?"
                market.slug = f"btc-{i}0k"
                markets.append(market)
            
            mock_get.return_value = markets
            
            # Search for bitcoin
            results = gamma_client.search_markets("bitcoin", limit=3)
            
            assert len(results) == 3
            mock_get.assert_called_once_with(limit=1000, active=True)
    
    def test_get_market_by_slug_still_works(self, gamma_client):
        """Test get_market_by_slug compatibility."""
        with patch.object(gamma_client, '_request_with_retry') as mock_request:
            # First call returns empty (direct query)
            mock_request.return_value.json.side_effect = [
                [],  # First call
                [{   # Second call (get_markets)
                    'slug': 'test-market',
                    'question': 'Test?',
                    'conditionId': '0x123',
                    'clobTokenIds': '["0x1", "0x2"]',
                    'outcomes': '["Yes", "No"]',
                    'active': True,
                    'closed': False,
                    'volume': 100000
                }]
            ]
            
            result = gamma_client.get_market_by_slug('test-market')
            
            # Should fall back to search and find it
            assert result is not None
            assert result.slug == 'test-market'
    
    def test_get_event_by_slug_still_works(self, gamma_client):
        """Test get_event_by_slug compatibility."""
        with patch.object(gamma_client, '_request_with_retry') as mock_request:
            mock_request.return_value.json.return_value = [{
                'id': '123',
                'slug': 'test-event',
                'title': 'Test Event',
                'description': 'Test',
                'markets': [],
                'active': True,
                'volume': 1000000
            }]
            
            result = gamma_client.get_event_by_slug('test-event')
            
            assert result is not None
            assert result.slug == 'test-event'
            assert result.title == 'Test Event'


class TestPolymarketAPIBackwardCompatibility:
    """Test PolymarketAPI maintains backward compatibility."""
    
    @pytest.fixture
    def api(self):
        """Create PolymarketAPI instance."""
        with patch('polymarket.api.api.GammaAPIClient'), \
             patch('polymarket.api.api.CLOBAPIClient'), \
             patch('polymarket.api.data_api.DataAPIClient'):
            return PolymarketAPI()
    
    def test_get_market_still_works(self, api):
        """Test get_market method compatibility."""
        # Mock the clients
        market = Mock()
        market.slug = 'test-market'
        market.question = 'Test?'
        
        api.clob_client.find_market_by_slug.return_value = market
        
        result = api.get_market('test-market')
        
        assert result == market
        api.clob_client.find_market_by_slug.assert_called_once_with('test-market')
    
    def test_search_markets_still_works(self, api):
        """Test search_markets compatibility."""
        markets = [Mock() for _ in range(5)]
        api.clob_client.search_markets.return_value = markets[:3]
        api.gamma_client.search_markets.return_value = markets[3:]
        
        results = api.search_markets('test', limit=5)
        
        assert len(results) == 5
        api.clob_client.search_markets.assert_called_once_with('test', 5)
    
    def test_get_price_history_still_works(self, api):
        """Test get_price_history compatibility."""
        market = Mock()
        market.token_ids = ['0x1', '0x2']
        market.outcomes = ['Yes', 'No']
        
        price_histories = {'Yes': Mock(), 'No': Mock()}
        api.clob_client.get_market_prices_all_outcomes.return_value = price_histories
        
        result = api.get_price_history(market)
        
        assert result == price_histories
        api.clob_client.get_market_prices_all_outcomes.assert_called_once()
    
    def test_get_event_still_works(self, api):
        """Test get_event compatibility."""
        event = Mock()
        event.slug = 'test-event'
        
        api.gamma_client.get_event_by_slug.return_value = event
        
        result = api.get_event('test-event')
        
        assert result == event
        api.gamma_client.get_event_by_slug.assert_called_once_with('test-event')


class TestExistingCodePatterns:
    """Test that common code patterns still work."""
    
    def test_typical_market_extraction_flow(self):
        """Test typical flow for extracting market data."""
        with patch('polymarket.api.api.GammaAPIClient'), \
             patch('polymarket.api.api.CLOBAPIClient'), \
             patch('polymarket.api.data_api.DataAPIClient'):
            
            api = PolymarketAPI()
            
            # Mock market
            market = Mock()
            market.slug = 'test-market'
            market.token_ids = ['0x1', '0x2']
            market.outcomes = ['Yes', 'No']
            
            api.get_market = Mock(return_value=market)
            api.get_price_history = Mock(return_value={'Yes': Mock(), 'No': Mock()})
            
            # Typical usage
            slug = 'test-market'
            market = api.get_market(slug)
            assert market is not None
            
            price_data = api.get_price_history(market)
            assert 'Yes' in price_data
            assert 'No' in price_data
    
    def test_typical_event_extraction_flow(self):
        """Test typical flow for extracting event data."""
        with patch('polymarket.api.api.GammaAPIClient'), \
             patch('polymarket.api.api.CLOBAPIClient'), \
             patch('polymarket.api.data_api.DataAPIClient'):
            
            api = PolymarketAPI()
            
            # Mock event with markets
            event = Mock()
            event.slug = 'test-event'
            event.markets = [Mock(), Mock(), Mock()]
            
            api.get_event = Mock(return_value=event)
            
            # Typical usage
            event = api.get_event('test-event')
            assert event is not None
            assert len(event.markets) == 3
    
    def test_old_cli_still_works(self):
        """Test that old CLI commands still function."""
        from mango_cli import MangoCLI
        
        with patch('mango_cli.PolymarketAPI'):
            cli = MangoCLI()
            
            # Mock basic search
            cli.api.search_markets = Mock(return_value=[])
            
            # Old style search (before we added direct gamma client use)
            # Should still work through the unified API
            markets = cli.api.search_markets('bitcoin', 20)
            
            assert markets == []
            cli.api.search_markets.assert_called_once_with('bitcoin', 20)