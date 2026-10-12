from pydantic import BaseModel, Field
import datetime as dt
from typing import Annotated

class AirRoute(BaseModel):
    """
    Class that represents an air route on Wikipedia's Airlines and Destinations 
    """
    origin: str
    destination: str
    airline: str = ""
    seasonal: bool = False
    charter: bool = False
    begins: dt.datetime | None = None
    resumes: dt.datetime | None = None
    ends: dt.datetime | None = None
    suspended: bool = False

class AirRouteID(BaseModel):
    """
    Contains all fields of AirRoute, but with added Wikidata QID fields for origin and destination
    airports.
    """
    origin: str
    origin_qid: Annotated[str, Field(pattern=r"^Q[1-9][0-9]*$")]
    destination: str
    destination_qid: Annotated[str, Field(pattern=r"^Q[1-9][0-9]*$")]
    airline: str = ""
    seasonal: bool = False
    charter: bool = False
    begins: dt.datetime | None = None
    resumes: dt.datetime | None = None
    ends: dt.datetime | None = None
    suspended: bool = False