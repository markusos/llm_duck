"""
Unit tests for the NYC 311 Data MCP Server.
"""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from .config import LoggerConfig
from .database import DatabaseManager
from .exceptions import DatabaseError, ValidationError
from .models import AppContext
from .server import create_mcp_server


class TestLoggerConfig:
    """Test cases for LoggerConfig class."""

    def test_setup_logger_creates_logger_with_handlers(self):
        """Test that setup_logger creates a logger with file and console handlers."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            log_path = Path(tmp_file.name)

        try:
            logger = LoggerConfig.setup_logger("test_logger", log_path)

            assert logger.name == "test_logger"
            assert len(logger.handlers) == 2  # file + console
            assert not logger.propagate
        finally:
            log_path.unlink(missing_ok=True)


class TestDatabaseManager:
    """Test cases for DatabaseManager class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_db = Mock()
        self.mock_logger = Mock()
        self.db_manager = DatabaseManager(self.mock_db, self.mock_logger)

    def test_execute_query_success_with_performance_logging(self):
        """Test successful query execution and performance logging."""
        # Mock database response
        self.mock_db.execute.return_value.fetchall.return_value = [("cat1",), ("cat2",)]
        self.mock_db.description = [("category",)]

        result = self.db_manager.execute_query("SELECT * FROM test")

        # Verify result structure
        assert result == [{"category": "cat1"}, {"category": "cat2"}]

        # Verify logging was called
        self.mock_logger.info.assert_called()

        # Check that performance metrics were logged
        info_calls = [call.args[0] for call in self.mock_logger.info.call_args_list]
        assert any("Executing query" in msg for msg in info_calls)
        assert any("Query executed successfully" in msg for msg in info_calls)

        # Check that execution time was logged in success call
        success_call = next(
            call
            for call in self.mock_logger.info.call_args_list
            if call.args[0] == "Query executed successfully"
        )
        assert "execution_time_ms" in success_call.kwargs["extra"]
        assert "row_count" in success_call.kwargs["extra"]

    def test_execute_query_with_params(self):
        """Test query execution with parameters."""
        self.mock_db.execute.return_value.fetchall.return_value = []
        self.mock_db.description = []

        params = {"table": "test_table"}
        self.db_manager.execute_query("SELECT * FROM ?", params)

        self.mock_db.execute.assert_called_with("SELECT * FROM ?", params)

    def test_execute_query_database_error(self):
        """Test query execution failure."""
        self.mock_db.execute.side_effect = Exception("DB Error")

        with pytest.raises(DatabaseError, match="Query execution failed"):
            self.db_manager.execute_query("SELECT * FROM test")

    def test_sql_validation_comprehensive(self):
        """Comprehensive test of SQL validation rules."""
        # Valid queries should pass
        valid_queries = [
            "SELECT * FROM table LIMIT 10",
            "SELECT col1, col2 FROM table",
            "   select col1, col2 from table   ",
        ]
        for query in valid_queries:
            self.db_manager.validate_sql_query(query)  # Should not raise

        # Invalid queries should fail
        invalid_cases = [
            ("", "SQL query cannot be empty"),
            ("   ", "SQL query cannot be empty"),
            ("SHOW TABLES", "Only SELECT queries are allowed"),
            ("SELECT * FROM table", "SELECT \\* queries must include a LIMIT clause"),
            ("DROP TABLE test", "forbidden keyword"),
            ("UPDATE table SET col=1", "forbidden keyword"),
            ("SELECT col1 FROM table -- DROP TABLE test", "forbidden keyword"),
        ]

        for query, expected_error in invalid_cases:
            with pytest.raises(ValidationError, match=expected_error):
                self.db_manager.validate_sql_query(query)


class TestAppContext:
    """Test cases for AppContext class."""

    @patch("data_mcp.models.duckdb")
    def test_app_context_initialization(self, mock_duckdb):
        """Test AppContext initialization and table setup."""
        mock_db = Mock()
        mock_duckdb.connect.return_value = mock_db

        with tempfile.TemporaryDirectory() as tmp_dir:
            data_dir = Path(tmp_dir)
            cityofnewyork_dir = data_dir / "cityofnewyork"
            cityofnewyork_dir.mkdir()

            # Create a dummy parquet file
            parquet_file = cityofnewyork_dir / "service_requests_2024.parquet"
            parquet_file.touch()

            AppContext(db=mock_db, data_dir=data_dir)

            # Verify table initialization was attempted - should be multiple calls now
            # (table creation + table comment + column comments)
            assert mock_db.execute.call_count > 1

            # Check that the first call was table creation
            first_call_args = mock_db.execute.call_args_list[0][0][0]
            assert "CREATE TABLE IF NOT EXISTS service_requests" in first_call_args

            # Check that table comment was added
            calls = [call[0][0] for call in mock_db.execute.call_args_list]
            table_comment_calls = [
                call for call in calls if "COMMENT ON TABLE service_requests" in call
            ]
            assert len(table_comment_calls) == 1

            # Check that column comments were added
            column_comment_calls = [
                call for call in calls if "COMMENT ON COLUMN service_requests." in call
            ]
            assert len(column_comment_calls) > 0


@pytest.fixture
def mcp_server():
    """Create an MCP server instance for testing."""
    from pathlib import Path

    data_dir = Path("/tmp")
    with tempfile.NamedTemporaryFile(suffix=".log", delete=False) as tmp_log:
        log_file = Path(tmp_log.name)

    try:
        with patch("data_mcp.config.LoggerConfig.setup_logger"):
            yield create_mcp_server(data_dir, log_file)
    finally:
        log_file.unlink(missing_ok=True)


class TestMCPServer:
    """Integration tests for MCP server functionality."""

    def test_server_configuration_and_tools(self, mcp_server):
        """Test server configuration, tools, and resources."""
        # Test server configuration
        assert mcp_server.name == "NYC 311 Data Server"
        assert (
            "specialized server for querying nyc 311" in mcp_server.instructions.lower()
        )
        assert mcp_server.settings.lifespan is not None

        # Test tools registration
        tools = mcp_server._tool_manager.list_tools()
        assert len(tools) >= 1

        query_tool = next(tool for tool in tools if tool.name == "query_data")
        assert "NYC 311 service requests data" in query_tool.description
        # Note: Full description may vary between real and mock implementations

        # Test resources registration
        resources = mcp_server._resource_manager.list_resources()
        resource_uris = [str(resource.uri) for resource in resources]
        assert "schema://service_requests" in resource_uris

        schema_resource = next(
            resource
            for resource in resources
            if str(resource.uri) == "schema://service_requests"
        )
        assert hasattr(schema_resource, "fn")  # Should be a function resource
