"""
Custom exceptions for the NYC 311 Data MCP Server.
"""


class DatabaseError(Exception):
    """Custom exception for database-related errors."""

    pass


class ValidationError(Exception):
    """Custom exception for input validation errors."""

    pass
