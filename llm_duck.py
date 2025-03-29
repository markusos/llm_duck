import duckdb
import requests
import json
import os

MODEL = "gemma-3-27b-it"
MODEL_TEMP = 0.7
MODEL_MAX_TOKENS = -1

# Check if trains.parquet exists, if not, download it
if not os.path.exists("trains.parquet"):
    print("trains.parquet not found. Downloading...")
    url = "http://blobs.duckdb.org/train_services.parquet"
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        with open("trains.parquet", "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print("Download complete.")
    except requests.exceptions.RequestException as e:
        print(f"Failed to download trains.parquet: {e}")
        exit(1)


# Define the UDF
def prompt(system_message, user_message):
    """
    Calls the local LLM API and returns the response.
    """
    url = "http://localhost:1234/v1/chat/completions"
    headers = {"Content-Type": "application/json"}
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_message},
        ],
        "temperature": MODEL_TEMP,
        "max_tokens": MODEL_MAX_TOKENS,
        "stream": False,
    }

    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        response.raise_for_status()  # Raise an error for HTTP codes 4xx/5xx
        return (
            response.json()
            .get("choices", [{}])[0]
            .get("message", {})
            .get("content", "No response")
        )
    except requests.exceptions.RequestException as e:
        # Raise an exception to ensure the query fails
        raise RuntimeError(f"API request failed: {str(e)}")


# Connect to DuckDB
con = duckdb.connect(database=":memory:", read_only=False)

# Register the Python function as a scalar UDF
con.create_function(
    "prompt",
    prompt,
    [str, str],  # Input argument types
    str,  # Return type
)

system_prompt = (
    "You are an expert on the worlds train network that can guess the country of a train station.\n"
    "Which country is the provided train station likely located in based of its station name and code.\n"
    "Respond ONLY with json in this format: ```json\n"
    '{"country": "country_name"}\n'
    "```"
)

# Example usage in DuckDB
query = f"""
SELECT 
    json_extract_string(
        regexp_replace(
            prompt(
                '{system_prompt}',
                'STATION NAME: ' || station_name || ', STATION CODE: ' || station_code
            ), 
            '```json|```', 
            '', 
            'g'
        ), 
        '$.country'
    )::VARCHAR AS country_guess,
    station_code,
    station_name
FROM (
    SELECT DISTINCT station_code, station_name 
    FROM "./trains.parquet" 
    LIMIT 10
)
"""

# Execute the query
print("Executing query...")
print(query)

result = con.execute(query).fetchall()
print(result)
