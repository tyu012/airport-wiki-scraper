from pydantic import BaseModel
import datetime as dt

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
    origin_qid: str
    destination: str
    destination_qid: str
    airline: str = ""
    seasonal: bool = False
    charter: bool = False
    begins: dt.datetime | None = None
    resumes: dt.datetime | None = None
    ends: dt.datetime | None = None
    suspended: bool = False