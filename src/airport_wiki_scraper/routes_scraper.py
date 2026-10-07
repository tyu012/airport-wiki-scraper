import mwparserfromhell as mwp
import dateutil.parser as dparser
import datetime as dt
from more_itertools import peekable
import requests
from airport_wiki_scraper.airroute import AirRoute
from airport_wiki_scraper.scraper import fetch_and_parse
import re


def get_apdl(page: mwp.wikicode.Wikicode) -> tuple[mwp.nodes.Template | None, mwp.nodes.Template | None]:
    """
    Returns a tuple containing the airport destination lists of the given Wikipedia article.
    - The first return element is the passenger list, otherwise None if the article only contains a
    cargo list.
    - The second return element is the cargo list if exists, otherwise None if the article only
    contains a passenger list.
    - Assume that the article contains at least one airport destination list.

    NOTE: Cargo information on Wikipedia is generally incomplete compared to passenger information.
    Therefore, the project is currently scoped towards scheduled passenger flights.
    """

    # Detect relevant headings and templates.
    regex = r"(Airlines and Destinations|Passenger|Cargo|{{Airport destination list|{{Airport-dest-list)"
    filtered_items = page.filter(recursive=False, matches=regex, flags=re.IGNORECASE)

    passenger_list = None
    cargo_list = None

    # Use headings to detect whether airport destination list is cargo.
    cargo = False
    for node in filtered_items:
        if type(node) == mwp.nodes.Heading:
            cargo = True if node.strip("=").lower() == "cargo" else False
        if type(node) == mwp.nodes.Template:
            if cargo and cargo != None:
                cargo_list = node
            else:
                passenger_list = node

    return passenger_list, cargo_list
    


def filter_apdl_dests(column: mwp.nodes.extras.Parameter) -> list[mwp.nodes.Node]:
    """
    Returns an ordered list of mwp nodes given a template parameter representative of an airport
    destination list column containing destinations for a particular airline.

    The data returned is as follows:
    - wikilinks for each destination
    - route begin dates, if applicable
    - route end dates, if applicable
    - route suspended info, if applicable
    - seasonal, charter, and seasonal charter headings
    """
    regex = r"(?i)\[\[|seasonal|charter|begins?|ends?|resumes?|suspended|\{\{date"
    dest_info = column.value.filter(recursive=False, matches=regex)
    # This may lead to <ref> tags being included. Need to remove them manually.
    return list(filter(lambda node: type(node) != mwp.nodes.tag.Tag or node.tag != "ref", dest_info))


def interpret_dests(
    filtered_dests: list[mwp.nodes.Node],
    origin: str="",
    airline: str=""
) -> list[AirRoute]:
    """
    Read an ordered list of mwp nodes returned by filter_apdl_dests and convert to a list of dicts.
    Specifically, reads a wikilink to add a new route, and then reads non-wikilink nodes afterwards to
    add information about begin/resume/end date, whether the route is seasonal and/or charter, and
    whether it is suspended (or all suspended).

    In practice, interpret_dests is for one airline at a time.

    TODO: Store destinations using a more stable identifier rather than wiki links.
    """
    structured_dests: list[AirRoute] = []
    seasonal = False
    charter = False
    iterator = peekable(filtered_dests.__iter__())
    for node in iterator:
        lowertext = node.lower()
        apply_all = "all" in lowertext or "both" in lowertext
        if type(node) == mwp.nodes.Wikilink:
            structured_dests.append(AirRoute(
                origin=origin,
                destination=str(node.title),
                airline=airline,
                seasonal=seasonal,
                charter=charter
            ))
        elif "seasonal charter" in lowertext:
            seasonal = True
            charter = True
        elif "seasonal" in lowertext:
            seasonal = True
            charter = False
        elif "charter" in lowertext:
            seasonal = False
            charter = True
        elif "suspended" in lowertext:
            # Suspended flights may include a date. Try to parse a date.
            _apply_air_route_prop(
                structured_dests,
                "suspended",
                True,
                apply_all)
            _apply_air_route_prop(
                structured_dests,
                "resumes",
                parse_date(lowertext, iterator),
                apply_all
            )

        elif "begin" in lowertext:
            _apply_air_route_prop(
                structured_dests,
                "begins",
                parse_date(lowertext, iterator),
                apply_all)

        elif "resume" in lowertext:
            _apply_air_route_prop(
                structured_dests,
                "resumes",
                parse_date(lowertext, iterator),
                apply_all)

        elif "end" in lowertext:
            _apply_air_route_prop(
                structured_dests,
                "ends",
                parse_date(lowertext, iterator),
                apply_all)
    return structured_dests


def _apply_air_route_prop(values: list[AirRoute], prop: str, value, apply_all: bool=False):
    """
    Applies values to properties in a list of AirRoute objects.

    `prop` is the name of the field to access.
    `value` is the value to set.
    `apply_all` determines whether the property should be applied to all list elements.
    """
    if apply_all:
        for elem in values:
            setattr(elem, prop, value)
    else:
        setattr(values[-1], prop, value)



def parse_date(
    current_node_text: str,
    filtered_dests: peekable[mwp.nodes.Node]
) -> dt.datetime | None:
    """
    Parses dates in a peekable iterator of wikitext nodes given in the order of filter_apdl_lists.

    This function handles edge cases for date representation on Wikipedia.

    Sometimes, the date is written in plain-text, where the date and significance of the date (begins,
    resumes, ends, etc.) are grouped into one node through filter_apdl_lists. However, other times,
    dates are represented in a template, making the same information represented in two nodes. This
    requires peeking to attempt to find and parse the date in the next node; if successful, the iterator
    advances to the next element.
    """
    date = None
    try:
        processed_text = process_date_str(current_node_text)
        date = dparser.parse(processed_text, fuzzy=True)
    except:
        try:
            date = dparser.parse(filtered_dests.peek().lower(), fuzzy=True)
            filtered_dests.__next__()
        except:
            print(f"Unable to find expected date for \"{filtered_dests.peek()}\". Note: Suspended flights may not have resume date.")
    return date


def process_date_str(date_str: str) -> str:
    """
    Attempts to remove extraneous text from the ends of a string containing a date, in the format of
    (begins January 1, 2026), (ends ...), (resumes ...), etc.

    This attempts to improve dparser fuzzy parsing accuracy.
    """
    regex_start = r"^\(?"
    regex_words = r"\b(all|flights?|until|temporary|temporarily|suspended|beginning|ending|resuming|starting|begins?|ends?|resumes?|starts?)\b"
    regex_end = r"\s*\)?\s*,?$"
    processed_date_str = re.sub(regex_start, "", date_str.strip(), flags=re.IGNORECASE)
    processed_date_str = re.sub(regex_end, "", processed_date_str, flags=re.IGNORECASE)
    processed_date_str = re.sub(regex_words, "", processed_date_str, flags=re.IGNORECASE)
    return processed_date_str.strip()


def extract_apdl(apdl: mwp.nodes.Template, origin: str = "") -> list[AirRoute]:
    """
    Extracts airline and destination data from the airport destination list template.
    Assumes list is formatted in accordance to Template:Airport Destination List

    Returns a list of AirRoute objects 
    """
    # Columns defaults to 2
    cols = 2
    counter = 0

    # State saved between iterations
    airline: str = ""
    air_routes = []

    named_params = [param for param in apdl.params if param.showkey]
    unnamed_params = [param for param in apdl.params if not param.showkey]

    for param in named_params:
        stripped_param_name = param.name.strip()
        print(stripped_param_name)
        # Check if 3rd or 4th columns are present
        if stripped_param_name == "3rdcoltitle" and cols < 3:
            cols = 3
        elif stripped_param_name == "4thcoltitle" and cols < 4:
            cols = 4
        elif stripped_param_name == "3rdcolunsortable" or stripped_param_name == "4thcolunsortable":
            # No action needed, since 3rdcoltitle and 4thcoltitle indicate column count
            pass

    for param in unnamed_params:
        # Parameter is either an airline or destination, determined by column position
        col_number = counter % cols
        if col_number == 0:
            # First column contains single airline wikilink
            airline = str(param.value.filter_wikilinks()[0].title)
            print("Airline: " + airline)
        if col_number == 1:
            filtered_items = filter_apdl_dests(param)
            airline_routes = interpret_dests(filtered_items, origin=origin, airline=airline)
            air_routes.extend(airline_routes)
            print("Collecting air routes")
        counter += 1
    return air_routes