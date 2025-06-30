"""
Database operations and management for the NYC 311 Data MCP Server.
"""

import logging
import time
from typing import Any

import duckdb

from .exceptions import DatabaseError, ValidationError


class DatabaseManager:
    """Handles database operations with proper error handling."""

    def __init__(self, db: duckdb.DuckDBPyConnection, logger: logging.Logger):
        self.db = db
        self.logger = logger

    def execute_query(
        self, query: str, params: dict | None = None
    ) -> list[dict[str, Any]]:
        """
        Execute a SQL query with parameter binding to prevent SQL injection.

        Args:
            query: SQL query string with parameter placeholders
            params: Dictionary of parameters to bind to the query

        Returns:
            List of dictionaries representing query results

        Raises:
            DatabaseError: If query execution fails
        """
        query_start_time = time.time()
        try:
            self.logger.info(
                "Executing query",
                extra={
                    "query_preview": query[:100] + "..." if len(query) > 100 else query,
                    "has_params": bool(params),
                    "param_count": len(params) if params else 0,
                },
            )

            # Use parameter binding instead of f-strings for security
            if params:
                result = self.db.execute(query, params).fetchall()
            else:
                result = self.db.execute(query).fetchall()

            columns = [desc[0] for desc in self.db.description]
            result_dicts = [dict(zip(columns, row, strict=True)) for row in result]

            query_duration = time.time() - query_start_time
            self.logger.info(
                "Query executed successfully",
                extra={
                    "row_count": len(result_dicts),
                    "execution_time_ms": round(query_duration * 1000, 2),
                    "column_count": len(columns),
                },
            )
            return result_dicts

        except Exception as e:
            query_duration = time.time() - query_start_time
            self.logger.error(
                "Database query failed",
                extra={
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "execution_time_ms": round(query_duration * 1000, 2),
                    "query_preview": query[:100] + "..." if len(query) > 100 else query,
                },
            )
            raise DatabaseError(f"Query execution failed: {e}") from e

    def validate_sql_query(self, sql: str) -> None:
        """
        Basic SQL validation to prevent dangerous operations.

        Args:
            sql: SQL query string to validate

        Raises:
            ValidationError: If query contains potentially dangerous operations
        """
        if not sql or not sql.strip():
            raise ValidationError("SQL query cannot be empty")

        sql_upper = sql.upper().strip()

        # Block dangerous operations
        dangerous_keywords = [
            "DROP",
            "DELETE",
            "UPDATE",
            "INSERT",
            "ALTER",
            "CREATE",
            "TRUNCATE",
            "EXEC",
            "EXECUTE",
            "PRAGMA",
        ]

        for keyword in dangerous_keywords:
            if keyword in sql_upper:
                raise ValidationError(f"Query contains forbidden keyword: {keyword}")

        # Ensure query starts with SELECT
        if not sql_upper.startswith("SELECT"):
            raise ValidationError("Only SELECT queries are allowed")

        # Check for potential performance issues
        if "SELECT *" in sql_upper and "LIMIT" not in sql_upper:
            raise ValidationError(
                "SELECT * queries must include a LIMIT clause for performance reasons"
            )

    def get_schema_info(self) -> str:
        """
        Get the schema information for the service_requests table including comments.

        Returns:
            Schema information including column names, types, and descriptions from metadata
        """
        try:
            # First, try to get comments from DuckDB metadata if available
            try:
                comments_query = """
                    SELECT column_name, comment
                    FROM duckdb_columns()
                    WHERE table_name = 'service_requests' AND comment IS NOT NULL
                """
                comment_result = self.db.execute(comments_query).fetchall()
                comments_dict = {row[0]: row[1] for row in comment_result}
            except Exception:
                # If that fails, we'll use our predefined descriptions
                comments_dict = {}

            # Get basic column information
            schema_query = """
                SELECT 
                    column_name, 
                    data_type, 
                    is_nullable
                FROM information_schema.columns
                WHERE table_name = 'service_requests'
                ORDER BY ordinal_position
            """

            result = self.db.execute(schema_query).fetchall()
            if result:
                schema_info = ["Service Requests Table Schema:"]
                schema_info.append(
                    "NYC 311 Service Requests data for 2024 containing complaint information, locations, agencies, and resolution details"
                )
                schema_info.append("")

                for row in result:
                    col_name, data_type, nullable = row
                    nullable_text = "nullable" if nullable == "YES" else "not null"
                    # Use comment from database if available
                    description = comments_dict.get(col_name, "")
                    comment_text = f" - {description}" if description else ""
                    schema_info.append(
                        f"- {col_name}: {data_type} ({nullable_text}){comment_text}"
                    )

                return "\n".join(schema_info)
            else:
                # Fallback to basic schema if no results
                return self._get_basic_schema_info()

        except Exception as e:
            self.logger.error(f"Failed to get schema with comments: {e}")
            return self._get_basic_schema_info()

    def _get_basic_schema_info(self) -> str:
        """
        Fallback method to get basic schema information without comments.

        Returns:
            Basic schema information
        """
        try:
            schema_query = """
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_name = 'service_requests'
                ORDER BY ordinal_position
            """

            result = self.db.execute(schema_query).fetchall()
            if result:
                schema_info = ["Service Requests Table Schema:"]
                for row in result:
                    col_name, data_type, nullable = row
                    nullable_text = "nullable" if nullable == "YES" else "not null"
                    schema_info.append(f"- {col_name}: {data_type} ({nullable_text})")
                return "\n".join(schema_info)

        except Exception as e:
            self.logger.error(f"Failed to get basic schema: {e}")
            return "Error retrieving schema information"
