import mwparserfromhell as mwp
import requests

API_URL = "https://en.wikipedia.org/w/api.php"

# Credit: https://mwparserfromhell.readthedocs.io/en/latest/usage.html
def fetch(title: str):
    params = {
            "action": "query",
            "prop": "revisions",
            "rvprop": "content",
            "rvslots": "main",
            "rvlimit": 1,
            "titles": title,
            "format": "json",
            "formatversion": "2",
        }
    headers = {
        "User-Agent": "AirWikiExplorer/0.1 (https://github.com/tyu012; yuyu.tim@gmail.com)"
    }
    req = requests.get(API_URL, headers=headers, params=params)
    res = req.json()
    revision = res["query"]["pages"][0]["revisions"][0]
    text = revision["slots"]["main"]["content"]
    return text


def parse(title: str) -> mwp.wikicode.Wikicode:
    text = fetch(title)
    return mwp.parse(text)