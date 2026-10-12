import pytest
from airport_wiki_scraper.airport_scraper import parse_coord, _dms_to_dec, parse_airport_infobox
from airport_wiki_scraper.airport import Airport
import mwparserfromhell as mwp
import re
from airport_wiki_scraper.utils import strip_ref_tags

@pytest.mark.parametrize("wikitext, lat, long", [
    ("{{coord|0|0}}", (0, 0, 0, True), (0, 0, 0, True)),
    ("{{Coord|0|0}}", (0, 0, 0, True), (0, 0, 0, True)),
    ("{{coord|25|15|10|N|055|21|52|E}}", (25, 15, 10, True), (55, 21, 52, True)),
    ("{{coord|25|15|display=title|10|N|055|21|52|E}}", (25, 15, 10, True), (55, 21, 52, True)),
    ("{{coord|25|15|10|S|55|21|52|W}}", (25, 15, 10, False), (55, 21, 52, False)),
    ("{{coord|25|15|10|S|55|myparam=value|21|52|W}}", (25, 15, 10, False), (55, 21, 52, False)),
    ("{{coord|25|15|10|S|55|21|52|W|unnamedparam}}", (25, 15, 10, False), (55, 21, 52, False)),
    ("{{coord|25|15|10.123|N|55|21|52.456|E}}", (25, 15, 10.123, True), (55, 21, 52.456, True)),
    ("{{coord|25|15|N|55|21|E}}", (25, 15, 0, True), (55, 21, 0, True)),
    ("{{coord|25|display=title|15|N|myparam=value|55|21|E|unnamedparam}}", (25, 15, 0, True), (55, 21, 0, True)),
    ("{{coord|25|N|55|E}}", (25, 0, 0, True), (55, 0, 0, True)),
    ("{{coord|display=title|25|N|55|E|unnamedparam}}", (25, 0, 0, True), (55, 0, 0, True)),
    ("{{coord|-25.123|-55.456}}", (25.123, 0, 0, False), (55.456, 0, 0, False)),
    ("{{coord|-25.123|display=title|-55.456|unnamedparam}}", (25.123, 0, 0, False), (55.456, 0, 0, False)),
])
def test_parse_coord(wikitext, lat, long):
    template = mwp.parse(wikitext).filter_templates(matches="coord", flags=re.IGNORECASE)[0]
    exp_lat = _dms_to_dec(*lat)
    actual_lat = parse_coord(template)[0]
    exp_long = _dms_to_dec(*long)
    actual_long = parse_coord(template)[1]
    assert pytest.approx(exp_lat) == actual_lat
    assert pytest.approx(exp_long) == actual_long


airport_a_title = "Los Angeles International Airport"
airport_a_infobox = """{{Infobox airport
| name              = Los Angeles International Airport
| IATA              = LAX
| ICAO              = KLAX
| coordinates       = {{Coord|12.34|56.78}}
}}"""
airport_a_infobox_no_iata = """{{Infobox airport
| name              = Los Angeles International Airport
| ICAO              = KLAX
| coordinates       = {{Coord|12.34|56.78}}
}}"""
airport_a_infobox_no_coord = """{{Infobox airport
| name              = Los Angeles International Airport
| IATA              = LAX
| ICAO              = KLAX
}}"""
airport_b_title = "EuroAirport Basel–Mulhouse–Freiburg"
airport_b_infobox = """{{Infobox airport
| name                   = EuroAirport Basel–Mulhouse–Freiburg
| ICAO                   = LFSB
}}"""
airport_c_title = "March Air Reserve Base"
airport_c_infobox = """{{Infobox military installation
| IATA                   = RIV
| ICAO                   = KRIV}}"""

DUMMY_QID = "Q123"
@pytest.mark.parametrize("infobox, title, expected", [
    (airport_a_infobox,           airport_a_title,
        Airport(qid=DUMMY_QID, icao="KLAX", wiki_title=airport_a_title, iata="LAX", coordinates=(12.34, 56.78))),
    (airport_a_infobox_no_iata,   airport_a_title,
        Airport(qid=DUMMY_QID, icao="KLAX", wiki_title=airport_a_title, coordinates=(12.34, 56.78))),
    (airport_a_infobox_no_coord,  airport_a_title,
        Airport(qid=DUMMY_QID, icao="KLAX", wiki_title=airport_a_title, iata="LAX")),
    (airport_b_infobox, airport_b_title,
        Airport(qid=DUMMY_QID, icao="LFSB", wiki_title=airport_b_title)),
    (airport_c_infobox, airport_c_title,
        Airport(qid=DUMMY_QID, icao="KRIV", wiki_title=airport_c_title, iata="RIV"))
])
def test_parse_airport_infobox(infobox, title, expected: Airport):
    parsed_infobox = parse_airport_infobox(mwp.parse(strip_ref_tags(infobox)), DUMMY_QID, title)
    assert parsed_infobox.icao == expected.icao, "matches ICAO"
    assert parsed_infobox.wiki_title == expected.wiki_title, "matches wiki title"
    assert parsed_infobox.iata == expected.iata, "matches IATA"
    if expected.coordinates != None:
        assert parsed_infobox.coordinates != None
        assert pytest.approx(parsed_infobox.coordinates[0]) == expected.coordinates[0], "matches latitude"
        assert pytest.approx(parsed_infobox.coordinates[1]) == expected.coordinates[1], "matches longitude"