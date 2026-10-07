# AirWikiExplorer

A Python-based Wikipedia scraper that parses "Airports and Destinations" tables (more precisely, `Airport destination list` templates).

# How to use

## Pre-generated data

The following pre-generated data is available in this repo:
- `data/structured/airroutes.jsonl` - All passenger air routes parsed from Wikipedia airport pages. Airport and airline names are directly retrieved from links.
- `data/wikitext/airport_articles.jsonl` - All Wikipedia articles (title and wikitext content) containing `Airport destination list` templates.
- `data/airports.txt` - List of all Wikipedia articles containing `Airport destination list` templates.

## Obtain data yourself

While pre-generated data is available, you can also run the pipeline to obtain data yourself.
Below are the steps:

- Install dependencies
```
uv sync
```

- Create a `.env` file in the root directory of this repo and add the following line.
  - **IMPORTANT:** Replace **EMAIL** with your own email.
```
MW_USER_AGENT="AirWikiExplorer/0.1 (EMAIL)"
```

- Run the cells of the Jupyter notebook `notebooks/demo.ipynb`

# Tech stack

- Python
- mwparserfromhell

## Why this architecture

Scraping and parsing wikitext instead of HTML (see [Related Works](#related-works)) is more robust and less prone to changes while making template metadata easier to access.
Using Python enables rapid prototyping via Jupyter Notebooks and potential integration with data analysis libraries.

# Related Works

- Raphael Cockx, [Wikipedia Airport Scraper](https://github.com/raphaelcockx/wikipedia-airport-scraper)
  - Scrapes similar data, but parses HTML instead of wikitext
- Cristóbal Gómez, [Aviation Scraper](https://github.com/cristobal-io/aviation-scraper)
  - Also parses HTML