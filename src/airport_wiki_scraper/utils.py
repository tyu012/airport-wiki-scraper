import re

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