import mwparserfromhell as mwp
import requests
from time import sleep
import random

API_URL = "https://en.wikipedia.org/w/api.php"

USER_AGENT = "AirWikiExplorer/0.1 (https://github.com/tyu012; yuyu.tim@gmail.com)" 

# Adapted from https://mwparserfromhell.readthedocs.io/en/latest/usage.html
def fetch(title: str):
    return fetch_multiple_articles([title])[0]["content"]


def mw_action_request(params: dict) -> dict:
    """
    Sends a request with the given parameters via the MediaWiki Action API.

    Response as JSON is returned to caller for further processing.

    Raises `AssertionError` if more than 50 titles are given as input.

    Raises `TooManyRequestsError` for rate limits reached (codes 429 or 503); exception contains
    retry_after field expressed in seconds.

    Raises `ValueError` for other status codes.

    Caller is responsible for handling missing article titles.
    Function is intended for internal use only since this abstracts a single API call.
    The API does not guarantee order.
    """
    headers = {
        "User-Agent": USER_AGENT
    }
    res = requests.get(API_URL, headers=headers, params=params)
    if res.status_code == 200:
        return res.json()
    elif res.status_code == 429 or res.status_code == 503:
        raise TooManyRequestsError(int(res.headers.get("Retry-After", "5")))
    elif res.status_code == 403:
        raise ValueError("Error 403 from MediaWiki Action API, invalid parameters")
    else:
        raise ValueError(f"Error {res.status_code} from MediaWiki Action API")


def fetch_multiple_articles(titles: list[str]) -> list[dict[str, str | None]]:
    """
    Fetches up to 50 Wikipedia articles with titles given as a list via the MediaWiki Action API.

    Returns wikitext content as a list of dicts, with keys "title" and "content":
    - "title" refers to the resolved title of the article, after redirects and normalization.
    - "content" contains the wikitext of the respective articles.
    - Pages not found are represented by "title" as given and "content" as None.

    Caller is responsible for handling missing article titles.
    Function is intended for internal use only since this abstracts a single API call.
    The API does not guarantee order.
    See `mw_action_request` for possible exceptions raised.
    """
    assert len(titles) <= 50
    params = {
            "action": "query",
            "prop": "revisions",
            "rvprop": "content",
            "titles": "|".join(titles),
            "format": "json",
            "formatversion": "2",
            "redirects": True
        }
    res_json = mw_action_request(params)
    texts = []
    if len(titles) > 0:
        pages = res_json["query"]["pages"]
        for page in pages:
            page_data = { "title": page["title"] }
            try:
                page_data["content"] = page["revisions"][0]["content"]
            except:
                page_data["content"] = None
            texts.append(page_data)
    return texts


def queue_fetch(
    titles: list[str], max_attempts: int=5, min_delay_ms: int=350, verbose: bool=False
) -> list[dict[str, str | None]]:
    """
    Fetches any number of Wikipedia articles with titles given as a list by executing a series of
    batched requests to the MediaWiki Action API.

    Each request will attempted for up to `max_attempts` times if rate-limited; if all attempts fail,
    only the content of articles successfully retrieved will be returned.

    Minimum delay time in ms between each request is `min_delay_ms`. By default, the delay is set
    to comply with the specified rate limit for unauthenticated bots with User-Agent as specified in
    [Wikimedia APIs/Rate limits](https://www.mediawiki.org/wiki/Wikimedia_APIs/Rate_limits).
    If a rate limit is reached, exponential backoff starting at the value of `min_delay_ms` is used,
    or the value of the Retry-After header, whichever is higher.

    The API does not guarantee order.
    """
    texts = []
    min_delay = min_delay_ms / 1000

    for lower_bound in range(0, len(titles), 50):
        for attempt in range(max_attempts):
            try:
                upper_bound = min(lower_bound + 50, len(titles))
                result = fetch_multiple_articles(titles[lower_bound:upper_bound])
                texts.extend(result)
                if verbose:
                    print(f"Fetched {upper_bound - lower_bound} articles. Waiting {min_delay} s.")
                sleep(min_delay)
                break
            except TooManyRequestsError as e:
                if verbose:
                    print(f"Unable to fetch {upper_bound - lower_bound} articles. This was attempt {attempt+1} of {max_attempts}")
                if attempt == max_attempts - 1:
                    return texts
                wait_time = max(e.retry_after, random.random() * min_delay * (2 ** attempt) + min_delay)
                sleep(wait_time)
    return texts


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
    def __init__(self, retry_after: int=0, msg: str="Too Many Requests"):
        self.retry_after = retry_after
        self.msg = msg
        super().__init__(self.msg)