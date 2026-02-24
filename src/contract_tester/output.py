import os
import sys


def supports_color() -> bool:
    if os.environ.get("NO_COLOR"):
        return False
    if not sys.stdout.isatty():
        return False
    return True


def _wrap(text: str, code: str, enabled: bool) -> str:
    if not enabled:
        return text
    return f"\x1b[{code}m{text}\x1b[0m"


def ok(text: str, enabled: bool) -> str:
    return _wrap(text, "32", enabled)


def warn(text: str, enabled: bool) -> str:
    return _wrap(text, "33", enabled)


def err(text: str, enabled: bool) -> str:
    return _wrap(text, "31", enabled)


def strong(text: str, enabled: bool) -> str:
    return _wrap(text, "1", enabled)
