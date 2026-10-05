from unittest.mock import Mock

import pytest

from routing.services.providers import NoRouteFound, RoutingUnavailable
from stations.models import Station

from .factories import LATITUDE, straight_route

URL = "/api/route/"
TRIP = {"start": f"{LATITUDE},-100", "finish": f"{LATITUDE},-85"}


@pytest.fixture
def provider(monkeypatch):
    provider = Mock()
    provider.route.return_value = straight_route(-100, -85)
    monkeypatch.setattr("routing.services.planner.get_provider", lambda: provider)
    return provider


def station(opis_id, lng, price, lat=LATITUDE):
    return Station.objects.create(
        opis_id=opis_id,
        name=f"Station {opis_id}",
        address="I-80, EXIT 1",
        city="Somewhere",
        state="NE",
        price=price,
        latitude=lat,
        longitude=lng,
    )


@pytest.mark.django_db
def test_returns_route_with_cheapest_stop(client, provider):
    station(1, -95, "3.500")
    station(2, -92, "3.000")
    station(3, -92, "2.000", lat=LATITUDE + 1)

    response = client.get(URL, TRIP)

    assert response.status_code == 200
    body = response.json()
    gallons = (body["distance_miles"] - 500) / 10
    assert [stop["name"] for stop in body["stops"]] == ["Station 2"]
    assert body["stops"][0]["gallons"] == pytest.approx(gallons, abs=0.01)
    assert body["total_cost"] == pytest.approx(gallons * 3, abs=0.02)
    assert body["route"]["type"] == "LineString"
    assert body["route"]["coordinates"][0] == [-100.0, LATITUDE]
    assert body["route"]["coordinates"][-1] == [-85.0, LATITUDE]


@pytest.mark.django_db
def test_repeat_request_is_served_from_cache(client, provider):
    station(1, -92, "3.000")

    first = client.get(URL, TRIP)
    second = client.get(URL, TRIP)

    assert first.json() == second.json()
    provider.route.assert_called_once()


@pytest.mark.django_db
def test_accepts_city_names(client, provider):
    response = client.get(URL, {"start": "Denver, CO", "finish": "Chicago, IL"})

    start, finish = provider.route.call_args.args
    assert response.status_code == 422
    assert (round(start.lat), round(start.lng)) == (40, -105)
    assert (round(finish.lat), round(finish.lng)) == (42, -88)


@pytest.mark.django_db
def test_route_without_reachable_station_is_unprocessable(client, provider):
    response = client.get(URL, TRIP)

    assert response.status_code == 422
    assert "mile 0" in response.json()["detail"]


@pytest.mark.parametrize(
    "params",
    [
        {"start": "Denver, CO"},
        {"start": "Denver", "finish": "Chicago, IL"},
        {"start": "Nowhereville, CO", "finish": "Chicago, IL"},
        {"start": "51.5,-0.12", "finish": "Chicago, IL"},
        {"start": "Chicago, IL", "finish": "Chicago, IL"},
    ],
)
def test_invalid_locations_are_rejected(client, provider, params):
    response = client.get(URL, params)

    assert response.status_code == 400
    provider.route.assert_not_called()


@pytest.mark.parametrize(
    ("error", "status"),
    [(RoutingUnavailable("down"), 502), (NoRouteFound("none"), 422)],
)
def test_routing_failures_map_to_http_errors(client, provider, error, status):
    provider.route.side_effect = error

    response = client.get(URL, TRIP)

    assert response.status_code == status
    assert response.json() == {"detail": str(error)}
