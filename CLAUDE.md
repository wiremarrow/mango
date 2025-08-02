# CLAUDE.md - Critical Project Context for Polymarket Data Extractor

## PROJECT MANDATE

You are working with a professional-grade Python library for extracting historical price data from Polymarket prediction markets. This codebase demands precision, reliability, and adherence to clean architecture principles.

## ESSENTIAL COMMANDS - MEMORIZE THESE

### New Mango CLI Commands - PRIMARY INTERFACE
```bash
# Market Discovery and Analysis
mango search "keyword" --min-volume 10000  # Search markets
mango market-info "slug" --show-book  # Get market details with order book
mango book "slug" --depth 50 --format json  # Export order book
mango price "slug"  # Real-time prices and spreads

# Portfolio Management
mango portfolio 0xADDRESS --min-size 100  # View positions
mango history 0xADDRESS --days 30 --type TRADE  # Trading history
mango holders "slug" --top 100  # Market holder analysis

# CRITICAL: Always use market slugs, NOT full URLs for mango commands
```

### Legacy Data Extraction
```bash
# Extract market data with default settings (30 days, daily intervals)
polymarket-extract "https://polymarket.com/event/market-slug"

# Extract with specific parameters - USE THESE EXACT FLAGS
polymarket-extract "URL" -i 1h -d 7  # 7 days of hourly data
polymarket-extract "URL" --start 2024-01-01 --end 2024-01-31  # Date range
polymarket-extract "URL" -o analysis -f csv json excel  # Multiple formats

# NEW: Extract ALL markets from an event
polymarket-extract "EVENT_URL" --extract-all-markets -o output_name -f csv
polymarket-extract "EVENT_URL" --extract-all-markets --column-format short  # Compact column names
```

### Development Commands
```bash
# ALWAYS run these for development
pytest --cov=polymarket  # Test with coverage
black polymarket/  # Format code
mypy polymarket/  # Type checking
```

### Critical Environment Variables
```bash
# SET THESE for production use
export POLYMARKET_API_KEY="your_key"  # Required for CLOB API
export POLYMARKET_LOG_LEVEL="DEBUG"  # For troubleshooting
export POLYMARKET_MAX_RETRIES="5"  # Increase for reliability
```

## ARCHITECTURE IMPERATIVES

### API Hierarchy - RESPECT THIS ORDER
1. **CLOB API** - PRIMARY for trading data (order books, prices, history)
2. **Gamma API** - FALLBACK for metadata (search, descriptions)
3. **Data API** - EXCLUSIVE for user data (positions, activity, holders)
4. **NEVER** mix API responsibilities

### Module Boundaries - DO NOT VIOLATE
- `api.py` - API communication and unified interface
- `data_api.py` - Data API client for user/portfolio data
- `orderbook.py` - Order book models and analysis ONLY
- `models.py` - Core data structures ONLY  
- `parser.py` - URL parsing ONLY
- `processor.py` - Data manipulation and export ONLY
- `config.py` - Configuration ONLY
- `exceptions.py` - Error definitions ONLY
- `mango_cli.py` - Enhanced CLI commands
- `polymarket_extract.py` - Legacy data extraction

### Data Flow - FOLLOW STRICTLY
1. Parse URL → Extract slug
2. Query APIs (CLOB first, then Gamma)
3. Fetch price history for ALL outcomes
4. Process and validate data
5. Export to requested formats

## CRITICAL IMPLEMENTATION RULES

### Error Handling
- ALWAYS use custom exceptions from `exceptions.py`
- NEVER catch generic Exception without re-raising
- ALWAYS log errors before raising
- IMPLEMENT retry logic for all API calls

### Data Validation
- Prices MUST be between 0.0 and 1.0
- Timestamps MUST be UTC
- Market slugs MUST be URL-safe
- VALIDATE all user inputs

### Performance Requirements
- Batch API requests when possible
- Use forward-fill for missing price data
- Limit DataFrame operations to necessary columns
- Cache API responses when appropriate

## COMMON USER REQUESTS - STANDARD RESPONSES

### "Search for markets about X"
1. Use `mango search` command with appropriate filters
2. Apply --min-volume filter for quality markets
3. Check both active and inactive if needed
4. Suggest specific market slugs for further analysis

### "Show me the order book"
1. Use `mango book` for detailed depth
2. Use `mango market-info --show-book` for overview
3. Export to JSON for programmatic analysis
4. Check spread and liquidity metrics

### "Track my portfolio"
1. Use `mango portfolio` with wallet address
2. Apply --min-size filter for significant positions
3. Show P&L calculations with --show-pnl
4. Export to JSON for further analysis

### "Extract historical data"
1. Use `polymarket-extract` for time series data
2. Validate URL format
3. Check if event or market URL
4. Default to data/ directory output
5. For event URLs: suggest --extract-all-markets flag

### "Extract all markets from an event"
1. Verify it's an event URL, not a market URL
2. Use --extract-all-markets flag
3. Choose appropriate column format (short for readability)
4. Warn about extraction time for large events (20+ markets)
5. Suggest appropriate time intervals (daily for long-term, hourly for short-term)

### "Why is data missing?"
1. Check market age (new markets have limited history)
2. Verify time interval compatibility
3. Confirm market is active
4. Check API rate limits
5. For order books: verify market has liquidity

### "Export failed"
1. Verify output directory exists
2. Check file size limits (CSV: 100MB, JSON: 50MB)
3. Ensure sufficient disk space
4. Validate export format
5. Check write permissions

## COLLABORATION GUIDELINES

### Challenge and Question
- **DO NOT** immediately agree or proceed with requests that seem suboptimal, unclear, or potentially problematic
- **ALWAYS** evaluate the technical merit and architectural fit of any proposed change
- **QUESTION** assumptions that conflict with established patterns

### Push Back Constructively
- **IDENTIFY** issues with proposed approaches immediately
- **SUGGEST** better alternatives with clear technical reasoning
- **EXPLAIN** why current architecture decisions exist
- **DEFEND** clean code principles and established patterns

### Think Critically
- **CONSIDER** edge cases before implementing any feature
- **EVALUATE** performance implications of all changes
- **ASSESS** maintainability impact of new code
- **ANTICIPATE** future scaling requirements

### Seek Clarification
- **ASK** follow-up questions when requirements are ambiguous
- **DEMAND** specific examples for vague requests
- **CLARIFY** success criteria before starting work
- **CONFIRM** understanding of complex requirements

### Propose Improvements
- **SUGGEST** better patterns when you see suboptimal code
- **RECOMMEND** more robust solutions for fragile implementations
- **ADVOCATE** for cleaner, more maintainable approaches
- **IDENTIFY** opportunities for code reuse and abstraction

### Be a Thoughtful Collaborator
- **ACT** as a senior engineer who improves overall code quality
- **PROVIDE** reasoning for all technical decisions
- **SHARE** knowledge about best practices and patterns
- **MAINTAIN** high standards for code review and implementation

## CRITICAL WARNINGS

### API Limitations
- CLOB API requires authentication for enhanced limits
- CLOB API prices endpoint doesn't support multiple token_ids in one request
- Individual price endpoints (/bid, /ask) may return 404 for low-liquidity markets
- Gamma API may return stale data for inactive markets
- Data API has no authentication but data may be delayed
- Rate limits: 60 requests/minute (ENFORCE THIS)
- Historical data limited by market age
- Order book depth depends on market liquidity

### Data Quirks
- Some markets use "Yes"/"No", others use custom outcomes
- Grouped markets (negRisk) require special handling
- Price precision limited to 4 decimal places
- Order book prices in string format (convert to Decimal)
- Token IDs are long hex strings, NOT market slugs
- Position sizes may include decimal places

### Common Pitfalls
- DO NOT hardcode API endpoints
- DO NOT skip URL validation for polymarket-extract
- DO NOT use URLs with mango commands (use slugs)
- DO NOT ignore retry logic
- DO NOT mix synchronous and async code
- DO NOT bypass the data/ directory convention
- DO NOT confuse market slugs with token IDs
- DO NOT try to fetch prices for multiple tokens in one API call

## DEBUGGING CHECKLIST

When issues arise, check in this order:
1. Validate input URL format
2. Confirm API connectivity
3. Check authentication if using CLOB
4. Verify market exists and is active
5. Examine log output (set DEBUG level)
6. Test with known working market
7. Check rate limit status

## PERFORMANCE OPTIMIZATION

### Required Optimizations
- Use batch operations for multiple markets
- Implement connection pooling for API clients
- Cache market metadata for 5 minutes
- Stream large datasets instead of loading to memory

### Forbidden Practices
- NO synchronous loops for API calls
- NO unbounded data fetching
- NO string concatenation in loops
- NO redundant DataFrame copies

## TESTING REQUIREMENTS

### Before ANY commit:
1. Run full test suite with coverage
2. Verify type hints pass mypy
3. Ensure black formatting applied
4. Confirm no flake8 violations
5. Test with real market URLs
6. Validate all export formats

### Integration Test Scenarios:
- Event URL with multiple markets
- Market with no historical data  
- Invalid/malformed URLs
- API timeout handling
- Large dataset exports
- Order book with no liquidity
- Portfolio with no positions
- Market search with no results
- Rate limit handling

### New Feature Tests:
- `mango search` with various filters
- `mango book` JSON export format
- `mango portfolio` P&L calculations
- `mango holders` pagination
- Order book depth analysis
- Market impact calculations

## FINAL DIRECTIVES

1. **MAINTAIN** the clean architecture at all costs
2. **PRESERVE** type safety throughout the codebase
3. **ENFORCE** consistent error handling patterns
4. **PROTECT** against malicious inputs
5. **OPTIMIZE** for reliability over speed
6. **DOCUMENT** any deviations from established patterns

Remember: This codebase serves financial analysis. Accuracy, reliability, and maintainability are non-negotiable. Every decision must reinforce these principles.