import argparse
import os
from dotenv import load_dotenv
import sys
from airport_wiki_scraper.load import load_to_db


def main():
    load_dotenv()

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

    if args.fetch:
        print("Fetching data from APIs...")
        print("Not implemented in main.py, please use notebooks/demo.ipynb instead")
    if args.resolve:
        print("Resolving fetched data...")
        print("Not implemented in main.py, please use notebooks/demo.ipynb instead")
    if args.load:
        print("Loading to database...")
        load_to_db()


if __name__ == "__main__":
    main()