from dotenv import load_dotenv

load_dotenv()

import argparse
from airport_wiki_scraper.load import load_to_db
from airport_wiki_scraper.routes_scraper import *
from airport_wiki_scraper.airport_scraper import *
from airport_wiki_scraper.airroute import AirRoute
from airport_wiki_scraper.scraper import *
from airport_wiki_scraper.resolver import extract_airport_data, resolve_routes, check_wd_completeness
from airport_wiki_scraper.utils import strip_ref_tags, write_pydantic_jsonl, normalize_wiki_url
import mwparserfromhell as mwp
import json
from pathlib import Path
from dataclasses import asdict
import sys
import psycopg
import os
import time

DATA_PATH = "data"


def main():
    if os.getenv("MW_USER_AGENT") == None:
        print("A value for the environment variable MW_USER_AGENT is required. See README.md for more info.")
        sys.exit(1)
    
    parser = argparse.ArgumentParser(
                    prog='airport_wiki_scraper',
                    description='ETL pipeline for Wikipedia airport destinations')
    parser.add_argument("-f", "--fetch", action="store_true",
                        help="Fetch data from Wikipedia and Wikidata APIs")
    parser.add_argument("-r", "--resolve", action="store_true",
                        help="Extract and resolve fetched data")
    parser.add_argument("-l", "--load", action="store_true", 
                        help="Load resolved data to database")
    args = parser.parse_args()

    print("Welcome to airport_wiki_scraper; for help please use the -h flag.")

    # Create directories if not present
    Path(f"{DATA_PATH}/structured").mkdir(parents=True, exist_ok=True)
    Path(f"{DATA_PATH}/wikitext").mkdir(parents=True, exist_ok=True)

    if args.fetch:
        print("=== Fetching data from APIs... (This could take approximately 5 minutes) ===")
        pipeline_fetch()
    if args.resolve:
        print("=== Resolving fetched data... ===")
        pipeline_resolve()
    if args.load:
        print("=== Loading to database... ===")
        load_to_db()


def pipeline_fetch():
    # Fetch titles of articles with APDLs
    time_start_titles = time.time()
    titles = fetch_apdl_article_titles()
    print(f"Fetched {len(titles)} titles of articles with airport destination lists. Took {int(time.time() - time_start_titles)} s.")

    with open(f"{DATA_PATH}/airports.txt", "w") as f:
        for title in titles:
            f.write(title + "\n")
    print(f"Saved to disk.")

    # Fetch article texts from API
    time_start_articles = time.time()
    articles = queue_fetch_articles(titles)
    print(f"Fetched {len(titles)} articles with airport destination lists. Took {int(time.time() - time_start_articles)} s.")

    with open(f"{DATA_PATH}/wikitext/airport_articles.jsonl", "w") as f:
        for article in articles:
            article_json = json.dumps(article)
            f.write(article_json + "\n")
    print(f"Saved to disk.")

    # Fetch Wikidata data about airports
    time_start_wd = time.time()
    wd_airport_info = fetch_wd_airport_info()
    print(f"Fetched data of {len(wd_airport_info)} airports from Wikidata. Took {int(time.time() - time_start_wd)} s.")

    with open(f"{DATA_PATH}/wd_airports.jsonl", "w") as f:
        for airport in wd_airport_info:
            airport_json = json.dumps(airport)
            f.write(airport_json + "\n")
    print(f"Saved to disk.")

    # Fetch redirects

    # Combine titles from Wikidata and those with APDLs on Wikipedia
    redir_articles_to_fetch = [normalize_wiki_url(airport["article"]["value"]) for airport in wd_airport_info]
    redir_articles_to_fetch.extend(titles)
    unique_redir_articles = set(redir_articles_to_fetch)

    # Fetch redirects from API
    time_start_redir = time.time()
    redirects = queue_fetch_redirects(unique_redir_articles)
    print(f"Fetched {len(redirects)} redirects. Took {int(time.time() - time_start_redir)} s.")

    # Save redirects
    with open(f"{DATA_PATH}/airport_redirects.jsonl", "w") as f:
        for redirect in redirects:
            redirect_json = json.dumps(redirect)
            f.write(redirect_json + "\n")
    print(f"Saved to disk.")


def pipeline_resolve():
    # Extract APDL data
    air_routes_count = 0
    with open(f"{DATA_PATH}/wikitext/airport_articles.jsonl", "r") as articles, open(f"{DATA_PATH}/structured/airroutes.jsonl", "w") as routes_file:
        for line in articles:
            article = json.loads(strip_ref_tags(line))
            wikitext = article["content"]
            passenger, _ = get_apdl(mwp.parse(wikitext))
            if passenger == None:
                continue
            try:
                air_routes = extract_apdl(passenger, article["title"])
                air_routes_count += len(air_routes)
                for route in air_routes:
                    routes_file.write(route.model_dump_json() + "\n")
            except Exception as e:
                raise Exception()
    print(f"Extracted {air_routes_count} air routes from article text. Saved to disk.")
    
    # Extract Wikidata airport data
    airport_data = extract_airport_data(f"{DATA_PATH}/wd_airports.jsonl")
    write_pydantic_jsonl(airport_data, f"{DATA_PATH}/structured/airport_info.jsonl")
    print(f"Extracted info for {len(airport_data)} airports Wikidata entries. Saved to disk.")

    # Check articles with airport destination lists missing Wikidata entries
    missing_data = check_wd_completeness(f"{DATA_PATH}/wd_airports.jsonl", f"{DATA_PATH}/airports.txt")
    print(f"There are {len(missing_data)} airports with airport destination lists missing Wikidata entries")

    # Resolved routes
    routes_resolved = resolve_routes(
        f"{DATA_PATH}/structured/airroutes.jsonl",
        f"{DATA_PATH}/structured/airport_info.jsonl",
        f"{DATA_PATH}/airport_redirects.jsonl"
    )
    write_pydantic_jsonl(routes_resolved, f"{DATA_PATH}/structured/airroutesid.jsonl")
    print(f"Successfully resolved {len(routes_resolved)} air routes with Wikidata entries on both ends. Saved to disk.")


if __name__ == "__main__":
    main()