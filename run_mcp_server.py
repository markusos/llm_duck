#!/usr/bin/env python3
"""
Wrapper script to run the NYC 311 Data MCP Server.
"""

import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

if __name__ == "__main__":
    from data_mcp.main import main

    main()
