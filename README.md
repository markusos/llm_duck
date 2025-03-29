# LLM Duck

This is a small sample setup to showcase how to use DuckDB with LM Studio to prompt LLMs wihth SQL. 

This is similar to the MotherDuck `prompt` method that is currently in preview: https://motherduck.com/docs/sql-reference/motherduck-sql-reference/ai-functions/prompt/

# Requirements

- DuckDB (https://duckdb.org/)
- LM Studio (https://lmstudio.ai/)
- uv (https://docs.astral.sh/uv/)

# Usage

1. Install DuckDB, uv and LM Studio.
2. Start LM Studio and load the model you want to use. 
    - The current model used in the code is `gemma-3-27b-it` model.
    - Start the development server, see: https://lmstudio.ai/docs/app/api
3. Clone this repository and navigate to the directory:
4. Install the required packages:
```bash
uv sync --dev
```
5. Run the script with the following command:
```bash
uv run llm_duck.py
```

The sample setup uses the LLM model to augment the data with a Country column by letting the LLM model guess the country based on the station name.

Example output:
```
Executing query...
[('Netherlands', 'AMF', 'Amersfoort Centraal'), ('Netherlands', 'ASD', 'Amsterdam Centraal'), ('Netherlands', 'GERP', 'Groningen Europapark'), ('Netherlands', 'WP', 'Weesp'), ('Netherlands', 'BDG', 'Bodegraven'), ('Netherlands', 'NA', 'Nieuw Amsterdam'), ('Netherlands', 'BRN', 'Baarn'), ('Netherlands', 'NWK', 'Nieuwerkerk a/d IJssel'), ('Netherlands', 'DTCP', 'Delft Campus'), ('Germany', 'EUN', 'Unna')]
```