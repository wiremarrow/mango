"""
Utility functions for Polymarket data extraction.

This module contains shared utility functions used across the codebase.
"""

from typing import Optional
from ..models import Market


def get_column_prefix(market: Market, market_slug: str, max_length: int = 20) -> str:
    """
    Generate a column prefix for market data export.
    
    Uses the market's group item title if available, otherwise extracts
    a meaningful prefix from the market slug.
    
    Args:
        market: Market object
        market_slug: Market slug identifier
        max_length: Maximum length for prefix if extracting from slug
        
    Returns:
        Column prefix string
    """
    # Use group item title if available (e.g., team names in sports markets)
    if market.group_item_title:
        return market.group_item_title.lower().replace(' ', '_')
    
    # Try to extract meaningful prefix from slug
    parts = market_slug.split('-')
    if 'will' in parts:
        # Extract the main subject after 'will'
        # e.g., "will-liverpool-win" -> "liverpool"
        idx = parts.index('will')
        if idx + 1 < len(parts):
            return parts[idx + 1]
    
    # Fallback to first part of slug (limited to max_length)
    return market_slug[:max_length]


def format_price(price: float, precision: int = 4) -> str:
    """
    Format a price value for display.
    
    Args:
        price: Price value between 0 and 1
        precision: Number of decimal places
        
    Returns:
        Formatted price string with $ prefix
    """
    return f"${price:.{precision}f}"


def format_volume(volume: float) -> str:
    """
    Format a volume value for display with appropriate units.
    
    Args:
        volume: Volume in dollars
        
    Returns:
        Formatted volume string
    """
    if volume >= 1_000_000:
        return f"${volume/1_000_000:.1f}M"
    elif volume >= 1_000:
        return f"${volume/1_000:.1f}k"
    else:
        return f"${volume:.2f}"