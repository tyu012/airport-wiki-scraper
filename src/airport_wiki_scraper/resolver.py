from airport_wiki_scraper.airport_scraper import parse_airport_infobox
from airport_wiki_scraper.airport_scraper import Airport
from urllib.parse import unquote
import os
import json


def resolve_airport_data(
    titles_path: str | os.PathLike[str],
    wd_path: str | os.PathLike[str],
    articles_path: str | os.PathLike[str] | None=None,
    verbose: bool=False
) -> list[Airport]:
    """
    Attempts to resolve data for each airport on `titles_path` (a txt file with each airport
    on its separate line) using the following files:

    - `wd_path`: a .jsonl file serialized from data fetched from Wikidata with the function
    `scraper.fetch_wd_airport_info`
    - TODO: `articles_path`: optionally, the .jsonl file serialized from
    `scraper.queue_fetch_articles`
    """
    # Load Wikidata data into a Wikipedia title-indexed dict for faster retrieval
    wd_dict = _load_wd_airports_jsonl(wd_path)

    airports_resolved = []

    # Read each airport in the file at titles_path and attempt to resolve:
    with open(titles_path, "r") as titles:
        for title in titles:
            stripped_title = title.strip()
            try:
                wd_airport = wd_dict[stripped_title]

                wd_qid: str = wd_airport["item"]["value"].removeprefix("http://www.wikidata.org/entity/")

                wd_icao = wd_airport.get("icao", None)
                wd_icao_val: str | None = wd_icao["value"] if wd_icao else None

                wd_iata = wd_airport.get("iata", None)
                wd_iata_val: str | None = wd_iata["value"] if wd_iata else None

                wd_coords = wd_airport.get("coords", None)
                wd_coords_tuple: tuple[float, float] | None = None
                if wd_coords:
                    wd_coords_val: str = wd_coords["value"]
                    wd_coords_split = wd_coords_val.removeprefix("Point(").removesuffix(")").split(" ")
                    if type(wd_coords_split) == list and len(wd_coords_split) >= 2:
                        # Wikidata gives the coordinates longitude-first
                        wd_coords_tuple = (
                            float(wd_coords_split[1]),
                            float(wd_coords_split[0])
                        )

                airports_resolved.append(Airport(
                    qid=wd_qid,
                    icao=wd_icao_val,
                    wiki_title=stripped_title,
                    iata=wd_iata_val,
                    coordinates=wd_coords_tuple
                ))
                if verbose:
                    print(f"Resolved data for {stripped_title}")

            except Exception as e:
                # raise(e)
                print(f"Warning: Unable to find Wikidata info for article {stripped_title}. Skipping article.")
                if verbose:
                    print(type(e), e)

    return airports_resolved




def _load_wd_airports_jsonl(path: str | os.PathLike[str]) -> dict[str, dict]:
    """
    Loads each line of wd_airports.jsonl, serialized from `scraper.fetch_wd_airport_info`, into a
    dict with the name of the Wikipedia article title as the key and the line, deserialized as a
    dict, as the value.
    """
    wd_airports_dict = {}
    with open(path, "r") as wd_airports_jsonl:
        for line in wd_airports_jsonl:
            stripped_line = line.strip()
            line_as_dict = json.loads(stripped_line)
            url: str = line_as_dict["article"]["value"]
            title = unquote(url.removeprefix("https://en.wikipedia.org/wiki/")).replace("_", " ")
            wd_airports_dict[title] = line_as_dict
    return wd_airports_dict