import mwparserfromhell as mwp
import requests
import os

API_URL = "https://en.wikipedia.org/w/api.php"

USER_AGENT = "AirWikiExplorer/0.1 (https://github.com/tyu012; yuyu.tim@gmail.com)" 

# Adapted from https://mwparserfromhell.readthedocs.io/en/latest/usage.html
def fetch(title: str):
    return fetch_multiple([title])[0]["content"]


def fetch_multiple(titles: list[str]) -> list[dict[str, str | None]]:
    """
    Fetches up to 50 Wikipedia articles with titles given as a list via the MediaWiki Action API.

    Returns wikitext content as a list of dicts, with keys "title" and "content".
    Pages not found are represented by content as None.

    Raises TooManyRequestsError for rate limits reached (codes 429 or 503); exception contains
    retry_after field expressed in seconds.

    Raises ValueError for other status codes.

    Caller is responsible for handling missing article titles and redirects.
    Function is intended for internal use only since this abstracts a single API call.
    """
    assert len(titles) <= 50
    params = {
            "action": "query",
            "prop": "revisions",
            "rvprop": "content",
            "titles": "|".join(titles),
            "format": "json",
            "formatversion": "2",
        }
    headers = {
        "User-Agent": USER_AGENT
    }
    res = requests.get(API_URL, headers=headers, params=params)
    if res.status_code == 200:
        res_json = res.json()
        pages = res_json["query"]["pages"]
        texts = []
        for page in pages:
            page_data = { "title": page["title"] }
            try:
                page_data["content"] = page["revisions"][0]["content"]
            except:
                page_data["content"] = None
            texts.append(page_data)
        return texts
    elif res.status_code == 429 or res.status_code == 503:
        raise TooManyRequestsError(int(res.headers.get("Retry-After", "5")))
    elif res.status_code == 403:
        raise ValueError("Error 403 from MediaWiki Action API, invalid parameters")
    else:
        raise ValueError(f"Error {res.status_code} from MediaWiki Action API")


# Adapted from https://mwparserfromhell.readthedocs.io/en/latest/usage.html
def fetch_and_parse(title: str) -> mwp.wikicode.Wikicode:
    text = fetch(title)
    return mwp.parse(text)


# def fetch_multiple_and_parse(titles: list[str]) -> list[mwp.wikicode.Wikicode]:
#     texts = fetch_multiple(titles)
#     return [ mwp.parse(text) for text in texts ]


class TooManyRequestsError(Exception):
    """
    Encodes a HTTP 429 error. The retry_after field encodes the Retry-After header, only in seconds
    since the MediaWiki API states the following when rate-limited:

    > Responses with status code 429 or 503 typically also have the Retry-After
    > header set, indicating how long the client should wait until it retries the
    > request. If no such header is present, clients should wait at least five
    > seconds, or implement exponential back-off. 
    """
    def __init__(self, retry_after: int=5, msg: str="Too Many Requests"):
        self.retry_after = retry_after
        self.msg = msg
        super().__init__(self.msg)