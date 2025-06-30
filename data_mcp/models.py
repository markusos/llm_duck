"""
Data models and context classes for the NYC 311 Data MCP Server.
"""

import contextlib
from dataclasses import dataclass
from pathlib import Path

import duckdb

from .exceptions import DatabaseError


@dataclass
class AppContext:
    """Application context containing shared resources."""

    db: duckdb.DuckDBPyConnection
    data_dir: Path

    def __post_init__(self) -> None:
        """Initialize database tables after context creation."""
        self._initialize_tables()

    def _initialize_tables(self) -> None:
        """Pre-load data tables and add metadata comments."""
        try:
            service_requests_file = (
                self.data_dir / "cityofnewyork/service_requests_2024.parquet"
            )
            if service_requests_file.exists():
                # Create the table from parquet file
                self.db.execute(f"""
                    CREATE TABLE IF NOT EXISTS service_requests AS
                    SELECT * FROM '{service_requests_file}';
                """)

                # Add table comment
                self.db.execute("""
                    COMMENT ON TABLE service_requests IS 'NYC 311 Service Requests data for 2024 containing complaint information, locations, agencies, and resolution details';
                """)

                # Add column comments
                column_comments = {
                    "unique_key": "Unique identifier for each service request",
                    "created_date": "Date/time the request was created",
                    "closed_date": "Date/time the request was closed",
                    "agency": "The agency responsible for the request",
                    "agency_name": "Full name of the responsible agency",
                    "complaint_type": "Type of complaint/request",
                    "descriptor": "Detailed description of the issue",
                    "location_type": "Type of location where issue occurred",
                    "incident_zip": "ZIP code of the incident",
                    "incident_address": "Street address of the incident",
                    "street_name": "Name of the street",
                    "cross_street_1": "First cross street",
                    "cross_street_2": "Second cross street",
                    "intersection_street_1": "First intersection street",
                    "intersection_street_2": "Second intersection street",
                    "address_type": "Type of address",
                    "city": "City name",
                    "landmark": "Nearby landmark",
                    "facility_type": "Type of facility",
                    "status": "Current status of the request",
                    "due_date": "Due date for resolution",
                    "resolution_description": "Description of resolution",
                    "resolution_action_updated_date": "Date resolution was updated",
                    "community_board": "Community board identifier",
                    "bbl": "Borough, Block, and Lot number",
                    "borough": "NYC borough name",
                    "x_coordinate_state_plane": "X coordinate (State Plane)",
                    "y_coordinate_state_plane": "Y coordinate (State Plane)",
                    "open_data_channel_type": "Channel used to submit request",
                    "park_facility_name": "Name of park facility",
                    "park_borough": "Borough of the park",
                    "vehicle_type": "Type of vehicle involved",
                    "taxi_company_borough": "Borough of taxi company",
                    "taxi_pick_up_location": "Taxi pickup location",
                    "bridge_highway_name": "Name of bridge or highway",
                    "bridge_highway_direction": "Direction on bridge/highway",
                    "road_ramp": "Road ramp information",
                    "bridge_highway_segment": "Bridge/highway segment",
                    "latitude": "Latitude coordinate",
                    "longitude": "Longitude coordinate",
                    "location": "Combined location information",
                }

                # Add comments to existing columns
                for column_name, comment in column_comments.items():
                    with contextlib.suppress(Exception):
                        # Skip if column doesn't exist in this dataset
                        self.db.execute(f"""
                            COMMENT ON COLUMN service_requests.{column_name} IS '{comment}';
                        """)

        except Exception as e:
            raise DatabaseError(f"Failed to initialize tables: {e}") from e
