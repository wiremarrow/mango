"""
CLI output handling for Polymarket tools.

This module provides a consistent interface for all user-facing output,
separating it from logging and internal error handling.
"""

import sys
from typing import Optional, List, Dict, Any
from datetime import datetime

from ..models import Market, Event, PriceHistory
from ..utils import format_price, format_volume
from ..utils.constants import (
    CLI_SEPARATOR, CLI_SUBSEPARATOR,
    ERROR_NO_TOKENS, ERROR_INACTIVE_NEGRISK, ERROR_PLACEHOLDER_OPTION,
    SUGGESTION_EVENT_EXTRACTION, SUGGESTION_USE_EXTRACT_ALL,
    INFO_EXTRACTING_MARKET
)


class CLIReporter:
    """Handles all CLI output in a consistent manner."""
    
    def __init__(self, verbose: bool = False):
        """
        Initialize the CLI reporter.
        
        Args:
            verbose: Whether to show verbose output
        """
        self.verbose = verbose
    
    def print(self, message: str = "", end: str = "\n") -> None:
        """Print a message to stdout."""
        print(message, end=end)
    
    def error(self, message: str) -> None:
        """Print an error message."""
        self.print(f"\nError: {message}")
    
    def warning(self, message: str) -> None:
        """Print a warning message."""
        self.print(f"\nWarning: {message}")
    
    def success(self, message: str) -> None:
        """Print a success message."""
        self.print(f"\n✓ {message}")
    
    def info(self, message: str) -> None:
        """Print an info message."""
        if self.verbose:
            self.print(message)
    
    def separator(self) -> None:
        """Print a separator line."""
        self.print(CLI_SEPARATOR)
    
    def subseparator(self) -> None:
        """Print a subseparator line."""
        self.print(CLI_SUBSEPARATOR)
    
    def market_summary(self, market: Market) -> None:
        """Display market summary information."""
        self.print(f"\nMarket: {market.question}")
        self.print(f"Condition ID: {market.condition_id}")
        if market.outcomes:
            self.print(f"Outcomes: {', '.join(market.outcomes)}")
        if market.active is not None:
            status = "Active" if market.active else "Inactive"
            self.print(f"Status: {status}")
        if market.volume:
            self.print(f"Volume: {format_volume(market.volume)}")
        
        # Display market age if available
        if market.created_at:
            from datetime import datetime
            age_days = (datetime.now(market.created_at.tzinfo) - market.created_at).days
            self.print(f"Market age: {age_days} days")
    
    def event_summary(self, event: Event) -> None:
        """Display event summary information."""
        self.print(f"\nEvent: {event.title}")
        if event.description:
            desc = event.description[:200] + "..." if len(event.description) > 200 else event.description
            self.print(f"Description: {desc}")
    
    def market_extraction_progress(self, current: int, total: int, market_name: str) -> None:
        """Display market extraction progress."""
        self.print(INFO_EXTRACTING_MARKET.format(
            current=current,
            total=total,
            name=market_name
        ))
    
    def price_history_summary(self, outcome: str, history: PriceHistory) -> None:
        """Display price history summary for an outcome."""
        if not history.price_points:
            return
            
        self.print(f"\n{outcome}:")
        self.print(f"  Data points: {history.data_points_count}")
        self.print(f"  Latest price: {format_price(history.latest_price)}")
        
        if history.price_change is not None:
            change_str = format_price(history.price_change)
            percent_str = f"{history.price_change_percent:.2f}%"
            self.print(f"  Change: {change_str} ({percent_str})")
    
    def inactive_negrisk_error(self, market: Market) -> None:
        """Display error for inactive negRisk market option."""
        self.error(ERROR_INACTIVE_NEGRISK)
        self.print(f"Market: {market.question}")
        self.print(ERROR_PLACEHOLDER_OPTION)
        self.print("\nSuggestions:")
        self.print(f"1. {SUGGESTION_EVENT_EXTRACTION}")
        self.print(f"2. {SUGGESTION_USE_EXTRACT_ALL}")
    
    def no_tokens_error(self) -> None:
        """Display error for market with no tokens."""
        self.error(ERROR_NO_TOKENS)
        self.print("It may be a future market that hasn't been activated for trading.")
    
    def extraction_statistics(self, total: int, active: int, 
                            inactive_negrisk: int, other_inactive: int) -> None:
        """Display extraction statistics for an event."""
        self.print(f"Total markets: {total}")
        self.print(f"Active markets: {active}")
        
        if inactive_negrisk > 0:
            self.print(f"Inactive negRisk options: {inactive_negrisk} (will be skipped)")
        
        if other_inactive > 0:
            self.print(f"Other inactive markets: {other_inactive} (will be skipped)")
    
    def market_skip_reason(self, reason: str) -> None:
        """Display why a market is being skipped."""
        self.print(f"  Skipping: {reason}")
    
    def market_list_item(self, index: int, market: Market, event_slug: str) -> None:
        """Display a market in a numbered list."""
        # Display title
        title = market.group_item_title or market.question
        self.print(f"\n{index}. {title}")
        
        # Build and display URL
        if market.slug and event_slug:
            from ..utils.parser import PolymarketURLParser
            parser = PolymarketURLParser()
            url = parser.build_market_url(event_slug, market.slug)
            self.print(f"   URL: {url}")
        
        # Display status and volume
        status_parts = []
        if market.active is not None:
            status_parts.append(f"Active: {market.active}")
        if market.volume is not None:
            status_parts.append(f"Volume: {format_volume(market.volume)}")
        
        if status_parts:
            self.print(f"   {', '.join(status_parts)}")
        
        # Show current prices if available
        if hasattr(market, 'metadata') and market.metadata.get('outcomePrices'):
            prices = market.metadata.get('outcomePrices', [])
            if len(prices) >= 2:
                yes_price = format_price(float(prices[0]), precision=3)
                no_price = format_price(float(prices[1]), precision=3)
                self.print(f"   Current: Yes: {yes_price}, No: {no_price}")