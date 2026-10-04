from airport_wiki_scraper.routes_scraper import *
from mwparserfromhell import parse
import mwparserfromhell as mwp
from airport_wiki_scraper.airroute import AirRoute
from datetime import datetime

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

example_b_4col = """{{Airport destination list
|3rdcoltitle={{Abbr|Refs.|References}}|3rdcolunsortable=yes
|4thcoltitle=Notes|4thcolunsortable=yes
| [[Oceanic Airlines]] | [[Athens International Airport|Athens]],<ref>Ref 1</ref> [[Los Angeles International Airport|Los Angeles]],<ref name=LA>Ref 2</ref> [[Sydney Airport|Sydney]],<ref>Ref 3</ref> [[Dulles International Airport|Washington–Dulles]]<ref name=LA/> | |
| [[Puño Airlines]] | [[Miami International Airport|Miami]] <br/> {{em|Seasonal:}} [[Grand Bahama International Airport|Freeport]] | <ref>Ref 4</ref> |
}}"""
example_b_4col_wt = parse(example_b_4col)

example_b_solutions = [
    # Uses simpler test cases, to test handling of 2 and 3 columns
    AirRoute(ORIGIN, "Athens International Airport", "Oceanic Airlines"),
    AirRoute(ORIGIN, "Los Angeles International Airport", "Oceanic Airlines"),
    AirRoute(ORIGIN, "Sydney Airport", "Oceanic Airlines"),
    AirRoute(ORIGIN, "Dulles International Airport", "Oceanic Airlines"),
    AirRoute(ORIGIN, "Miami International Airport", "Puño Airlines"),
    AirRoute(ORIGIN, "Grand Bahama International Airport", "Puño Airlines", seasonal=True)
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


def test_get_apdl():
    passenger, cargo = get_apdl(example_page_wt)
    assert passenger.name.strip() == "Airport destination list", "correct template name"
    assert len(passenger.params) == 4, "correct first template size"
    assert type(cargo) == mwp.nodes.Template, "detected second template"
    assert cargo.name.strip() == "Airport-dest-list", "correct template name that is a redirect"
    assert len(cargo.params) == 2, "correct second template size"


def test_extract_apdl_2col():
    passenger, cargo = get_apdl(example_a_2col_wt)
    results = extract_apdl(passenger, ORIGIN)
    assert len(results) == len(example_a_solutions), "same number of results"
    assert results == example_a_solutions, "result contents equal and match order"


def test_extract_apdl_3col():
    passenger, cargo = get_apdl(example_b_3col_wt)
    results = extract_apdl(passenger, ORIGIN)
    print(results)
    assert len(results) == len(example_b_solutions), "same number of results"
    assert results == example_b_solutions, "result contents equal and match order"


def test_extract_apdl_4col():
    passenger, cargo = get_apdl(example_b_4col_wt)
    results = extract_apdl(passenger, ORIGIN)
    assert len(results) == len(example_b_solutions), "same number of results"
    assert results == example_b_solutions, "result contents equal and match order"