"""
Order book models and processing for Polymarket CLOB.

This module provides data structures and utilities for working with
order book data including bids, asks, depth analysis, and spreads.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple
from decimal import Decimal
from datetime import datetime


@dataclass
class OrderLevel:
    """Represents a single price level in the order book."""
    price: Decimal
    size: Decimal
    
    @classmethod
    def from_api_response(cls, data: List[str]) -> 'OrderLevel':
        """Create OrderLevel from API response [price, size]."""
        return cls(
            price=Decimal(data[0]),
            size=Decimal(data[1])
        )
    
    @property
    def notional(self) -> Decimal:
        """Calculate notional value (price * size)."""
        return self.price * self.size


@dataclass
class OrderBook:
    """Complete order book for a market outcome."""
    market_id: str
    token_id: str
    outcome: str
    bids: List[OrderLevel] = field(default_factory=list)
    asks: List[OrderLevel] = field(default_factory=list)
    timestamp: Optional[datetime] = None
    
    @classmethod
    def from_api_response(cls, data: Dict[str, Any], token_id: str, outcome: str = "") -> 'OrderBook':
        """Create OrderBook from API response."""
        bids = [OrderLevel.from_api_response(bid) for bid in data.get('bids', [])]
        asks = [OrderLevel.from_api_response(ask) for ask in data.get('asks', [])]
        
        # Sort bids descending (highest first) and asks ascending (lowest first)
        bids.sort(key=lambda x: x.price, reverse=True)
        asks.sort(key=lambda x: x.price)
        
        return cls(
            market_id=data.get('market', ''),
            token_id=token_id,
            outcome=outcome,
            bids=bids,
            asks=asks,
            timestamp=datetime.now()
        )
    
    @property
    def best_bid(self) -> Optional[OrderLevel]:
        """Get the best (highest) bid."""
        return self.bids[0] if self.bids else None
    
    @property
    def best_ask(self) -> Optional[OrderLevel]:
        """Get the best (lowest) ask."""
        return self.asks[0] if self.asks else None
    
    @property
    def mid_price(self) -> Optional[Decimal]:
        """Calculate mid-point price."""
        if self.best_bid and self.best_ask:
            return (self.best_bid.price + self.best_ask.price) / 2
        return None
    
    @property
    def spread(self) -> Optional[Decimal]:
        """Calculate bid-ask spread."""
        if self.best_bid and self.best_ask:
            return self.best_ask.price - self.best_bid.price
        return None
    
    @property
    def spread_percent(self) -> Optional[Decimal]:
        """Calculate spread as percentage of mid price."""
        if self.mid_price and self.spread:
            return (self.spread / self.mid_price) * 100
        return None
    
    def get_depth(self, levels: int = 10) -> Dict[str, List[OrderLevel]]:
        """Get order book depth up to specified levels."""
        return {
            'bids': self.bids[:levels],
            'asks': self.asks[:levels]
        }
    
    def get_cumulative_depth(self, price_range: Decimal = Decimal('0.1')) -> Dict[str, Decimal]:
        """
        Calculate cumulative depth within price range from mid.
        
        Args:
            price_range: Price range from mid (e.g., 0.1 = 10 cents)
            
        Returns:
            Dict with cumulative bid/ask sizes
        """
        if not self.mid_price:
            return {'bid_depth': Decimal('0'), 'ask_depth': Decimal('0')}
        
        bid_limit = self.mid_price - price_range
        ask_limit = self.mid_price + price_range
        
        bid_depth = sum(level.size for level in self.bids if level.price >= bid_limit)
        ask_depth = sum(level.size for level in self.asks if level.price <= ask_limit)
        
        return {
            'bid_depth': bid_depth,
            'ask_depth': ask_depth,
            'total_depth': bid_depth + ask_depth
        }
    
    def get_market_impact(self, size: Decimal, side: str) -> Optional[Dict[str, Decimal]]:
        """
        Calculate market impact of a given order size.
        
        Args:
            size: Order size to simulate
            side: 'buy' or 'sell'
            
        Returns:
            Dict with average price, slippage, and levels consumed
        """
        levels = self.asks if side.lower() == 'buy' else self.bids
        if not levels:
            return None
        
        remaining_size = size
        total_cost = Decimal('0')
        levels_consumed = 0
        
        for level in levels:
            if remaining_size <= 0:
                break
                
            fill_size = min(remaining_size, level.size)
            total_cost += fill_size * level.price
            remaining_size -= fill_size
            levels_consumed += 1
            
        if remaining_size > 0:
            # Not enough liquidity
            return None
            
        avg_price = total_cost / size
        best_price = levels[0].price
        slippage = abs(avg_price - best_price)
        slippage_percent = (slippage / best_price) * 100
        
        return {
            'average_price': avg_price,
            'best_price': best_price,
            'slippage': slippage,
            'slippage_percent': slippage_percent,
            'levels_consumed': levels_consumed,
            'total_cost': total_cost
        }


@dataclass
class MarketOrderBooks:
    """Order books for all outcomes in a market."""
    market_id: str
    question: str
    books: Dict[str, OrderBook] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    
    def get_outcome_book(self, outcome: str) -> Optional[OrderBook]:
        """Get order book for specific outcome."""
        return self.books.get(outcome)
    
    def get_spreads(self) -> Dict[str, Optional[Decimal]]:
        """Get spreads for all outcomes."""
        return {
            outcome: book.spread 
            for outcome, book in self.books.items()
        }
    
    def get_mid_prices(self) -> Dict[str, Optional[Decimal]]:
        """Get mid prices for all outcomes."""
        return {
            outcome: book.mid_price 
            for outcome, book in self.books.items()
        }
    
    def get_best_prices(self) -> Dict[str, Dict[str, Optional[Decimal]]]:
        """Get best bid/ask for all outcomes."""
        result = {}
        for outcome, book in self.books.items():
            result[outcome] = {
                'bid': book.best_bid.price if book.best_bid else None,
                'ask': book.best_ask.price if book.best_ask else None
            }
        return result