from dataclasses import dataclass

@dataclass
class Airport:
    """
    Class that represents selected infobox data and metadata from Wikipedia airport articles.
    """
    icao: str
    iata: str | None
    wiki_title: str
    coordinates: tuple[float, float] | None