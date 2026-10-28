"""Platform-neutral recent-project validation; keeps editor and dialogs in sync."""
from __future__ import annotations
from pathlib import Path


def tidy_recent(paths: list[str] | str | None, maximum: int = 8) -> list[str]:
    """Keep existing distinct project paths, newest first; never store invalid items."""
    if isinstance(paths, str):
        paths = [paths]
    seen: set[str] = set()
    result = []
    for value in paths or []:
        try:
            path = Path(value).expanduser().resolve()
            if path.suffix.lower() != '.mellowzip' or not path.is_file():
                continue
            key = str(path).casefold()
            if key in seen:
                continue
            seen.add(key)
            result.append(str(path))
        except (OSError, TypeError, ValueError):
            continue
        if len(result) >= maximum:
            break
    return result
