# This file contains the UDF for calling the local LLM API.
# Register the Python function as a scalar UDF
# con.create_function("prompt", prompt, [str, str, str, float], str)

import json

import requests

MODEL = "gemma-3-27b-it"
MODEL_TEMP = 0.4
MODEL_MAX_TOKENS = -1


# Define the UDF
def prompt(
    prompt_text: str,
    system_message: str | None = None,
    json_schema: str | None = None,
    temperature: float | None = None,
) -> str:
    """
    Calls the local LLM API and returns the response.
    """
    url = "http://localhost:1234/v1/chat/completions"
    headers = {"Content-Type": "application/json"}
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "user", "content": prompt_text},
        ],
        "temperature": MODEL_TEMP,
        "max_tokens": MODEL_MAX_TOKENS,
        "stream": False,
    }

    # Set system message if provided
    if system_message is not None:
        payload["messages"].insert(0, {"role": "system", "content": system_message})

    # Set temperature if provided
    if temperature is not None:
        payload["temperature"] = temperature

    if json_schema:
        payload["response_format"] = {
            "type": "json_schema",
            "json_schema": json.loads(json_schema),
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
    except Exception as e:
        # Handle any other exceptions
        raise RuntimeError(f"An error occurred: {str(e)}") from e
