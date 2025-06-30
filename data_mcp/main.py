"""
Main entry point for the NYC 311 Data MCP Server.

This module provides a Model Context Protocol (MCP) server for querying NYC 311 service request data.
"""

import logging
import sys

from .config import LoggerConfig
from .server import create_mcp_server


def main() -> None:
    """Main entry point for the MCP server."""
    try:
        # Get configuration paths
        script_dir, data_dir, log_file = LoggerConfig.get_paths()

        # Create and start server
        server = create_mcp_server(data_dir, log_file)
        logger = logging.getLogger(__name__)
        logger.info("Starting NYC 311 Data MCP server...")
        server.run()
    except Exception as e:
        print(f"Failed to start server: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
