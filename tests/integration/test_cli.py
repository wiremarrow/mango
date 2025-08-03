"""
Integration tests for CLI commands.
"""

import pytest
import sys
from io import StringIO
from unittest.mock import patch, Mock
from pathlib import Path

from polymarket_extract import main as extract_main
from mango_cli import main as mango_main
from polymarket.models.models import Market, Event, PriceHistory, PricePoint
from datetime import datetime


class TestPolymarketExtractCLI:
    """Test polymarket-extract CLI."""
    
    @patch('polymarket_extract.PolymarketExtractor')
    def test_basic_extraction(self, mock_extractor_class):
        """Test basic market extraction."""
        # Mock extractor instance
        mock_extractor = Mock()
        mock_extractor_class.return_value = mock_extractor
        
        # Mock extraction result
        mock_market = Market(
            id="1",
            slug="test",
            condition_id="0x1",
            question="Test?",
            outcomes=["Yes", "No"],
            token_ids=["0x1", "0x2"]
        )
        
        mock_data = Mock()
        mock_data.market = mock_market
        mock_data.has_data = True
        mock_data.price_histories = {"Yes": Mock()}
        
        mock_extractor.extract_from_url.return_value = mock_data
        
        # Test command
        test_args = [
            'polymarket_extract.py',
            'https://polymarket.com/test-market'
        ]
        
        with patch.object(sys, 'argv', test_args):
            with patch('polymarket_extract.DataProcessor.to_csv', return_value="timestamp,Yes_price\n2024-01-01,0.5"):
                result = extract_main()
        
        assert result == 0
        mock_extractor.extract_from_url.assert_called_once()
    
    @patch('polymarket_extract.PolymarketExtractor')
    def test_event_extraction_with_streaming(self, mock_extractor_class):
        """Test event extraction with streaming."""
        # Mock extractor instance
        mock_extractor = Mock()
        mock_extractor_class.return_value = mock_extractor
        
        # Mock parser
        mock_extractor.parser.parse.return_value = {'event_slug': 'test-event'}
        mock_extractor.parser.is_event_url.return_value = False  # It's a market within event
        
        # Mock event
        mock_event = Event(
            id="1",
            slug="test-event",
            title="Test Event",
            description="Test",
            markets=[Mock() for _ in range(15)]  # More than threshold
        )
        
        mock_extractor.api.get_event.return_value = mock_event
        
        # Mock event data
        mock_event_data = Mock()
        mock_event_data.has_data = True
        mock_event_data.total_markets = 15
        
        mock_extractor.extract_all_event_markets.return_value = mock_event_data
        
        # Test command with streaming
        test_args = [
            'polymarket_extract.py',
            'https://polymarket.com/event/test-event',
            '--extract-all-markets',
            '-o', 'test_output'
        ]
        
        with patch.object(sys, 'argv', test_args):
            with patch('polymarket_extract.DataProcessor.stream_event_to_csv'):
                result = extract_main()
        
        assert result == 0
        # Should auto-enable streaming for large event
        mock_extractor.extract_all_event_markets.assert_called_once()
        call_args = mock_extractor.extract_all_event_markets.call_args
        assert call_args.kwargs['enable_gc'] is True  # Streaming enabled
    
    @patch('polymarket_extract.PolymarketExtractor')
    def test_cli_with_parameters(self, mock_extractor_class):
        """Test CLI with various parameters."""
        mock_extractor = Mock()
        mock_extractor_class.return_value = mock_extractor
        
        mock_extractor.extract_from_url.return_value = None  # No data
        
        test_args = [
            'polymarket_extract.py',
            'https://polymarket.com/test',
            '-i', '1h',
            '-d', '7',
            '--start', '2024-01-01',
            '--end', '2024-01-07',
            '--api-key', 'test-key',
            '-v'
        ]
        
        with patch.object(sys, 'argv', test_args):
            result = extract_main()
        
        assert result == 1  # No data
        
        # Check parameters passed
        call_args = mock_extractor.extract_from_url.call_args
        assert call_args.kwargs['interval'] == '1h'
        assert call_args.kwargs['days_back'] == 7
        assert call_args.kwargs['start_date'] == '2024-01-01'
        assert call_args.kwargs['end_date'] == '2024-01-07'
    
    @patch('polymarket_extract.PolymarketExtractor')
    def test_invalid_url_handling(self, mock_extractor_class):
        """Test handling of invalid URLs."""
        mock_extractor = Mock()
        mock_extractor_class.return_value = mock_extractor
        
        mock_extractor.extract_from_url.side_effect = Exception("Invalid URL")
        
        test_args = [
            'polymarket_extract.py',
            'https://invalid.com/market'
        ]
        
        with patch.object(sys, 'argv', test_args):
            result = extract_main()
        
        assert result == 1  # Error


class TestMangoCLI:
    """Test mango CLI commands."""
    
    @patch('mango_cli.PolymarketAPI')
    def test_search_command(self, mock_api_class):
        """Test search command."""
        mock_api = Mock()
        mock_api_class.return_value = mock_api
        
        mock_markets = [
            Market(
                id="1",
                slug="btc-100k",
                condition_id="0x1",
                question="Will BTC hit 100k?",
                outcomes=["Yes", "No"],
                token_ids=["0x1", "0x2"],
                volume=1000000.0
            )
        ]
        
        mock_api.search_markets.return_value = mock_markets
        
        test_args = [
            'mango',
            'search',
            'bitcoin',
            '--min-volume', '10000'
        ]
        
        with patch.object(sys, 'argv', test_args):
            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                result = mango_main()
        
        assert result == 0
        output = mock_stdout.getvalue()
        assert "BTC hit 100k" in output
        assert "$1.0M" in output  # Volume formatting
    
    @patch('mango_cli.PolymarketAPI')
    def test_market_info_command(self, mock_api_class):
        """Test market-info command."""
        mock_api = Mock()
        mock_api_class.return_value = mock_api
        
        mock_market = Market(
            id="1",
            slug="test-market",
            condition_id="0x1",
            question="Test market?",
            outcomes=["Yes", "No"],
            token_ids=["0x1", "0x2"],
            volume=500000.0,
            liquidity=250000.0
        )
        
        mock_api.get_market.return_value = mock_market
        
        test_args = [
            'mango',
            'market-info',
            'test-market'
        ]
        
        with patch.object(sys, 'argv', test_args):
            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                result = mango_main()
        
        assert result == 0
        output = mock_stdout.getvalue()
        assert "Test market?" in output
        assert "Volume: $500.0k" in output
    
    @patch('mango_cli.PolymarketAPI')
    def test_portfolio_command(self, mock_api_class):
        """Test portfolio command."""
        mock_api = Mock()
        mock_api_class.return_value = mock_api
        
        mock_positions = [
            {
                "market": {"question": "Test market?"},
                "outcome": "Yes",
                "size": 1000.0,
                "average_price": 0.45,
                "current_price": 0.50,
                "current_value": 500.0,
                "pnl": 50.0,
                "pnl_percent": 11.11
            }
        ]
        
        mock_api.get_user_positions.return_value = mock_positions
        
        test_args = [
            'mango',
            'portfolio',
            '0xuser123',
            '--min-size', '100'
        ]
        
        with patch.object(sys, 'argv', test_args):
            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                result = mango_main()
        
        assert result == 0
        output = mock_stdout.getvalue()
        assert "Test market?" in output
        assert "1000" in output  # Size
        assert "$50.00" in output  # P&L
    
    @patch('mango_cli.PolymarketAPI')
    def test_book_command_json_export(self, mock_api_class):
        """Test book command with JSON export."""
        mock_api = Mock()
        mock_api_class.return_value = mock_api
        
        mock_market = Market(
            id="1",
            slug="test",
            condition_id="0x1",
            question="Test?",
            outcomes=["Yes", "No"],
            token_ids=["0x1", "0x2"]
        )
        
        mock_books = Mock()
        mock_books.to_dict.return_value = {
            "market_id": "1",
            "books": {
                "Yes": {"bids": [], "asks": []},
                "No": {"bids": [], "asks": []}
            }
        }
        
        mock_api.get_market.return_value = mock_market
        mock_api.get_order_books.return_value = mock_books
        
        test_args = [
            'mango',
            'book',
            'test',
            '--format', 'json',
            '-o', 'test_book.json'
        ]
        
        with patch.object(sys, 'argv', test_args):
            with patch('builtins.open', create=True) as mock_open:
                mock_file = Mock()
                mock_open.return_value.__enter__.return_value = mock_file
                
                result = mango_main()
        
        assert result == 0
        mock_file.write.assert_called()  # JSON written to file