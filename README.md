# AirWikiExplorer

A Python-based Wikipedia scraper that parses "Airports and Destinations" tables (more precisely, `Airport destination list` templates).

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