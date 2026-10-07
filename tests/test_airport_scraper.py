import pytest
from airport_wiki_scraper.airport_scraper import parse_coord, _dms_to_dec
import mwparserfromhell as mwp

@pytest.mark.parametrize("wikitext, lat, long", [
    ("{{coord|0|0}}", (0, 0, 0, True), (0, 0, 0, True)),
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
    template = mwp.parse(wikitext).filter_templates(matches="coord")[0]
    exp_lat = _dms_to_dec(*lat)
    actual_lat = parse_coord(template)[0]
    exp_long = _dms_to_dec(*long)
    actual_long = parse_coord(template)[1]
    assert pytest.approx(exp_lat) == actual_lat
    assert pytest.approx(exp_long) == actual_long