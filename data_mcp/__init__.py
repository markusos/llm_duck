"""
NYC 311 Data MCP Server Package.

This package provides a Model Context Protocol (MCP) server for querying NYC 311 service request data.
"""

from .exceptions import DatabaseError, ValidationError
from .main import main

__version__ = "1.0.0"
__all__ = ["main", "DatabaseError", "ValidationError"]
