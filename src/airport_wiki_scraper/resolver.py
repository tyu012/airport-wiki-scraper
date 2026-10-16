from airport_wiki_scraper.airport_scraper import parse_airport_infobox
from airport_wiki_scraper.airport import Airport
from airport_wiki_scraper.airroute import AirRoute, AirRouteID
from airport_wiki_scraper.utils import load_pydantic_jsonl, normalize_wiki_url
from urllib.parse import unquote
import os
import json
import re


def extract_airport_data(
    wd_path: str | os.PathLike[str],
    verbose: bool=False
) -> list[Airport]:
    """
    Extracts Wikidata airport data fetched from `scraper.fetch_wd_airport_info` and returns a list.

    - `wd_path`: a .jsonl file serialized from data fetched from Wikidata with the function
    `scraper.fetch_wd_airport_info`
    """

    airports_resolved = []

    # Read each airport in the file at titles_path and attempt to resolve:
    with open(wd_path, "r") as wd_airports:
        for airport_json in wd_airports:
            wd_airport = json.loads(airport_json)

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

            url: str = wd_airport["article"]["value"]
            title = normalize_wiki_url(url)

            airports_resolved.append(Airport(
                qid=wd_qid,
                icao=wd_icao_val,
                wiki_title=title,
                iata=wd_iata_val,
                coordinates=wd_coords_tuple
            ))
            if verbose:
                print(f"Resolved data for {title}")


    return airports_resolved




def check_wd_completeness(
    wd_path: str | os.PathLike[str],
    apdl_titles_path: str | os.PathLike[str]
) -> list[str]:
    """
    Return a list of titles of Wikipedia articles with airport destination lists for which
    corresponding Wikidata entries are not found
    """
    # Load Wikidata data into a Wikipedia title-indexed dict for faster retrieval
    wd_dict = _load_wd_airports_jsonl(wd_path)
    wd_not_found = []

    with open(apdl_titles_path) as titles:
        for title in titles:
            title_stripped = title.strip()
            try:
                wd_dict[title_stripped]
            except:
                wd_not_found.append(title_stripped)

    return wd_not_found





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




def resolve_routes(
    routes_path: str | os.PathLike[str],
    airports_path: str | os.PathLike[str],
    redirects_path: str | os.PathLike[str],
    verbose: bool=False
) -> list[AirRouteID]:
    """
    Resolves Wikidata QIDs for AirRoute objects deserialized from a .jsonl file specified by
    `routes_path`, given Airport objects (also from .jsonl) at `airports_path`, using
    a redirects table (from .jsonl, each object has a "from" and "to" field) at `redirects_path`.
    """
    redirects_table = _load_redirects_jsonl(redirects_path)
    airports: list[Airport] = load_pydantic_jsonl(airports_path, Airport)
    airroutes: list[AirRoute] = load_pydantic_jsonl(routes_path, AirRoute)

    # Load airports into a dict for faster lookup
    airports_dict = _airports_to_dict(airports)

    resolved_air_routes: list[AirRouteID] = []

    # Resolve each air route
    for route in airroutes:
        origin_title = route.origin

        # Resolve the canonical destination redirect title, if applicable

        destination_title = route.destination
        # Normalize destination title - replace underscore with space, remove multiple spaces,
        # capitalize first letter
        destination_title = re.sub(r"\_", " ", destination_title)
        destination_title = re.sub(r" +", " ", destination_title)
        destination_title = destination_title[:1].upper() + destination_title[1:]

        destination_title = redirects_table.get(destination_title, destination_title)

        # Resolve Wikidata QIDs
        try:
            origin_qid = airports_dict[origin_title].qid
            destination_qid = airports_dict[destination_title].qid

            resolved_air_routes.append(AirRouteID.model_validate({
                **route.model_dump(),
                "origin_qid": origin_qid,
                "destination_qid": destination_qid
            }))
        except:
            print(f"Warning: unable to get QIDs for route {origin_title} -> {destination_title}. Skipping.")

    return resolved_air_routes




def _load_redirects_jsonl(path: str | os.PathLike[str]) -> dict[str, str]:
    """
    Load a .jsonl file representing Wikipedia redirects; each object has a "from" and "to" field.
    Returns a dict with each "from" field as a key and corresponding "to" field as its value.
    """
    redirects_table = {}
    with open(path, "r") as redirects_jsonl:
        for line in redirects_jsonl:
            stripped_line = line.strip()
            line_as_dict = json.loads(stripped_line)
            redirects_table[line_as_dict["from"]] = line_as_dict["to"]
    return redirects_table



def _airports_to_dict(airports: list[Airport]) -> dict[str, Airport]:
    """
    Load a list of Airport objects into a dict, with the Wikipedia title of the airport as keys
    and the corresponding Airport object as the its value.
    """
    airports_dict = {}
    for airport in airports:
        airports_dict[airport.wiki_title] = airport
    return airports_dict