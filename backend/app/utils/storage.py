"""
Lightweight JSON storage helper.

We use flat JSON files instead of SQLite for this project because the
data volume is tiny (single-user portfolio project) and JSON keeps the
codebase easy to read for anyone reviewing it on GitHub. Every module
(resume parser, job parser, interview engine, scoring engine...) reuses
these two functions so there is exactly one place that knows how data
is written to disk.
"""

import json
import os
from typing import Any

from app.config import settings


def save_json(filename: str, data: dict[str, Any], subdir: str = "") -> str:
    """Save a dict as a JSON file under STORAGE_DIR (or a subdirectory of it).

    Returns the absolute path the file was written to.
    """
    target_dir = os.path.join(settings.STORAGE_DIR, subdir) if subdir else settings.STORAGE_DIR
    os.makedirs(target_dir, exist_ok=True)

    filepath = os.path.join(target_dir, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    return filepath


def load_json(filename: str, subdir: str = "") -> dict[str, Any]:
    """Load a dict from a JSON file under STORAGE_DIR."""
    target_dir = os.path.join(settings.STORAGE_DIR, subdir) if subdir else settings.STORAGE_DIR
    filepath = os.path.join(target_dir, filename)

    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)
