"""
Unit tests for utility functions.
"""

import pytest
from polymarket.utils.utils import get_column_prefix, format_price, format_volume
from polymarket.models.models import Market


class TestGetColumnPrefix:
    """Test get_column_prefix function."""
    
    def test_with_group_item_title(self):
        """Test prefix generation with group item title."""
        market = Market(
            id="1",
            slug="person-a-win",
            condition_id="0x123",
            question="Will Person A win?",
            outcomes=["Yes", "No"],
            token_ids=["0x1", "0x2"],
            active=True,
            closed=False,
            group_item_title="Person A"
        )
        
        prefix = get_column_prefix(market, "person-a-win")
        assert prefix == "person_a"
    
    def test_with_will_in_slug(self):
        """Test prefix extraction from slug with 'will'."""
        market = Market(
            id="1",
            slug="will-liverpool-win-premier-league",
            condition_id="0x123",
            question="Will Liverpool win?",
            outcomes=["Yes", "No"],
            token_ids=["0x1", "0x2"],
            active=True,
            closed=False
        )
        
        prefix = get_column_prefix(market, "will-liverpool-win-premier-league")
        assert prefix == "liverpool"
    
    def test_fallback_to_slug_truncation(self):
        """Test fallback to slug truncation."""
        market = Market(
            id="1",
            slug="btc-price-above-100k-december",
            condition_id="0x123",
            question="BTC above 100k?",
            outcomes=["Yes", "No"],
            token_ids=["0x1", "0x2"],
            active=True,
            closed=False
        )
        
        prefix = get_column_prefix(market, "btc-price-above-100k-december", max_length=10)
        assert prefix == "btc-price-"
    
    def test_spaces_replaced_with_underscores(self):
        """Test that spaces in group item title are replaced."""
        market = Market(
            id="1",
            slug="team-name-win",
            condition_id="0x123",
            question="Will Team Name win?",
            outcomes=["Yes", "No"],
            token_ids=["0x1", "0x2"],
            active=True,
            closed=False,
            group_item_title="Team Name With Spaces"
        )
        
        prefix = get_column_prefix(market, "team-name-win")
        assert prefix == "team_name_with_spaces"


class TestFormatPrice:
    """Test format_price function."""
    
    def test_default_precision(self):
        """Test formatting with default precision."""
        assert format_price(0.1234) == "$0.1234"
        assert format_price(0.5) == "$0.5000"
        assert format_price(0.99999) == "$1.0000"
    
    def test_custom_precision(self):
        """Test formatting with custom precision."""
        assert format_price(0.123456, precision=2) == "$0.12"
        assert format_price(0.5, precision=6) == "$0.500000"
        assert format_price(0.999, precision=1) == "$1.0"
    
    def test_edge_cases(self):
        """Test edge cases."""
        assert format_price(0.0) == "$0.0000"
        assert format_price(1.0) == "$1.0000"
        assert format_price(0.0001, precision=3) == "$0.000"


class TestFormatVolume:
    """Test format_volume function."""
    
    def test_millions_formatting(self):
        """Test formatting for millions."""
        assert format_volume(1_000_000) == "$1.0M"
        assert format_volume(5_500_000) == "$5.5M"
        assert format_volume(10_000_000) == "$10.0M"
        assert format_volume(999_999_999) == "$1000.0M"
    
    def test_thousands_formatting(self):
        """Test formatting for thousands."""
        assert format_volume(1_000) == "$1.0k"
        assert format_volume(10_500) == "$10.5k"
        assert format_volume(999_999) == "$1000.0k"
    
    def test_small_amounts(self):
        """Test formatting for amounts under 1000."""
        assert format_volume(0) == "$0.00"
        assert format_volume(1) == "$1.00"
        assert format_volume(999.99) == "$999.99"
        assert format_volume(100.5) == "$100.50"
    
    def test_precision(self):
        """Test precision in formatting."""
        assert format_volume(1_234_567) == "$1.2M"
        assert format_volume(1_234) == "$1.2k"
        assert format_volume(123.456) == "$123.46"