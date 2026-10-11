from pydantic import BaseModel, Field
from typing import Annotated

class Airport(BaseModel):
    """
    Class that represents selected infobox data and metadata from Wikipedia airport articles.
    """
    icao: str = Field(min_length=4, max_length=4)
    wiki_title: str
    iata: Annotated[str, Field(min_length=3, max_length=3)] | None = None
    coordinates: tuple[float, float] | None = None