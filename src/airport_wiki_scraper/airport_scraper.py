import mwparserfromhell as mwp
from airport_wiki_scraper.airport import Airport

def parse_airport_infobox(page: mwp.wikicode.Wikicode, title: str="") -> Airport:
    infobox = page.filter_templates(matches=r'(Infobox airport|Infobox aerodrome|Infobox Airport)')[0]
    print(infobox.params)
    icao = str(infobox.get("ICAO").value).strip()
    iata = infobox.get("IATA", None)
    if iata != None:
        iata = str(iata.value).strip()
    try:
        coordinates = parse_coord(
            infobox.get("coordinates").value.filter_templates(matches="coord")[0])
    except:
        coordinates = None

    return Airport(
        icao=icao,
        iata=iata,
        wiki_title=title,
        coordinates=coordinates
    )


def parse_coord(template: mwp.nodes.Template) -> tuple[float, float]:
    """
    Parses a coordinate given by Wikipedia's `coord` template and returns the decimal (lat, long)
    value as a tuple.

    Supports the following cases, with any number of named parameters at any position and any
    number of unnamed parameters after the end of the unnamed coordinate parameters.
    ```
    {{coord|deg|min|sec|N|deg|min|sec|E}}
    {{coord|deg|min|N|deg|min|E}}
    {{coord|deg|N|deg|E}}
    {{coord|signed deg|signed deg}}
    ```
    """
    filtered_params = [param.strip().lower() for param in template.params if not param.showkey]

    # Check for positions of "e" and "w" and whether they are present to determine format
    # NOTE: compare letters to lower-case only
    params = len(filtered_params)

    if params >= 8 and (filtered_params[7] == "e" or filtered_params[7].lower() == "w"):
        lat_dms = [float(filtered_params[0]), float(filtered_params[1]), float(filtered_params[2]), filtered_params[3] == "n"]
        long_dms = [float(filtered_params[4]), float(filtered_params[5]), float(filtered_params[6]), filtered_params[7] == "e"]
    elif params >= 6 and (filtered_params[5] == "e" or filtered_params[5].lower() == "w"):
        lat_dms = [float(filtered_params[0]), float(filtered_params[1]), 0, filtered_params[2] == "n"]
        long_dms = [float(filtered_params[3]), float(filtered_params[4]), 0, filtered_params[5] == "e"]
    elif params >= 4 and (filtered_params[3] == "e" or filtered_params[3].lower() == "w"):
        lat_dms = [float(filtered_params[0]), 0, 0, filtered_params[1] == "n"]
        long_dms = [float(filtered_params[2]), 0, 0, filtered_params[3] == "e"]
    else:
        return (float(filtered_params[0]), float(filtered_params[1]))
   
    lat = _dms_to_dec(*lat_dms)
    long = _dms_to_dec(*long_dms)

    return (lat, long)


def _dms_to_dec(deg: float=0, min: float=0, sec: float=0, positive: bool=True) -> float:
    """
    Converts latitude or longitude values in degree/minute/second format to decimal format.

    Adapted from https://stackoverflow.com/a/54294962
    """
    return (deg + min / 60 + sec / (3600)) * (1 if positive else -1)