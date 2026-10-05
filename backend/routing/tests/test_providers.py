from unittest.mock import Mock

import pytest
import requests

from geo.coordinates import METERS_PER_MILE, Coordinate
from routing.services.providers import NoRouteFound, OSRMProvider, RoutingUnavailable

START = Coordinate(40.0, -100.0)
FINISH = Coordinate(41.0, -99.0)


@pytest.fixture
def provider():
    provider = OSRMProvider()
    provider.session = Mock()
    return provider


def respond(provider, body):
    provider.session.get.return_value.json.return_value = body


def test_parses_route_and_makes_one_request(provider, settings):
    settings.OSRM_BASE_URL = "https://osrm.test"
    respond(
        provider,
        {
            "code": "Ok",
            "routes": [
                {
                    "distance": 100 * METERS_PER_MILE,
                    "duration": 5400,
                    "geometry": {"coordinates": [[-100.0, 40.0], [-99.0, 41.0]]},
                }
            ],
        },
    )

    route = provider.route(START, FINISH)

    assert route.distance_miles == pytest.approx(100)
    assert route.duration_seconds == 5400
    assert route.coordinates.tolist() == [[-100.0, 40.0], [-99.0, 41.0]]
    provider.session.get.assert_called_once()
    url = provider.session.get.call_args.args[0]
    assert url == "https://osrm.test/route/v1/driving/-100.0,40.0;-99.0,41.0"


def test_no_route_is_reported(provider):
    respond(provider, {"code": "NoRoute", "message": "Impossible route"})

    with pytest.raises(NoRouteFound):
        provider.route(START, FINISH)


def test_error_payload_means_unavailable(provider):
    respond(provider, {"message": "Too Many Requests"})

    with pytest.raises(RoutingUnavailable, match="Too Many Requests"):
        provider.route(START, FINISH)


@pytest.mark.parametrize("error", [requests.Timeout(), requests.JSONDecodeError("bad", "", 0)])
def test_transport_failure_means_unavailable(provider, error):
    provider.session.get.side_effect = error

    with pytest.raises(RoutingUnavailable):
        provider.route(START, FINISH)
