from pydantic import BaseModel, Field, BeforeValidator, ValidationError
from typing import Annotated, Any
import re
from airport_wiki_scraper.utils import str_validate_or_none

ICAO_REGEX = r"^[A-Z]{4}$"
IATA_REGEX = r"^[A-Z]{3}$"

class Airport(BaseModel):
    """
    Class that represents selected infobox data and metadata from Wikipedia airport articles.

    NOTE: `coordinates` is ordered `(Latitude, Longitude)`. Wikipedia coord templates use this
    order, but Wikidata's ordering is reversed.
    """
    qid: str = Field(pattern=r"^Q[1-9][0-9]*$")
    wiki_title: str
    icao: Annotated[str | None, BeforeValidator(str_validate_or_none(ICAO_REGEX))] = None
    iata: Annotated[str | None, BeforeValidator(str_validate_or_none(IATA_REGEX))] = None
    coordinates: tuple[float, float] | None = None

 