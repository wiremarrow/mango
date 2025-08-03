"""
Polymarket data extraction logic.

This module contains the core business logic for extracting historical data
from Polymarket markets and events.
"""

import logging
import time
import gc
from datetime import datetime
from typing import Optional, Union

from ..api import PolymarketAPI
from ..utils.parser import PolymarketURLParser
from ..models import MarketHistoricalData, EventHistoricalData, TimeInterval
from .cli_output import CLIReporter
from ..utils.constants import (
    MAX_RETRIES, RATE_LIMIT_CHUNK_DELAY,
    MAX_MARKET_QUESTION_DISPLAY,
    SUCCESS_EXTRACTION_COMPLETE
)
from ..utils.exceptions import (
    PolymarketError, InvalidURLError, MarketNotFoundError
)
from ..utils.config import DEFAULT_API_KEY, DEFAULT_INTERVAL, DEFAULT_DAYS_BACK


logger = logging.getLogger(__name__)


class PolymarketExtractor:
    """Main class for extracting Polymarket historical data."""
    
    def __init__(self, api_key: Optional[str] = None, verbose: bool = False):
        """
        Initialize the extractor with optional API key.
        
        Args:
            api_key: Optional API key for enhanced rate limits
            verbose: Whether to show verbose output
        """
        self.api = PolymarketAPI(api_key or DEFAULT_API_KEY)
        self.parser = PolymarketURLParser()
        self.reporter = CLIReporter(verbose=verbose)
    
    def extract_from_url(self,
                        url: str,
                        interval: str = DEFAULT_INTERVAL,
                        days_back: int = DEFAULT_DAYS_BACK,
                        start_date: Optional[str] = None,
                        end_date: Optional[str] = None,
) -> Optional[MarketHistoricalData]:
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
                self._handle_event_url(parsed_url, url)
                return None
            
            # Extract market data
            market = self._fetch_market(parsed_url)
            if not market:
                return None
            
            # Display market info
            self.reporter.market_summary(market)
            
            # Validate market has tokens
            if not self._validate_market_tokens(market):
                return None
            
            # Calculate time range
            start_ts, end_ts = self._calculate_time_range(start_date, end_date, days_back)
            
            # Fetch price history
            price_histories = self._fetch_price_history_with_retry(
                market, interval, start_ts, end_ts
            )
            
            if not price_histories:
                self.reporter.warning("No historical price data available for this market")
                return None
            
            # Create result object
            data = MarketHistoricalData(
                market=market,
                price_histories=price_histories
            )
            
            # Display summary
            for outcome, history in price_histories.items():
                self.reporter.price_history_summary(outcome, history)
            
            return data
            
        except InvalidURLError as e:
            logger.error(f"Invalid URL: {e}")
            self.reporter.error(str(e))
            return None
        except MarketNotFoundError as e:
            logger.error(f"Market not found: {e}")
            self.reporter.error(str(e))
            self.reporter.print("Tip: Make sure you're using the exact market URL from Polymarket.com")
            return None
        except PolymarketError as e:
            logger.error(f"Polymarket error: {e}")
            self.reporter.error(str(e))
            return None
        except Exception as e:
            logger.exception("Unexpected error")
            self.reporter.error(f"Unexpected error: {e}")
            return None
    
    def extract_all_event_markets(self,
                                 event_slug: str,
                                 interval: Union[str, TimeInterval] = DEFAULT_INTERVAL,
                                 days_back: int = DEFAULT_DAYS_BACK,
                                 start_date: Optional[str] = None,
                                 end_date: Optional[str] = None,
                                 enable_gc: bool = False) -> Optional[EventHistoricalData]:
        """
        Extract historical data for all markets in an event.
        
        Args:
            event_slug: Event slug from URL
            interval: Time interval for data points
            days_back: Number of days of history (if start_date not provided)
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            enable_gc: Enable garbage collection between markets for memory efficiency
            
        Returns:
            EventHistoricalData object or None if extraction fails
        """
        try:
            # Fetch the event
            event = self._fetch_event(event_slug)
            if not event or not event.markets:
                return None
            
            # Display event info
            self.reporter.event_summary(event)
            
            # Analyze markets
            active_markets, inactive_negrisk, other_inactive = self._analyze_markets(event.markets)
            self.reporter.extraction_statistics(
                len(event.markets), len(active_markets), 
                inactive_negrisk, other_inactive
            )
            
            # Calculate time range
            start_ts, end_ts = self._calculate_time_range(start_date, end_date, days_back)
            
            # Create result object
            event_data = EventHistoricalData(event=event)
            
            # Extract data for each market
            successful, failed = self._extract_markets(
                event.markets, event_data, interval, 
                start_ts, end_ts, enable_gc
            )
            
            # Display final statistics
            self.reporter.print(f"\n\n{SUCCESS_EXTRACTION_COMPLETE.format(successful=successful, failed=failed)}")
            
            if event_data.has_data:
                return event_data
            else:
                self.reporter.print("\nNo data was successfully extracted.")
                return None
                
        except Exception as e:
            logger.exception("Failed to extract event markets")
            self.reporter.error(f"Error extracting event markets: {e}")
            return None
    
    def _handle_event_url(self, parsed_url: dict, url: str) -> None:
        """Handle event URL by displaying available markets."""
        event_slug = parsed_url['event_slug']
        logger.info(f"Event URL detected. Fetching event: {event_slug}")
        
        event = self.api.get_event(event_slug)
        if not event:
            self.reporter.error(f"Event not found: {event_slug}")
            self.reporter.print("Tip: Make sure you're using the exact event URL from Polymarket.com")
            return
        
        self.reporter.event_summary(event)
        
        if not event.markets:
            self.reporter.print("\nNo markets found in this event.")
            return
        
        # Display market type
        if event.neg_risk and event.neg_risk_market_id:
            self.reporter.print(f"\nThis is a group prediction market with {len(event.markets)} options:")
        else:
            self.reporter.print(f"\nFound {len(event.markets)} markets:")
        
        # Display markets
        for i, market in enumerate(event.markets, 1):
            self.reporter.market_list_item(i, market, event_slug)
        
        self.reporter.print("\nPlease use a specific market URL from the list above.")
    
    def _fetch_market(self, parsed_url: dict):
        """Fetch market data from API."""
        slug = self.parser.get_api_slug(parsed_url['url'])
        logger.info(f"Extracted slug: {slug}")
        
        logger.info("Fetching market metadata...")
        market = self.api.get_market(slug)
        
        if not market:
            raise MarketNotFoundError(slug)
        
        logger.info(f"Found market: {market.question}")
        return market
    
    def _fetch_event(self, event_slug: str):
        """Fetch event data from API."""
        logger.info(f"Fetching event: {event_slug}")
        event = self.api.get_event(event_slug)
        
        if not event:
            logger.warning(f"Event not found: {event_slug}")
            self.reporter.error(f"Event not found: {event_slug}")
            return None
        
        if not event.markets:
            logger.warning(f"No markets found in event: {event_slug}")
            self.reporter.print("\nNo markets found in this event.")
            return None
        
        return event
    
    def _validate_market_tokens(self, market) -> bool:
        """Validate that market has tradeable tokens."""
        if not market.token_ids or all(not tid for tid in market.token_ids):
            logger.warning("Market has no valid token IDs")
            
            if market.is_inactive_negrisk_option():
                self.reporter.inactive_negrisk_error(market)
            else:
                self.reporter.no_tokens_error()
            
            return False
        return True
    
    def _calculate_time_range(self, start_date: Optional[str], 
                             end_date: Optional[str], 
                             days_back: int) -> tuple:
        """Calculate timestamp range for data extraction."""
        if start_date:
            start_ts = int(datetime.strptime(start_date, "%Y-%m-%d").timestamp())
        else:
            start_ts = int(time.time()) - (days_back * 24 * 60 * 60)
            
        if end_date:
            end_ts = int(datetime.strptime(end_date, "%Y-%m-%d").timestamp())
        else:
            end_ts = int(time.time())
        
        return start_ts, end_ts
    
    def _fetch_price_history_with_retry(self, market, interval: str, 
                                      start_ts: int, end_ts: int):
        """Fetch price history with retry logic for API limits."""
        logger.info(f"Fetching price history (interval: {interval})...")
        self.reporter.print("\nFetching price history...")
        
        retry_count = 0
        current_start = start_ts
        current_end = end_ts
        
        while retry_count < MAX_RETRIES:
            try:
                price_histories = self.api.get_price_history(
                    market, interval, current_start, current_end
                )
                
                if price_histories:
                    return price_histories
                    
            except Exception as e:
                if "interval is too long" in str(e) and retry_count < MAX_RETRIES - 1:
                    # Reduce the time range by 50%
                    time_span = current_end - current_start
                    new_span = time_span // 2
                    current_start = current_end - new_span
                    
                    days = new_span // (24*60*60)
                    logger.warning(f"Time range too long, reducing to {days} days...")
                    self.reporter.print(f"API limit reached, adjusting to {days} days...")
                    retry_count += 1
                    continue
                else:
                    # Re-raise other errors or if we've exhausted retries
                    raise
            
            # If we get here with no data and no exception, break
            break
        
        return None
    
    def _analyze_markets(self, markets: list) -> tuple:
        """Analyze markets to categorize active vs inactive."""
        active_markets = []
        inactive_negrisk = 0
        other_inactive = 0
        
        for market in markets:
            if market.token_ids and any(tid for tid in market.token_ids):
                active_markets.append(market)
            elif market.is_inactive_negrisk_option():
                inactive_negrisk += 1
            else:
                other_inactive += 1
        
        return active_markets, inactive_negrisk, other_inactive
    
    def _extract_markets(self, markets: list, event_data: EventHistoricalData,
                        interval: str, start_ts: int, end_ts: int, 
                        enable_gc: bool) -> tuple:
        """Extract price data for all markets in an event."""
        successful = 0
        failed = 0
        
        for i, market in enumerate(markets, 1):
            market_name = market.group_item_title or market.question[:MAX_MARKET_QUESTION_DISPLAY]
            self.reporter.market_extraction_progress(i, len(markets), market_name)
            
            # Skip markets without valid token IDs
            if not market.token_ids or all(not tid for tid in market.token_ids):
                if market.is_inactive_negrisk_option():
                    self.reporter.market_skip_reason("Inactive negRisk option (placeholder)")
                else:
                    self.reporter.market_skip_reason("No tradeable tokens available")
                failed += 1
                continue
            
            try:
                # Fetch price history for this market
                price_histories = self._fetch_price_history_with_retry(
                    market, interval, start_ts, end_ts
                )
                
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
                            self.reporter.print(
                                f"  {outcome}: {history.data_points_count} data points, "
                                f"latest: ${history.latest_price:.4f}"
                            )
                else:
                    self.reporter.print("  Warning: No data available")
                    failed += 1
                    
            except Exception as e:
                logger.error(f"Failed to extract market {market.slug}: {e}")
                self.reporter.print(f"  Error: {e}")
                failed += 1
            
            # Memory management and rate limiting
            if enable_gc:
                gc.collect()
                logger.debug(f"Garbage collection after market {i}/{len(markets)}")
            
            # Rate limiting - small delay between markets
            if i < len(markets):
                time.sleep(RATE_LIMIT_CHUNK_DELAY)
        
        return successful, failed
    
    def close(self):
        """Close API connections."""
        self.api.close()