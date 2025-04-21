# Setup datasets for the project
# This script checks if the CSV file exists, and if not, it raises an error.
import os

import duckdb

# Load the CSV file into DuckDB
service_requests_csv_file = "./data/cityofnewyork/service_requests.csv"
modzcta_csv_file = "./data/cityofnewyork/modzcta.csv"

# Transformed files used for analysis
# The CSV file is large, so we convert it to Parquet for faster access.
service_requests_parquet_file = "./data/cityofnewyork/service_requests.parquet"

# The Parquet file for 2024 data
service_requests_parquet_file_2024 = (
    "./data/cityofnewyork/service_requests_2024.parquet"
)

# Check if service_requests.csv exists, if not, raise an error.
# This file can be downloaded from the NYC Open Data portal.
# https://data.cityofnewyork.us/api/views/erm2-nwe9/rows.csv
# Note: The file is large, so it may take some time to download.
# As of 2025-03-30, the full file is 22.78 GB.
if not os.path.exists(service_requests_csv_file):
    raise FileNotFoundError(
        f"The file '{service_requests_csv_file}' does not exist. "
        "Please download it with: "
        "wget https://data.cityofnewyork.us/api/views/erm2-nwe9/rows.csv -O {service_requests_csv_file}"
    )

# Check if modzcta.csv exists, if not, raise an error.
# This file can be downloaded from the NYC Open Data portal.
# https://data.cityofnewyork.us/api/views/pri4-ifjk/rows.csv?accessType=DOWNLOAD
# Note: As of 2025-03-30, the full file is 3.1 MB.
if not os.path.exists(modzcta_csv_file):
    raise FileNotFoundError(
        f"The file '{modzcta_csv_file}' does not exist. "
        "Please download it with: "
        "wget https://data.cityofnewyork.us/api/views/pri4-ifjk/rows.csv -O {modzcta_csv_file}"
    )

# Connect to DuckDB
con = duckdb.connect(database=":memory:", read_only=False)

# Create parquet file if it doesn't exist
if not os.path.exists(service_requests_parquet_file):
    try:
        # Execute the SQL to read CSV and write to Parquet
        # Maps the CSV columns to the appropriate data types and cleans up the haders
        con.execute(f"""
            COPY (SELECT * FROM read_csv('{service_requests_csv_file}', 
                header=true,
                columns={{
                    'unique_key': 'BIGINT',
                    'created_date': 'TIMESTAMP',
                    'closed_date': 'TIMESTAMP',
                    'agency': 'VARCHAR',
                    'agency_name': 'VARCHAR',
                    'complaint_type': 'VARCHAR',
                    'descriptor': 'VARCHAR',
                    'location_type': 'VARCHAR',
                    'incident_zip': 'VARCHAR',
                    'incident_address': 'VARCHAR',
                    'street_name': 'VARCHAR',
                    'cross_street_1': 'VARCHAR',
                    'cross_street_2': 'VARCHAR',
                    'intersection_street_1': 'VARCHAR',
                    'intersection_street_2': 'VARCHAR',
                    'address_type': 'VARCHAR',
                    'city': 'VARCHAR',
                    'landmark': 'VARCHAR',
                    'facility type': 'VARCHAR',
                    'status': 'VARCHAR',
                    'due_date': 'TIMESTAMP',
                    'resolution_description': 'VARCHAR',
                    'resolution_action_updated_date': 'TIMESTAMP',
                    'community_board': 'VARCHAR',
                    'bbl': 'BIGINT',
                    'borough': 'VARCHAR',
                    'x_coordinate_state_plane': 'BIGINT',
                    'y_coordinate_state_plane': 'BIGINT',
                    'open_data_channel_type': 'VARCHAR',
                    'park_facility_name': 'VARCHAR',
                    'park_borough': 'VARCHAR',
                    'vehicle_type': 'VARCHAR',
                    'taxi_company_borough': 'VARCHAR',
                    'taxi_pick_up_location': 'VARCHAR',
                    'bridge_highway_name': 'VARCHAR',
                    'bridge_highway_direction': 'VARCHAR',
                    'road_ramp': 'VARCHAR',
                    'bridge_highway_segment': 'VARCHAR',
                    'latitude': 'DOUBLE',
                    'longitude': 'DOUBLE',
                    'location': 'VARCHAR'
                }})) 
            TO "{service_requests_parquet_file}" (FORMAT 'parquet');
        """)
        print(
            f"Exported {service_requests_csv_file} to {service_requests_parquet_file} successfully."
        )
    except Exception as e:
        raise Exception(f"Failed to export CSV to Parquet: {e}") from e


# Create parquet file for 2024 if it doesn't exist
if not os.path.exists(service_requests_parquet_file_2024):
    try:
        # Execute the SQL to read CSV and write to Parquet
        con.execute(f"""
            COPY (
                FROM "{service_requests_parquet_file}"
                WHERE created_date between '2024-01-01' and '2024-12-31'
            ) TO "{service_requests_parquet_file_2024}";
        """)
        print(
            f"Exported {service_requests_parquet_file} to {service_requests_parquet_file_2024} successfully."
        )
    except Exception as e:
        raise Exception(f"Failed to export CSV to Parquet: {e}") from e

# Close the connection
con.close()
