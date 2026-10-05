import csv
from decimal import Decimal
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction

from geo.gazetteer import find_place
from stations.index import get_station_index
from stations.models import Station


class Command(BaseCommand):
    help = "Load fuel stations from the OPIS price list, located by city."

    def add_arguments(self, parser):
        parser.add_argument("csv_path", nargs="?", type=Path, default=settings.FUEL_PRICES_CSV)

    def handle(self, *args, csv_path, **options):
        with open(csv_path, encoding="utf-8", newline="") as f:
            rows = list(csv.DictReader(f))

        stations = {}
        unmatched = 0
        for row in rows:
            city, state = row["City"].strip(), row["State"].strip()
            place = find_place(city, state)
            if place is None:
                unmatched += 1
                continue
            station = Station(
                opis_id=int(row["OPIS Truckstop ID"]),
                name=row["Truckstop Name"].strip(),
                address=row["Address"].strip(),
                city=city,
                state=state,
                price=Decimal(row["Retail Price"]).quantize(Decimal("0.001")),
                latitude=place.lat,
                longitude=place.lng,
            )
            current = stations.get(station.opis_id)
            if current is None or station.price < current.price:
                stations[station.opis_id] = station

        with transaction.atomic():
            Station.objects.all().delete()
            Station.objects.bulk_create(stations.values(), batch_size=1000)
        get_station_index.cache_clear()

        self.stdout.write(
            f"{len(rows)} rows read, {len(stations)} stations imported, "
            f"{unmatched} rows skipped (city not found in the US gazetteer)"
        )
