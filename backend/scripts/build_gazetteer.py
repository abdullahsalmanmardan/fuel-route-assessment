"""Builds geo/data/us_places.csv.gz from the GeoNames US dump (US.txt, CC BY 4.0)."""

import csv
import gzip
import sys

from geo.gazetteer import DATA_FILE, place_key

ALIAS_MIN_POPULATION = 100_000


def build(source: str) -> None:
    primary: dict[tuple[str, str], tuple[int, str, str]] = {}
    aliases: dict[tuple[str, str], tuple[int, str, str]] = {}

    with open(source, encoding="utf-8", newline="") as f:
        for row in csv.reader(f, delimiter="\t", quoting=csv.QUOTE_NONE):
            if row[6] != "P" or row[8] != "US" or not row[10]:
                continue
            state, population = row[10], int(row[14] or 0)
            place = (population, f"{float(row[4]):.4f}", f"{float(row[5]):.4f}")
            for name in {row[1], row[2]}:
                key = (place_key(name), state)
                if key[0] and place > primary.get(key, (-1,)):
                    primary[key] = place
            if population >= ALIAS_MIN_POPULATION:
                for name in row[3].split(","):
                    key = (place_key(name), state)
                    if key[0] and place > aliases.get(key, (-1,)):
                        aliases[key] = place

    places = aliases | primary
    with gzip.open(DATA_FILE, "wt", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        for (key, state), (_, lat, lng) in sorted(places.items()):
            writer.writerow((key, state, lat, lng))
    print(f"{len(places)} places written to {DATA_FILE}")


if __name__ == "__main__":
    build(sys.argv[1])
