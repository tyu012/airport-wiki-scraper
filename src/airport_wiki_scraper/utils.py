import re
from pydantic import BaseModel
import os
from urllib.parse import unquote

REF_PAIRED_RE = re.compile(r"<ref\b[^>]*>.*?</ref>", re.IGNORECASE | re.DOTALL)
REF_SELF_CLOSING_RE = re.compile(r"<ref\b[^<>]*?/\s*>", re.IGNORECASE)
REF_MALFORMED_RE = re.compile(r"<ref\b[^<>]*?/\s*(?=<|$)", re.IGNORECASE)

def strip_ref_tags(text: str, origin: str = "") -> str:
    """
    Removes <ref> tags from wikitext before it is parsed as a template.

    Reference tags are irrelevant to route extraction, but when their markup is malformed (e.g. a
    missing ">" in `<ref name="x"/<ref>`), the "=" characters inside their contents can leak into
    template parameter boundaries and shift every subsequent row. Malformed fragments are reported
    as warnings since they are likely editing errors worth fixing on Wikipedia.
    """
    malformed = REF_MALFORMED_RE.findall(text)
    if malformed:
        print(f"Warning: malformed ref tag(s) for '{origin}': {malformed}")
    # Self-closing refs must be removed before paired refs, otherwise a self-closing tag such as
    # `<ref name=x/>` is mistaken for an opening tag and swallows content up to the next `</ref>`.
    text = REF_SELF_CLOSING_RE.sub("", text)
    text = REF_PAIRED_RE.sub("", text)
    text = REF_MALFORMED_RE.sub("", text)
    return text


def str_validate_or_none(regex):
    """
    Generates a validator function that validates a string, or returns None if invalid
    """
    return (lambda value: value if isinstance(value, str) and re.fullmatch(regex, value) else None)


def write_pydantic_jsonl(values: list, path: str | os.PathLike[str]):
    """
    Write a list of Pydantic model objects to .jsonl format
    """
    with open(path, "w") as f:
        f.writelines([v.model_dump_json() + "\n" for v in values])


def load_pydantic_jsonl(path: str | os.PathLike[str], model) -> list:
    """
    Open a .jsonl file representing objects of a Pydantic model class and return objects as a list
    """
    with open(path, "r") as f:
        values = [model.model_validate_json(line.strip()) for line in f.readlines()]
    return values


def normalize_wiki_url(url: str) -> str:
    return unquote(url.removeprefix("https://en.wikipedia.org/wiki/")).replace("_", " ").strip()