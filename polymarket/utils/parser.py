"""
URL parser for Polymarket.

This module handles parsing of Polymarket URLs to extract market and event
identifiers for API queries.
"""

import re
from urllib.parse import urlparse, unquote
from typing import Optional, Dict, Union

from .exceptions import InvalidURLError


class PolymarketURLParser:
    """Parser for extracting slugs and identifiers from Polymarket URLs."""
    
    BASE_URL = "https://polymarket.com"
    
    # URL patterns
    EVENT_MARKET_PATTERN = re.compile(r'/event/([^/]+)(?:/([^/?]+))?')
    MARKET_DIRECT_PATTERN = re.compile(r'/market/([^/?]+)')
    DIRECT_SLUG_PATTERN = re.compile(r'^/?([^/?]+)$')  # Direct market URLs like /will-jd-vance-win...
    
    def parse(self, url: str) -> Dict[str, Union[str, None]]:
        """
        Parse a Polymarket URL and extract relevant identifiers.
        
        Args:
            url: The Polymarket URL to parse
            
        Returns:
            Dictionary containing:
                - url: Original URL
                - type: 'event', 'market', or None
                - event_slug: Event slug if present
                - market_slug: Market slug if present
                - path: Clean path
                
        Raises:
            InvalidURLError: If the URL is not a valid Polymarket URL
        """
        if not url:
            raise InvalidURLError("URL cannot be empty")
            
        # Parse the URL
        parsed = urlparse(url)
        
        # Validate it's a Polymarket URL
        if 'polymarket.com' not in parsed.netloc:
            raise InvalidURLError(url)
            
        # Clean up the path
        path = parsed.path.strip('/')
        
        # Initialize result
        result = {
            'url': url,
            'type': None,
            'event_slug': None,
            'market_slug': None,
            'path': path
        }
        
        # Try to match event/market pattern
        event_match = self.EVENT_MARKET_PATTERN.search(parsed.path)
        if event_match:
            result['event_slug'] = unquote(event_match.group(1))
            if event_match.group(2):
                result['type'] = 'market'
                result['market_slug'] = unquote(event_match.group(2))
            else:
                result['type'] = 'event'
            return result
            
        # Try to match direct market pattern
        market_match = self.MARKET_DIRECT_PATTERN.search(parsed.path)
        if market_match:
            result['type'] = 'market'
            result['market_slug'] = unquote(market_match.group(1))
            return result
            
        # Try to match direct slug pattern (e.g., /will-jd-vance-win-the-2028-us-presidential-election)
        direct_match = self.DIRECT_SLUG_PATTERN.match(parsed.path)
        if direct_match:
            slug = unquote(direct_match.group(1))
            # Exclude common non-market paths
            if slug not in ['markets', 'elections', 'leaderboard', 'about', 'docs', 'help']:
                result['type'] = 'market'
                result['market_slug'] = slug
                return result
            
        # If no patterns match, it's an invalid URL
        raise InvalidURLError(f"Cannot parse Polymarket URL: {url}")
    
    def extract_slug(self, url: str) -> Optional[str]:
        """
        Extract the most specific slug from a URL.
        
        For market URLs, returns the market slug.
        For event URLs, returns the event slug.
        
        Args:
            url: The Polymarket URL
            
        Returns:
            The extracted slug or None
            
        Raises:
            InvalidURLError: If the URL is invalid
        """
        parsed = self.parse(url)
        return parsed.get('market_slug') or parsed.get('event_slug')
    
    def get_api_slug(self, url: str) -> Optional[str]:
        """
        Get the slug that should be used for API queries.
        
        Args:
            url: The Polymarket URL
            
        Returns:
            The slug to use for API queries
            
        Raises:
            InvalidURLError: If the URL is invalid
        """
        parsed = self.parse(url)
        
        if parsed['type'] == 'market':
            return parsed['market_slug']
        elif parsed['type'] == 'event':
            return parsed['event_slug']
        return None
    
    def is_event_url(self, url: str) -> bool:
        """Check if the URL is an event URL."""
        try:
            parsed = self.parse(url)
            return parsed['type'] == 'event' and not parsed['market_slug']
        except InvalidURLError:
            return False
    
    def is_market_url(self, url: str) -> bool:
        """Check if the URL is a market URL."""
        try:
            parsed = self.parse(url)
            return parsed['type'] == 'market'
        except InvalidURLError:
            return False
    
    def build_market_url(self, event_slug: str, market_slug: str) -> str:
        """
        Build a market URL from event and market slugs.
        
        Args:
            event_slug: The event slug
            market_slug: The market slug
            
        Returns:
            Complete market URL
        """
        return f"{self.BASE_URL}/event/{event_slug}/{market_slug}"