import mwparserfromhell as mwp
import dateutil.parser as dparser
import datetime as dt
from more_itertools import peekable
import requests
from airroute import AirRoute

API_URL = "https://en.wikipedia.org/w/api.php"

# Credit: https://mwparserfromhell.readthedocs.io/en/latest/usage.html
def fetch(title: str):
    params = {
            "action": "query",
            "prop": "revisions",
            "rvprop": "content",
            "rvslots": "main",
            "rvlimit": 1,
            "titles": title,
            "format": "json",
            "formatversion": "2",
        }
    headers = {
        "User-Agent": "AirWikiExplorer/0.1 (https://github.com/tyu012; yuyu.tim@gmail.com)"
    }
    req = requests.get(API_URL, headers=headers, params=params)
    res = req.json()
    revision = res["query"]["pages"][0]["revisions"][0]
    text = revision["slots"]["main"]["content"]
    return text


def parse(title: str):
    text = fetch(title)
    return mwp.parse(text)


def get_apdl(title: str) -> tuple[mwp.nodes.Template, mwp.nodes.Template | None]:
    """
    Returns a tuple containing the airport destination lists of the titled Wikipedia article.
    The first element is the passenger list.
    The second element is the cargo list if exists, otherwise None.
    Assume that the article contains at least one airport destination list.
    """
    page = parse(title)
    regex = r"Airport destination list|Airport-dest-list" # includes all redirects
    destination_lists = page.filter_templates(matches=regex)
    """
    According to WP:AIRPORTSG,
    Cargo airlines may be included after Airlines and destinations but are not necessary. 
    Therefore, assume the first 'Airport destination list' is for passenger and the second is
    for cargo.
    """
    passenger = destination_lists[0]
    cargo = destination_lists[1] if len(destination_lists) > 1 else None
    return passenger, cargo


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
            resume_date = parse_date(lowertext, iterator)

            if "all" in lowertext:
                # Handle "all suspended" at end - apply to all 
                for route in structured_dests:
                    route.suspended = True
                    route.resumes = resume_date
            else:
                structured_dests[-1].suspended = True
                structured_dests[-1].resumes = resume_date
        elif "begins" in lowertext:
            structured_dests[-1].begins = parse_date(lowertext, iterator)
        elif "resumes" in lowertext:
            structured_dests[-1].resumes = parse_date(lowertext, iterator)
        elif "ends" in lowertext:
            structured_dests[-1].ends = parse_date(lowertext, iterator)
    return structured_dests


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
        date = dparser.parse(current_node_text, fuzzy=True)
    except:
        try:
            date = dparser.parse(filtered_dests.peek().lower(), fuzzy=True)
            filtered_dests.__next__()
        except:
            print("Unable to find expected date")
    return date


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

    for param in apdl.params:
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
        else:
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