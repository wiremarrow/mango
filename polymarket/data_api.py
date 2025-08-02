"""
Data API client for Polymarket user and holdings data.

This module provides access to the data-api endpoints for retrieving
user positions, on-chain activity, and market holder information.
"""

import logging
from typing import Optional, List, Dict, Any, Literal
from datetime import datetime

from .api import BaseAPIClient
from .config import DATA_API_URL, DEFAULT_TIMEOUT
from .exceptions import APIError, AuthenticationError


logger = logging.getLogger(__name__)


ActivityType = Literal["TRADE", "SPLIT", "MERGE", "REDEEM", "REWARD", "CONVERSION"]
TradeSide = Literal["BUY", "SELL"]
SortField = Literal["TIMESTAMP", "TOKENS", "CASH", "SIZE", "VALUE"]
SortOrder = Literal["ASC", "DESC"]


class DataAPIClient(BaseAPIClient):
    """Client for Polymarket's Data API (user positions and activity)."""
    
    def __init__(self, timeout: float = DEFAULT_TIMEOUT):
        super().__init__(DATA_API_URL, timeout)
    
    def get_user_positions(self,
                          address: str,
                          min_size: float = 1.0,
                          redeemable: Optional[bool] = None,
                          mergeable: Optional[bool] = None,
                          market: Optional[str] = None,
                          event: Optional[str] = None,
                          limit: int = 50,
                          offset: int = 0,
                          sort_by: SortField = "VALUE",
                          sort_order: SortOrder = "DESC") -> List[Dict[str, Any]]:
        """
        Get current positions for a user address.
        
        Args:
            address: User's wallet address
            min_size: Minimum position size to include (default: 1.0)
            redeemable: Filter positions that are redeemable
            mergeable: Filter positions that are mergeable
            market: Filter by market title
            event: Filter by event ID (cannot be used with market)
            limit: Max number of positions (default: 50, max: 500)
            offset: Pagination offset (default: 0)
            sort_by: Field to sort by
            sort_order: Sort direction
            
        Returns:
            List of position objects
        """
        params = {
            "address": address,
            "min_size": min_size,
            "limit": min(limit, 500),
            "offset": offset,
            "sort_by": sort_by,
            "sort_order": sort_order
        }
        
        if redeemable is not None:
            params["redeemable"] = redeemable
        if mergeable is not None:
            params["mergeable"] = mergeable
        if market:
            params["market"] = market
        if event:
            if market:
                raise ValueError("Cannot use both market and event filters")
            params["event"] = event
            
        try:
            response = self._request_with_retry('GET', '/positions', params=params)
            return response.json()
        except Exception as e:
            logger.error(f"Error fetching user positions: {e}")
            raise APIError(f"Failed to fetch positions: {e}")
    
    def get_user_activity(self,
                         address: str,
                         activity_types: Optional[List[ActivityType]] = None,
                         side: Optional[TradeSide] = None,
                         market: Optional[str] = None,
                         start_date: Optional[datetime] = None,
                         end_date: Optional[datetime] = None,
                         limit: int = 100,
                         offset: int = 0,
                         sort_by: Literal["TIMESTAMP", "TOKENS", "CASH"] = "TIMESTAMP",
                         sort_order: SortOrder = "DESC") -> List[Dict[str, Any]]:
        """
        Get on-chain activity history for a user.
        
        Args:
            address: User's wallet address
            activity_types: Filter by activity types
            side: Filter trades by side (BUY/SELL)
            market: Filter by market
            start_date: Start date filter
            end_date: End date filter
            limit: Max number of activities
            offset: Pagination offset
            sort_by: Field to sort by
            sort_order: Sort direction
            
        Returns:
            List of activity objects
        """
        params = {
            "address": address,
            "limit": limit,
            "offset": offset,
            "sort_by": sort_by,
            "sort_order": sort_order
        }
        
        if activity_types:
            params["activity_types"] = ",".join(activity_types)
        if side:
            params["side"] = side
        if market:
            params["market"] = market
        if start_date:
            params["start_date"] = start_date.isoformat()
        if end_date:
            params["end_date"] = end_date.isoformat()
            
        try:
            response = self._request_with_retry('GET', '/activity', params=params)
            return response.json()
        except Exception as e:
            logger.error(f"Error fetching user activity: {e}")
            raise APIError(f"Failed to fetch activity: {e}")
    
    def get_market_holders(self,
                          market_id: str,
                          outcome: Optional[str] = None,
                          min_size: float = 0.0,
                          limit: int = 100,
                          offset: int = 0) -> List[Dict[str, Any]]:
        """
        Get holders for a specific market.
        
        Args:
            market_id: Market condition ID
            outcome: Filter by specific outcome
            min_size: Minimum position size
            limit: Max number of holders
            offset: Pagination offset
            
        Returns:
            List of holder objects with positions
        """
        params = {
            "market_id": market_id,
            "min_size": min_size,
            "limit": limit,
            "offset": offset
        }
        
        if outcome:
            params["outcome"] = outcome
            
        try:
            response = self._request_with_retry('GET', '/holders', params=params)
            return response.json()
        except Exception as e:
            logger.error(f"Error fetching market holders: {e}")
            raise APIError(f"Failed to fetch holders: {e}")
    
    def get_holdings_value(self,
                          address: str,
                          start_date: Optional[datetime] = None,
                          end_date: Optional[datetime] = None,
                          interval: str = "1d") -> Dict[str, Any]:
        """
        Get historical holdings value for a user.
        
        Args:
            address: User's wallet address
            start_date: Start date for history
            end_date: End date for history
            interval: Time interval (1h, 1d, 1w)
            
        Returns:
            Holdings value history
        """
        params = {
            "address": address,
            "interval": interval
        }
        
        if start_date:
            params["start_date"] = start_date.isoformat()
        if end_date:
            params["end_date"] = end_date.isoformat()
            
        try:
            response = self._request_with_retry('GET', '/holdings-value', params=params)
            return response.json()
        except Exception as e:
            logger.error(f"Error fetching holdings value: {e}")
            raise APIError(f"Failed to fetch holdings value: {e}")
    
    def get_user_trades(self,
                       address: str,
                       market: Optional[str] = None,
                       start_ts: Optional[int] = None,
                       end_ts: Optional[int] = None,
                       limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get trades for a specific user.
        
        Args:
            address: User's wallet address
            market: Filter by market
            start_ts: Start timestamp
            end_ts: End timestamp
            limit: Max number of trades
            
        Returns:
            List of trade objects
        """
        params = {
            "address": address,
            "limit": limit
        }
        
        if market:
            params["market"] = market
        if start_ts:
            params["start_ts"] = start_ts
        if end_ts:
            params["end_ts"] = end_ts
            
        try:
            response = self._request_with_retry('GET', '/trades', params=params)
            return response.json()
        except Exception as e:
            logger.error(f"Error fetching user trades: {e}")
            raise APIError(f"Failed to fetch trades: {e}")