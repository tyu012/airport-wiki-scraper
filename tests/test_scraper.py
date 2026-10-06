from airport_wiki_scraper.scraper import *
import pytest

@pytest.fixture
def fetch_multiple_mocker(mocker):
    mock_get = mocker.patch("requests.get")
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = {
        "query": {
            "pages": [
                {
                    "title": "title1",
                    "revisions": [
                        { "content": "EXAMPLE1" },
                    ]
                },
                {
                    "title": "title2",
                    "revisions": [
                        { "content": "EXAMPLE2" }
                    ]
                }
            ]
        }
    }
    return mock_get


def test_fetch_multiple(fetch_multiple_mocker):
    result = fetch_multiple(["title1", "title2"])
    assert result == [
        { "title": "title1", "content": "EXAMPLE1" },
        { "title": "title2", "content": "EXAMPLE2" }
    ], "fetch_multiple correctly retrieves correct results"


def test_fetch(fetch_multiple_mocker):
    result = fetch("title1")
    assert result == "EXAMPLE1", "fetch correctly retrieves one result"


def test_rate_limit(mocker):
    mock_get = mocker.patch("requests.get")
    mock_get.return_value.status_code = 429
    mock_get.return_value.headers = { "Retry-After": "1" }
    with pytest.raises(TooManyRequestsError):
        fetch_multiple(["title1", "title2"])


def test_forbidden(mocker):
    mock_get = mocker.patch("requests.get")
    mock_get.return_value.status_code = 403
    with pytest.raises(ValueError):
        fetch_multiple(["badtitle1", "badtitle2"]) 


def test_missing_article(mocker):
    mock_get = mocker.patch("requests.get")
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = {
        "query": {
            "pages": [
                {
                    "title": "bad title",
                    "missing": True
                },
            ]
        }
    } 
    result = fetch_multiple(["bad title"])
    assert result == [{ "title": "bad title", "content": None }]


def test_redirect(mocker):
    mock_get = mocker.patch("requests.get")
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = {
        "query": {
            "pages": [
                {
                    "title": "redirect title",
                    "revisions": [
                        {
                            "content": "#REDIRECT [[title]]"
                        }
                    ]
                },
            ]
        }
    } 
    result = fetch_multiple(["redirect title"])
    assert result == [{ "title": "redirect title", "content": "#REDIRECT [[title]]" }]