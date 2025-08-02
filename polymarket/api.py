"""
Consolidated API clients for Polymarket.

This module provides a unified interface for interacting with various Polymarket APIs,
including CLOB, Gamma, and price history endpoints.
"""

import httpx
import asyncio
import time
import logging
from typing import Optional, Dict, List, Any, Union
from abc import ABC, abstractmethod
from datetime import datetime

from .models import Market, Event, PriceHistory, PricePoint, TimeInterval
from .config import (
    CLOB_BASE_URL, GAMMA_BASE_URL, DEFAULT_TIMEOUT,
    MAX_RETRIES, RETRY_DELAY, USER_AGENT
)
from .exceptions import APIError, RateLimitError, MarketNotFoundError


logger = logging.getLogger(__name__)


class BaseAPIClient(ABC):
    """Base class for all API clients with common functionality."""
    
    def __init__(self, base_url: str, timeout: float = DEFAULT_TIMEOUT):
        self.base_url = base_url
        self.timeout = timeout
        self._client = None
        
    @property
    def client(self) -> httpx.Client:
        """Get or create the HTTP client."""
        if self._client is None:
            self._client = httpx.Client(
                base_url=self.base_url,
                timeout=self.timeout,
                headers={
                    'User-Agent': USER_AGENT,
                    'Accept': 'application/json'
                }
            )
        return self._client
    
    def _request_with_retry(self, method: str, endpoint: str, **kwargs) -> httpx.Response:
        """Make a request with retry logic."""
        for attempt in range(MAX_RETRIES):
            try:
                response = self.client.request(method, endpoint, **kwargs)
                response.raise_for_status()
                return response
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429:  # Rate limited
                    if attempt < MAX_RETRIES - 1:
                        delay = RETRY_DELAY * (2 ** attempt)
                        logger.warning(f"Rate limited, retrying in {delay}s...")
                        time.sleep(delay)
                        continue
                    raise RateLimitError("Rate limit exceeded")
                raise APIError(f"HTTP {e.response.status_code}: {e.response.text}")
            except (httpx.RequestError, httpx.TimeoutException) as e:
                if attempt < MAX_RETRIES - 1:
                    logger.warning(f"Request failed, retrying: {e}")
                    time.sleep(RETRY_DELAY)
                    continue
                raise APIError(f"Request failed: {e}")
    
    def close(self):
        """Close the HTTP client."""
        if self._client:
            self._client.close()
            self._client = None
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


class GammaAPIClient(BaseAPIClient):
    """Client for Polymarket's Gamma API (market metadata)."""
    
    def __init__(self, timeout: float = DEFAULT_TIMEOUT):
        super().__init__(GAMMA_BASE_URL, timeout)
    
    def get_market_by_slug(self, slug: str) -> Optional[Market]:
        """Fetch a market by its slug."""
        try:
            # First try direct query
            response = self._request_with_retry('GET', '/markets', params={'slug': slug})
            data = response.json()
            
            if data and isinstance(data, list) and len(data) > 0:
                return Market.from_gamma_response(data[0])
            
            # If not found, search through all markets
            logger.debug(f"Market not found by slug query, searching all markets...")
            markets = self.get_markets(limit=1000, active=True)
            for market in markets:
                if market.slug == slug or slug in market.slug:
                    return market
                    
            return None
        except Exception as e:
            logger.error(f"Error fetching market by slug {slug}: {e}")
            return None
    
    def get_markets(self, 
                   limit: int = 100,
                   offset: int = 0,
                   active: Optional[bool] = None,
                   closed: Optional[bool] = None,
                   order: str = 'volume',
                   ascending: bool = False) -> List[Market]:
        """Fetch multiple markets with filtering options."""
        params = {
            'limit': limit,
            'offset': offset,
            'order': order,
            'ascending': ascending
        }
        
        if active is not None:
            params['active'] = active
        if closed is not None:
            params['closed'] = closed
            
        try:
            response = self._request_with_retry('GET', '/markets', params=params)
            data = response.json()
            return [Market.from_gamma_response(market) for market in data]
        except Exception as e:
            logger.error(f"Error fetching markets: {e}")
            return []
    
    def search_markets(self, query: str, limit: int = 10) -> List[Market]:
        """Search for markets by text query."""
        all_markets = self.get_markets(limit=1000, active=True)
        
        query_lower = query.lower()
        matching = []
        
        for market in all_markets:
            if (query_lower in market.question.lower() or 
                query_lower in market.slug.lower()):
                matching.append(market)
                if len(matching) >= limit:
                    break
                    
        return matching
    
    def get_event_by_slug(self, slug: str) -> Optional[Event]:
        """Fetch an event by its slug."""
        try:
            # Direct query by slug
            response = self._request_with_retry('GET', '/events', params={'slug': slug})
            data = response.json()
            
            if data and isinstance(data, list) and len(data) > 0:
                return Event.from_gamma_response(data[0])
            
            return None
        except Exception as e:
            logger.error(f"Error fetching event by slug {slug}: {e}")
            return None
    
    def get_events(self, 
                  limit: int = 100,
                  offset: int = 0,
                  active: Optional[bool] = None,
                  closed: Optional[bool] = None,
                  order: str = 'volume',
                  ascending: bool = False) -> List[Event]:
        """Fetch multiple events with filtering options."""
        params = {
            'limit': limit,
            'offset': offset,
            'order': order,
            'ascending': ascending
        }
        
        if active is not None:
            params['active'] = active
        if closed is not None:
            params['closed'] = closed
            
        try:
            response = self._request_with_retry('GET', '/events', params=params)
            data = response.json()
            return [Event.from_gamma_response(event) for event in data]
        except Exception as e:
            logger.error(f"Error fetching events: {e}")
            return []


class CLOBAPIClient(BaseAPIClient):
    """Client for Polymarket's CLOB API (trading and price data)."""
    
    def __init__(self, api_key: Optional[str] = None, timeout: float = DEFAULT_TIMEOUT):
        super().__init__(CLOB_BASE_URL, timeout)
        self.api_key = api_key
        
        # Add API key to headers if provided
        if api_key and self._client:
            self._client.headers['Authorization'] = f'Bearer {api_key}'
    
    def get_markets(self, next_cursor: Optional[str] = None) -> Dict[str, Any]:
        """Get markets from CLOB API with pagination."""
        params = {}
        if next_cursor:
            params["next_cursor"] = next_cursor
            
        try:
            response = self._request_with_retry('GET', '/markets', params=params)
            return response.json()
        except Exception as e:
            logger.error(f"Error fetching CLOB markets: {e}")
            return {}
    
    def find_market_by_slug(self, slug: str) -> Optional[Market]:
        """Find a market by its slug in CLOB API."""
        next_cursor = None
        
        while True:
            data = self.get_markets(next_cursor)
            if not data or 'data' not in data:
                break
                
            for market_data in data['data']:
                if market_data.get('market_slug') == slug:
                    return Market.from_clob_response(market_data)
            
            next_cursor = data.get('next_cursor')
            if not next_cursor or next_cursor == 'LTE=':
                break
                
        return None
    
    def search_markets(self, query: str, limit: int = 10) -> List[Market]:
        """Search for markets containing the query string."""
        results = []
        next_cursor = None
        query_lower = query.lower()
        
        while len(results) < limit:
            data = self.get_markets(next_cursor)
            if not data or 'data' not in data:
                break
                
            for market_data in data['data']:
                question = market_data.get('question', '').lower()
                slug = market_data.get('market_slug', '').lower()
                
                if query_lower in question or query_lower in slug:
                    results.append(Market.from_clob_response(market_data))
                    
                    if len(results) >= limit:
                        break
            
            next_cursor = data.get('next_cursor')
            if not next_cursor or next_cursor == 'LTE=':
                break
                
        return results
    
    def get_price_history(self,
                         market_id: str,
                         interval: Union[str, TimeInterval] = TimeInterval.ONE_DAY,
                         start_ts: Optional[int] = None,
                         end_ts: Optional[int] = None,
                         fidelity: Optional[int] = None) -> Optional[PriceHistory]:
        """Fetch historical price data for a market."""
        if isinstance(interval, str):
            interval = TimeInterval.from_string(interval)
            
        params = {
            'market': market_id,
            'interval': interval.value
        }
        
        if start_ts:
            params['startTs'] = start_ts
        if end_ts:
            params['endTs'] = end_ts
        if fidelity:
            params['fidelity'] = fidelity
            
        try:
            response = self._request_with_retry('GET', '/prices-history', params=params)
            data = response.json()
            
            price_points = [PricePoint.from_api_response(point) 
                          for point in data.get('history', [])]
            
            return PriceHistory(
                market_id=market_id,
                token_id=market_id,
                outcome='',  # Will be set by caller
                interval=interval,
                start_time=datetime.fromtimestamp(start_ts) if start_ts else None,
                end_time=datetime.fromtimestamp(end_ts) if end_ts else None,
                price_points=price_points
            )
        except Exception as e:
            logger.error(f"Error fetching price history for market {market_id}: {e}")
            return None
    
    def get_market_prices_all_outcomes(self,
                                     token_ids: List[str],
                                     outcomes: List[str],
                                     interval: Union[str, TimeInterval] = TimeInterval.ONE_DAY,
                                     start_ts: Optional[int] = None,
                                     end_ts: Optional[int] = None) -> Dict[str, PriceHistory]:
        """Fetch price history for all outcomes of a market."""
        results = {}
        
        for token_id, outcome in zip(token_ids, outcomes):
            history = self.get_price_history(token_id, interval, start_ts, end_ts)
            if history:
                history.outcome = outcome
                results[outcome] = history
                
        return results


class PolymarketAPI:
    """
    Unified API interface for all Polymarket operations.
    
    This class provides a single entry point for interacting with multiple
    Polymarket APIs, handling fallbacks and providing a consistent interface.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.gamma_client = GammaAPIClient()
        self.clob_client = CLOBAPIClient(api_key=api_key)
        
    def get_market(self, slug: str) -> Optional[Market]:
        """
        Get market by slug, trying multiple APIs with fallback.
        
        Args:
            slug: Market slug identifier
            
        Returns:
            Market object or None if not found
        """
        # Try CLOB API first (most up-to-date)
        logger.debug(f"Searching for market '{slug}' in CLOB API...")
        market = self.clob_client.find_market_by_slug(slug)
        if market:
            logger.info(f"Found market in CLOB API: {market.question}")
            return market
        
        # Fallback to Gamma API
        logger.debug(f"Market not found in CLOB API, trying Gamma API...")
        market = self.gamma_client.get_market_by_slug(slug)
        if market:
            logger.info(f"Found market in Gamma API: {market.question}")
            return market
        
        logger.warning(f"Market not found: {slug}")
        return None
    
    def search_markets(self, query: str, limit: int = 20) -> List[Market]:
        """
        Search for markets across all APIs.
        
        Args:
            query: Search query
            limit: Maximum number of results
            
        Returns:
            List of matching markets
        """
        # Search in CLOB API
        clob_results = self.clob_client.search_markets(query, limit)
        
        # If not enough results, supplement with Gamma API
        if len(clob_results) < limit:
            gamma_results = self.gamma_client.search_markets(
                query, limit - len(clob_results)
            )
            
            # Merge results, avoiding duplicates by slug
            seen_slugs = {m.slug for m in clob_results}
            for market in gamma_results:
                if market.slug not in seen_slugs:
                    clob_results.append(market)
        
        return clob_results[:limit]
    
    def get_price_history(self,
                         market: Market,
                         interval: Union[str, TimeInterval] = TimeInterval.ONE_DAY,
                         start_ts: Optional[int] = None,
                         end_ts: Optional[int] = None) -> Dict[str, PriceHistory]:
        """
        Get price history for all outcomes of a market.
        
        Args:
            market: Market object
            interval: Time interval for data points
            start_ts: Start timestamp (Unix)
            end_ts: End timestamp (Unix)
            
        Returns:
            Dictionary mapping outcome names to PriceHistory objects
        """
        return self.clob_client.get_market_prices_all_outcomes(
            market.token_ids,
            market.outcomes,
            interval,
            start_ts,
            end_ts
        )
    
    def get_event(self, slug: str) -> Optional[Event]:
        """
        Get event by slug from Gamma API.
        
        Args:
            slug: Event slug identifier
            
        Returns:
            Event object or None if not found
        """
        logger.debug(f"Fetching event '{slug}' from Gamma API...")
        return self.gamma_client.get_event_by_slug(slug)
    
    def get_market_from_direct_url(self, slug: str) -> Optional[Market]:
        """
        Get market from a direct URL slug, checking if it's part of an event.
        
        Args:
            slug: Market slug from direct URL
            
        Returns:
            Market object or None if not found
        """
        # First try to get the market directly
        market = self.get_market(slug)
        if not market:
            return None
            
        # Check if this market is part of an event by searching events
        # This is a simplified approach - in production you might want to
        # query the market's event relationship directly
        return market
    
    def close(self):
        """Close all API clients."""
        self.gamma_client.close()
        self.clob_client.close()
        
    def __enter__(self):
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()