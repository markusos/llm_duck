import json

import duckdb
import requests
from jinja2 import Template

MODEL = "gemma-3-27b-it"
MODEL_TEMP = 0.7
MODEL_MAX_TOKENS = -1


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
        raise RuntimeError(f"API request failed: {str(e)}") from e


# Connect to DuckDB
con = duckdb.connect(database=":memory:", read_only=False)

# Register the Python function as a scalar UDF
con.create_function(
    "prompt",
    prompt,
    [str, str],  # Input argument types
    str,  # Return type
)

parquet_file = "./data/service_requests.parquet"

system_prompt = (
    "You are a government auditor. You are reviewing data from New Yorks 311 system.\n"
    "Based of a given service requests resolution description you are to determine if a reasonable action was taken to resolve the issue.\n"
    "Respond ONLY with json in this format: ```json\n"
    '{"reasoning": "STRING" "action_taken": "BOOLEAN"}\n'
    "```"
)

# Define the SQL query template
query_template = """
COPY (
    WITH llm_reasoning AS (
        SELECT
            regexp_replace(
                prompt(
                    '{{ system_prompt }}',
                    'RESOLUTION_DESCRIPTION: ' || resolution_description
                ),
                '```json|```',
                '',
                'g'
            )::VARCHAR AS llm_response,
            json_extract_string(llm_response, '$.reasoning')::VARCHAR AS reasoning,
            json_extract_string(llm_response, '$.action_taken')::VARCHAR AS action_taken,
            resolution_description,
            description_count
        FROM (
            SELECT resolution_description, count(*) as description_count
            FROM "{{ data_file }}"
            GROUP BY resolution_description
            ORDER BY description_count DESC
            LIMIT {{ limit }}
        )
    )

    SELECT
        resolution_description,
        description_count,
        reasoning,
        action_taken
    FROM llm_reasoning
) TO './output/llm_reasoning_output.csv';
"""

# # Render the template with variables
template = Template(query_template)
query = template.render(system_prompt=system_prompt, data_file=parquet_file, limit=10)

# # Execute the query
print("Executing query...")
print(query)

result = con.execute(query).fetchall()
print(result)
