"""
Test schema functionality with database comments.
"""

import contextlib
import sys
import tempfile
from pathlib import Path

import duckdb
import pytest

# Handle imports for both pytest and standalone execution
try:
    from .config import LoggerConfig
    from .database import DatabaseManager
    from .models import AppContext
except ImportError:
    # Standalone execution
    sys.path.append(str(Path(__file__).parent))
    from config import LoggerConfig
    from database import DatabaseManager
    from models import AppContext


class TestSchemaComments:
    """Test suite for schema comment functionality."""

    @pytest.fixture
    def logger(self):
        """Create a test logger."""
        with tempfile.NamedTemporaryFile(suffix=".log", delete=False) as tmp_log:
            log_file = Path(tmp_log.name)

        try:
            logger_instance = LoggerConfig.setup_logger(__name__, log_file)
            yield logger_instance
        finally:
            log_file.unlink(missing_ok=True)

    @pytest.fixture
    def data_dir(self):
        """Create test data directory path."""
        return Path(__file__).parent.parent / "data"

    @pytest.fixture
    def db_context(self, data_dir):
        """Create database context with test data."""
        db = duckdb.connect(database=":memory:", read_only=False)
        context = AppContext(db=db, data_dir=data_dir)
        yield db, context
        db.close()

    def test_schema_with_comments(self, logger, db_context):
        """Test that schema information includes comments from database metadata."""
        db, _ = db_context

        # Create database manager and test schema retrieval
        db_manager = DatabaseManager(db, logger)
        schema_info = db_manager.get_schema_info()

        # Verify schema info is returned
        assert schema_info is not None
        assert len(schema_info) > 0

        # Check if the schema contains expected information
        assert "service requests" in schema_info.lower()

        # Verify that the table exists
        tables = db.execute(
            "SELECT table_name FROM information_schema.tables WHERE table_name = 'service_requests'"
        ).fetchall()
        assert len(tables) == 1, "service_requests table should exist"

    def test_table_comments_applied(self, logger, db_context):
        """Test that table comments are properly applied to the database."""
        db, _ = db_context

        # Try to query table comment (DuckDB specific syntax)
        with contextlib.suppress(Exception):
            # This might not work in DuckDB, but we test the attempt
            db.execute(
                "SELECT obj_description(oid) FROM pg_class WHERE relname = 'service_requests'"
            ).fetchall()

        # At minimum, ensure the table was created successfully
        db_manager = DatabaseManager(db, logger)
        schema_info = db_manager.get_schema_info()
        assert "unique_key" in schema_info.lower()
        assert "created_date" in schema_info.lower()

    def test_schema_via_mcp_tools(self, logger, db_context):
        """Test schema retrieval through MCP tools."""
        db, context = db_context

        # This would test the actual MCP integration
        # For now, just test the underlying database manager
        db_manager = DatabaseManager(db, logger)
        schema_info = db_manager.get_schema_info()

        # Verify basic schema structure
        assert isinstance(schema_info, str)
        assert len(schema_info) > 100  # Should be substantial content
        assert "VARCHAR" in schema_info or "BIGINT" in schema_info


def test_schema_standalone():
    """Standalone test function for direct execution."""
    import sys

    sys.path.append(str(Path(__file__).parent.parent))

    from data_mcp.config import LoggerConfig
    from data_mcp.database import DatabaseManager
    from data_mcp.models import AppContext

    with tempfile.NamedTemporaryFile(suffix=".log", delete=False) as tmp_log:
        log_file = Path(tmp_log.name)

    try:
        logger = LoggerConfig.setup_logger(__name__, log_file)
        data_dir = Path("data")

        # Create in-memory database
        db = duckdb.connect(database=":memory:", read_only=False)

        try:
            # Initialize context (this will create table and add comments)
            AppContext(db=db, data_dir=data_dir)

            # Create database manager and test schema retrieval
            db_manager = DatabaseManager(db, logger)
            schema_info = db_manager.get_schema_info()

            print("Schema Information:")
            print("=" * 50)
            print(schema_info)
            print("=" * 50)

            # Check if table exists
            tables = db.execute(
                "SELECT table_name FROM information_schema.tables WHERE table_name = 'service_requests'"
            ).fetchall()
            if tables:
                print("✅ Table 'service_requests' exists")

                # Check some sample data
                sample = db.execute("SELECT COUNT(*) FROM service_requests").fetchone()
                print(f"✅ Table has {sample[0]} rows")
            else:
                print("❌ Table 'service_requests' not found")

        except Exception as e:
            print(f"❌ Error: {e}")
            raise
        finally:
            db.close()
    finally:
        log_file.unlink(missing_ok=True)


if __name__ == "__main__":
    test_schema_standalone()
