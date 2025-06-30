# NYC 311 Data MCP Server

A specialized [Model Context Protocol](https://modelcontextprotocol.io/introduction) (MCP) server that read-only access to NYC 311 service request data through SQL queries. This server enables AI assistants to analyze and explore New York City's public service request data from 2024.

## What is MCP?

The Model Context Protocol (MCP) is an open protocol that standardizes how applications provide context to Large Language Models (LLMs). Think of MCP like a USB-C port for AI applications - it provides a standardized way to connect AI models to different data sources and tools.

## Overview

This MCP server exposes NYC 311 service request data through:
- **SQL Query Tool**: Execute read-only SELECT queries against the service requests database
- **Schema Resource**: Access table structure and column information
- **Built-in Security**: Query validation prevents dangerous operations
- **Performance Monitoring**: Detailed logging and execution tracking

## Features

### 🛡️ Security First
- **Read-only access**: Only SELECT queries are permitted
- **Query validation**: Blocks dangerous SQL operations (DROP, DELETE, UPDATE, etc.)
- **Parameter binding**: Prevents SQL injection attacks
- **Performance limits**: Requires LIMIT clauses for SELECT * queries

### 📊 Rich Data Access
- **2024 NYC 311 Data**: Complete service request dataset with location, complaint types, agencies, and timestamps
- **Spatial Analysis**: Includes borough and geographic information
- **Time Series**: Temporal data for trend analysis
- **Categorized Complaints**: Pre-processed complaint type categories

### 🔧 Developer Friendly
- **FastMCP Framework**: Built on the modern FastMCP server framework
- **Async Support**: Non-blocking operations with progress reporting
- **Comprehensive Logging**: Detailed execution logs and error tracking
- **DuckDB Backend**: High-performance analytics database

## Installation & Setup

### Prerequisites
- Python 3.9+
- uv package manager
- MCP-compatible client (Claude Desktop, LM Studio, etc.)

### Configuration

Add this server to your MCP host configuration file (`mcp.json`):

```json
{
  "mcpServers": {
    "nyc_311_data": {
      "command": "uv",
      "args": [
        "--directory",
        "/ABSOLUTE/PATH/TO/llm_duck",
        "run",
        "run_mcp_server.py"
      ]
    }
  }
}
```

**Important**: Replace `/ABSOLUTE/PATH/TO/llm_duck` with the actual absolute path to your project directory.

### Client Setup Examples

#### Claude Desktop
1. Open Claude Desktop
2. Navigate to Settings → Developer
3. Edit your `mcp.json` configuration file
4. Add the server configuration above
5. Restart Claude Desktop

#### LM Studio
For LM Studio setup instructions, see: https://lmstudio.ai/blog/lmstudio-v0.3.17

## Usage

### Available Tools

#### `query_data`
Execute SQL SELECT queries against the NYC 311 service requests data.

**Parameters:**
- `sql` (string): A SELECT SQL query

**Example Queries:**
```sql
-- Top 10 complaint types
SELECT complaint_type, COUNT(*) as count 
FROM service_requests 
GROUP BY complaint_type 
ORDER BY count DESC 
LIMIT 10

-- Recent requests by borough
SELECT borough, COUNT(*) as requests
FROM service_requests 
WHERE created_date >= '2024-01-01'
GROUP BY borough
ORDER BY requests DESC

-- Monthly trend analysis
SELECT 
    DATE_TRUNC('month', created_date) as month,
    COUNT(*) as request_count
FROM service_requests 
WHERE created_date >= '2024-01-01'
GROUP BY month
ORDER BY month
```

### Available Resources

#### `schema://service_requests`
Provides schema information for the service_requests table, including:
- Column names and data types
- Nullable/non-null constraints
- Table structure overview

## Data Schema

The `service_requests` table contains NYC 311 service request data with columns including:
- **Location data**: Borough, ZIP code, latitude/longitude
- **Request details**: Complaint type, agency, status, resolution
- **Temporal data**: Created date, closed date, due date
- **Administrative**: Unique key, agency name, descriptor

Access the complete schema using the `schema://service_requests` resource.

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   MCP Client    │    │   NYC 311 Data   │    │   DuckDB        │
│  (Claude, etc.) │◄──►│   MCP Server     │◄──►│   Database      │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                                       ▲
                                                       |
                                                       ▼
                                               ┌─────────────────┐
                                               │  Parquet Files  │
                                               │  (Data Sources) │
                                               └─────────────────┘
```

### Components

- **`main.py`**: Entry point and server initialization
- **`server.py`**: MCP server setup, tools, and resources
- **`database.py`**: Database operations and query management
- **`models.py`**: Data models and application context
- **`config.py`**: Configuration and logging setup
- **`exceptions.py`**: Custom exception classes

## Development

### Running Locally
```bash
# From project root
uv run run_mcp_server.py
```

### Testing
```bash
# Run tests
uv run pytest data_mcp/test_main.py -v
```

### Logging
Server logs are written to `data_mcp/mcp_server.log` and include:
- Query execution details
- Performance metrics
- Error tracking
- Security validation events

