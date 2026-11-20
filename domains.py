import re
_VALID_RE = re.compile(r"[A-Za-z0-9-]+(\.[A-Za-z0-9-]+)*\.?")

def is_valid_domain(text: str) -> bool:
    """True if `text` is a valid domain input (non-empty, allowed chars only)."""
    return _VALID_RE.fullmatch(text) is not None

def normalize(name: str) -> str:
    name = name.lower()
    if name.endswith("."):
        name = name[:-1]
    return name

def matches(name: str, entries: set) -> bool:
    return any(name == e or name.endswith("." + e) for e in entries)
