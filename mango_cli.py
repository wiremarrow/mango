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
                   active_only: bool = True, min_volume: float = 0) -> None:
        """Search for markets by keyword."""
        logger.info(f"Searching for markets: '{query}'")
        markets = self.api.search_markets(query, limit)
        
        if active_only:
            markets = [m for m in markets if m.active]
        if min_volume > 0:
            markets = [m for m in markets if m.volume >= min_volume]
        
        if not markets:
            print(f"No markets found matching '{query}'")
            return
        
        print(f"\nFound {len(markets)} markets:\n")
        
        table_data = []
        for i, market in enumerate(markets, 1):
            table_data.append([
                i,
                market.slug[:40] + "..." if len(market.slug) > 40 else market.slug,
                market.question[:60] + "..." if len(market.question) > 60 else market.question,
                f"${market.volume:,.0f}",
                "Active" if market.active else "Inactive"
            ])
        
        print(tabulate(table_data, 
                      headers=["#", "Slug", "Question", "Volume", "Status"],
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
    search_parser.add_argument("--min-volume", type=float, default=0, help="Minimum volume filter")
    
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
                          not args.inactive, args.min_volume)
        
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