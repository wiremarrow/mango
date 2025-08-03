#!/usr/bin/env python3
"""Test CLOB API for old EPL market price history."""

import sys
sys.path.insert(0, '/Users/admin/code/mango')

from polymarket.api.api import CLOBAPIClient
from polymarket.models.models import TimeInterval, Market
import time

# Initialize CLOB client
clob = CLOBAPIClient()

# Create a market object from the Gamma data
market = Market(
    slug="will-manchester-city-win-the-2021-22-english-premier-league",
    condition_id="0xe4379668f9589c5f19077c31c0db5bca1e60220b590a5186093f7d70e16c84ac",
    question="Will Manchester City win the 2021-22 English Premier League?",
    token_ids=['71706238556750469139285578416882221276770266920777432183149854842033834493212', 
               '51686618752792814291022024686116135440222167667278708779858842116098088241937'],
    outcomes=['Yes', 'No'],
    active=True,
    closed=True,
    volume=3456.28
)

print(f"Testing CLOB API for market: {market.slug}\n")

# Test 1: Try with interval=max
print("Test 1: Using interval=max (no date parameters)")
try:
    history = clob.get_price_history(
        market.token_ids[0],  # Yes token
        interval=TimeInterval.MAX,
        start_ts=None,
        end_ts=None
    )
    
    if history and history.price_points:
        print(f"✓ Success! Got {len(history.price_points)} price points")
        print(f"  First: {history.price_points[0].timestamp} - ${history.price_points[0].price}")
        print(f"  Last: {history.price_points[-1].timestamp} - ${history.price_points[-1].price}")
    else:
        print("✗ No data returned (empty response)")
except Exception as e:
    print(f"✗ Error: {e}")

# Test 2: Try with specific date range from market lifetime
print("\nTest 2: Using specific date range (Jan 2022 - May 2022)")
start_ts = int(time.mktime((2022, 1, 12, 0, 0, 0, 0, 0, 0)))
end_ts = int(time.mktime((2022, 5, 22, 0, 0, 0, 0, 0, 0)))

try:
    history = clob.get_price_history(
        market.token_ids[0],
        interval=TimeInterval.ONE_DAY,
        start_ts=start_ts,
        end_ts=end_ts
    )
    
    if history and history.price_points:
        print(f"✓ Success! Got {len(history.price_points)} price points")
        print(f"  First: {history.price_points[0].timestamp} - ${history.price_points[0].price}")
        print(f"  Last: {history.price_points[-1].timestamp} - ${history.price_points[-1].price}")
    else:
        print("✗ No data returned (empty response)")
except Exception as e:
    print(f"✗ Error: {e}")

# Test 3: Try to get current prices/order book
print("\nTest 3: Checking current prices/order book")
try:
    # Try to get order book
    book = clob.get_order_book(market.token_ids[0])
    if book:
        print(f"✓ Order book data available")
        print(f"  Bids: {len(book.get('bids', []))}")
        print(f"  Asks: {len(book.get('asks', []))}")
    else:
        print("✗ No order book data")
        
    # Try to get midpoint
    mid = clob.get_midpoint(market.token_ids[0])
    if mid is not None:
        print(f"✓ Midpoint price: ${mid}")
    else:
        print("✗ No midpoint price available")
        
except Exception as e:
    print(f"✗ Error: {e}")

# Test 4: Search for market in CLOB
print("\nTest 4: Searching for market in CLOB markets list")
found = clob.find_market_by_slug(market.slug)
if found:
    print(f"✓ Market found in CLOB")
    print(f"  Active: {found.active}")
    print(f"  Closed: {found.closed}")
else:
    print("✗ Market not found in CLOB markets list")