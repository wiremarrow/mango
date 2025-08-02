# Polymarket Data Extractor

A professional Python library for extracting historical price data from Polymarket prediction markets. Built with clean architecture principles for algorithmic trading applications.

## Features

- **Clean Architecture**: Modular design with clear separation of concerns
- **Multiple API Support**: Seamlessly integrates CLOB and Gamma APIs with automatic fallback
- **Comprehensive Data**: Fetches complete price history for all market outcomes
- **Flexible Time Intervals**: Support for 1m, 1h, 6h, 1d, 1w, and max intervals
- **Multiple Export Formats**: CSV, JSON, Excel, and Parquet
- **Robust Error Handling**: Retry logic, rate limiting, and clear error messages
- **Type Safety**: Full type hints throughout the codebase
- **Configurable**: Environment variables and configuration management
- **Logging**: Comprehensive logging for debugging and monitoring

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

### Basic Usage

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

# Export to multiple formats
polymarket-extract "URL" -o market_data -f csv json excel

# With API key
polymarket-extract "URL" --api-key YOUR_API_KEY
```

## Library Usage

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

# Process and export data
from polymarket.models import MarketHistoricalData
data = MarketHistoricalData(market=market, price_histories=price_histories)

# Export to CSV
DataProcessor.save_to_file(data, "output.csv", format="csv")

# Get statistics
for outcome, history in price_histories.items():
    stats = DataProcessor.calculate_statistics(history)
    print(f"{outcome}: {stats}")
```

## Project Structure

```
polymarket-data/
├── polymarket/              # Main package
│   ├── __init__.py         # Package initialization and exports
│   ├── api.py              # API clients (CLOB, Gamma, unified interface)
│   ├── models.py           # Data models and type definitions
│   ├── parser.py           # URL parsing and slug extraction
│   ├── processor.py        # Data processing, statistics, and export
│   ├── config.py           # Configuration and environment variables
│   └── exceptions.py       # Custom exception hierarchy
├── polymarket_extract.py    # CLI script entry point
├── setup.py                # Package setup and metadata
├── requirements.txt        # Production dependencies
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

## Command Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `url` | Polymarket market or event URL | Required |
| `-i, --interval` | Time interval (1m, 1h, 6h, 1d, 1w, max) | 1d |
| `-d, --days` | Number of days of history | 30 |
| `--start` | Start date (YYYY-MM-DD) | None |
| `--end` | End date (YYYY-MM-DD) | None |
| `-o, --output` | Output file path (without extension) | None |
| `-f, --formats` | Output formats (csv, json, excel, parquet) | csv |
| `--api-key` | CLOB API key | None |
| `--summary` | Print summary report | False |
| `--no-metadata` | Exclude metadata from CSV | False |
| `-v, --verbose` | Enable verbose logging | False |

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

## API Architecture

The library uses multiple Polymarket APIs with intelligent fallback:

### 1. CLOB API (Primary)
- **Base URL**: `https://clob.polymarket.com`
- **Purpose**: Trading data and real-time market information
- **Features**: Market discovery, price history endpoints
- **Authentication**: Optional API key support

### 2. Gamma API (Fallback)
- **Base URL**: `https://gamma-api.polymarket.com`
- **Purpose**: Market and event metadata
- **Features**: Rich market details, event grouping, search functionality
- **Authentication**: Public API, no key required

### 3. Unified API Interface
The `PolymarketAPI` class provides a seamless interface that:
- Automatically tries CLOB API first for most up-to-date data
- Falls back to Gamma API if market not found
- Merges search results from both APIs
- Handles authentication and rate limiting transparently

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

### Extract Event Markets
```bash
# View all markets in an event
polymarket-extract "https://polymarket.com/event/2024-presidential-election"
```

### Extract Specific Market Data
```bash
# Daily data for 30 days
polymarket-extract "https://polymarket.com/will-x-happen-by-2025"

# Minute-level data for past 24 hours
polymarket-extract "https://polymarket.com/will-x-happen" -i 1m -d 1

# Export last 90 days to all formats
polymarket-extract "URL" -d 90 -o analysis -f csv json excel parquet

# Generate summary report
polymarket-extract "URL" --summary
```

### Programmatic Usage
```python
from polymarket import PolymarketAPI, PolymarketURLParser, DataProcessor
from polymarket.models import TimeInterval, MarketHistoricalData

# Parse URL
parser = PolymarketURLParser()
slug = parser.get_api_slug("https://polymarket.com/market/example")

# Fetch data
api = PolymarketAPI()
market = api.get_market(slug)
histories = api.get_price_history(market, TimeInterval.ONE_HOUR)

# Analyze
data = MarketHistoricalData(market=market, price_histories=histories)
for outcome, history in histories.items():
    stats = DataProcessor.calculate_statistics(history)
    print(f"{outcome}: Mean={stats['mean']:.4f}, Vol={stats['volatility']:.4f}")

# Export
DataProcessor.save_to_file(data, "analysis.xlsx", format="excel")
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

- Historical data availability depends on market age and activity
- Rate limits may apply for high-frequency requests
- Some older markets may not have complete historical data
- Price data is limited to 4 decimal places precision
- Maximum time range depends on selected interval

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