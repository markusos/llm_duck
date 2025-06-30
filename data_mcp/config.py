"""Configuration settings for the NYC 311 Data MCP Server."""

import logging
import sys
from dataclasses import dataclass
from pathlib import Path


class LoggerConfig:
    """Centralized logging configuration."""

    @staticmethod
    def setup_logger(
        name: str, log_file: Path, level: int = logging.INFO
    ) -> logging.Logger:
        """Configure and return a logger instance."""
        logger = logging.getLogger(name)
        logger.setLevel(level)

        # Avoid duplicate handlers
        if logger.handlers:
            return logger

        # File handler
        file_handler = logging.FileHandler(log_file, mode="a", encoding="utf-8")
        file_handler.setLevel(level)

        # Console handler for development
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)

        # Formatter
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        logger.propagate = False

        return logger

    @staticmethod
    def get_paths() -> tuple[Path, Path, Path]:
        """Get configured paths for script directory, data directory, and log file."""
        script_dir = Path(__file__).parent
        data_dir = script_dir.parent / "data"
        log_file = script_dir / "mcp_server.log"
        return script_dir, data_dir, log_file


@dataclass
class ServerConfig:
    """Configuration for the MCP server."""

    # Server identification
    server_name: str = "NYC 311 Data Server"
    server_version: str = "1.0.0"

    # Database settings
    database_type: str = ":memory:"
    read_only: bool = False

    # File paths (relative to project root)
    categories_file: str = "data/categories.json"
    service_requests_file: str = "data/cityofnewyork/service_requests_2024.parquet"

    # Logging configuration
    log_level: str = "INFO"
    log_file: str = "mcp_server.log"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # Query limitations
    max_query_results: int = 10000
    query_timeout_seconds: int = 30

    # Allowed SQL operations
    allowed_sql_keywords: tuple[str, ...] = (
        "SELECT",
        "WITH",
        "ORDER",
        "GROUP",
        "HAVING",
        "LIMIT",
    )
    forbidden_sql_keywords: tuple[str, ...] = (
        "DROP",
        "DELETE",
        "UPDATE",
        "INSERT",
        "ALTER",
        "CREATE",
        "TRUNCATE",
        "EXEC",
        "EXECUTE",
    )


# Default configuration instance
default_config = ServerConfig()
