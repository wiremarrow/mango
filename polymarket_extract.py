#!/usr/bin/env python3
"""
Polymarket Data Extractor

Main script for extracting historical price data from Polymarket markets.
Provides a clean CLI interface for data extraction and export.
"""

import argparse
import sys
import logging
import time
import gc
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Union

from polymarket import (
    PolymarketAPI, PolymarketURLParser, DataProcessor,
    MarketHistoricalData, TimeInterval, EventHistoricalData, Market
)
from polymarket.config import (
    DEFAULT_DAYS_BACK, DEFAULT_INTERVAL,
    LOG_LEVEL, LOG_FORMAT, DEFAULT_API_KEY, MARKET_SEARCH_LIMIT
)
from polymarket.exceptions import (
    PolymarketError, InvalidURLError, MarketNotFoundError
)


# Configure logging
logging.basicConfig(level=LOG_LEVEL, format=LOG_FORMAT)
logger = logging.getLogger(__name__)


class PolymarketExtractor:
    """Main class for extracting Polymarket historical data."""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the extractor with optional API key."""
        self.api = PolymarketAPI(api_key or DEFAULT_API_KEY)
        self.parser = PolymarketURLParser()
        
    # Auto-dates detection methods removed for simplicity
    
    def extract_from_url(self,
                        url: str,
                        interval: str = DEFAULT_INTERVAL,
                        days_back: int = DEFAULT_DAYS_BACK,
                        start_date: Optional[str] = None,
                        end_date: Optional[str] = None,
                        auto_dates: bool = False,
                        use_max_interval: bool = False) -> Optional[MarketHistoricalData]:
        """
        Extract historical data from a Polymarket URL.
        
        Args:
            url: Polymarket market or event URL
            interval: Time interval for data points
            days_back: Number of days of history (if start_date not provided)
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            
        Returns:
            MarketHistoricalData object or None if extraction fails
        """
        try:
            # Parse the URL
            logger.info(f"Parsing URL: {url}")
            parsed_url = self.parser.parse(url)
            
            # Handle event URLs
            if self.parser.is_event_url(url):
                event_slug = parsed_url['event_slug']
                logger.info(f"Event URL detected. Fetching event: {event_slug}")
                
                # Fetch the event data directly
                event = self.api.get_event(event_slug)
                
                if not event:
                    logger.warning(f"Event not found: {event_slug}")
                    print(f"\nError: Event not found: {event_slug}")
                    print("Tip: Make sure you're using the exact event URL from Polymarket.com")
                    return None
                
                # Display event information
                print(f"\nEvent: {event.title}")
                print(f"Description: {event.description[:200]}..." if len(event.description) > 200 else f"Description: {event.description}")
                
                if not event.markets:
                    logger.warning(f"No markets found in event: {event_slug}")
                    print(f"\nNo markets found in this event.")
                    return None
                
                # Group markets by negRiskMarketID if it's a negRisk event
                if event.neg_risk and event.neg_risk_market_id:
                    print(f"\nThis is a group prediction market with {len(event.markets)} options:")
                else:
                    print(f"\nFound {len(event.markets)} markets:")
                
                # Display markets
                for i, market in enumerate(event.markets, 1):
                    if market.group_item_title:
                        print(f"\n{i}. {market.group_item_title}")
                    else:
                        print(f"\n{i}. {market.question}")
                    
                    if market.slug:
                        if parsed_url['event_slug']:
                            market_url = self.parser.build_market_url(event_slug, market.slug)
                        else:
                            market_url = f"{self.parser.BASE_URL}/{market.slug}"
                        print(f"   URL: {market_url}")
                    
                    print(f"   Active: {market.active}, Volume: ${market.volume:,.2f}")
                    
                    # Show current prices if available
                    if hasattr(market, 'outcome_prices') and market.metadata.get('outcomePrices'):
                        prices = market.metadata.get('outcomePrices', [])
                        if len(prices) >= 2:
                            print(f"   Current: Yes: ${float(prices[0]):.3f}, No: ${float(prices[1]):.3f}")
                
                print("\nPlease use a specific market URL from the list above.")
                return None
            
            # Get the market slug
            slug = self.parser.get_api_slug(url)
            logger.info(f"Extracted slug: {slug}")
            
            # Fetch market metadata
            logger.info("Fetching market metadata...")
            market = self.api.get_market(slug)
            
            if not market:
                raise MarketNotFoundError(slug)
            
            logger.info(f"Found market: {market.question}")
            print(f"\nMarket: {market.question}")
            print(f"Condition ID: {market.condition_id}")
            print(f"Outcomes: {', '.join(market.outcomes)}")
            
            # Check if market has valid token IDs
            if not market.token_ids or all(not tid for tid in market.token_ids):
                logger.warning(f"Market has no valid token IDs")
                if market.is_inactive_negrisk_option():
                    print("\nError: This option in the grouped market is not yet active for trading.")
                    print(f"Market: {market.question}")
                    print("This appears to be a placeholder or unactivated option in a negRisk market.")
                    print("\nSuggestions:")
                    print("1. Try extracting active options from the event page")
                    print("2. Use --extract-all-markets on the event URL (active options only)")
                else:
                    print("\nError: This market does not have tradeable tokens yet.")
                    print("It may be a future market that hasn't been activated for trading.")
                return None
            
            # Calculate time range
            if start_date:
                start_ts = int(datetime.strptime(start_date, "%Y-%m-%d").timestamp())
            else:
                start_ts = int(time.time()) - (days_back * 24 * 60 * 60)
                
            if end_date:
                end_ts = int(datetime.strptime(end_date, "%Y-%m-%d").timestamp())
            else:
                end_ts = int(time.time())
            
            # Fetch price history with retry logic
            logger.info(f"Fetching price history (interval: {interval})...")
            print(f"\nFetching price history...")
            
            price_histories = None
            retry_count = 0
            max_retries = 3
            current_start = start_ts
            current_end = end_ts
            
            # Standard retry logic with date ranges
            while retry_count < max_retries:
                try:
                    price_histories = self.api.get_price_history(
                        market, interval, current_start, current_end
                    )
                    
                    if price_histories:
                        break  # Success!
                        
                except Exception as e:
                    if "interval is too long" in str(e) and retry_count < max_retries - 1:
                        # Reduce the time range by 50%
                        time_span = current_end - current_start
                        new_span = time_span // 2
                        current_start = current_end - new_span
                        
                        logger.warning(f"Time range too long, reducing to {new_span // (24*60*60)} days...")
                        print(f"API limit reached, adjusting to {new_span // (24*60*60)} days...")
                        retry_count += 1
                        continue
                    else:
                        # Re-raise other errors or if we've exhausted retries
                        raise
                
                # If we get here with no data and no exception, break
                break
            
            if not price_histories:
                logger.warning("No price history available")
                print("\nWarning: No historical price data available for this market")
                return None
            
            # Create MarketHistoricalData object
            data = MarketHistoricalData(
                market=market,
                price_histories=price_histories
            )
            
            # Print summary
            for outcome, history in price_histories.items():
                if history.price_points:
                    print(f"\n{outcome}:")
                    print(f"  Data points: {history.data_points_count}")
                    print(f"  Latest price: ${history.latest_price:.4f}")
                    if history.price_change is not None:
                        print(f"  Change: ${history.price_change:.4f} ({history.price_change_percent:.2f}%)")
            
            return data
            
        except InvalidURLError as e:
            logger.error(f"Invalid URL: {e}")
            print(f"\nError: {e}")
            return None
        except MarketNotFoundError as e:
            logger.error(f"Market not found: {e}")
            print(f"\nError: {e}")
            print("Tip: Make sure you're using the exact market URL from Polymarket.com")
            return None
        except PolymarketError as e:
            logger.error(f"Polymarket error: {e}")
            print(f"\nError: {e}")
            return None
        except Exception as e:
            logger.exception("Unexpected error")
            print(f"\nUnexpected error: {e}")
            return None
    
    def extract_all_event_markets(self,
                                 event_slug: str,
                                 interval: Union[str, TimeInterval] = DEFAULT_INTERVAL,
                                 days_back: int = DEFAULT_DAYS_BACK,
                                 start_date: Optional[str] = None,
                                 end_date: Optional[str] = None,
                                 chunk_size: Optional[int] = None,
                                 enable_gc: bool = False,
                                 auto_dates: bool = False,
                                 use_max_interval: bool = False) -> Optional[EventHistoricalData]:
        """
        Extract historical data for all markets in an event.
        
        Args:
            event_slug: Event slug from URL
            interval: Time interval for data points
            days_back: Number of days of history (if start_date not provided)
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            chunk_size: Process markets in chunks (None = process all at once)
            enable_gc: Enable garbage collection between markets
            
        Returns:
            EventHistoricalData object or None if extraction fails
        """
        try:
            # Fetch the event
            logger.info(f"Fetching event: {event_slug}")
            event = self.api.get_event(event_slug)
            
            if not event:
                logger.warning(f"Event not found: {event_slug}")
                print(f"\nError: Event not found: {event_slug}")
                return None
            
            if not event.markets:
                logger.warning(f"No markets found in event: {event_slug}")
                print(f"\nNo markets found in this event.")
                return None
            
            # Display event information
            print(f"\nEvent: {event.title}")
            
            # Count active vs inactive markets
            active_markets = []
            inactive_negrisk = 0
            other_inactive = 0
            
            for market in event.markets:
                if market.token_ids and any(tid for tid in market.token_ids):
                    active_markets.append(market)
                elif market.is_inactive_negrisk_option():
                    inactive_negrisk += 1
                else:
                    other_inactive += 1
            
            print(f"Total markets: {len(event.markets)}")
            print(f"Active markets: {len(active_markets)}")
            if inactive_negrisk > 0:
                print(f"Inactive negRisk options: {inactive_negrisk} (will be skipped)")
            if other_inactive > 0:
                print(f"Other inactive markets: {other_inactive} (will be skipped)")
            
            # Calculate time range
            if start_date:
                start_ts = int(datetime.strptime(start_date, "%Y-%m-%d").timestamp())
            else:
                start_ts = int(time.time()) - (days_back * 24 * 60 * 60)
                
            if end_date:
                end_ts = int(datetime.strptime(end_date, "%Y-%m-%d").timestamp())
            else:
                end_ts = int(time.time())
            
            # Create EventHistoricalData object
            event_data = EventHistoricalData(event=event)
            
            # Extract data for each market
            successful = 0
            failed = 0
            
            for i, market in enumerate(event.markets, 1):
                market_name = market.group_item_title or market.question[:50]
                print(f"\n[{i}/{len(event.markets)}] Extracting: {market_name}...")
                
                # Skip markets without valid token IDs
                if not market.token_ids or all(not tid for tid in market.token_ids):
                    if market.is_inactive_negrisk_option():
                        print(f"  Skipping: Inactive negRisk option (placeholder)")
                    else:
                        print(f"  Skipping: No tradeable tokens available")
                    failed += 1
                    continue
                
                try:
                    # Fetch price history for this market with retry logic
                    price_histories = None
                    retry_count = 0
                    max_retries = 3
                    current_start = start_ts
                    current_end = end_ts
                    
                    # Standard date range approach
                    while retry_count < max_retries:
                            try:
                                price_histories = self.api.get_price_history(
                                    market, interval, current_start, current_end
                                )
                                break  # Success!
                            except Exception as api_error:
                                if "interval is too long" in str(api_error) and retry_count < max_retries - 1:
                                    # Reduce the time range by 50%
                                    time_span = current_end - current_start
                                    new_span = time_span // 2
                                    current_start = current_end - new_span
                                    
                                    logger.warning(f"Time range too long for {market_name}, reducing to {new_span // (24*60*60)} days...")
                                    retry_count += 1
                                    continue
                                else:
                                    # Re-raise for other errors or if exhausted retries
                                    raise
                    
                    if price_histories:
                        # Create MarketHistoricalData
                        market_data = MarketHistoricalData(
                            market=market,
                            price_histories=price_histories
                        )
                        event_data.market_data[market.slug] = market_data
                        successful += 1
                        
                        # Show brief summary
                        for outcome, history in price_histories.items():
                            if history.price_points:
                                print(f"  {outcome}: {history.data_points_count} data points, "
                                     f"latest: ${history.latest_price:.4f}")
                    else:
                        print(f"  Warning: No data available")
                        failed += 1
                        
                except Exception as e:
                    logger.error(f"Failed to extract market {market.slug}: {e}")
                    print(f"  Error: {e}")
                    failed += 1
                
                # Memory management and rate limiting
                if enable_gc:
                    gc.collect()
                    logger.debug(f"Garbage collection after market {i}/{len(event.markets)}")
                
                # Rate limiting - small delay between markets
                if i < len(event.markets):
                    time.sleep(0.5)  # 500ms delay
            
            print(f"\n\nExtraction complete: {successful} succeeded, {failed} failed")
            
            if event_data.has_data:
                return event_data
            else:
                print("\nNo data was successfully extracted.")
                return None
                
        except Exception as e:
            logger.exception("Failed to extract event markets")
            print(f"\nError extracting event markets: {e}")
            return None
    
    def close(self):
        """Close API connections."""
        self.api.close()


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Extract historical price data from Polymarket markets",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Extract 30 days of daily data
  %(prog)s "https://polymarket.com/event/market-name"
  
  # Extract hourly data for the last 7 days
  %(prog)s "https://polymarket.com/event/market-name" -i 1h -d 7
  
  # Extract data for a specific date range
  %(prog)s "https://polymarket.com/event/market-name" --start 2024-01-01 --end 2024-01-31
  
  # Export to CSV (default format)
  %(prog)s "https://polymarket.com/event/market-name" -o market_data
  
  # Get maximum available data
  %(prog)s "https://polymarket.com/event/market-name" -i max
        """
    )
    
    parser.add_argument(
        "url",
        help="Polymarket market or event URL"
    )
    
    parser.add_argument(
        "-i", "--interval",
        default=DEFAULT_INTERVAL,
        choices=["1m", "1h", "6h", "1d", "1w", "max"],
        help=f"Time interval for data points (default: {DEFAULT_INTERVAL})"
    )
    
    parser.add_argument(
        "-d", "--days",
        type=int,
        default=DEFAULT_DAYS_BACK,
        help=f"Number of days of history to fetch (default: {DEFAULT_DAYS_BACK})"
    )
    
    parser.add_argument(
        "--start",
        help="Start date in YYYY-MM-DD format"
    )
    
    parser.add_argument(
        "--end",
        help="End date in YYYY-MM-DD format"
    )
    
    parser.add_argument(
        "-o", "--output",
        help="Output file path (without extension)"
    )
    
    # CSV is the only supported format now
    
    parser.add_argument(
        "--api-key",
        help="CLOB API key (optional, can also use POLYMARKET_API_KEY env var)"
    )
    
    parser.add_argument(
        "--extract-all-markets",
        action="store_true",
        help="Extract data for all markets in an event (only works with event URLs)"
    )
    
    # Column format is always 'short' now
    
    parser.add_argument(
        "--streaming",
        action="store_true",
        help="Use memory-efficient streaming mode for CSV exports (auto-enabled for large events)"
    )
    
    # Memory optimization simplified to just --streaming
    
    # Date detection removed for simplicity
    
    parser.add_argument(
        "--summary",
        action="store_true",
        help="Print summary report to console"
    )
    
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Create extractor
    extractor = PolymarketExtractor(api_key=args.api_key)
    
    try:
        # Check if we should extract all markets from an event
        if args.extract_all_markets:
            # Parse URL to get event slug
            parsed_url = extractor.parser.parse(args.url)
            
            if not extractor.parser.is_event_url(args.url):
                print("\nError: --extract-all-markets can only be used with event URLs")
                return 1
            
            event_slug = parsed_url['event_slug']
            
            # Check if we should auto-enable streaming for large events
            event = extractor.api.get_event(event_slug)
            auto_streaming = event and len(event.markets) > 10 and not args.streaming
            
            if auto_streaming:
                print(f"\nAuto-enabling streaming mode for {len(event.markets)} markets")
            
            # Enable optimizations if requested
            use_streaming = args.streaming or auto_streaming
            
            # Extract all markets
            event_data = extractor.extract_all_event_markets(
                event_slug,
                interval=args.interval,
                days_back=args.days,
                start_date=args.start,
                end_date=args.end,
                chunk_size=None,
                enable_gc=use_streaming,
                auto_dates=False,
                use_max_interval=False
            )
            
            if not event_data:
                logger.error("Failed to extract event data")
                return 1
                
            if not event_data.has_data:
                logger.warning("No historical price data available")
                print("\nWarning: No historical price data available for any markets")
                return 1
            
            # Export event data
            if args.output:
                print(f"\nExporting event data...")
                
                try:
                    # If output path doesn't start with / or contain /, prepend data/
                    if not args.output.startswith('/') and '/' not in args.output:
                        filepath = f"data/{args.output}.csv"
                    else:
                        filepath = f"{args.output}.csv"
                    
                    # Check if we should use streaming
                    if use_streaming:
                        print("Using memory-efficient streaming mode...")
                        DataProcessor.stream_event_to_csv(event_data, filepath)
                    else:
                        DataProcessor.save_event_to_file(event_data, filepath)
                    
                    print(f"  Saved CSV: {filepath}")
                    
                except Exception as e:
                    logger.error(f"Failed to save CSV: {e}")
                    print(f"  Failed to save CSV: {e}")
            else:
                print("\nExtraction complete. Use -o to specify output path.")
        
        else:
            # Single market extraction (original behavior)
            data = extractor.extract_from_url(
                args.url,
                interval=args.interval,
                days_back=args.days,
                start_date=args.start,
                end_date=args.end,
                auto_dates=False,
                use_max_interval=False
            )
            
            if not data:
                logger.error("Failed to extract historical data")
                return 1
                
            if not data.has_data:
                logger.warning("No historical price data available")
                print("\nWarning: No historical price data available for this market")
                return 1
                
            # Print summary if requested
            if args.summary:
                print("\n" + DataProcessor.create_summary_report(data))
            
            # Export data if output path provided
            if args.output:
                print(f"\nExporting data...")
                
                try:
                    # If output path doesn't start with / or contain /, prepend data/
                    if not args.output.startswith('/') and '/' not in args.output:
                        filepath = f"data/{args.output}.csv"
                    else:
                        filepath = f"{args.output}.csv"
                    
                    DataProcessor.save_to_file(
                        data, 
                        filepath, 
                        include_metadata=True
                    )
                        
                    print(f"  Saved CSV: {filepath}")
                    
                except Exception as e:
                    logger.error(f"Failed to save CSV: {e}")
                    print(f"  Failed to save CSV: {e}")
            else:
                # If no output specified, print CSV to console
                print("\n" + DataProcessor.to_csv(data, include_metadata=True))
                
        return 0
        
    except KeyboardInterrupt:
        print("\nInterrupted by user")
        return 1
    except Exception as e:
        logger.exception("Unexpected error in main")
        print(f"\nError: {e}")
        return 1
    finally:
        extractor.close()


if __name__ == "__main__":
    sys.exit(main())