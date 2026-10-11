import mwparserfromhell as mwp
import dateutil.parser as dparser
import datetime as dt
from more_itertools import peekable
import requests
from airport_wiki_scraper.airroute import AirRoute
from airport_wiki_scraper.scraper import fetch_and_parse
import re


def get_apdl(
    page: mwp.wikicode.Wikicode, verbose=False
) -> tuple[mwp.nodes.Template | None, mwp.nodes.Template | None]:
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

    page = mwp.parse(strip_ref_tags(str(page)))

    regex = r"(Airlines and Destinations|Passenger|Cargo|\{\{\s*Airport([ _]destination[ _]list|-dest-list))"
    filtered_items = page.filter(recursive=True, matches=regex, flags=re.IGNORECASE)

    passenger_list = None
    cargo_list = None

    # Use content of previous nodes to detect whether airport destination list is cargo.
    cargo = False
    for node in filtered_items:
        if (type(node) == mwp.nodes.template.Template and
            re.search(r"Airport([ _]+destination[ _]+list|-dest-list)",
                      node.name.strip(), flags=re.IGNORECASE)):
            if cargo:
                cargo_list = node
            else:
                passenger_list = node
        elif (type(node) == mwp.nodes.heading.Heading or
              (type(node) == mwp.nodes.tag.Tag and node.wiki_markup == "'''")):
            cargo = True if "cargo" in node.lower() else False

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
    airline: str="",
    verbose: bool=False
) -> list[AirRoute]:
    """
    Read an ordered list of mwp nodes returned by filter_apdl_dests and convert to a list of dicts.
    Specifically, reads a wikilink to add a new route, and then reads non-wikilink nodes afterwards to
    add information about begin/resume/end date, whether the route is seasonal and/or charter, and
    whether it is suspended (or all suspended).

    In practice, interpret_dests is for one airline at a time.

    Limitations:
    - Unreliably but gracefully attempts to handle destinations without wikilinks if those pass any
    filters.

    TODO: Store destinations using a more stable identifier rather than wiki links.
    """
    structured_dests: list[AirRoute] = []
    seasonal = False
    charter = False

    iterator = peekable(filtered_dests.__iter__())
    for node in iterator:
        lowertext = node.lower()
        apply_all = "all" in lowertext or "both" in lowertext

        if "<!--" in node or "{{efn" in node or "<ref>" in node or "</ref>" in node:
            # Sometimes comments and explanatory footnotes resolve to Wikilink types if wikilinks
            # are contained. They can be ignored.
            continue

        if type(node) == mwp.nodes.Wikilink:
            structured_dests.append(AirRoute(
                origin=origin,
                destination=str(node.title).strip(),
                airline=airline,
                seasonal=seasonal,
                charter=charter,
            ))
            if verbose:
                print(f"Added route: {origin} - {str(node.title)} ({airline})")

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
                apply_all)

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

        elif "ends" in lowertext or "ending" in lowertext:
            _apply_air_route_prop(
                structured_dests,
                "ends",
                parse_date(lowertext, iterator),
                apply_all)


        else:
            # Other text, assume airports without wikilink 
            # Labels like "Cropdusting: " are ignored by filter_apdl_dests - see Jarikaba Airstrip
            # Warning: is unreliable; very few airports have this edge case. Mainly used as a
            # fallback.
            dests = str(node).split(",")
            for dest in dests:
                if dest.strip() != "":
                    structured_dests.append(AirRoute(
                        origin=origin, destination=dest.strip(), airline=airline
                    ))
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
            next_node = filtered_dests.peek().lower()
            date = dparser.parse(next_node, fuzzy=True)
            filtered_dests.__next__()
        except:
            print(f"Unable to find expected date. Note: Suspended flights may not have resume date.")
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


REF_PAIRED_RE = re.compile(r"<ref\b[^>]*>.*?</ref>", re.IGNORECASE | re.DOTALL)
REF_SELF_CLOSING_RE = re.compile(r"<ref\b[^<>]*?/\s*>", re.IGNORECASE)
REF_MALFORMED_RE = re.compile(r"<ref\b[^<>]*?/\s*(?=<|$)", re.IGNORECASE)


def strip_ref_tags(text: str, origin: str = "") -> str:
    """
    Removes <ref> tags from wikitext before it is parsed as a template.

    Reference tags are irrelevant to route extraction, but when their markup is malformed (e.g. a
    missing ">" in `<ref name="x"/<ref>`), the "=" characters inside their contents can leak into
    template parameter boundaries and shift every subsequent row. Malformed fragments are reported
    as warnings since they are likely editing errors worth fixing on Wikipedia.
    """
    malformed = REF_MALFORMED_RE.findall(text)
    if malformed:
        print(f"Warning: malformed ref tag(s) for '{origin}': {malformed}")
    # Self-closing refs must be removed before paired refs, otherwise a self-closing tag such as
    # `<ref name=x/>` is mistaken for an opening tag and swallows content up to the next `</ref>`.
    text = REF_SELF_CLOSING_RE.sub("", text)
    text = REF_PAIRED_RE.sub("", text)
    text = REF_MALFORMED_RE.sub("", text)
    return text


def _could_be_airline(param: mwp.nodes.extras.Parameter) -> bool:
    """
    Heuristically determines whether a template parameter in the first column represents an airline.

    An airline cell contains at most one wikilink (possibly wrapped in a nowrap template). A cell
    containing multiple wikilinks is more likely a misplaced destination list, indicating that the
    template's columns are misaligned.

    Examples:
    ```
    [[Airline|Full Airline Name]]
    [[Airline]]
    Airline
    {{nowrap|[[Airline]]}}
    {{nowrap|Airline}}
    [[Airline A]] operated by [[Airline B]]    # non-compliant, will parse first airline
    [[Airline B]] for [[Airline A]]            # non-compliant, will parse first airline
    ```
    """
    value = param.value

    # Check for nowrap template, if so, extract content
    nowrap = value.filter_templates(matches="nowrap")
    if len(nowrap) > 0:
        value = nowrap[0].params[0].value

    # If there is zero or one wikilinks, then assume the parameter represents an airline.
    # Exception: if "operated" is in the value
    wikilinks = len(value.filter_wikilinks())
    if "operated" in value or " for " in value:
        return wikilinks <= 2
    else:
        return wikilinks <= 1


def _extract_airline(param: mwp.nodes.extras.Parameter) -> str:
    """
    Extracts an airline name from a first-column template parameter, handling nowrap templates and
    airlines given without a wikilink.
    """
    param_value = param.value
    param_nowrap = param_value.filter_templates(matches="nowrap")
    if len(param_nowrap) > 0:
        airline_wikicode = param_nowrap[0].params[0].value
    else:
        airline_wikicode = param_value

    try:
        return str(airline_wikicode.filter_wikilinks()[0].title)
    except:
        try:
            return str(airline_wikicode.filter_text()[0]).strip()
        except:
            return ""


def extract_apdl(apdl_template: mwp.nodes.Template, origin: str = "", verbose: bool=False) -> list[AirRoute]:
    """
    Extracts airline and destination data from the airport destination list template.
    Assumes list is formatted in accordance to Template:Airport Destination List

    Returns a list of AirRoute objects 
    """
    # Columns defaults to 2
    cols = 2

    # State saved between iterations
    air_routes: list[AirRoute] = []

    # Convert to string, replace newlines with spaces, and re-parse as template to avoid issues
    # with parameters stretched across lines
    apdl_str = str(apdl_template).replace("\n", " ")
    # Attempt to strip reference tags
    apdl = mwp.parse(apdl_str).filter_templates()[0]

    named_params = [param for param in apdl.params if param.showkey]
    unnamed_params = [param for param in apdl.params if not param.showkey]

    for param in named_params:
        stripped_param_name = param.name.strip()
        # print(stripped_param_name)
        # Check if 3rd or 4th columns are present; param value must be non-empty since MediaWiki
        # ignores empty params
        if stripped_param_name == "3rdcoltitle" and param.value.strip() and cols < 3:
            cols = 3
        elif stripped_param_name == "4thcoltitle" and param.value.strip() and cols < 4:
            cols = 4
        elif stripped_param_name == "3rdcolunsortable" or stripped_param_name == "4thcolunsortable":
            # No action needed, since 3rdcoltitle and 4thcoltitle indicate column count
            pass

    # Ignore stray trailing empty cells so they do not look like an incomplete row
    while (
        unnamed_params
        and len(unnamed_params) % cols != 0
        and not str(unnamed_params[-1].value).strip()
    ):
        unnamed_params.pop()

    # Process parameters in rows, so a misaligned row can be skipped as a whole
    rows = [unnamed_params[i:i + cols] for i in range(0, len(unnamed_params), cols)]
    for row in rows:
        # To account for editors missing third columns at the end, and given that the parser will
        # always divide the rows array into `cols` columns possibly except for the last few columns,
        # we only need to check if len(row) < 2.
        if len(row) < 2 or not _could_be_airline(row[0]):
            cells = [str(param.value).strip() for param in row]
            print(f"Warning: skipping misaligned row for '{origin}': {cells}")
            continue

        # First column contains the airline
        airline = _extract_airline(row[0])

        # Second column contains the destinations for that airline
        filtered_items = filter_apdl_dests(row[1])
        airline_routes = interpret_dests(filtered_items, origin=origin, airline=airline, verbose=verbose)
        for route in airline_routes:
            air_routes.append(route)

    return air_routes