"""
Constants used throughout the Polymarket library.

This module centralizes magic numbers, strings, and other constants
to improve maintainability and make the codebase more configurable.
"""

# API retry configuration
MAX_RETRIES = 3
RETRY_DELAY = 1.0  # seconds
RETRY_BACKOFF_FACTOR = 2  # exponential backoff multiplier

# Rate limiting
RATE_LIMIT_DELAY = 0.1  # 100ms between requests
RATE_LIMIT_CHUNK_DELAY = 0.5  # 500ms between market extractions

# Data extraction limits
MAX_COLUMN_PREFIX_LENGTH = 20
MAX_MARKET_QUESTION_DISPLAY = 50
DEFAULT_FLOAT_PRECISION = 4

# Memory optimization thresholds
AUTO_STREAMING_THRESHOLD = 10  # markets
GARBAGE_COLLECTION_INTERVAL = 5  # markets

# Progress display
PROGRESS_UPDATE_INTERVAL = 10  # seconds

# CLI output formatting
CLI_SEPARATOR = "=" * 80
CLI_SUBSEPARATOR = "-" * 40

# Error messages
ERROR_NO_TOKENS = "This market does not have tradeable tokens yet."
ERROR_INACTIVE_NEGRISK = "This option in the grouped market is not yet active for trading."
ERROR_PLACEHOLDER_OPTION = "This appears to be a placeholder or unactivated option in a negRisk market."
ERROR_MARKET_NOT_FOUND = "Market not found: {slug}"
ERROR_EVENT_NOT_FOUND = "Event not found: {slug}"

# Success messages
SUCCESS_EXTRACTION_COMPLETE = "Extraction complete: {successful} succeeded, {failed} failed"
SUCCESS_DATA_SAVED = "Saved {format} to: {filepath}"

# Info messages
INFO_FETCHING_MARKET = "Fetching market metadata..."
INFO_FETCHING_EVENT = "Fetching event: {slug}"
INFO_FETCHING_PRICE_HISTORY = "Fetching price history..."
INFO_EXTRACTING_MARKET = "[{current}/{total}] Extracting: {name}..."

# Suggestions
SUGGESTION_EVENT_EXTRACTION = "Try extracting active options from the event page"
SUGGESTION_USE_EXTRACT_ALL = "Use --extract-all-markets on the event URL (active options only)"
SUGGESTION_CHECK_URL = "Make sure you're using the exact market URL from Polymarket.com"