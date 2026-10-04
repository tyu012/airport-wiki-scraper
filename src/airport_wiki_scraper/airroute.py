from dataclasses import dataclass
import datetime as dt

@dataclass
class AirRoute:
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