"""
Comprehensive tests for mango CLI advanced features.
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock, call
from io import StringIO
import sys

from mango_cli import MangoCLI, create_parser


class TestMangoCLIAdvancedSearch:
    """Test advanced search functionality in mango CLI."""
    
    @pytest.fixture
    def cli(self):
        """Create MangoCLI instance."""
        with patch('mango_cli.PolymarketAPI'):
            return MangoCLI()
    
    @pytest.fixture
    def sample_markets(self):
        """Create sample market objects."""
        markets = []
        for i in range(3):
            market = Mock()
            market.id = i + 1
            market.slug = f"test-market-{i+1}"
            market.question = f"Will test {i+1} happen?"
            market.volume = (i + 1) * 100000
            market.liquidity = (i + 1) * 50000
            market.active = True
            market.archived = False
            markets.append(market)
        return markets
    
    @patch('sys.stdout', new_callable=StringIO)
    def test_cmd_search_basic(self, mock_stdout, cli):
        """Test basic search command."""
        cli.api.gamma_client.get_markets.return_value = []
        
        cli.cmd_search("bitcoin", limit=10)
        
        cli.api.gamma_client.get_markets.assert_called_once()
        assert "No markets found" in mock_stdout.getvalue()
    
    @patch('sys.stdout', new_callable=StringIO)
    def test_cmd_search_with_filters(self, mock_stdout, cli, sample_markets):
        """Test search with all filter parameters."""
        cli.api.gamma_client.get_markets.return_value = sample_markets
        
        cli.cmd_search(
            "test",
            limit=20,
            active_only=True,
            min_volume=50000,
            archived=False,
            max_volume=1000000,
            min_liquidity=25000,
            max_liquidity=500000,
            tag=5,
            start_after="2024-01-01",
            end_before="2024-12-31"
        )
        
        # Verify API call parameters
        call_args = cli.api.gamma_client.get_markets.call_args[1]
        assert call_args['limit'] == 1000  # Gets more to filter
        assert call_args['active'] == True
        assert call_args['archived'] == False
        assert call_args['volume_num_min'] == 50000
        assert call_args['volume_num_max'] == 1000000
        assert call_args['liquidity_num_min'] == 25000
        assert call_args['liquidity_num_max'] == 500000
        assert call_args['tag_id'] == 5
        assert call_args['start_date_min'] == "2024-01-01T00:00:00Z"
        assert call_args['end_date_max'] == "2024-12-31T23:59:59Z"
        
        output = mock_stdout.getvalue()
        assert "Found 3 markets" in output
        assert "test-market-1" in output
    
    @patch('sys.stdout', new_callable=StringIO)
    def test_cmd_search_query_filtering(self, mock_stdout, cli, sample_markets):
        """Test that search properly filters by query text."""
        # Add a market that doesn't match
        non_matching = Mock()
        non_matching.slug = "other-market"
        non_matching.question = "Different topic?"
        non_matching.volume = 500000
        non_matching.liquidity = 100000
        non_matching.active = True
        non_matching.archived = False
        
        all_markets = sample_markets + [non_matching]
        cli.api.gamma_client.get_markets.return_value = all_markets
        
        cli.cmd_search("test", limit=10)
        
        output = mock_stdout.getvalue()
        assert "Found 3 markets" in output  # Only test markets
        assert "other-market" not in output
    
    @patch('sys.stdout', new_callable=StringIO)
    def test_cmd_search_archived_status(self, mock_stdout, cli):
        """Test archived market display."""
        archived_market = Mock()
        archived_market.slug = "archived-market"
        archived_market.question = "Old question?"
        archived_market.volume = 100000
        archived_market.liquidity = 50000
        archived_market.active = False
        archived_market.archived = True
        
        cli.api.gamma_client.get_markets.return_value = [archived_market]
        
        cli.cmd_search("old", archived=True)
        
        output = mock_stdout.getvalue()
        assert "Archived" in output


class TestMangoCLIMarketsAdvanced:
    """Test markets-advanced command functionality."""
    
    @pytest.fixture
    def cli(self):
        """Create MangoCLI instance."""
        with patch('mango_cli.PolymarketAPI'):
            return MangoCLI()
    
    @pytest.fixture
    def kwargs_basic(self):
        """Basic kwargs for markets-advanced."""
        return {
            'limit': 50,
            'offset': 0,
            'sort': 'volume',
            'ascending': False,
            'format': 'table'
        }
    
    @pytest.fixture
    def kwargs_complex(self):
        """Complex kwargs with all parameters."""
        return {
            'limit': 100,
            'offset': 50,
            'sort': 'liquidity',
            'ascending': True,
            'format': 'json',
            'output': 'test_output.json',
            'active': True,
            'closed': False,
            'archived': False,
            'ids': [123, 456, 789],
            'slugs': ['market-1', 'market-2'],
            'condition_ids': ['0xcond1', '0xcond2'],
            'token_ids': ['0xtoken1', '0xtoken2'],
            'min_volume': 100000,
            'max_volume': 5000000,
            'min_liquidity': 50000,
            'max_liquidity': 1000000,
            'tag': 5,
            'related_tags': True,
            'clob_only': True,
            'start_after': '2024-01-01',
            'start_before': '2024-06-30',
            'end_after': '2024-07-01',
            'end_before': '2024-12-31'
        }
    
    @patch('sys.stdout', new_callable=StringIO)
    def test_cmd_markets_advanced_basic(self, mock_stdout, cli, kwargs_basic):
        """Test basic markets-advanced command."""
        cli.api.gamma_client.get_markets.return_value = []
        
        cli.cmd_markets_advanced(**kwargs_basic)
        
        cli.api.gamma_client.get_markets.assert_called_once()
        assert "No markets found" in mock_stdout.getvalue()
    
    @patch('sys.stdout', new_callable=StringIO)
    def test_cmd_markets_advanced_complex_filters(self, mock_stdout, cli, kwargs_complex):
        """Test markets-advanced with all parameters."""
        market = Mock()
        market.id = 123
        market.slug = "test-market"
        market.question = "Test question?"
        market.condition_id = "0x123"
        market.volume = 1000000
        market.liquidity = 200000
        market.active = True
        market.closed = False
        market.archived = False
        market.outcomes = ["Yes", "No"]
        market.token_ids = ["0xtoken1", "0xtoken2"]
        market.created_at = None
        market.end_date = None
        
        cli.api.gamma_client.get_markets.return_value = [market]
        
        # Mock file writing
        with patch('builtins.open', create=True) as mock_open:
            mock_file = MagicMock()
            mock_open.return_value.__enter__.return_value = mock_file
            
            cli.cmd_markets_advanced(**kwargs_complex)
        
        # Verify API call
        call_args = cli.api.gamma_client.get_markets.call_args[1]
        assert call_args['limit'] == 100
        assert call_args['offset'] == 50
        assert call_args['order'] == 'liquidity'
        assert call_args['ascending'] == True
        assert call_args['active'] == True
        assert call_args['id'] == [123, 456, 789]
        assert call_args['slug'] == ['market-1', 'market-2']
        assert call_args['volume_num_min'] == 100000
        assert call_args['tag_id'] == 5
        assert call_args['enableOrderBook'] == True
        
        # Verify file was written
        mock_open.assert_called_once_with('test_output.json', 'w')
        mock_file.write.assert_called()
    
    @patch('sys.stdout', new_callable=StringIO)
    def test_cmd_markets_advanced_table_output(self, mock_stdout, cli, kwargs_basic):
        """Test table output format."""
        markets = []
        for i in range(3):
            market = Mock()
            market.id = i + 1
            market.slug = f"market-{i+1}"
            market.question = f"Question {i+1}?"
            market.volume = (i + 1) * 100000
            market.liquidity = (i + 1) * 50000
            market.active = True if i < 2 else False
            market.archived = True if i == 2 else False
            markets.append(market)
        
        cli.api.gamma_client.get_markets.return_value = markets
        
        cli.cmd_markets_advanced(**kwargs_basic)
        
        output = mock_stdout.getvalue()
        assert "Found 3 markets" in output
        assert "market-1" in output
        assert "Active" in output
        assert "Archived" in output
    
    @patch('sys.stdout', new_callable=StringIO)
    @patch('json.dump')
    def test_cmd_markets_advanced_json_output_stdout(self, mock_json_dump, mock_stdout, cli):
        """Test JSON output to stdout."""
        market = Mock()
        market.id = 1
        market.slug = "test"
        market.question = "Test?"
        market.condition_id = "0x123"
        market.volume = 100000
        market.liquidity = 50000
        market.active = True
        market.closed = False
        market.archived = False
        market.outcomes = ["Yes", "No"]
        market.token_ids = ["0x1", "0x2"]
        market.created_at = None
        market.end_date = None
        
        cli.api.gamma_client.get_markets.return_value = [market]
        
        kwargs = {
            'limit': 50,
            'offset': 0,
            'sort': 'volume',
            'ascending': False,
            'format': 'json'
        }
        
        cli.cmd_markets_advanced(**kwargs)
        
        # Verify JSON output structure
        output = mock_stdout.getvalue()
        assert "Found 1 markets" in output
    
    def test_cmd_markets_advanced_date_conversion(self, cli):
        """Test date parameter conversion."""
        cli.api.gamma_client.get_markets.return_value = []
        
        kwargs = {
            'start_after': '2024-01-01',
            'start_before': '2024-06-30',
            'end_after': '2024-07-01',
            'end_before': '2024-12-31'
        }
        
        cli.cmd_markets_advanced(**kwargs)
        
        call_args = cli.api.gamma_client.get_markets.call_args[1]
        assert call_args['start_date_min'] == '2024-01-01T00:00:00Z'
        assert call_args['start_date_max'] == '2024-06-30T23:59:59Z'
        assert call_args['end_date_min'] == '2024-07-01T00:00:00Z'
        assert call_args['end_date_max'] == '2024-12-31T23:59:59Z'


class TestMangoCLITags:
    """Test tags command functionality."""
    
    @pytest.fixture
    def cli(self):
        """Create MangoCLI instance."""
        with patch('mango_cli.PolymarketAPI'):
            return MangoCLI()
    
    @patch('sys.stdout', new_callable=StringIO)
    def test_cmd_tags_markets(self, mock_stdout, cli):
        """Test tags command for markets."""
        markets = []
        for i in range(3):
            market = Mock()
            market.slug = f"tagged-market-{i+1}"
            market.question = f"Tagged question {i+1}?"
            market.volume = (i + 1) * 100000
            market.active = True
            markets.append(market)
        
        cli.api.gamma_client.get_markets_by_tags.return_value = markets
        
        cli.cmd_tags(tag_id=5, type="markets", related=False, limit=50)
        
        cli.api.gamma_client.get_markets_by_tags.assert_called_once_with(5, include_related=False)
        
        output = mock_stdout.getvalue()
        assert "Searching for markets with tag ID 5" in output
        assert "Found 3 markets" in output
        assert "tagged-market-1" in output
    
    @patch('sys.stdout', new_callable=StringIO)
    def test_cmd_tags_events(self, mock_stdout, cli):
        """Test tags command for events."""
        events = []
        for i in range(2):
            event = Mock()
            event.slug = f"tagged-event-{i+1}"
            event.title = f"Tagged Event {i+1}"
            event.markets = [Mock() for _ in range(i + 2)]
            event.volume = (i + 1) * 500000
            event.active = True
            events.append(event)
        
        cli.api.gamma_client.get_events_by_tags.return_value = events
        
        cli.cmd_tags(tag_id=10, type="events", related=True, limit=20)
        
        cli.api.gamma_client.get_events_by_tags.assert_called_once_with(10, include_related=True)
        
        output = mock_stdout.getvalue()
        assert "Searching for events with tag ID 10" in output
        assert "Found 2 events" in output
        assert "tagged-event-1" in output
        assert "2" in output  # Number of markets
    
    @patch('sys.stdout', new_callable=StringIO)
    def test_cmd_tags_no_results(self, mock_stdout, cli):
        """Test tags command with no results."""
        cli.api.gamma_client.get_markets_by_tags.return_value = []
        
        cli.cmd_tags(tag_id=99, type="markets", related=False, limit=10)
        
        output = mock_stdout.getvalue()
        assert "No markets found with tag ID 99" in output
    
    @patch('sys.stdout', new_callable=StringIO)
    def test_cmd_tags_limit_applied(self, mock_stdout, cli):
        """Test that limit is properly applied."""
        # Create more markets than limit
        markets = [Mock() for _ in range(10)]
        for i, market in enumerate(markets):
            market.slug = f"market-{i}"
            market.question = f"Question {i}?"
            market.volume = 100000
            market.active = True
        
        cli.api.gamma_client.get_markets_by_tags.return_value = markets
        
        cli.cmd_tags(tag_id=5, type="markets", related=False, limit=3)
        
        output = mock_stdout.getvalue()
        assert "Found 3 markets" in output  # Should only show 3
        assert "market-0" in output
        assert "market-2" in output
        assert "market-3" not in output  # Beyond limit


class TestMangoCLIArgumentParsing:
    """Test CLI argument parsing."""
    
    def test_search_parser(self):
        """Test search command parser."""
        parser = create_parser()
        
        args = parser.parse_args([
            'search', 'bitcoin',
            '--limit', '50',
            '--inactive',
            '--archived',
            '--min-volume', '100000',
            '--max-volume', '5000000',
            '--min-liquidity', '50000',
            '--max-liquidity', '1000000',
            '--tag', '5',
            '--start-after', '2024-01-01',
            '--end-before', '2024-12-31'
        ])
        
        assert args.command == 'search'
        assert args.query == 'bitcoin'
        assert args.limit == 50
        assert args.inactive == True
        assert args.archived == True
        assert args.min_volume == 100000
        assert args.max_volume == 5000000
        assert args.min_liquidity == 50000
        assert args.max_liquidity == 1000000
        assert args.tag == 5
        assert args.start_after == '2024-01-01'
        assert args.end_before == '2024-12-31'
    
    def test_markets_advanced_parser(self):
        """Test markets-advanced command parser."""
        parser = create_parser()
        
        args = parser.parse_args([
            'markets-advanced',
            '--ids', '123', '456',
            '--slugs', 'market-1', 'market-2',
            '--condition-ids', '0x1', '0x2',
            '--token-ids', '0xa', '0xb',
            '--tag', '5',
            '--related-tags',
            '--min-volume', '100000',
            '--max-volume', '5000000',
            '--active',
            '--clob-only',
            '--sort', 'liquidity',
            '--ascending',
            '--format', 'json',
            '-o', 'output.json'
        ])
        
        assert args.command == 'markets-advanced'
        assert args.ids == [123, 456]
        assert args.slugs == ['market-1', 'market-2']
        assert args.condition_ids == ['0x1', '0x2']
        assert args.token_ids == ['0xa', '0xb']
        assert args.tag == 5
        assert args.related_tags == True
        assert args.min_volume == 100000
        assert args.max_volume == 5000000
        assert args.active == True
        assert args.clob_only == True
        assert args.sort == 'liquidity'
        assert args.ascending == True
        assert args.format == 'json'
        assert args.output == 'output.json'
    
    def test_tags_parser(self):
        """Test tags command parser."""
        parser = create_parser()
        
        args = parser.parse_args([
            'tags', '17',
            '--type', 'events',
            '--related',
            '--limit', '100'
        ])
        
        assert args.command == 'tags'
        assert args.tag_id == 17
        assert args.type == 'events'
        assert args.related == True
        assert args.limit == 100
    
    def test_parser_defaults(self):
        """Test parser default values."""
        parser = create_parser()
        
        # Test search defaults
        args = parser.parse_args(['search', 'test'])
        assert args.limit == 20
        assert args.inactive == False
        assert args.archived == False
        assert args.min_volume == 0
        assert args.max_volume is None
        
        # Test markets-advanced defaults
        args = parser.parse_args(['markets-advanced'])
        assert args.limit == 100
        assert args.offset == 0
        assert args.sort == 'volume'
        assert args.ascending == False
        assert args.format == 'table'
        
        # Test tags defaults
        args = parser.parse_args(['tags', '5'])
        assert args.type == 'markets'
        assert args.related == False
        assert args.limit == 50