# Mango - Enhanced Polymarket Toolkit

A comprehensive Python library and CLI for Polymarket prediction markets. Extract historical data, monitor order books, track portfolios, and analyze markets with professional-grade tools.

## Features

### Core Capabilities
- **Historical Data Extraction**: Complete price history for all market outcomes
- **Event-Wide Data Extraction**: Extract all markets from an event in one command (NEW!)
- **Order Book Analysis**: Real-time order book depth, spreads, and liquidity
- **Portfolio Tracking**: Monitor positions, P&L, and trading activity
- **Market Discovery**: Search and analyze markets with advanced filters
- **Multi-API Integration**: CLOB, Gamma, and Data APIs with automatic fallback

### Technical Features
- **Clean Architecture**: Modular design with clear separation of concerns
- **Multiple Export Formats**: CSV, JSON, Excel, and Parquet
- **Robust Error Handling**: Retry logic, rate limiting, and clear error messages
- **Type Safety**: Full type hints throughout the codebase
- **Flexible Configuration**: Environment variables and settings management
- **Professional CLI**: Rich command-line interface with multiple output formats

## Installation

### From Source

```bash
git clone https://github.com/yourusername/polymarket-data.git
cd polymarket-data
pip install -e .
```

### Requirements

- Python 3.9+
- Dependencies listed in `requirements.txt`

## Quick Start

### Mango CLI - New Enhanced Commands

#### Market Discovery
```bash
# Search for markets
mango search "presidential election" --min-volume 10000

# Get detailed market information with order book
mango market-info "will-trump-win-2024" --show-book --depth 20

# View real-time order book
mango book "will-trump-win-2024" --format json -o orderbook.json

# Get current prices and spreads
mango price "will-trump-win-2024"
```

#### Portfolio Management
```bash
# View portfolio positions
mango portfolio 0xYourAddress --min-size 100 --show-pnl

# Get trading history
mango history 0xYourAddress --days 30 --type TRADE

# Analyze market holders
mango holders "will-trump-win-2024" --top 50 --outcome "Yes"
```

### Historical Data Extraction (Original)

Extract 30 days of daily price data:
```bash
polymarket-extract "https://polymarket.com/event/us-recession-in-2025/us-recession-in-2025"
```

### With Custom Parameters

```bash
# Hourly data for the last 7 days
polymarket-extract "URL" -i 1h -d 7

# Specific date range
polymarket-extract "URL" --start 2024-01-01 --end 2024-01-31

# Export to multiple formats (saves to data/ directory by default)
polymarket-extract "URL" -o market_data -f csv json excel

# Export to specific directory
polymarket-extract "URL" -o /path/to/output -f csv

# With API key
polymarket-extract "URL" --api-key YOUR_API_KEY
```

## Library Usage

### Basic Market Data
```python
from polymarket import PolymarketAPI, DataProcessor
from polymarket.models import TimeInterval

# Initialize API
api = PolymarketAPI(api_key="optional_key")

# Get market by URL slug
market = api.get_market("us-recession-in-2025")

# Fetch price history
price_histories = api.get_price_history(
    market, 
    interval=TimeInterval.ONE_HOUR,
    start_ts=1234567890,
    end_ts=1234567890
)
```

### Order Book Analysis
```python
# Get order books for all outcomes
order_books = api.get_order_books(market)

# Analyze specific outcome
yes_book = order_books.get_outcome_book("Yes")
print(f"Best bid: ${yes_book.best_bid.price}")
print(f"Best ask: ${yes_book.best_ask.price}")
print(f"Spread: ${yes_book.spread} ({yes_book.spread_percent:.2f}%)")

# Calculate market impact
impact = yes_book.get_market_impact(size=10000, side='buy')
print(f"Avg price for 10k shares: ${impact['average_price']}")
print(f"Slippage: {impact['slippage_percent']:.2f}%")
```

### Portfolio Management
```python
# Get user positions
positions = api.get_user_positions(
    "0xUserAddress",
    min_size=100,
    sort_by="VALUE"
)

# Get trading activity
activities = api.get_user_activity(
    "0xUserAddress",
    activity_types=["TRADE", "REWARD"],
    limit=100
)

# Analyze market holders
holders = api.get_market_holders(
    market.condition_id,
    outcome="Yes",
    min_size=1000
)
```

## Project Structure

```
mango/
├── polymarket/              # Main package
│   ├── __init__.py         # Package initialization and exports
│   ├── api.py              # API clients (CLOB, Gamma, unified interface)
│   ├── data_api.py         # Data API client for positions and activity
│   ├── orderbook.py        # Order book models and analysis
│   ├── models.py           # Data models and type definitions
│   ├── parser.py           # URL parsing and slug extraction
│   ├── processor.py        # Data processing, statistics, and export
│   ├── config.py           # Configuration and environment variables
│   └── exceptions.py       # Custom exception hierarchy
├── mango_cli.py            # Enhanced CLI with new commands
├── polymarket_extract.py   # Original data extraction CLI
├── setup.py                # Package setup and metadata
├── requirements.txt        # Production dependencies
├── CLAUDE.md              # AI assistant context document
└── README.md              # This file
```

## Configuration

Configuration via environment variables:

```bash
# API Configuration
export POLYMARKET_API_KEY="your_api_key"
export POLYMARKET_CLOB_URL="https://clob.polymarket.com"
export POLYMARKET_GAMMA_URL="https://gamma-api.polymarket.com"

# Request Settings
export POLYMARKET_TIMEOUT="30.0"
export POLYMARKET_MAX_RETRIES="3"
export POLYMARKET_RETRY_DELAY="1.0"
export POLYMARKET_USER_AGENT="PolymarketDataExtractor/1.0"

# Data Settings
export POLYMARKET_DEFAULT_DAYS="30"
export POLYMARKET_DEFAULT_INTERVAL="1d"
export POLYMARKET_MAX_POINTS="10000"

# Search Settings
export POLYMARKET_SEARCH_LIMIT="20"
export POLYMARKET_EVENT_MARKETS_LIMIT="100"

# Export Settings
export POLYMARKET_EXPORT_FORMAT="csv"
export POLYMARKET_MAX_CSV_MB="100"
export POLYMARKET_MAX_JSON_MB="50"

# Rate Limiting
export POLYMARKET_RATE_LIMIT="60"

# Cache Settings
export POLYMARKET_ENABLE_CACHE="false"
export POLYMARKET_CACHE_TTL="300"

# Polygon Chain Settings
export POLYGON_CHAIN_ID="137"
export POLYGON_RPC_URL="https://polygon-rpc.com"

# Logging
export POLYMARKET_LOG_LEVEL="INFO"
```

## Mango CLI Commands

### Market Commands

| Command | Description | Example |
|---------|-------------|---------|
| `search` | Search for markets by keyword | `mango search "bitcoin" --limit 10` |
| `market-info` | Get detailed market information | `mango market-info "btc-50k-2024" --show-book` |
| `book` | View order book depth | `mango book "btc-50k-2024" --depth 50` |
| `price` | Get current prices and spreads | `mango price "btc-50k-2024"` |

### Portfolio Commands

| Command | Description | Example |
|---------|-------------|---------|
| `portfolio` | View user positions | `mango portfolio 0xABC123 --min-size 100` |
| `history` | Get trading activity | `mango history 0xABC123 --days 7` |
| `holders` | Analyze market holders | `mango holders "btc-50k-2024" --top 20` |

## Original Extract Command Options

| Option | Description | Default |
|--------|-------------|---------|
| `url` | Polymarket market or event URL | Required |
| `-i, --interval` | Time interval (1m, 1h, 6h, 1d, 1w, max) | 1d |
| `-d, --days` | Number of days of history | 30 |
| `--start` | Start date (YYYY-MM-DD) | None |
| `--end` | End date (YYYY-MM-DD) | None |
| `-o, --output` | Output file path (without extension). Saves to `data/` by default | None |
| `-f, --formats` | Output formats (csv, json, excel, parquet) | csv |
| `--api-key` | CLOB API key | None |
| `--summary` | Print summary report | False |
| `--no-metadata` | Exclude metadata from CSV | False |
| `-v, --verbose` | Enable verbose logging | False |
| `--extract-all-markets` | Extract all markets from an event URL | False |
| `--column-format` | Column naming for event exports (short, full, descriptive) | short |

## Architecture

### Design Principles

1. **Single Responsibility**: Each module has a clear, focused purpose
2. **Dependency Inversion**: High-level modules don't depend on low-level modules
3. **Interface Segregation**: Clean interfaces with minimal coupling
4. **Open/Closed**: Easy to extend without modifying existing code

### Key Components

- **API Module**: Unified interface for all Polymarket APIs with automatic fallback
- **Models Module**: Type-safe data models with validation
- **Parser Module**: Robust URL parsing with error handling
- **Processor Module**: Data transformation, statistics, and export
- **Config Module**: Centralized configuration management
- **Exceptions Module**: Hierarchical exception structure

## Event Data Extraction (NEW!)

The `--extract-all-markets` flag enables extracting data from all markets within an event simultaneously:

### How It Works
1. Fetches all markets in the specified event
2. Extracts price history for each market with progress tracking
3. Merges all data into a single wide-format DataFrame
4. Exports with customizable column naming

### Column Naming Formats
- **short**: Uses team/candidate names (e.g., `liverpool_yes`, `liverpool_no`)
- **full**: Uses complete market slugs
- **descriptive**: Uses full question text

### Output Format
The CSV output has timestamps as rows and market outcomes as columns:
```
timestamp,liverpool_yes,liverpool_no,manchester_city_yes,manchester_city_no,...
2024-01-01 00:00:00,0.335,0.665,0.205,0.795,...
2024-01-01 01:00:00,0.336,0.664,0.204,0.796,...
```

### Example Use Cases
- **Elections**: Track all candidates in one file
- **Sports Championships**: Monitor all teams' odds over time
- **Economic Events**: Compare multiple outcome scenarios

### Performance Note
Extracting large events (20+ markets) may take several minutes due to rate limiting.

## API Architecture

The library uses multiple Polymarket APIs with intelligent fallback:

### 1. CLOB API (Primary)
- **Base URL**: `https://clob.polymarket.com`
- **Purpose**: Trading data and real-time market information
- **Endpoints**: 
  - Order books (`/book`, `/books`)
  - Current prices (`/midpoint`, `/spread`) - Note: `/prices` requires individual requests
  - Individual price endpoints (`/bid`, `/ask`) - May return 404 for low liquidity
  - Historical data (`/prices-history`)
  - Market discovery (`/markets`)
- **Authentication**: Optional API key for enhanced limits
- **Implementation Note**: Price fetching uses individual requests with fallback to order books

### 2. Gamma API (Metadata)
- **Base URL**: `https://gamma-api.polymarket.com`
- **Purpose**: Market and event metadata
- **Endpoints**:
  - Market search and filtering
  - Event grouping and relationships
  - Rich metadata (descriptions, tags, etc.)
- **Authentication**: Public API, no key required

### 3. Data API (Portfolio)
- **Base URL**: `https://data-api.polymarket.com`
- **Purpose**: User positions and on-chain activity
- **Endpoints**:
  - User positions (`/positions`)
  - Trading activity (`/activity`)
  - Market holders (`/holders`)
  - Holdings value history (`/holdings-value`)
- **Authentication**: No key required for public data

### 4. Unified API Interface
The `PolymarketAPI` class provides a seamless interface that:
- Automatically routes requests to the appropriate API
- Handles fallbacks for redundant data sources
- Manages authentication and rate limiting
- Provides consistent data models across APIs

## Data Models

### TimeInterval
Enum representing supported time intervals for price data:
- `ONE_MINUTE` (1m)
- `ONE_HOUR` (1h)
- `SIX_HOURS` (6h)
- `ONE_DAY` (1d)
- `ONE_WEEK` (1w)
- `MAX` (maximum available data)

### PricePoint
Represents a single price observation:
- `timestamp`: datetime of the price
- `price`: float value between 0 and 1

### PriceHistory
Complete price history for a market outcome:
- `market_id`: Market identifier
- `token_id`: Token contract ID
- `outcome`: Outcome name (e.g., "Yes", "No")
- `interval`: TimeInterval used
- `price_points`: List of PricePoint objects
- Calculated properties: `latest_price`, `oldest_price`, `price_change`, `price_change_percent`

### Market
Unified market representation with data from any API:
- Core fields: `slug`, `condition_id`, `question`, `outcomes`, `token_ids`
- Status: `active`, `closed`, `archived`
- Metrics: `volume`, `liquidity`
- Dates: `start_date`, `end_date`
- Special fields for grouped markets: `neg_risk`, `neg_risk_market_id`, `group_item_title`

### Event
Container for related markets:
- `id`, `ticker`, `slug`, `title`, `description`
- `markets`: List of Market objects
- Aggregate metrics: `liquidity`, `volume`
- Status flags: `active`, `closed`, `archived`, `featured`

### MarketHistoricalData
Complete dataset for analysis:
- `market`: Market object
- `price_histories`: Dict mapping outcomes to PriceHistory
- `extracted_at`: Timestamp of data extraction

### OrderBook
Real-time order book data:
- `bids`: List of OrderLevel objects (price, size)
- `asks`: List of OrderLevel objects (price, size)
- Properties: `best_bid`, `best_ask`, `mid_price`, `spread`
- Methods: `get_depth()`, `get_market_impact()`, `get_cumulative_depth()`

### MarketOrderBooks
Order books for all outcomes in a market:
- `books`: Dict mapping outcomes to OrderBook objects
- Methods: `get_spreads()`, `get_mid_prices()`, `get_best_prices()`

## URL Parser

The `PolymarketURLParser` handles various Polymarket URL formats:

### Supported URL Patterns
1. **Event URLs**: `https://polymarket.com/event/{event-slug}`
   - Returns list of all markets in the event
   
2. **Event Market URLs**: `https://polymarket.com/event/{event-slug}/{market-slug}`
   - Direct market within an event
   
3. **Direct Market URLs**: `https://polymarket.com/market/{market-slug}`
   - Standalone market page
   
4. **Short Market URLs**: `https://polymarket.com/{market-slug}`
   - Shortened market URLs

### Parser Methods
- `parse(url)`: Extract all components from URL
- `extract_slug(url)`: Get the most specific slug
- `get_api_slug(url)`: Get slug for API queries
- `is_event_url(url)`: Check if URL points to event
- `is_market_url(url)`: Check if URL points to market

## Data Processing

The `DataProcessor` class provides comprehensive data manipulation:

### Statistical Analysis
- `calculate_statistics(history)`: Compute mean, std, min, max, median, volatility
- Returns metrics including price changes and data point counts

### Data Transformation
- `merge_price_histories(histories)`: Combine multiple outcomes into single DataFrame
- Forward-fills missing values for continuous time series
- Maintains timestamp alignment across outcomes

### Export Formats

#### CSV Format
- Optional metadata header with market details
- Columnar format: timestamp, outcome1_price, outcome2_price
- Configurable decimal precision

#### JSON Format
- Nested structure with market metadata and price data
- ISO format timestamps
- Pretty-printing option

#### Excel Format
- Multiple sheets:
  - "Price History": Time series data
  - "Metadata": Market information
  - "{Outcome} Stats": Statistical summary per outcome
- Formatted for readability

#### Parquet Format
- Efficient binary format for large datasets
- Preserves data types and precision
- Ideal for further analysis in pandas/spark

### Summary Reports
- Human-readable text format
- Market overview and current status
- Statistical summary for each outcome
- Price changes and volatility metrics

## Exception Hierarchy

```
PolymarketError (base)
├── APIError
│   ├── RateLimitError
│   └── AuthenticationError
├── MarketNotFoundError
├── InvalidURLError
├── DataProcessingError
│   └── ExportError
└── ValidationError
    ├── PriceValidationError
    ├── TimeIntervalError
    └── InsufficientDataError
```

## CLI Features

### Event URL Handling
When provided an event URL, the CLI will:
1. Fetch event metadata
2. Display all markets within the event
3. Show current prices for each market
4. Provide direct URLs to access specific markets

### Market Groups
For grouped prediction markets (negRisk):
- Displays group title and options
- Shows relationship between markets
- Handles special group pricing logic

### Interactive Features
- Progress indicators during data fetching
- Colored output for better readability
- Graceful handling of interrupts (Ctrl+C)
- Detailed error messages with helpful tips

## Examples

### Market Discovery and Analysis
```bash
# Search for active markets with volume
mango search "climate change" --min-volume 50000 --limit 10

# Get detailed market info with order book
mango market-info "will-global-temp-rise-2c" --show-book --depth 20

# Export order book data
mango book "will-global-temp-rise-2c" --format json -o data/climate_book.json

# Monitor real-time prices
mango price "will-global-temp-rise-2c"
```

### Portfolio Management
```bash
# View all positions worth over $100
mango portfolio 0x123...abc --min-size 100 --show-pnl

# Get 30-day trading history
mango history 0x123...abc --days 30 --type TRADE --format json

# Find top holders in a market
mango holders "will-btc-hit-100k" --top 50 --outcome "Yes"
```

### Historical Data Extraction
```bash
# Extract single market
polymarket-extract "https://polymarket.com/will-x-happen"

# Get minute-level data for analysis
polymarket-extract "https://polymarket.com/will-x-happen" -i 1m -d 1

# Export last 90 days to all formats
polymarket-extract "URL" -d 90 -o analysis -f csv json excel parquet

# Extract ALL markets from an event (new feature!)
polymarket-extract "https://polymarket.com/event/english-premier-league-winner" \
  --extract-all-markets -o epl_all_teams -f csv

# Extract event with custom column naming
polymarket-extract "https://polymarket.com/event/2024-presidential-election" \
  --extract-all-markets --column-format short -o election_data
```

### Programmatic Usage
```python
from polymarket import PolymarketAPI, OrderBook
from decimal import Decimal

# Initialize API
api = PolymarketAPI(api_key="your_key")

# Market discovery
markets = api.search_markets("inflation", limit=5)
for market in markets:
    print(f"{market.question}: ${market.volume:,.0f}")

# Order book analysis
market = api.get_market("fed-rate-hike-2024")
books = api.get_order_books(market)

yes_book = books.get_outcome_book("Yes")
print(f"Best bid: ${yes_book.best_bid.price}")
print(f"Best ask: ${yes_book.best_ask.price}")
print(f"Spread: {yes_book.spread_percent:.2f}%")

# Calculate market impact for large order
impact = yes_book.get_market_impact(
    size=Decimal('50000'), 
    side='buy'
)
print(f"50k shares would move price by {impact['slippage_percent']:.2f}%")

# Portfolio tracking
positions = api.get_user_positions(
    "0xYourAddress",
    min_size=500,
    sort_by="VALUE"
)

total_value = sum(p['current_value'] for p in positions)
print(f"Portfolio value: ${total_value:,.2f}")
```

## Development

### Setting Up Development Environment

```bash
# Clone repository
git clone https://github.com/yourusername/polymarket-data.git
cd polymarket-data

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
pip install -e ".[dev]"
```

### Running Tests

```bash
# Run all tests
pytest

# With coverage
pytest --cov=polymarket

# Specific test file
pytest tests/test_api.py
```

### Code Quality

```bash
# Format code
black polymarket/

# Sort imports
isort polymarket/

# Type checking
mypy polymarket/

# Linting
flake8 polymarket/
```

### Development Dependencies
- `pytest`: Testing framework
- `pytest-asyncio`: Async test support
- `pytest-cov`: Coverage reporting
- `black`: Code formatting
- `isort`: Import sorting
- `mypy`: Static type checking
- `flake8`: Linting

### Code Style Guidelines
- Follow PEP 8
- Use type hints for all functions
- Maintain test coverage above 80%
- Document all public APIs
- Use meaningful variable names
- Keep functions focused and small

## Limitations

### Data Limitations
- Historical data availability depends on market age and activity
- Some older markets may not have complete historical data
- Price data is limited to 4 decimal places precision
- Maximum time range depends on selected interval
- Order book depth varies by market liquidity

### API Limitations
- Rate limits: 60 requests per minute across all endpoints
- CLOB API prices endpoint requires individual requests per token
- Direct price endpoints (/bid, /ask) may return 404 for low-liquidity markets
- The library automatically falls back to order book data when price endpoints fail
- Small delays are added between multiple requests to respect rate limits

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes with tests
4. Ensure code quality checks pass
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Submit a pull request

### Contribution Guidelines
- Add tests for new features
- Update documentation
- Follow existing code style
- Keep commits atomic and well-described

## License

MIT License - see LICENSE file for details

## Support

For issues and feature requests, please use the GitHub issue tracker.

## Acknowledgments

Built for the Polymarket community to enable better market analysis and research.