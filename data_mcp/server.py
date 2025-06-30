"""
MCP server setup and tools for the NYC 311 Data MCP Server.
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

import duckdb

from .config import LoggerConfig
from .database import DatabaseManager
from .exceptions import DatabaseError, ValidationError
from .models import AppContext


def create_mcp_server(data_dir, log_file):
    """Factory function to create and configure the MCP server."""
    from mcp.server.fastmcp import FastMCP

    # Logger setup
    logger = LoggerConfig.setup_logger(__name__, log_file)

    @asynccontextmanager
    async def app_lifespan(server) -> AsyncIterator[AppContext]:
        """Manage application lifecycle with proper resource cleanup."""
        db = None
        try:
            # Initialize database connection
            logger.info("Initializing database connection")
            db = duckdb.connect(database=":memory:", read_only=False)

            # Create and yield context
            context = AppContext(db=db, data_dir=data_dir)
            logger.info("Application context created successfully")
            yield context

        except Exception as e:
            logger.error(f"Failed to initialize application: {e}")
            raise
        finally:
            # Cleanup resources
            if db:
                logger.info("Closing database connection")
                db.close()
            logger.info("Application shutdown complete")

    # Create MCP server instance
    mcp = FastMCP(
        name="NYC 311 Data Server",
        instructions="A specialized server for querying NYC 311 service request data. Use the query_data tool with SQL SELECT statements to explore the service_requests table. Check the schema resource (schema://service_requests) or use the get_table_schema tool for table structure information.",
        lifespan=app_lifespan,
    )

    @mcp.tool()
    async def query_data(sql: str, ctx=None) -> list[dict[str, Any]]:
        """
        Query the NYC 311 service requests data using a SQL query.

        Available tables:
        - service_requests: Contains all service requests data for 2024
          with columns for location, complaint type, agency, timestamps, etc.

        Example queries:
        - Count by complaint type: SELECT complaint_type, COUNT(*) as count FROM service_requests GROUP BY complaint_type ORDER BY count DESC LIMIT 10
        - Recent requests: SELECT * FROM service_requests WHERE created_date >= '2024-01-01' LIMIT 100
        - Borough analysis: SELECT borough, COUNT(*) FROM service_requests GROUP BY borough

        Args:
            sql: A SELECT SQL query string (other operations are forbidden)
            ctx: FastMCP context for logging and notifications

        Returns:
            The result of the SQL query as a list of dictionaries, where each dictionary
            represents a row with column names as keys.

        Raises:
            ValidationError: If the SQL query is invalid or contains forbidden operations
            DatabaseError: If database operation fails
        """
        if not sql or not sql.strip():
            raise ValidationError("SQL query cannot be empty")

        try:
            if ctx:
                await ctx.info("Processing SQL query request")

            app_context = mcp.get_context()
            db_manager = DatabaseManager(
                app_context.request_context.lifespan_context.db, logger
            )

            # Validate query before execution
            db_manager.validate_sql_query(sql)

            if ctx:
                await ctx.debug("Query validation passed, executing...")
                await ctx.report_progress(
                    0.3, 1.0, "Validation complete, executing query..."
                )

            # Execute the query
            result = db_manager.execute_query(sql)

            if ctx:
                await ctx.report_progress(
                    0.9, 1.0, "Query execution complete, formatting results..."
                )
                await ctx.info(f"Query completed successfully with {len(result)} rows")
                await ctx.report_progress(1.0, 1.0, "Results ready")

            return result

        except (DatabaseError, ValidationError):
            if ctx:
                await ctx.error("Query failed validation or execution")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in query_data: {e}")
            if ctx:
                await ctx.error(f"Unexpected error: {str(e)}")
            raise DatabaseError(f"Failed to execute query: {e}") from e

    # Add resource for database schema information
    @mcp.resource("schema://service_requests")
    async def get_schema() -> str:
        """
        Get the schema information for the service_requests table.

        Returns:
            Schema information including column names, types, and descriptions from database metadata
        """
        try:
            app_context = mcp.get_context()
            db = app_context.request_context.lifespan_context.db
            db_manager = DatabaseManager(db, logger)
            return db_manager.get_schema_info()
        except Exception as e:
            logger.error(f"Failed to get schema: {e}")
            return f"Error retrieving schema: {e}"

    @mcp.tool()
    async def get_table_schema(ctx=None) -> str:
        """
        Get the schema information for the service_requests table.

        This tool provides the same information as the schema resource but as a callable tool.

        Returns:
            Schema information including column names, types, and descriptions from database metadata
        """
        try:
            if ctx:
                await ctx.info("Retrieving table schema information")

            app_context = mcp.get_context()
            db = app_context.request_context.lifespan_context.db
            db_manager = DatabaseManager(db, logger)

            return db_manager.get_schema_info()
        except Exception as e:
            logger.error(f"Failed to get schema via tool: {e}")
            if ctx:
                await ctx.error(f"Schema retrieval failed: {str(e)}")

            return f"Error retrieving schema: {e}"

    return mcp
