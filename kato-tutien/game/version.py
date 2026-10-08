"""Application version metadata and consistency checks."""
from __future__ import annotations

from pathlib import Path
import re


ROOT = Path(__file__).resolve().parent.parent
_VERSION_RE = re.compile(r"^\s*version\s*=\s*[\"']([^\"']+)[\"']\s*$", re.MULTILINE)


def _read_version_file() -> str:
    path = ROOT / "VERSION.txt"
    try:
        value = path.read_text(encoding="utf-8").strip()
    except OSError:
        return "unknown"
    return value or "unknown"


def _read_pyproject_version() -> str:
    path = ROOT / "pyproject.toml"
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return "unknown"
    match = _VERSION_RE.search(text)
    return match.group(1).strip() if match else "unknown"


VERSION = _read_version_file()
PYPROJECT_VERSION = _read_pyproject_version()


def version_status() -> dict[str, str | bool]:
    consistent = VERSION != "unknown" and PYPROJECT_VERSION != "unknown" and VERSION == PYPROJECT_VERSION
    return {
        "version": VERSION,
        "pyproject_version": PYPROJECT_VERSION,
        "consistent": consistent,
    }
