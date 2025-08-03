#!/usr/bin/env python3
"""
Polymarket Data Extractor CLI

Command-line interface for extracting historical price data from Polymarket markets.
"""

import argparse
import sys
import logging
from pathlib import Path

from polymarket import (
    PolymarketExtractor, DataProcessor, CLIReporter
)
from polymarket.utils.config import (
    DEFAULT_DAYS_BACK, DEFAULT_INTERVAL,
    LOG_LEVEL, LOG_FORMAT
)
from polymarket.utils.constants import (
    AUTO_STREAMING_THRESHOLD, SUCCESS_DATA_SAVED
)


# Configure logging
logging.basicConfig(level=LOG_LEVEL, format=LOG_FORMAT)
logger = logging.getLogger(__name__)


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
        "--fidelity",
        type=int,
        help="Resolution of data in minutes (e.g., 5 for 5-minute intervals, 60 for hourly)"
    )
    
    parser.add_argument(
        "-o", "--output",
        help="Output file path (without extension)"
    )
    
    parser.add_argument(
        "--api-key",
        help="CLOB API key (optional, can also use POLYMARKET_API_KEY env var)"
    )
    
    parser.add_argument(
        "--extract-all-markets",
        action="store_true",
        help="Extract data for all markets in an event (only works with event URLs)"
    )
    
    parser.add_argument(
        "--streaming",
        action="store_true",
        help="Use memory-efficient streaming mode for CSV exports (auto-enabled for large events)"
    )
    
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
    
    # Create extractor and reporter
    extractor = PolymarketExtractor(api_key=args.api_key, verbose=args.verbose)
    reporter = CLIReporter(verbose=args.verbose)
    
    try:
        # Check if we should extract all markets from an event
        if args.extract_all_markets:
            # Parse URL to get event slug
            parsed_url = extractor.parser.parse(args.url)
            
            if not extractor.parser.is_event_url(args.url):
                reporter.error("--extract-all-markets can only be used with event URLs")
                return 1
            
            event_slug = parsed_url['event_slug']
            
            # Check if we should auto-enable streaming for large events
            event = extractor.api.get_event(event_slug)
            auto_streaming = event and len(event.markets) > AUTO_STREAMING_THRESHOLD and not args.streaming
            
            if auto_streaming:
                reporter.print(f"\nAuto-enabling streaming mode for {len(event.markets)} markets")
            
            # Enable optimizations if requested
            use_streaming = args.streaming or auto_streaming
            
            # Extract all markets
            event_data = extractor.extract_all_event_markets(
                event_slug,
                interval=args.interval,
                days_back=args.days,
                start_date=args.start,
                end_date=args.end,
                enable_gc=use_streaming,
                fidelity=args.fidelity
            )
            
            if not event_data:
                logger.error("Failed to extract event data")
                return 1
                
            if not event_data.has_data:
                logger.warning("No historical price data available")
                reporter.warning("No historical price data available for any markets")
                return 1
            
            # Export event data
            if args.output:
                reporter.print("\nExporting event data...")
                
                try:
                    # If output path doesn't start with / or contain /, prepend data/
                    if not args.output.startswith('/') and '/' not in args.output:
                        filepath = f"data/{args.output}.csv"
                    else:
                        filepath = f"{args.output}.csv"
                    
                    # Check if we should use streaming
                    if use_streaming:
                        reporter.print("Using memory-efficient streaming mode...")
                        DataProcessor.stream_event_to_csv(event_data, filepath)
                    else:
                        DataProcessor.save_event_to_file(event_data, filepath)
                    
                    reporter.print(f"  {SUCCESS_DATA_SAVED.format(format='CSV', filepath=filepath)}")
                    
                except Exception as e:
                    logger.error(f"Failed to save CSV: {e}")
                    reporter.error(f"Failed to save CSV: {e}")
            else:
                reporter.print("\nExtraction complete. Use -o to specify output path.")
        
        else:
            # Single market extraction (original behavior)
            data = extractor.extract_from_url(
                args.url,
                interval=args.interval,
                days_back=args.days,
                start_date=args.start,
                end_date=args.end,
                fidelity=args.fidelity
            )
            
            if not data:
                logger.error("Failed to extract historical data")
                return 1
                
            if not data.has_data:
                logger.warning("No historical price data available")
                reporter.warning("No historical price data available for this market")
                return 1
                
            # Print summary if requested
            if args.summary:
                reporter.print("\n" + DataProcessor.create_summary_report(data))
            
            # Export data if output path provided
            if args.output:
                reporter.print("\nExporting data...")
                
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
                        
                    reporter.print(f"  {SUCCESS_DATA_SAVED.format(format='CSV', filepath=filepath)}")
                    
                except Exception as e:
                    logger.error(f"Failed to save CSV: {e}")
                    reporter.error(f"Failed to save CSV: {e}")
            else:
                # If no output specified, print CSV to console
                reporter.print("\n" + DataProcessor.to_csv(data, include_metadata=True))
                
        return 0
        
    except KeyboardInterrupt:
        reporter.print("\nInterrupted by user")
        return 1
    except Exception as e:
        logger.exception("Unexpected error in main")
        reporter.error(f"Error: {e}")
        return 1
    finally:
        extractor.close()


if __name__ == "__main__":
    sys.exit(main())