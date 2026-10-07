from airport_wiki_scraper.routes_scraper import *
from mwparserfromhell import parse
import mwparserfromhell as mwp
from airport_wiki_scraper.airroute import AirRoute
from datetime import datetime
import dateutil.parser as dparser
import pytest

# Below examples adapted from:
# Template:Airport_destination_list
# Wikipedia:WikiProject_Aviation/Style_guide/Layout_(Airports)

# Tested using Wikipedia sandbox to ensure they are correctly rendered on Wikipedia

ORIGIN = "MyAirport"

example_a_2col = """{{Airport destination list
| [[Oceanic Airlines]] | [[Athens International Airport|Athens]],<ref>Ref 1</ref> [[Los Angeles International Airport|Los Angeles]] (begins {{date|2026-10-1}}),<ref name=LA>Ref 2</ref> [[Sydney Airport|Sydney]] (ends March 1, 2018),<ref>Ref 3</ref> [[Dulles International Airport|Washington–Dulles]]<ref name=LA/> (suspended)<br />'''Charter:''' [[Calvi – Sainte-Catherine Airport|Calvi]], [[Dublin Airport|Dublin]]<br/> {{em|Seasonal Charter:}} [[Grand Bahama International Airport|Freeport]]
| [[Puño Airlines]] | [[Miami International Airport|Miami]]<ref name=Puno>Ref 4</ref> <br/> {{em|Seasonal:}} [[Grand Bahama International Airport|Freeport]]<ref name=Puno/>
}}"""
example_a_2col_wt = parse(example_a_2col)

example_a_solutions = [
    # A regular test case
    AirRoute(ORIGIN, "Athens International Airport", "Oceanic Airlines"),

    # Case with begin date and uses date template
    AirRoute(ORIGIN, "Los Angeles International Airport", "Oceanic Airlines", begins=datetime(2026, 10, 1)),

    # Case with end date and uses date in plain text
    AirRoute(ORIGIN, "Sydney Airport", "Oceanic Airlines", ends=datetime(2018, 3, 1)),

    # Suspended flight
    AirRoute(ORIGIN, "Dulles International Airport", "Oceanic Airlines", suspended=True),

    # Charter flight
    AirRoute(ORIGIN, "Calvi – Sainte-Catherine Airport", "Oceanic Airlines", charter=True),

    # Test handling of multiple charter flights grouped together
    AirRoute(ORIGIN, "Dublin Airport", "Oceanic Airlines", charter=True),

    # Seasonal charter flight, uses italics formatting for seasonal charter label
    AirRoute(ORIGIN, "Grand Bahama International Airport", "Oceanic Airlines", seasonal=True, charter=True),

    # Test second airline, seasonal and charter flags should be reset
    AirRoute(ORIGIN, "Miami International Airport", "Puño Airlines"),

    # Seasonal flight, uses italics formatting for seasonal label
    AirRoute(ORIGIN, "Grand Bahama International Airport", "Puño Airlines", seasonal=True)
]

example_b_3col = """{{Airport destination list
|3rdcoltitle={{Abbr|Refs.|References}}|3rdcolunsortable=yes
| [[Oceanic Airlines]] | [[Athens International Airport|Athens]],<ref>Ref 1</ref> [[Los Angeles International Airport|Los Angeles]],<ref name=LA>Ref 2</ref> [[Sydney Airport|Sydney]],<ref>Ref 3</ref> [[Dulles International Airport|Washington–Dulles]]<ref name=LA/> |
| [[Puño Airlines]] | [[Miami International Airport|Miami]] <br/> {{em|Seasonal:}} [[Grand Bahama International Airport|Freeport]] | <ref>Ref 4</ref>
}}"""
example_b_3col_wt = parse(example_b_3col)

example_b_3col_end = """{{Airport destination list
| [[Oceanic Airlines]] | [[Athens International Airport|Athens]],<ref>Ref 1</ref> [[Los Angeles International Airport|Los Angeles]],<ref name=LA>Ref 2</ref> [[Sydney Airport|Sydney]],<ref>Ref 3</ref> [[Dulles International Airport|Washington–Dulles]]<ref name=LA/> |
| [[Puño Airlines]] | [[Miami International Airport|Miami]] <br/> {{em|Seasonal:}} [[Grand Bahama International Airport|Freeport]] | <ref>Ref 4</ref>
|3rdcoltitle={{Abbr|Refs.|References}}|3rdcolunsortable=yes
}}"""
example_b_3col_end_wt = parse(example_b_3col_end)

example_b_4col = """{{Airport destination list
|3rdcoltitle={{Abbr|Refs.|References}}|3rdcolunsortable=yes
|4thcoltitle=Notes|4thcolunsortable=yes
| [[Oceanic Airlines]] | [[Athens International Airport|Athens]],<ref>Ref 1</ref> [[Los Angeles International Airport|Los Angeles]],<ref name=LA>Ref 2</ref> [[Sydney Airport|Sydney]],<ref>Ref 3</ref> [[Dulles International Airport|Washington–Dulles]]<ref name=LA/> | |
| [[Puño Airlines]] | [[Miami International Airport|Miami]] <br/> {{em|Seasonal:}} [[Grand Bahama International Airport|Freeport]] | <ref>Ref 4</ref> |
}}"""
example_b_4col_wt = parse(example_b_4col)

example_b_4col_end = """{{Airport destination list
| [[Oceanic Airlines]] | [[Athens International Airport|Athens]],<ref>Ref 1</ref> [[Los Angeles International Airport|Los Angeles]],<ref name=LA>Ref 2</ref> [[Sydney Airport|Sydney]],<ref>Ref 3</ref> [[Dulles International Airport|Washington–Dulles]]<ref name=LA/> | |
| [[Puño Airlines]] | [[Miami International Airport|Miami]] <br/> {{em|Seasonal:}} [[Grand Bahama International Airport|Freeport]] | <ref>Ref 4</ref> |
|3rdcoltitle={{Abbr|Refs.|References}}|3rdcolunsortable=yes
|4thcoltitle=Notes|4thcolunsortable=yes
}}"""
example_b_4col_end_wt = parse(example_b_4col_end)

example_b_solutions = [
    # Uses simpler test cases, to test handling of 2 and 3 columns
    AirRoute(ORIGIN, "Athens International Airport", "Oceanic Airlines"),
    AirRoute(ORIGIN, "Los Angeles International Airport", "Oceanic Airlines"),
    AirRoute(ORIGIN, "Sydney Airport", "Oceanic Airlines"),
    AirRoute(ORIGIN, "Dulles International Airport", "Oceanic Airlines"),
    AirRoute(ORIGIN, "Miami International Airport", "Puño Airlines"),
    AirRoute(ORIGIN, "Grand Bahama International Airport", "Puño Airlines", seasonal=True)
]

example_c_2col = """{{Airport destination list
| [[Oceanic Airlines]] | [[Athens International Airport|Athens]],<ref>Ref 1</ref> [[Los Angeles International Airport|Los Angeles]],<ref name=LA>Ref 2</ref> [[Sydney Airport|Sydney]] (all flights suspended until 24 October 2026)
}}"""
example_c_2col_wt = parse(example_c_2col)

example_c_solutions = [
    # Tests "all suspended"
    AirRoute(ORIGIN, "Athens International Airport", "Oceanic Airlines", resumes=datetime(2026, 10, 24), suspended=True),
    AirRoute(ORIGIN, "Los Angeles International Airport", "Oceanic Airlines", resumes=datetime(2026, 10, 24), suspended=True),
    AirRoute(ORIGIN, "Sydney Airport", "Oceanic Airlines", resumes=datetime(2026, 10, 24), suspended=True),
]

example_d_2col = """{{Airport destination list
| [[Oceanic Airlines]] | [[Athens International Airport|Athens]] (suspended until October 24, 2026)
}}"""
example_d_2col_wt = parse(example_d_2col)

example_d_solutions = [
    # Tests "suspended until + date"
    AirRoute(ORIGIN, "Athens International Airport", "Oceanic Airlines", resumes=datetime(2026, 10, 24), suspended=True),
]

example_page = """{{Infobox airport}}
=Airlines and Destinations=
==Passenger==
{{Airport destination list
| [[Oceanic Airlines]] | [[Athens International Airport|Athens]],<ref>Ref 1</ref> [[Los Angeles International Airport|Los Angeles]] (begins {{date|2026-10-1}}),<ref name=LA>Ref 2</ref> [[Sydney Airport|Sydney]] (ends March 1, 2018),<ref>Ref 3</ref> [[Dulles International Airport|Washington–Dulles]]<ref name=LA/> (suspended)<br />'''Charter:''' [[Calvi – Sainte-Catherine Airport|Calvi]], [[Dublin Airport|Dublin]]<br/> {{em|Seasonal Charter:}} [[Grand Bahama International Airport|Freeport]]
| [[Puño Airlines]] | [[Miami International Airport|Miami]]<ref name=Puno>Ref 4</ref> <br/> {{em|Seasonal:}} [[Grand Bahama International Airport|Freeport]]<ref name=Puno/>
}}
==Cargo==
{{Airport-dest-list
| [[Oceanic Airlines Cargo]] | [[Athens International Airport|Athens]]
}}"""
example_page_wt = parse(example_page)


example_page_cargo = """{{Infobox airport}}
=Airlines and Destinations=
==Cargo==
{{Airport-dest-list
| [[Oceanic Airlines Cargo]] | [[Athens International Airport|Athens]]
}}"""
example_page_cargo_wt = parse(example_page_cargo)


example_page_pass = """{{Infobox airport}}
=Airlines and Destinations=
{{Airport destination list
| [[Oceanic Airlines]] | [[Athens International Airport|Athens]],<ref>Ref 1</ref> [[Los Angeles International Airport|Los Angeles]] (begins {{date|2026-10-1}}),<ref name=LA>Ref 2</ref> [[Sydney Airport|Sydney]] (ends March 1, 2018),<ref>Ref 3</ref> [[Dulles International Airport|Washington–Dulles]]<ref name=LA/> (suspended)<br />'''Charter:''' [[Calvi – Sainte-Catherine Airport|Calvi]], [[Dublin Airport|Dublin]]<br/> {{em|Seasonal Charter:}} [[Grand Bahama International Airport|Freeport]]
| [[Puño Airlines]] | [[Miami International Airport|Miami]]<ref name=Puno>Ref 4</ref> <br/> {{em|Seasonal:}} [[Grand Bahama International Airport|Freeport]]<ref name=Puno/>
}}"""
example_page_pass_wt = parse(example_page_pass)


example_page_cargo_2 = """==Airlines and destinations==
===Cargo===
{{Airport destination list
<!-- -->
| [[Ameriflight]]|'''Seasonal:''' [[Hollywood Burbank Airport|Burbank]]
}}
"""
example_page_cargo_2_wt = parse(example_page_cargo_2)

@pytest.mark.parametrize("input, has_passenger, has_cargo, pass_params, cargo_params", [
    (example_page_wt,         True, True, 4, 2),
    (example_page_cargo_wt,   False, True, 0, 2),
    (example_page_pass_wt,    True, False, 4, 0),
    (example_page_cargo_2_wt, False, True, 0, 2)
])
def test_get_apdl(input, has_passenger, has_cargo, pass_params, cargo_params):
    p, c = get_apdl(input)
    if has_passenger:
        assert type(p) == mwp.nodes.Template
        assert "Airport destination list" in p.name or "Airport-dest-list" in p.name
        assert len(p.params) == pass_params
    else:
        assert p == None
    if has_cargo:
        assert type(c) == mwp.nodes.Template
        assert "Airport destination list" in c.name or "Airport-dest-list" in c.name
        assert len(c.params) == cargo_params
    else:
        assert c == None


@pytest.mark.parametrize("input, expected, name", [
    (example_a_2col_wt,     example_a_solutions, "2 columns with multiple cases"),
    (example_b_3col_wt,     example_b_solutions, "3 columns"),
    (example_b_3col_end_wt, example_b_solutions, "3 columns with named params at end"),
    (example_b_4col_wt,     example_b_solutions, "4 columns"),
    (example_b_4col_end_wt, example_b_solutions, "4 columns with named params at end"),
    (example_c_2col_wt,     example_c_solutions, "test 'all suspended'"),
    (example_d_2col_wt,     example_d_solutions, "test 'suspended until'"),
])
def test_extract_apdl(input, expected, name):
    passenger, _ = get_apdl(input)
    assert passenger != None
    results = extract_apdl(passenger, ORIGIN)
    assert len(results) == len(expected), f"{name}: same number of results"
    assert results == expected, f"{name}: contents equal"


@pytest.mark.parametrize("input, exp_processed, exp_date", [
    ("(begins October 1, 2025)", "October 1, 2025", datetime(2025, 10, 1)),
    ("(begins 1 October 2025)", "1 October 2025", datetime(2025, 10, 1)),
    ("(begins 2025 October 1)", "2025 October 1", datetime(2025, 10, 1)),
    ("(   begins 2025 October 1  )", "2025 October 1", datetime(2025, 10, 1)),
    ("begins March 15, 2019", "March 15, 2019", datetime(2019, 3, 15)),
    ("(begins March 15, 2019)", "March 15, 2019", datetime(2019, 3, 15)),
    ("(ends April 5, 2028)", "April 5, 2028", datetime(2028, 4, 5)),
    ("(resumes June 29, 2028)", "June 29, 2028", datetime(2028, 6, 29)),
    ("(beginning March 15, 2019)", "March 15, 2019", datetime(2019, 3, 15)),
    ("(ending April 5, 2028)", "April 5, 2028", datetime(2028, 4, 5)),
    ("(resuming June 29, 2028)", "June 29, 2028", datetime(2028, 6, 29)),
    ("(all flights suspended until 24 October 2026)", "24 October 2026", datetime(2026, 10, 24)),
    ("(suspended until 24 October 2026)", "24 October 2026", datetime(2026, 10, 24)),
])
def test_process_date_str(input, exp_processed, exp_date):
    processed = process_date_str(input)
    assert processed == exp_processed, f"'{input}' correctly processed"
    date = dparser.parse(processed, fuzzy=True)
    assert date == exp_date, f"date correctly parsed from '{processed}'"