"""
Comprehensive tests for Gamma API parameter support.
"""

import pytest
from unittest.mock import Mock, patch, call
from datetime import datetime
from typing import List

from polymarket.api.api import GammaAPIClient
from polymarket.models.models import Market, Event


class TestGammaAPIParameterSupport:
    """Test all new Gamma API parameter functionality."""
    
    @pytest.fixture
    def gamma_client(self):
        """Create a GammaAPIClient instance."""
        return GammaAPIClient()
    
    @pytest.fixture
    def sample_market_data(self):
        """Sample market data from Gamma API."""
        return {
            'id': 123,
            'slug': 'test-market',
            'question': 'Test question?',
            'conditionId': '0x123',
            'clobTokenIds': '["0xtoken1", "0xtoken2"]',
            'outcomes': '["Yes", "No"]',
            'active': True,
            'closed': False,
            'archived': False,
            'volume': 100000.0,
            'liquidity': 50000.0,
            'createdAt': '2024-01-01T00:00:00Z',
            'enableOrderBook': True,
            'negRisk': False
        }
    
    @pytest.fixture
    def sample_event_data(self):
        """Sample event data from Gamma API."""
        return {
            'id': '456',
            'ticker': 'TEST',
            'slug': 'test-event',
            'title': 'Test Event',
            'description': 'Test event description',
            'markets': [],
            'active': True,
            'closed': False,
            'archived': False,
            'volume': 1000000.0,
            'liquidity': 200000.0
        }
    
    # Tests for get_markets() with all parameters
    
    @patch('polymarket.api.api.GammaAPIClient._request_with_retry')
    def test_get_markets_basic_parameters(self, mock_request, gamma_client):
        """Test get_markets with basic parameters."""
        mock_request.return_value.json.return_value = []
        
        gamma_client.get_markets(
            limit=50,
            offset=100,
            active=True,
            closed=False,
            archived=False,
            order='liquidity',
            ascending=True
        )
        
        # Verify the parameters were passed correctly
        args, kwargs = mock_request.call_args
        assert args[0] == 'GET'
        assert args[1] == '/markets'
        
        # Check params list
        params = kwargs['params']
        param_dict = dict(params)
        
        assert param_dict['limit'] == 50
        assert param_dict['offset'] == 100
        assert param_dict['active'] == True
        assert param_dict['closed'] == False
        assert param_dict['archived'] == False
        assert param_dict['order'] == 'liquidity'
        assert param_dict['ascending'] == True
    
    @patch('polymarket.api.api.GammaAPIClient._request_with_retry')
    def test_get_markets_with_id_lists(self, mock_request, gamma_client):
        """Test get_markets with multiple IDs and slugs."""
        mock_request.return_value.json.return_value = []
        
        gamma_client.get_markets(
            id=[123, 456, 789],
            slug=['market-1', 'market-2'],
            clob_token_ids=['0xtoken1', '0xtoken2'],
            condition_ids=['0xcond1', '0xcond2']
        )
        
        # Get the params list
        params = mock_request.call_args[1]['params']
        
        # Count occurrences of each parameter
        id_count = sum(1 for p in params if p[0] == 'id')
        slug_count = sum(1 for p in params if p[0] == 'slug')
        token_count = sum(1 for p in params if p[0] == 'clob_token_ids')
        condition_count = sum(1 for p in params if p[0] == 'condition_ids')
        
        assert id_count == 3
        assert slug_count == 2
        assert token_count == 2
        assert condition_count == 2
        
        # Verify specific values
        id_values = [p[1] for p in params if p[0] == 'id']
        assert id_values == [123, 456, 789]
        
        slug_values = [p[1] for p in params if p[0] == 'slug']
        assert slug_values == ['market-1', 'market-2']
    
    @patch('polymarket.api.api.GammaAPIClient._request_with_retry')
    def test_get_markets_with_volume_liquidity_filters(self, mock_request, gamma_client):
        """Test get_markets with volume and liquidity filters."""
        mock_request.return_value.json.return_value = []
        
        gamma_client.get_markets(
            volume_num_min=100000.0,
            volume_num_max=5000000.0,
            liquidity_num_min=50000.0,
            liquidity_num_max=1000000.0
        )
        
        params = dict(mock_request.call_args[1]['params'])
        
        assert params['volume_num_min'] == 100000.0
        assert params['volume_num_max'] == 5000000.0
        assert params['liquidity_num_min'] == 50000.0
        assert params['liquidity_num_max'] == 1000000.0
    
    @patch('polymarket.api.api.GammaAPIClient._request_with_retry')
    def test_get_markets_with_date_filters(self, mock_request, gamma_client):
        """Test get_markets with date range filters."""
        mock_request.return_value.json.return_value = []
        
        gamma_client.get_markets(
            start_date_min='2024-01-01T00:00:00Z',
            start_date_max='2024-06-30T23:59:59Z',
            end_date_min='2024-07-01T00:00:00Z',
            end_date_max='2024-12-31T23:59:59Z'
        )
        
        params = dict(mock_request.call_args[1]['params'])
        
        assert params['start_date_min'] == '2024-01-01T00:00:00Z'
        assert params['start_date_max'] == '2024-06-30T23:59:59Z'
        assert params['end_date_min'] == '2024-07-01T00:00:00Z'
        assert params['end_date_max'] == '2024-12-31T23:59:59Z'
    
    @patch('polymarket.api.api.GammaAPIClient._request_with_retry')
    def test_get_markets_with_tag_filters(self, mock_request, gamma_client):
        """Test get_markets with tag filters."""
        mock_request.return_value.json.return_value = []
        
        gamma_client.get_markets(
            tag_id=5,
            related_tags=True,
            enableOrderBook=True
        )
        
        params = dict(mock_request.call_args[1]['params'])
        
        assert params['tag_id'] == 5
        assert params['related_tags'] == True
        assert params['enableOrderBook'] == True
    
    @patch('polymarket.api.api.GammaAPIClient._request_with_retry')
    def test_get_markets_returns_market_objects(self, mock_request, gamma_client, sample_market_data):
        """Test that get_markets returns proper Market objects."""
        mock_request.return_value.json.return_value = [sample_market_data]
        
        markets = gamma_client.get_markets(limit=1)
        
        assert len(markets) == 1
        assert isinstance(markets[0], Market)
        assert markets[0].id == 123
        assert markets[0].slug == 'test-market'
        assert markets[0].volume == 100000.0
        assert markets[0].liquidity == 50000.0
    
    # Tests for get_events() with all parameters
    
    @patch('polymarket.api.api.GammaAPIClient._request_with_retry')
    def test_get_events_basic_parameters(self, mock_request, gamma_client):
        """Test get_events with basic parameters."""
        mock_request.return_value.json.return_value = []
        
        gamma_client.get_events(
            limit=25,
            offset=50,
            active=True,
            closed=False,
            archived=True,
            order='volume',
            ascending=False
        )
        
        params = dict(mock_request.call_args[1]['params'])
        
        assert params['limit'] == 25
        assert params['offset'] == 50
        assert params['active'] == True
        assert params['closed'] == False
        assert params['archived'] == True
        assert params['order'] == 'volume'
        assert params['ascending'] == False
    
    @patch('polymarket.api.api.GammaAPIClient._request_with_retry')
    def test_get_events_with_id_slug_lists(self, mock_request, gamma_client):
        """Test get_events with multiple IDs and slugs."""
        mock_request.return_value.json.return_value = []
        
        gamma_client.get_events(
            id=[100, 200, 300],
            slug=['event-1', 'event-2']
        )
        
        params = mock_request.call_args[1]['params']
        
        id_count = sum(1 for p in params if p[0] == 'id')
        slug_count = sum(1 for p in params if p[0] == 'slug')
        
        assert id_count == 3
        assert slug_count == 2
        
        id_values = [p[1] for p in params if p[0] == 'id']
        assert id_values == [100, 200, 300]
    
    @patch('polymarket.api.api.GammaAPIClient._request_with_retry')
    def test_get_events_with_volume_liquidity_filters(self, mock_request, gamma_client):
        """Test get_events with volume and liquidity filters."""
        mock_request.return_value.json.return_value = []
        
        gamma_client.get_events(
            volume_min=500000.0,
            volume_max=10000000.0,
            liquidity_min=100000.0,
            liquidity_max=5000000.0
        )
        
        params = dict(mock_request.call_args[1]['params'])
        
        assert params['volume_min'] == 500000.0
        assert params['volume_max'] == 10000000.0
        assert params['liquidity_min'] == 100000.0
        assert params['liquidity_max'] == 5000000.0
    
    @patch('polymarket.api.api.GammaAPIClient._request_with_retry')
    def test_get_events_with_tag_filters(self, mock_request, gamma_client):
        """Test get_events with tag filters."""
        mock_request.return_value.json.return_value = []
        
        gamma_client.get_events(
            tag='politics',
            tag_id=10,
            tag_slug='us-politics',
            related_tags=True
        )
        
        params = dict(mock_request.call_args[1]['params'])
        
        assert params['tag'] == 'politics'
        assert params['tag_id'] == 10
        assert params['tag_slug'] == 'us-politics'
        assert params['related_tags'] == True
    
    @patch('polymarket.api.api.GammaAPIClient._request_with_retry')
    def test_get_events_returns_event_objects(self, mock_request, gamma_client, sample_event_data):
        """Test that get_events returns proper Event objects."""
        mock_request.return_value.json.return_value = [sample_event_data]
        
        events = gamma_client.get_events(limit=1)
        
        assert len(events) == 1
        assert isinstance(events[0], Event)
        assert events[0].id == '456'
        assert events[0].slug == 'test-event'
        assert events[0].volume == 1000000.0
    
    # Tests for helper methods
    
    @patch('polymarket.api.api.GammaAPIClient.get_markets')
    def test_get_markets_by_ids(self, mock_get_markets, gamma_client):
        """Test get_markets_by_ids helper method."""
        mock_get_markets.return_value = []
        
        gamma_client.get_markets_by_ids([100, 200, 300])
        
        mock_get_markets.assert_called_once_with(id=[100, 200, 300], limit=3)
    
    @patch('polymarket.api.api.GammaAPIClient.get_markets')
    def test_get_markets_by_ids_empty_list(self, mock_get_markets, gamma_client):
        """Test get_markets_by_ids with empty list."""
        result = gamma_client.get_markets_by_ids([])
        
        assert result == []
        mock_get_markets.assert_not_called()
    
    @patch('polymarket.api.api.GammaAPIClient.get_markets')
    def test_get_markets_by_condition_ids(self, mock_get_markets, gamma_client):
        """Test get_markets_by_condition_ids helper method."""
        mock_get_markets.return_value = []
        
        gamma_client.get_markets_by_condition_ids(['0xcond1', '0xcond2'])
        
        mock_get_markets.assert_called_once_with(
            condition_ids=['0xcond1', '0xcond2'], 
            limit=1000
        )
    
    @patch('polymarket.api.api.GammaAPIClient.get_markets')
    def test_get_markets_by_tags(self, mock_get_markets, gamma_client):
        """Test get_markets_by_tags helper method."""
        mock_get_markets.return_value = []
        
        gamma_client.get_markets_by_tags(tag_id=5, include_related=True)
        
        mock_get_markets.assert_called_once_with(
            tag_id=5,
            related_tags=True,
            limit=1000
        )
    
    @patch('polymarket.api.api.GammaAPIClient.get_events')
    def test_get_events_by_ids(self, mock_get_events, gamma_client):
        """Test get_events_by_ids helper method."""
        mock_get_events.return_value = []
        
        gamma_client.get_events_by_ids([10, 20, 30])
        
        mock_get_events.assert_called_once_with(id=[10, 20, 30], limit=3)
    
    @patch('polymarket.api.api.GammaAPIClient.get_events')
    def test_get_events_by_tags(self, mock_get_events, gamma_client):
        """Test get_events_by_tags helper method."""
        mock_get_events.return_value = []
        
        gamma_client.get_events_by_tags(tag_id=7, include_related=False)
        
        mock_get_events.assert_called_once_with(
            tag_id=7,
            related_tags=False,
            limit=1000
        )
    
    # Edge cases and error handling
    
    @patch('polymarket.api.api.GammaAPIClient._request_with_retry')
    def test_get_markets_with_none_values(self, mock_request, gamma_client):
        """Test that None values are not included in params."""
        mock_request.return_value.json.return_value = []
        
        gamma_client.get_markets(
            volume_num_min=None,
            volume_num_max=None,
            tag_id=None
        )
        
        params = dict(mock_request.call_args[1]['params'])
        
        assert 'volume_num_min' not in params
        assert 'volume_num_max' not in params
        assert 'tag_id' not in params
    
    @patch('polymarket.api.api.GammaAPIClient._request_with_retry')
    def test_get_markets_empty_lists_not_sent(self, mock_request, gamma_client):
        """Test that empty lists are not sent as parameters."""
        mock_request.return_value.json.return_value = []
        
        gamma_client.get_markets(
            id=None,
            slug=[]
        )
        
        params = mock_request.call_args[1]['params']
        
        # Check that no 'id' or 'slug' params were sent
        id_count = sum(1 for p in params if p[0] == 'id')
        slug_count = sum(1 for p in params if p[0] == 'slug')
        
        assert id_count == 0
        assert slug_count == 0
    
    @patch('polymarket.api.api.GammaAPIClient._request_with_retry')
    def test_get_markets_handles_api_error(self, mock_request, gamma_client):
        """Test error handling in get_markets."""
        mock_request.side_effect = Exception("API Error")
        
        result = gamma_client.get_markets(limit=10)
        
        assert result == []  # Should return empty list on error
    
    @patch('polymarket.api.api.GammaAPIClient._request_with_retry')
    def test_get_events_handles_api_error(self, mock_request, gamma_client):
        """Test error handling in get_events."""
        mock_request.side_effect = Exception("API Error")
        
        result = gamma_client.get_events(limit=10)
        
        assert result == []  # Should return empty list on error


class TestGammaAPIParameterCombinations:
    """Test various parameter combinations."""
    
    @pytest.fixture
    def gamma_client(self):
        """Create a GammaAPIClient instance."""
        return GammaAPIClient()
    
    @patch('polymarket.api.api.GammaAPIClient._request_with_retry')
    def test_complex_market_query(self, mock_request, gamma_client):
        """Test complex query with many parameters."""
        mock_request.return_value.json.return_value = []
        
        gamma_client.get_markets(
            limit=50,
            offset=100,
            active=True,
            archived=False,
            id=[1, 2, 3],
            volume_num_min=100000,
            volume_num_max=5000000,
            liquidity_num_min=50000,
            tag_id=5,
            related_tags=True,
            enableOrderBook=True,
            start_date_min='2024-01-01T00:00:00Z',
            end_date_max='2024-12-31T23:59:59Z'
        )
        
        params = mock_request.call_args[1]['params']
        
        # Verify all parameters are present
        param_dict = {}
        for key, value in params:
            if key in param_dict:
                if not isinstance(param_dict[key], list):
                    param_dict[key] = [param_dict[key]]
                param_dict[key].append(value)
            else:
                param_dict[key] = value
        
        assert param_dict['limit'] == 50
        assert param_dict['offset'] == 100
        assert param_dict['active'] == True
        assert param_dict['archived'] == False
        assert param_dict['id'] == [1, 2, 3]
        assert param_dict['volume_num_min'] == 100000
        assert param_dict['volume_num_max'] == 5000000
        assert param_dict['liquidity_num_min'] == 50000
        assert param_dict['tag_id'] == 5
        assert param_dict['related_tags'] == True
        assert param_dict['enableOrderBook'] == True
        assert param_dict['start_date_min'] == '2024-01-01T00:00:00Z'
        assert param_dict['end_date_max'] == '2024-12-31T23:59:59Z'
    
    @patch('polymarket.api.api.GammaAPIClient._request_with_retry')
    def test_order_parameter_variations(self, mock_request, gamma_client):
        """Test different order parameter values."""
        mock_request.return_value.json.return_value = []
        
        # Test each order option
        for order in ['volume', 'liquidity', 'created', 'end_date']:
            gamma_client.get_markets(order=order)
            params = dict(mock_request.call_args[1]['params'])
            assert params['order'] == order
    
    @patch('polymarket.api.api.GammaAPIClient._request_with_retry')
    def test_boolean_parameter_combinations(self, mock_request, gamma_client):
        """Test various boolean parameter combinations."""
        mock_request.return_value.json.return_value = []
        
        # Test different boolean combinations
        test_cases = [
            {'active': True, 'closed': False, 'archived': False},
            {'active': False, 'closed': True, 'archived': False},
            {'active': False, 'closed': False, 'archived': True},
            {'active': None, 'closed': None, 'archived': None}  # All markets
        ]
        
        for test_case in test_cases:
            gamma_client.get_markets(**test_case)
            params = dict(mock_request.call_args[1]['params'])
            
            for key, expected_value in test_case.items():
                if expected_value is not None:
                    assert params[key] == expected_value
                else:
                    assert key not in params