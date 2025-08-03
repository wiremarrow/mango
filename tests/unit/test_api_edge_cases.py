"""
Edge case and error handling tests for API functionality.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import httpx
from datetime import datetime

from polymarket.api.api import GammaAPIClient, CLOBAPIClient, PolymarketAPI
from polymarket.models.models import Market, Event
from polymarket.utils.exceptions import APIError, RateLimitError


class TestGammaAPIEdgeCases:
    """Test edge cases and error scenarios for Gamma API."""
    
    @pytest.fixture
    def gamma_client(self):
        """Create a GammaAPIClient instance."""
        return GammaAPIClient()
    
    def test_empty_parameter_lists(self, gamma_client):
        """Test that empty lists don't cause issues."""
        with patch.object(gamma_client, '_request_with_retry') as mock_request:
            mock_request.return_value.json.return_value = []
            
            # Empty lists should be ignored
            result = gamma_client.get_markets(
                id=[],
                slug=[],
                clob_token_ids=[],
                condition_ids=[]
            )
            
            # Verify no list parameters were sent
            params = mock_request.call_args[1]['params']
            param_keys = [p[0] for p in params]
            assert 'id' not in param_keys
            assert 'slug' not in param_keys
            assert 'clob_token_ids' not in param_keys
            assert 'condition_ids' not in param_keys
    
    def test_none_parameters_ignored(self, gamma_client):
        """Test that None parameters are properly ignored."""
        with patch.object(gamma_client, '_request_with_retry') as mock_request:
            mock_request.return_value.json.return_value = []
            
            result = gamma_client.get_markets(
                active=None,
                volume_num_min=None,
                tag_id=None,
                start_date_min=None
            )
            
            # Verify None parameters weren't sent
            params = dict(mock_request.call_args[1]['params'])
            assert 'active' not in params
            assert 'volume_num_min' not in params
            assert 'tag_id' not in params
            assert 'start_date_min' not in params
    
    def test_zero_values_sent(self, gamma_client):
        """Test that zero values are properly sent (not ignored)."""
        with patch.object(gamma_client, '_request_with_retry') as mock_request:
            mock_request.return_value.json.return_value = []
            
            result = gamma_client.get_markets(
                offset=0,
                volume_num_min=0,
                tag_id=0
            )
            
            # Verify zero values were sent
            params = dict(mock_request.call_args[1]['params'])
            assert params['offset'] == 0
            assert params['volume_num_min'] == 0
            assert params['tag_id'] == 0
    
    def test_special_characters_in_slugs(self, gamma_client):
        """Test handling of special characters in slug parameters."""
        with patch.object(gamma_client, '_request_with_retry') as mock_request:
            mock_request.return_value.json.return_value = []
            
            # Slugs with special characters
            result = gamma_client.get_markets(
                slug=['market-with-dash', 'market_with_underscore', 'market.with.dot']
            )
            
            params = mock_request.call_args[1]['params']
            slug_values = [p[1] for p in params if p[0] == 'slug']
            assert 'market-with-dash' in slug_values
            assert 'market_with_underscore' in slug_values
            assert 'market.with.dot' in slug_values
    
    def test_very_large_limit(self, gamma_client):
        """Test handling of very large limit values."""
        with patch.object(gamma_client, '_request_with_retry') as mock_request:
            mock_request.return_value.json.return_value = []
            
            result = gamma_client.get_markets(limit=10000)
            
            params = dict(mock_request.call_args[1]['params'])
            assert params['limit'] == 10000
    
    def test_invalid_date_format_handling(self, gamma_client):
        """Test that invalid date formats are passed through (API will handle)."""
        with patch.object(gamma_client, '_request_with_retry') as mock_request:
            mock_request.return_value.json.return_value = []
            
            # Pass invalid date format
            result = gamma_client.get_markets(
                start_date_min='2024/01/01',  # Wrong format
                end_date_max='01-01-2024'     # Wrong format
            )
            
            # Should still pass through to API
            params = dict(mock_request.call_args[1]['params'])
            assert params['start_date_min'] == '2024/01/01'
            assert params['end_date_max'] == '01-01-2024'
    
    def test_conflicting_status_parameters(self, gamma_client):
        """Test handling of conflicting status parameters."""
        with patch.object(gamma_client, '_request_with_retry') as mock_request:
            mock_request.return_value.json.return_value = []
            
            # All status flags true (logically impossible but API should handle)
            result = gamma_client.get_markets(
                active=True,
                closed=True,
                archived=True
            )
            
            params = dict(mock_request.call_args[1]['params'])
            assert params['active'] == True
            assert params['closed'] == True
            assert params['archived'] == True
    
    def test_negative_numeric_values(self, gamma_client):
        """Test handling of negative numeric values."""
        with patch.object(gamma_client, '_request_with_retry') as mock_request:
            mock_request.return_value.json.return_value = []
            
            # Negative values (should be passed to API for validation)
            result = gamma_client.get_markets(
                offset=-10,
                volume_num_min=-1000
            )
            
            params = dict(mock_request.call_args[1]['params'])
            assert params['offset'] == -10
            assert params['volume_num_min'] == -1000
    
    def test_min_greater_than_max(self, gamma_client):
        """Test when min values are greater than max values."""
        with patch.object(gamma_client, '_request_with_retry') as mock_request:
            mock_request.return_value.json.return_value = []
            
            # Min > Max (API should handle validation)
            result = gamma_client.get_markets(
                volume_num_min=1000000,
                volume_num_max=100000,
                liquidity_num_min=500000,
                liquidity_num_max=50000
            )
            
            params = dict(mock_request.call_args[1]['params'])
            assert params['volume_num_min'] == 1000000
            assert params['volume_num_max'] == 100000
    
    def test_api_error_returns_empty_list(self, gamma_client):
        """Test that API errors return empty list instead of raising."""
        with patch.object(gamma_client, '_request_with_retry') as mock_request:
            mock_request.side_effect = Exception("Network error")
            
            result = gamma_client.get_markets(limit=10)
            
            assert result == []
    
    def test_malformed_response_handling(self, gamma_client):
        """Test handling of malformed API responses."""
        with patch.object(gamma_client, '_request_with_retry') as mock_request:
            # Non-list response
            mock_request.return_value.json.return_value = {"error": "Invalid request"}
            
            result = gamma_client.get_markets(limit=10)
            
            # Should handle gracefully and return empty list
            assert result == []
    
    def test_partial_market_data(self, gamma_client):
        """Test handling of markets with missing fields."""
        with patch.object(gamma_client, '_request_with_retry') as mock_request:
            # Market missing some fields
            mock_request.return_value.json.return_value = [{
                'slug': 'test-market',
                'question': 'Test?',
                # Missing many required fields
            }]
            
            # Should handle gracefully (Market.from_gamma_response should handle)
            result = gamma_client.get_markets(limit=1)
            
            # May create market with defaults or skip
            assert isinstance(result, list)


class TestHelperMethodEdgeCases:
    """Test edge cases for helper methods."""
    
    @pytest.fixture
    def gamma_client(self):
        """Create a GammaAPIClient instance."""
        return GammaAPIClient()
    
    def test_get_markets_by_ids_with_duplicates(self, gamma_client):
        """Test helper with duplicate IDs."""
        with patch.object(gamma_client, 'get_markets') as mock_get:
            mock_get.return_value = []
            
            # Duplicate IDs
            gamma_client.get_markets_by_ids([1, 2, 2, 3, 1])
            
            # Should pass all IDs including duplicates
            mock_get.assert_called_once_with(id=[1, 2, 2, 3, 1], limit=5)
    
    def test_get_markets_by_ids_with_none(self, gamma_client):
        """Test helper with None in list."""
        with patch.object(gamma_client, 'get_markets') as mock_get:
            mock_get.return_value = []
            
            # None values in list
            gamma_client.get_markets_by_ids([1, None, 2, None])
            
            # Should pass as-is (API will handle)
            mock_get.assert_called_once_with(id=[1, None, 2, None], limit=4)
    
    def test_get_markets_by_tags_negative_id(self, gamma_client):
        """Test tag helper with negative ID."""
        with patch.object(gamma_client, 'get_markets') as mock_get:
            mock_get.return_value = []
            
            gamma_client.get_markets_by_tags(tag_id=-1, include_related=True)
            
            # Should pass negative ID to API
            mock_get.assert_called_once_with(tag_id=-1, related_tags=True, limit=1000)


class TestCLIEdgeCases:
    """Test edge cases in CLI handling."""
    
    def test_search_with_empty_query(self):
        """Test search with empty query string."""
        from mango_cli import MangoCLI
        
        with patch('mango_cli.PolymarketAPI'):
            cli = MangoCLI()
            cli.api.gamma_client.get_markets.return_value = []
            
            # Empty query should still work
            cli.cmd_search("", limit=10)
            
            cli.api.gamma_client.get_markets.assert_called_once()
    
    def test_markets_advanced_all_none_kwargs(self):
        """Test markets-advanced with all None values."""
        from mango_cli import MangoCLI
        
        with patch('mango_cli.PolymarketAPI'):
            cli = MangoCLI()
            cli.api.gamma_client.get_markets.return_value = []
            
            kwargs = {key: None for key in [
                'ids', 'slugs', 'condition_ids', 'token_ids',
                'min_volume', 'max_volume', 'min_liquidity', 'max_liquidity',
                'tag', 'related_tags', 'clob_only',
                'start_after', 'start_before', 'end_after', 'end_before',
                'active', 'closed', 'archived'
            ]}
            kwargs['limit'] = 10
            kwargs['format'] = 'table'
            
            cli.cmd_markets_advanced(**kwargs)
            
            # Should still make API call with defaults
            cli.api.gamma_client.get_markets.assert_called_once()
    
    def test_tags_with_zero_tag_id(self):
        """Test tags command with tag ID 0."""
        from mango_cli import MangoCLI
        
        with patch('mango_cli.PolymarketAPI'):
            cli = MangoCLI()
            cli.api.gamma_client.get_markets_by_tags.return_value = []
            
            cli.cmd_tags(tag_id=0, type="markets")
            
            # Should handle tag ID 0
            cli.api.gamma_client.get_markets_by_tags.assert_called_once_with(0, include_related=False)


class TestDateHandling:
    """Test date parameter handling edge cases."""
    
    def test_date_conversion_edge_cases(self):
        """Test edge cases in date conversion."""
        from mango_cli import MangoCLI
        
        with patch('mango_cli.PolymarketAPI'):
            cli = MangoCLI()
            cli.api.gamma_client.get_markets.return_value = []
            
            # Test with various date formats
            cli.cmd_search("test", start_after="2024-1-1", end_before="2024-12-31")
            
            call_args = cli.api.gamma_client.get_markets.call_args[1]
            # Should still convert even with single digit month/day
            assert call_args['start_date_min'] == "2024-1-1T00:00:00Z"
            assert call_args['end_date_max'] == "2024-12-31T23:59:59Z"
    
    def test_invalid_date_string(self):
        """Test handling of invalid date strings."""
        from mango_cli import MangoCLI
        
        with patch('mango_cli.PolymarketAPI'):
            cli = MangoCLI()
            cli.api.gamma_client.get_markets.return_value = []
            
            # Invalid date format
            cli.cmd_search("test", start_after="not-a-date")
            
            call_args = cli.api.gamma_client.get_markets.call_args[1]
            # Should still pass through
            assert call_args['start_date_min'] == "not-a-dateT00:00:00Z"