# LLM Duck

This is a set of experiments around data analysis and augmentation using LLMs, DuckDB and other Python libraries.

### llm_duck.py

This sample implementds a SQL UDF that is similar to the MotherDuck `prompt` method that is currently in preview: https://motherduck.com/docs/sql-reference/motherduck-sql-reference/ai-functions/prompt/

### geo.py

Using pandas, cartopy and matplotlib to vizualize geo tagged service call events from the NYC 311 dataset.

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
5. Setup the data needed for the scripts
```bash
uv run setup.py
```
6. Run the llm sql script with the following command:
```bash
uv run llm_duck.py
```
7. Run the geo script with the following command:
```bash
uv run geo.py
```