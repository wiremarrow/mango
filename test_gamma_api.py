#!/usr/bin/env python3
"""Test Gamma API for old EPL market data."""

import sys
sys.path.insert(0, '/Users/admin/code/mango')

from polymarket.api import GammaAPIClient
import json

# Initialize Gamma client
gamma = GammaAPIClient()

# Test the 2021-22 EPL event
event_slug = "who-will-win-the-21-22-english-premier-league"

print(f"Testing Gamma API for event: {event_slug}\n")

# Try to get the event
event = gamma.get_event_by_slug(event_slug)

if event:
    print("Event found!")
    print(f"Title: {event.title}")
    print(f"Description: {event.description[:100]}...")
    print(f"Active: {event.active}")
    print(f"Closed: {event.closed}")
    print(f"Start date: {event.start_date}")
    print(f"End date: {event.end_date}")
    print(f"Volume: ${event.volume:,.2f}")
    print(f"Liquidity: ${event.liquidity:,.2f}")
    print(f"\nNumber of markets: {len(event.markets)}")
    
    # Show first few markets
    for i, market in enumerate(event.markets[:5]):
        print(f"\nMarket {i+1}:")
        print(f"  Question: {market.question}")
        print(f"  Slug: {market.slug}")
        print(f"  Condition ID: {market.condition_id}")
        print(f"  Active: {market.active}")
        print(f"  Closed: {market.closed}")
        print(f"  Volume: ${market.volume:,.2f}")
        print(f"  Token IDs: {market.token_ids}")
        print(f"  Outcomes: {market.outcomes}")
else:
    print("Event not found in Gamma API")

# Try direct market search
print("\n\nSearching for EPL 2021-22 markets...")
markets = gamma.search_markets("english premier league 2021", limit=20)

epl_2021_markets = [m for m in markets if "2021" in m.question or "21-22" in m.question]
print(f"Found {len(epl_2021_markets)} markets related to 2021-22 EPL")

for market in epl_2021_markets[:3]:
    print(f"\nMarket: {market.question}")
    print(f"  Slug: {market.slug}")
    print(f"  Active: {market.active}, Closed: {market.closed}")
    print(f"  Volume: ${market.volume:,.2f}")