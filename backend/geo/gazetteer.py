import csv
import gzip
import re
from functools import cache
from pathlib import Path

from .coordinates import Coordinate

DATA_FILE = Path(__file__).resolve().parent / "data" / "us_places.csv.gz"

ABBREVIATIONS = {"saint": "st", "sainte": "st", "ste": "st", "mount": "mt", "fort": "ft"}


def place_key(name: str) -> str:
    words = re.sub(r"[^a-z0-9 ]", "", name.lower().replace("-", " ")).split()
    return "".join(ABBREVIATIONS.get(word, word) for word in words)


@cache
def _places() -> dict[tuple[str, str], tuple[float, float]]:
    with gzip.open(DATA_FILE, "rt", encoding="utf-8", newline="") as f:
        return {(key, state): (float(lat), float(lng)) for key, state, lat, lng in csv.reader(f)}


def find_place(city: str, state: str) -> Coordinate | None:
    position = _places().get((place_key(city), state.strip().upper()))
    return Coordinate(*position) if position else None
