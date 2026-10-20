# AirWikiExplorer

A Python-based Wikipedia ETL pipeline that parses "Airports and Destinations" tables (more precisely, `Airport destination list` templates).

# Features

- Parses airport destination lists from wikitext of more than **4,500** Wikipedia articles
- Retrieves over **100,000** passenger air routes consisting of origin, destination, airline, and other attributes (seasonal, charter, suspended, start/end/resume dates)
- Resolves 99.3% of origin and destination airports of air routes to Wikidata entries.
- Loads resolved data to a PostgreSQL database
- Calls MediaWiki Action API to obtain Wikipedia articles, respecting Wikimedia Foundation rate limits
- Uses a SPARQL query to fetch airport data from Wikidata, maximizing coverage of articles with airport destination lists
- Robustly handles edge cases when parsing
- Test cases cover a range of edge cases found during the development process

# How to use

## Obtain data

- Install dependencies
```
uv sync
```

- Create a `.env` file in the root directory of this repo and add the following lines
  - **IMPORTANT:** Replace **EMAIL** with your own email.
  - Replace the database environment variables with your Postgres database information.
```
MW_USER_AGENT="AirWikiExplorer/0.3 (EMAIL)"
POSTGRES_DB=[Postgres database name]
POSTGRES_USER=[Postgres username]
POSTGRES_PASSWORD=[Postgres password]
DB_HOST=[Postgres database host]
DB_PORT=[Postgres database port]
```

- Run the cells of the Jupyter notebook `notebooks/demo.ipynb` to fetch, extract, and transform the data.

- Run `docker compose up` to start the PostgreSQL database.

- Run the script `uv run airport-wiki-scraper -l` to start the PostgreSQL database.

## Generated data locations:

The following data will be generated:

- `data/structured/airroutesid.jsonl` - All passenger air routes from `data/structured/airroutes.jsonl` where the Wikidata QID of both the route's origin and destination can be resolved.
- `data/structured/airroutes.jsonl` - All passenger air routes parsed from Wikipedia airport pages. Airport and airline names are directly retrieved from links.
- `data/structured/airport_info.jsonl` - Wikidata airport information transformed into a Pydantic model and then serialized into JSON; contains Wikidata QID, Wikipedia article title, IATA and ICAO codes (if applicable), and coordinates.
- `data/wikitext/airport_articles.jsonl` - All Wikipedia articles (title and wikitext content) containing `Airport destination list` templates.
- `data/airports.txt` - List of all Wikipedia articles containing `Airport destination list` templates.
- `data/airport_redirects.jsonl` - Titles that redirect to any article listed in `data/airports.txt`
- `data/wd_airports.jsonl` - Data about airports fetched from a Wikidata SPARQL query
- `postgres_data` - The PostgreSQL database folder.

# Tech stack

- Python
- mwparserfromhell
- Pydantic

## Why this architecture

Scraping and parsing wikitext instead of HTML (see [Related Works](#related-works)) is more robust and less prone to changes while making template metadata easier to access.
Using Python enables rapid prototyping via Jupyter Notebooks and potential integration with data analysis libraries.

## Generative AI information

Large language model (LLM) tools have been used in this project.
Agentic tools were used to debug edge cases by analyzing outputs.
Chatbots were used for researching technologies and generating usage examples of libraries I use.
The vast majority of code was written by myself, except for the ref tag stripping and table alignment detection code.
I verify, understand, and edit (when necessary) all LLM-edited or suggested code.

# Related Works

- Raphael Cockx, [Wikipedia Airport Scraper](https://github.com/raphaelcockx/wikipedia-airport-scraper)
  - Scrapes similar data, but parses HTML instead of wikitext
- Cristóbal Gómez, [Aviation Scraper](https://github.com/cristobal-io/aviation-scraper)
  - Also parses HTML
- Michael Borohovski, [Travel Hacking Toolkit](https://github.com/borski/travel-hacking-toolkit)
  - Includes an AI agent skill that reads Wikipedia airport destination lists, but rules-based parsers are more efficient at large scale.