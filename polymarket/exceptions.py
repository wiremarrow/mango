"""
Custom exceptions for the Polymarket library.

This module defines all custom exceptions used throughout the library,
providing clear error handling and debugging capabilities.
"""


class PolymarketError(Exception):
    """Base exception for all Polymarket-related errors."""
    pass


class APIError(PolymarketError):
    """Raised when an API request fails."""
    pass


class RateLimitError(APIError):
    """Raised when API rate limit is exceeded."""
    pass


class AuthenticationError(APIError):
    """Raised when API authentication fails."""
    pass


class MarketNotFoundError(PolymarketError):
    """Raised when a requested market cannot be found."""
    def __init__(self, slug: str):
        self.slug = slug
        super().__init__(f"Market not found: {slug}")


class InvalidURLError(PolymarketError):
    """Raised when a Polymarket URL cannot be parsed."""
    def __init__(self, url: str):
        self.url = url
        super().__init__(f"Invalid Polymarket URL: {url}")


class DataProcessingError(PolymarketError):
    """Raised when data processing fails."""
    pass


class ExportError(DataProcessingError):
    """Raised when data export fails."""
    pass


class ValidationError(PolymarketError):
    """Raised when data validation fails."""
    pass


class PriceValidationError(ValidationError):
    """Raised when price data is invalid."""
    def __init__(self, price: float, message: str = ""):
        self.price = price
        msg = f"Invalid price: {price}"
        if message:
            msg += f" - {message}"
        super().__init__(msg)


class TimeIntervalError(ValidationError):
    """Raised when an invalid time interval is specified."""
    def __init__(self, interval: str):
        self.interval = interval
        super().__init__(f"Invalid time interval: {interval}")


class InsufficientDataError(PolymarketError):
    """Raised when there's not enough data for the requested operation."""
    pass