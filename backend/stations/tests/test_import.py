from decimal import Decimal
from io import StringIO

import pytest
from django.core.management import call_command

from stations.models import Station

CSV = """OPIS Truckstop ID,Truckstop Name,Address,City,State,Rack ID,Retail Price
7,WOODSHED OF BIG CABIN,"I-44, EXIT 283 & US-69",Big Cabin,OK,307,3.00733333
20,PILOT TRAVEL CENTER #1243,"I-8, EXIT 119 & SR-85",Gila Bend,AZ,930,3.899
20,PILOT #1243,"I-8, EXIT 119 & SR-85",Gila Bend,AZ,930,3.759
31,FLYING J,"SR-11",Calgary,AB,12,4.10
32,GHOST STOP,"I-10, EXIT 1",Nowhereville,TX,13,2.50
"""


@pytest.fixture
def csv_path(tmp_path):
    path = tmp_path / "prices.csv"
    path.write_text(CSV)
    return path


@pytest.mark.django_db
def test_import_dedupes_on_lowest_price_and_skips_unmatched_cities(csv_path):
    out = StringIO()

    call_command("import_stations", csv_path, stdout=out)

    assert set(Station.objects.values_list("opis_id", flat=True)) == {7, 20}
    pilot = Station.objects.get(opis_id=20)
    assert (pilot.name, pilot.price) == ("PILOT #1243", Decimal("3.759"))
    woodshed = Station.objects.get(opis_id=7)
    assert woodshed.price == Decimal("3.007")
    assert (round(woodshed.latitude, 1), round(woodshed.longitude, 1)) == (36.5, -95.2)
    assert "2 stations imported, 2 rows skipped" in out.getvalue()


@pytest.mark.django_db
def test_import_replaces_previous_stations(csv_path):
    call_command("import_stations", csv_path, stdout=StringIO())
    call_command("import_stations", csv_path, stdout=StringIO())

    assert Station.objects.count() == 2
