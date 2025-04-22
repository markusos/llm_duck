# LLM Duck

This project explores data analysis and augmentation using LLMs, DuckDB, and other Python libraries. It demonstrates how to categorize and visualize the NYC 311 dataset using a SQL UDF and various data visualization techniques.

### llm_categorize.ipynb

This notebook implements a SQL UDF similar to MotherDuck's `prompt` method. It categorizes the NYC 311 dataset into categories and subcategories using this UDF.

### animate_event_maps.ipynb

This notebook uses pandas, cartopy, and matplotlib to visualize geo-tagged service call events from the NYC 311 dataset. Using the categorization from the previous notebook, it visualizes the events per category on a map and animates them over time.

## Data Sources

* [NYC 311 Service Requests Dataset](https://data.cityofnewyork.us/Social-Services/311-Service-Requests-from-2010-to-Present/erm2-nwe9/about_data)
* [NYC Modified Zip Code Tabulation Areas (MODZCTA)](https://data.cityofnewyork.us/api/views/pri4-ifjk/rows.csv?accessType=DOWNLOAD)


## Requirements

* DuckDB ([https://duckdb.org/](https://duckdb.org/))
* LM Studio ([https://lmstudio.ai/](https://lmstudio.ai/))
* uv ([https://docs.astral.sh/uv/](https://docs.astral.sh/uv/))

## Usage

1.  Install DuckDB, uv, and LM Studio.
2.  Start LM Studio and load the desired model.
    *   The code currently uses the `gemma-3-27b-it` model.
    *   Start the development server (see: [https://lmstudio.ai/docs/app/api](https://lmstudio.ai/docs/app/api)).
3.  Clone this repository and navigate to the directory.
4.  Install the required packages:

    ```bash
    uv sync --dev
    ```
5.  Set up the data needed for the notebooks:

    ```bash
    uv run setup.py
    ```

    This script prepares the necessary data for the notebooks to run, including downloading and preprocessing the NYC 311 dataset.
6.  Run the notebooks in a Jupyter environment (VSCode is recommended):
    *   [VSCode Jupyter Notebooks Documentation](https://code.visualstudio.com/docs/datascience/jupyter-notebooks)
    *   Run the notebooks in the following order:

        1.  `llm_categorize.ipynb`
        2.  `animate_event_maps.ipynb`
