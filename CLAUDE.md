# CLAUDE.md - Critical Project Context for Polymarket Data Extractor

## PROJECT MANDATE

You are working with a professional-grade Python library for extracting historical price data from Polymarket prediction markets. This codebase demands precision, reliability, and adherence to clean architecture principles.

## ESSENTIAL COMMANDS - MEMORIZE THESE

### Primary Operations
```bash
# Extract market data with default settings (30 days, daily intervals)
polymarket-extract "https://polymarket.com/event/market-slug"

# Extract with specific parameters - USE THESE EXACT FLAGS
polymarket-extract "URL" -i 1h -d 7  # 7 days of hourly data
polymarket-extract "URL" --start 2024-01-01 --end 2024-01-31  # Date range
polymarket-extract "URL" -o analysis -f csv json excel  # Multiple formats

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
1. **CLOB API** - ALWAYS try first (most current data)
2. **Gamma API** - Fallback only (metadata rich but potentially stale)
3. **NEVER** skip the fallback chain

### Module Boundaries - DO NOT VIOLATE
- `api.py` - API communication ONLY
- `models.py` - Data structures ONLY  
- `parser.py` - URL parsing ONLY
- `processor.py` - Data manipulation ONLY
- `config.py` - Configuration ONLY
- `exceptions.py` - Error definitions ONLY

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

### "Extract data from this market"
1. Validate URL format
2. Check if event or market URL
3. Extract appropriate data
4. Default to data/ directory output

### "Why is data missing?"
1. Check market age (new markets have limited history)
2. Verify time interval compatibility
3. Confirm market is active
4. Check API rate limits

### "Export failed"
1. Verify output directory exists
2. Check file size limits (CSV: 100MB, JSON: 50MB)
3. Ensure sufficient disk space
4. Validate export format

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
- CLOB API requires authentication for some endpoints
- Gamma API may return stale data for inactive markets
- Rate limits: 60 requests/minute (respect this)
- Historical data limited by market age

### Data Quirks
- Some markets use "Yes"/"No", others use custom outcomes
- Grouped markets (negRisk) require special handling
- Price precision limited to 4 decimal places
- Timestamps may have microsecond variations

### Common Pitfalls
- DO NOT hardcode API endpoints
- DO NOT skip URL validation
- DO NOT ignore retry logic
- DO NOT mix synchronous and async code
- DO NOT bypass the data/ directory convention

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

## FINAL DIRECTIVES

1. **MAINTAIN** the clean architecture at all costs
2. **PRESERVE** type safety throughout the codebase
3. **ENFORCE** consistent error handling patterns
4. **PROTECT** against malicious inputs
5. **OPTIMIZE** for reliability over speed
6. **DOCUMENT** any deviations from established patterns

Remember: This codebase serves financial analysis. Accuracy, reliability, and maintainability are non-negotiable. Every decision must reinforce these principles.