#!/usr/bin/env python3
"""
Mango CLI - Enhanced Polymarket command-line interface.

This module provides comprehensive CLI commands for interacting with
Polymarket's APIs including market data, order books, and portfolio tracking.
"""

import argparse
import sys
import logging
import json
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any
from decimal import Decimal
from tabulate import tabulate

from polymarket import (
    PolymarketAPI, PolymarketURLParser, DataProcessor,
    MarketHistoricalData, TimeInterval, OrderBook
)
from polymarket.utils.config import (
    DEFAULT_API_KEY, LOG_LEVEL, LOG_FORMAT
)
from polymarket.utils.exceptions import (
    PolymarketError, InvalidURLError, MarketNotFoundError
)


# Configure logging
logging.basicConfig(level=LOG_LEVEL, format=LOG_FORMAT)
logger = logging.getLogger(__name__)


class MangoCLI:
    """Enhanced CLI for Polymarket operations."""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize CLI with API key."""
        self.api = PolymarketAPI(api_key or DEFAULT_API_KEY)
        self.parser = PolymarketURLParser()
    
    def cmd_search(self, query: str, limit: int = 20, 
                   active_only: bool = True, min_volume: float = 0,
                   archived: bool = False, max_volume: Optional[float] = None,
                   min_liquidity: Optional[float] = None, max_liquidity: Optional[float] = None,
                   tag: Optional[int] = None, start_after: Optional[str] = None,
                   end_before: Optional[str] = None) -> None:
        """Search for markets by keyword with advanced filtering."""
        logger.info(f"Searching for markets: '{query}'")
        
        # Use Gamma API for advanced filtering
        gamma_client = self.api.gamma_client
        
        # Convert date strings to ISO format if provided
        start_date_min = None
        end_date_max = None
        if start_after:
            start_date_min = f"{start_after}T00:00:00Z"
        if end_before:
            end_date_max = f"{end_before}T23:59:59Z"
        
        # Get markets with filters
        all_markets = gamma_client.get_markets(
            limit=1000,  # Get more to filter by query
            active=not archived if active_only else None,
            archived=archived,
            volume_num_min=min_volume if min_volume > 0 else None,
            volume_num_max=max_volume,
            liquidity_num_min=min_liquidity,
            liquidity_num_max=max_liquidity,
            tag_id=tag,
            start_date_min=start_date_min,
            end_date_max=end_date_max
        )
        
        # Filter by query text
        query_lower = query.lower()
        markets = []
        for market in all_markets:
            if (query_lower in market.question.lower() or 
                query_lower in market.slug.lower()):
                markets.append(market)
                if len(markets) >= limit:
                    break
        
        if not markets:
            print(f"No markets found matching '{query}' with the specified filters")
            return
        
        print(f"\nFound {len(markets)} markets:\n")
        
        table_data = []
        for i, market in enumerate(markets, 1):
            status = "Archived" if market.archived else ("Active" if market.active else "Inactive")
            table_data.append([
                i,
                market.slug[:40] + "..." if len(market.slug) > 40 else market.slug,
                market.question[:60] + "..." if len(market.question) > 60 else market.question,
                f"${market.volume:,.0f}",
                f"${market.liquidity:,.0f}",
                status
            ])
        
        print(tabulate(table_data, 
                      headers=["#", "Slug", "Question", "Volume", "Liquidity", "Status"],
                      tablefmt="grid"))
    
    def cmd_market_info(self, slug: str, show_book: bool = False, 
                       depth: int = 10) -> None:
        """Get detailed market information."""
        market = self.api.get_market(slug)
        if not market:
            print(f"Market not found: {slug}")
            return
        
        print(f"\n{'='*80}")
        print(f"Market: {market.question}")
        print(f"{'='*80}")
        print(f"Slug: {market.slug}")
        print(f"Condition ID: {market.condition_id}")
        print(f"Outcomes: {', '.join(market.outcomes)}")
        print(f"Status: {'Active' if market.active else 'Inactive'}")
        print(f"Volume: ${market.volume:,.2f}")
        print(f"Liquidity: ${market.liquidity:,.2f}")
        
        # Get current prices
        prices = self.api.get_market_prices(market, 'mid')
        if prices:
            print(f"\nCurrent Prices:")
            for outcome, price in prices.items():
                print(f"  {outcome}: ${price:.4f}")
        
        if show_book:
            print(f"\n{'='*80}")
            print("Order Book")
            print(f"{'='*80}")
            
            books = self.api.get_order_books(market)
            for outcome, book in books.books.items():
                print(f"\n{outcome}:")
                if book.best_bid and book.best_ask:
                    print(f"  Spread: ${book.spread:.4f} ({book.spread_percent:.2f}%)")
                    print(f"  Mid: ${book.mid_price:.4f}")
                
                depth_data = book.get_depth(depth)
                
                # Display bids and asks side by side
                bid_data = []
                ask_data = []
                
                for i in range(min(depth, max(len(depth_data['bids']), len(depth_data['asks'])))):
                    bid_row = ["", "", ""]
                    ask_row = ["", "", ""]
                    
                    if i < len(depth_data['bids']):
                        bid = depth_data['bids'][i]
                        bid_row = [f"${bid.price:.4f}", f"{bid.size:,.0f}", f"${bid.notional:,.2f}"]
                    
                    if i < len(depth_data['asks']):
                        ask = depth_data['asks'][i]
                        ask_row = [f"${ask.price:.4f}", f"{ask.size:,.0f}", f"${ask.notional:,.2f}"]
                    
                    bid_data.append(bid_row)
                    ask_data.append(ask_row)
                
                # Combine bid and ask data
                combined_data = []
                for i, (bid, ask) in enumerate(zip(bid_data, ask_data)):
                    combined_data.append(bid + ["│"] + ask)
                
                headers = ["Bid Price", "Size", "Total", "│", "Ask Price", "Size", "Total"]
                print(tabulate(combined_data, headers=headers, tablefmt="simple"))
    
    def cmd_book(self, slug: str, depth: int = 50, 
                 format: str = "table", output: Optional[str] = None) -> None:
        """View order book for a market."""
        market = self.api.get_market(slug)
        if not market:
            print(f"Market not found: {slug}")
            return
        
        books = self.api.get_order_books(market)
        
        if format == "json":
            data = {
                "market": market.question,
                "timestamp": datetime.now().isoformat(),
                "books": {}
            }
            
            for outcome, book in books.books.items():
                data["books"][outcome] = {
                    "bids": [[str(b.price), str(b.size)] for b in book.bids[:depth]],
                    "asks": [[str(a.price), str(a.size)] for a in book.asks[:depth]],
                    "spread": str(book.spread) if book.spread else None,
                    "mid": str(book.mid_price) if book.mid_price else None
                }
            
            json_str = json.dumps(data, indent=2)
            
            if output:
                Path(output).parent.mkdir(parents=True, exist_ok=True)
                Path(output).write_text(json_str)
                print(f"Order book saved to: {output}")
            else:
                print(json_str)
        else:
            # Table format
            self.cmd_market_info(slug, show_book=True, depth=depth)
    
    def cmd_price(self, slug: str, show_spread: bool = True, 
                  show_midpoint: bool = True) -> None:
        """Get real-time pricing information."""
        market = self.api.get_market(slug)
        if not market:
            print(f"Market not found: {slug}")
            return
        
        print(f"\nMarket: {market.question}")
        print(f"{'='*60}")
        
        # Get all price types
        bid_prices = self.api.get_market_prices(market, 'bid')
        ask_prices = self.api.get_market_prices(market, 'ask')
        mid_prices = self.api.get_market_prices(market, 'mid')
        
        table_data = []
        for outcome in market.outcomes:
            row = [outcome]
            
            if outcome in bid_prices:
                row.append(f"${bid_prices[outcome]:.4f}")
            else:
                row.append("-")
                
            if outcome in ask_prices:
                row.append(f"${ask_prices[outcome]:.4f}")
            else:
                row.append("-")
                
            if show_midpoint and outcome in mid_prices:
                row.append(f"${mid_prices[outcome]:.4f}")
            else:
                row.append("-")
                
            if show_spread and outcome in bid_prices and outcome in ask_prices:
                spread = ask_prices[outcome] - bid_prices[outcome]
                spread_pct = (spread / mid_prices[outcome] * 100) if outcome in mid_prices else 0
                row.append(f"${spread:.4f} ({spread_pct:.2f}%)")
            else:
                row.append("-")
            
            table_data.append(row)
        
        headers = ["Outcome", "Bid", "Ask"]
        if show_midpoint:
            headers.append("Mid")
        if show_spread:
            headers.append("Spread")
            
        print(tabulate(table_data, headers=headers, tablefmt="grid"))
    
    def cmd_portfolio(self, address: str, min_size: float = 10.0,
                     show_pnl: bool = True, format: str = "table") -> None:
        """View user portfolio positions."""
        positions = self.api.get_user_positions(address, min_size=min_size)
        
        if not positions:
            print(f"No positions found for address: {address}")
            return
        
        print(f"\nPortfolio for: {address}")
        print(f"{'='*80}")
        print(f"Total positions: {len(positions)}")
        
        if format == "json":
            print(json.dumps(positions, indent=2))
            return
        
        # Calculate totals
        total_value = sum(p.get('current_value', 0) for p in positions)
        total_invested = sum(p.get('invested', 0) for p in positions)
        total_pnl = total_value - total_invested if show_pnl else 0
        
        print(f"Total value: ${total_value:,.2f}")
        if show_pnl:
            print(f"Total invested: ${total_invested:,.2f}")
            print(f"Total P&L: ${total_pnl:,.2f} ({total_pnl/total_invested*100:.2f}%)")
        
        print(f"\nPositions:")
        
        table_data = []
        for pos in positions:
            row = [
                pos.get('market_title', 'Unknown')[:40] + "...",
                pos.get('outcome', 'Unknown'),
                f"{pos.get('shares', 0):,.0f}",
                f"${pos.get('current_price', 0):.4f}",
                f"${pos.get('current_value', 0):,.2f}"
            ]
            
            if show_pnl:
                pnl = pos.get('current_value', 0) - pos.get('invested', 0)
                pnl_pct = (pnl / pos.get('invested', 1)) * 100 if pos.get('invested', 0) > 0 else 0
                row.append(f"${pnl:,.2f} ({pnl_pct:.1f}%)")
            
            table_data.append(row)
        
        headers = ["Market", "Outcome", "Shares", "Price", "Value"]
        if show_pnl:
            headers.append("P&L")
            
        print(tabulate(table_data, headers=headers, tablefmt="grid"))
    
    def cmd_history(self, address: str, days: int = 30,
                   activity_type: Optional[str] = None,
                   format: str = "table") -> None:
        """Get user trading history."""
        start_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        start_date = start_date.replace(day=start_date.day - days)
        
        activity_types = None
        if activity_type:
            activity_types = [activity_type.upper()]
        
        activities = self.api.get_user_activity(
            address, 
            activity_types=activity_types,
            start_date=start_date
        )
        
        if not activities:
            print(f"No activity found for address: {address}")
            return
        
        print(f"\nActivity History for: {address}")
        print(f"Last {days} days")
        print(f"{'='*80}")
        
        if format == "json":
            print(json.dumps(activities, indent=2))
            return
        
        table_data = []
        for act in activities:
            timestamp = datetime.fromisoformat(act.get('timestamp', ''))
            row = [
                timestamp.strftime("%Y-%m-%d %H:%M"),
                act.get('type', 'Unknown'),
                act.get('market_title', 'Unknown')[:30] + "...",
                act.get('outcome', ''),
                act.get('side', ''),
                f"{act.get('shares', 0):,.0f}",
                f"${act.get('price', 0):.4f}",
                f"${act.get('value', 0):,.2f}"
            ]
            table_data.append(row)
        
        headers = ["Time", "Type", "Market", "Outcome", "Side", "Shares", "Price", "Value"]
        print(tabulate(table_data, headers=headers, tablefmt="grid"))
    
    def cmd_holders(self, slug: str, top: int = 100,
                   outcome: Optional[str] = None,
                   format: str = "table") -> None:
        """Analyze market holders."""
        market = self.api.get_market(slug)
        if not market:
            print(f"Market not found: {slug}")
            return
        
        holders = self.api.get_market_holders(market.condition_id, outcome=outcome, limit=top)
        
        if not holders:
            print(f"No holders found for market: {slug}")
            return
        
        print(f"\nTop {top} Holders")
        print(f"Market: {market.question}")
        if outcome:
            print(f"Outcome: {outcome}")
        print(f"{'='*80}")
        
        if format == "json":
            print(json.dumps(holders, indent=2))
            return
        
        table_data = []
        total_holdings = sum(h.get('shares', 0) for h in holders)
        
        for i, holder in enumerate(holders, 1):
            shares = holder.get('shares', 0)
            pct = (shares / total_holdings * 100) if total_holdings > 0 else 0
            
            row = [
                i,
                holder.get('address', '')[:10] + "...",
                f"{shares:,.0f}",
                f"{pct:.2f}%",
                f"${holder.get('value', 0):,.2f}"
            ]
            table_data.append(row)
        
        headers = ["Rank", "Address", "Shares", "% of Total", "Value"]
        print(tabulate(table_data, headers=headers, tablefmt="grid"))
        
        print(f"\nTotal shares held by top {top}: {total_holdings:,.0f}")
    
    def close(self):
        """Close API connections."""
        self.api.close()

    
    def cmd_markets_advanced(self, **kwargs) -> None:
        """Advanced market search with all filtering options."""
        gamma_client = self.api.gamma_client
        
        # Convert date parameters to ISO format
        date_params = {}
        if kwargs.get('start_after'):
            date_params['start_date_min'] = f"{kwargs['start_after']}T00:00:00Z"
        if kwargs.get('start_before'):
            date_params['start_date_max'] = f"{kwargs['start_before']}T23:59:59Z"
        if kwargs.get('end_after'):
            date_params['end_date_min'] = f"{kwargs['end_after']}T00:00:00Z"
        if kwargs.get('end_before'):
            date_params['end_date_max'] = f"{kwargs['end_before']}T23:59:59Z"
        
        # Build filter parameters
        filter_params = {
            'limit': kwargs.get('limit', 100),
            'offset': kwargs.get('offset', 0),
            'order': kwargs.get('sort', 'volume'),
            'ascending': kwargs.get('ascending', False),
        }
        
        # Add status filters (mutually exclusive)
        if kwargs.get('active'):
            filter_params['active'] = True
        elif kwargs.get('closed'):
            filter_params['closed'] = True
        elif kwargs.get('archived'):
            filter_params['archived'] = True
        
        # Add list parameters
        if kwargs.get('ids'):
            filter_params['id'] = kwargs['ids']
        if kwargs.get('slugs'):
            filter_params['slug'] = kwargs['slugs']
        if kwargs.get('condition_ids'):
            filter_params['condition_ids'] = kwargs['condition_ids']
        if kwargs.get('token_ids'):
            filter_params['clob_token_ids'] = kwargs['token_ids']
        
        # Add numeric filters
        if kwargs.get('min_volume') is not None:
            filter_params['volume_num_min'] = kwargs['min_volume']
        if kwargs.get('max_volume') is not None:
            filter_params['volume_num_max'] = kwargs['max_volume']
        if kwargs.get('min_liquidity') is not None:
            filter_params['liquidity_num_min'] = kwargs['min_liquidity']
        if kwargs.get('max_liquidity') is not None:
            filter_params['liquidity_num_max'] = kwargs['max_liquidity']
        
        # Add tag filters
        if kwargs.get('tag') is not None:
            filter_params['tag_id'] = kwargs['tag']
        if kwargs.get('related_tags'):
            filter_params['related_tags'] = True
        if kwargs.get('clob_only'):
            filter_params['enableOrderBook'] = True
        
        # Merge date parameters
        filter_params.update(date_params)
        
        # Fetch markets
        markets = gamma_client.get_markets(**filter_params)
        
        if not markets:
            print("No markets found with the specified filters")
            return
        
        print(f"\nFound {len(markets)} markets:\n")
        
        # Handle output format
        if kwargs.get('format') == 'json':
            import json
            data = [{
                'id': market.id,
                'slug': market.slug,
                'question': market.question,
                'condition_id': market.condition_id,
                'volume': market.volume,
                'liquidity': market.liquidity,
                'active': market.active,
                'closed': market.closed,
                'archived': market.archived,
                'outcomes': market.outcomes,
                'token_ids': market.token_ids,
                'created_at': market.created_at.isoformat() if market.created_at else None,
                'end_date': market.end_date.isoformat() if market.end_date else None
            } for market in markets]
            
            if kwargs.get('output'):
                with open(kwargs['output'], 'w') as f:
                    json.dump(data, f, indent=2)
                print(f"Saved {len(markets)} markets to {kwargs['output']}")
            else:
                print(json.dumps(data, indent=2))
        else:
            # Table format
            table_data = []
            for i, market in enumerate(markets, 1):
                status = "Archived" if market.archived else ("Active" if market.active else "Inactive")
                table_data.append([
                    i,
                    str(market.id) if market.id else "N/A",
                    market.slug[:30] + "..." if len(market.slug) > 30 else market.slug,
                    market.question[:40] + "..." if len(market.question) > 40 else market.question,
                    f"${market.volume:,.0f}",
                    f"${market.liquidity:,.0f}",
                    status
                ])
            
            print(tabulate(table_data, 
                          headers=["#", "ID", "Slug", "Question", "Volume", "Liquidity", "Status"],
                          tablefmt="grid"))
    
    def cmd_tags(self, tag_id: int, type: str = "markets", 
                 related: bool = False, limit: int = 50) -> None:
        """Explore markets or events by tag."""
        gamma_client = self.api.gamma_client
        
        print(f"\nSearching for {type} with tag ID {tag_id}...\n")
        
        if type == "markets":
            items = gamma_client.get_markets_by_tags(tag_id, include_related=related)[:limit]
            
            if not items:
                print(f"No markets found with tag ID {tag_id}")
                return
            
            print(f"Found {len(items)} markets:\n")
            
            table_data = []
            for i, market in enumerate(items, 1):
                table_data.append([
                    i,
                    market.slug[:40] + "..." if len(market.slug) > 40 else market.slug,
                    market.question[:50] + "..." if len(market.question) > 50 else market.question,
                    f"${market.volume:,.0f}",
                    "Active" if market.active else "Inactive"
                ])
            
            print(tabulate(table_data, 
                          headers=["#", "Slug", "Question", "Volume", "Status"],
                          tablefmt="grid"))
        else:  # events
            items = gamma_client.get_events_by_tags(tag_id, include_related=related)[:limit]
            
            if not items:
                print(f"No events found with tag ID {tag_id}")
                return
            
            print(f"Found {len(items)} events:\n")
            
            table_data = []
            for i, event in enumerate(items, 1):
                table_data.append([
                    i,
                    event.slug[:30] + "..." if len(event.slug) > 30 else event.slug,
                    event.title[:40] + "..." if len(event.title) > 40 else event.title,
                    len(event.markets),
                    f"${event.volume:,.0f}",
                    "Active" if event.active else "Inactive"
                ])
            
            print(tabulate(table_data, 
                          headers=["#", "Slug", "Title", "Markets", "Volume", "Status"],
                          tablefmt="grid"))


def create_parser():
    """Create argument parser for CLI commands."""
    parser = argparse.ArgumentParser(
        description="Mango - Enhanced Polymarket CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        "--api-key",
        help="Polymarket API key"
    )
    
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Search command
    search_parser = subparsers.add_parser("search", help="Search for markets")
    search_parser.add_argument("query", help="Search query")
    search_parser.add_argument("--limit", type=int, default=20, help="Max results")
    search_parser.add_argument("--inactive", action="store_true", help="Include inactive markets")
    search_parser.add_argument("--archived", action="store_true", help="Include archived markets")
    search_parser.add_argument("--min-volume", type=float, default=0, help="Minimum volume filter")
    search_parser.add_argument("--max-volume", type=float, help="Maximum volume filter")
    search_parser.add_argument("--min-liquidity", type=float, help="Minimum liquidity filter")
    search_parser.add_argument("--max-liquidity", type=float, help="Maximum liquidity filter")
    search_parser.add_argument("--tag", type=int, help="Filter by tag ID")
    search_parser.add_argument("--start-after", help="Markets starting after date (YYYY-MM-DD)")
    search_parser.add_argument("--end-before", help="Markets ending before date (YYYY-MM-DD)")
    
    # Market info command
    info_parser = subparsers.add_parser("market-info", help="Get market details")
    info_parser.add_argument("slug", help="Market slug")
    info_parser.add_argument("--show-book", action="store_true", help="Show order book")
    info_parser.add_argument("--depth", type=int, default=10, help="Order book depth")
    
    # Order book command
    book_parser = subparsers.add_parser("book", help="View order book")
    book_parser.add_argument("slug", help="Market slug")
    book_parser.add_argument("--depth", type=int, default=50, help="Book depth")
    book_parser.add_argument("--format", choices=["table", "json"], default="table")
    book_parser.add_argument("-o", "--output", help="Output file for JSON format")
    
    # Price command
    price_parser = subparsers.add_parser("price", help="Get pricing info")
    price_parser.add_argument("slug", help="Market slug")
    price_parser.add_argument("--no-spread", action="store_true", help="Hide spread info")
    price_parser.add_argument("--no-midpoint", action="store_true", help="Hide midpoint")
    
    # Portfolio command
    portfolio_parser = subparsers.add_parser("portfolio", help="View user portfolio")
    portfolio_parser.add_argument("address", help="Wallet address")
    portfolio_parser.add_argument("--min-size", type=float, default=10.0, help="Min position size")
    portfolio_parser.add_argument("--no-pnl", action="store_true", help="Hide P&L info")
    portfolio_parser.add_argument("--format", choices=["table", "json"], default="table")
    
    # History command
    history_parser = subparsers.add_parser("history", help="Get trading history")
    history_parser.add_argument("address", help="Wallet address")
    history_parser.add_argument("--days", type=int, default=30, help="Days of history")
    history_parser.add_argument("--type", help="Activity type filter")
    history_parser.add_argument("--format", choices=["table", "json"], default="table")
    
    # Holders command
    holders_parser = subparsers.add_parser("holders", help="Analyze market holders")
    holders_parser.add_argument("slug", help="Market slug")
    holders_parser.add_argument("--top", type=int, default=100, help="Top N holders")
    holders_parser.add_argument("--outcome", help="Filter by outcome")
    holders_parser.add_argument("--format", choices=["table", "json"], default="table")
    
    # Advanced markets command
    advanced_parser = subparsers.add_parser("markets-advanced", 
                                           help="Advanced market search with all filters")
    advanced_parser.add_argument("--ids", nargs="+", type=int, help="Specific market IDs")
    advanced_parser.add_argument("--slugs", nargs="+", help="Specific market slugs")
    advanced_parser.add_argument("--condition-ids", nargs="+", help="Filter by condition IDs")
    advanced_parser.add_argument("--token-ids", nargs="+", help="Filter by CLOB token IDs")
    advanced_parser.add_argument("--tag", type=int, help="Filter by tag ID")
    advanced_parser.add_argument("--related-tags", action="store_true", help="Include related tags")
    advanced_parser.add_argument("--min-volume", type=float, help="Minimum volume")
    advanced_parser.add_argument("--max-volume", type=float, help="Maximum volume")
    advanced_parser.add_argument("--min-liquidity", type=float, help="Minimum liquidity")
    advanced_parser.add_argument("--max-liquidity", type=float, help="Maximum liquidity")
    advanced_parser.add_argument("--start-after", help="Start date after (YYYY-MM-DD)")
    advanced_parser.add_argument("--start-before", help="Start date before (YYYY-MM-DD)")
    advanced_parser.add_argument("--end-after", help="End date after (YYYY-MM-DD)")
    advanced_parser.add_argument("--end-before", help="End date before (YYYY-MM-DD)")
    advanced_parser.add_argument("--active", action="store_true", help="Only active markets")
    advanced_parser.add_argument("--closed", action="store_true", help="Only closed markets")
    advanced_parser.add_argument("--archived", action="store_true", help="Only archived markets")
    advanced_parser.add_argument("--clob-only", action="store_true", help="Only CLOB tradeable")
    advanced_parser.add_argument("--limit", type=int, default=100, help="Max results")
    advanced_parser.add_argument("--offset", type=int, default=0, help="Pagination offset")
    advanced_parser.add_argument("--sort", default="volume", 
                               choices=["volume", "liquidity", "created", "end_date"],
                               help="Sort field")
    advanced_parser.add_argument("--ascending", action="store_true", help="Sort ascending")
    advanced_parser.add_argument("--format", choices=["table", "json"], default="table")
    advanced_parser.add_argument("-o", "--output", help="Output file for JSON format")
    
    # Tags command
    tags_parser = subparsers.add_parser("tags", help="Explore markets by tags")
    tags_parser.add_argument("tag_id", type=int, help="Tag ID to explore")
    tags_parser.add_argument("--type", choices=["markets", "events"], default="markets",
                           help="Search markets or events")
    tags_parser.add_argument("--related", action="store_true", help="Include related tags")
    tags_parser.add_argument("--limit", type=int, default=50, help="Max results")
    
    # Legacy extract command (for compatibility)
    extract_parser = subparsers.add_parser("extract", help="Extract historical data (legacy)")
    extract_parser.add_argument("url", help="Polymarket URL")
    extract_parser.add_argument("-i", "--interval", default="1d", help="Time interval")
    extract_parser.add_argument("-d", "--days", type=int, default=30, help="Days of history")
    extract_parser.add_argument("-o", "--output", help="Output path")
    extract_parser.add_argument("-f", "--formats", nargs="+", default=["csv"], help="Output formats")
    
    return parser


def main():
    """Main entry point for Mango CLI."""
    parser = create_parser()
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Create CLI instance
    cli = MangoCLI(api_key=args.api_key)
    
    try:
        # Execute command
        if args.command == "search":
            cli.cmd_search(args.query, args.limit, 
                          not args.inactive, args.min_volume,
                          args.archived, args.max_volume,
                          args.min_liquidity, args.max_liquidity,
                          args.tag, args.start_after, args.end_before)
        
        elif args.command == "market-info":
            cli.cmd_market_info(args.slug, args.show_book, args.depth)
        
        elif args.command == "book":
            cli.cmd_book(args.slug, args.depth, args.format, args.output)
        
        elif args.command == "price":
            cli.cmd_price(args.slug, not args.no_spread, not args.no_midpoint)
        
        elif args.command == "portfolio":
            cli.cmd_portfolio(args.address, args.min_size, 
                            not args.no_pnl, args.format)
        
        elif args.command == "history":
            cli.cmd_history(args.address, args.days, args.type, args.format)
        
        elif args.command == "holders":
            cli.cmd_holders(args.slug, args.top, args.outcome, args.format)
        
        elif args.command == "markets-advanced":
            # Convert args namespace to dict for kwargs
            kwargs = vars(args).copy()
            kwargs.pop('command')  # Remove command from kwargs
            kwargs.pop('api_key', None)  # Remove api_key from kwargs
            cli.cmd_markets_advanced(**kwargs)
        
        elif args.command == "tags":
            cli.cmd_tags(args.tag_id, args.type, args.related, args.limit)
        
        elif args.command == "extract":
            # Legacy support - redirect to polymarket_extract
            from polymarket_extract import main as extract_main
            sys.argv = ["polymarket-extract", args.url]
            if args.interval:
                sys.argv.extend(["-i", args.interval])
            if args.days:
                sys.argv.extend(["-d", str(args.days)])
            if args.output:
                sys.argv.extend(["-o", args.output])
            if args.formats:
                sys.argv.extend(["-f"] + args.formats)
            return extract_main()
        
        return 0
        
    except KeyboardInterrupt:
        print("\nInterrupted by user")
        return 1
    except Exception as e:
        logger.exception("Error in CLI")
        print(f"\nError: {e}")
        return 1
    finally:
        cli.close()


if __name__ == "__main__":
    sys.exit(main())