from pydantic import BaseModel, Field

class Airport(BaseModel):
    """
    Class that represents selected infobox data and metadata from Wikipedia airport articles.
    """
    icao: str = Field(min_length=4, max_length=4)
    wiki_title: str
    iata: str | None = Field(default=None, min_length=3, max_length=3)
    coordinates: tuple[float, float] | None = None