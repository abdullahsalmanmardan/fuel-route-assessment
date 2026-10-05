from dataclasses import dataclass
from functools import cache
from typing import Protocol

import numpy as np
import requests
from django.conf import settings
from django.utils.module_loading import import_string

from geo.coordinates import METERS_PER_MILE, Coordinate


@dataclass(frozen=True)
class Route:
    coordinates: np.ndarray
    distance_miles: float
    duration_seconds: float


class RoutingUnavailable(Exception):
    pass


class NoRouteFound(Exception):
    pass


class RoutingProvider(Protocol):
    def route(self, start: Coordinate, finish: Coordinate) -> Route: ...


class OSRMProvider:
    def __init__(self):
        self.session = requests.Session()

    def route(self, start: Coordinate, finish: Coordinate) -> Route:
        url = (
            f"{settings.OSRM_BASE_URL}/route/v1/driving/"
            f"{start.lng},{start.lat};{finish.lng},{finish.lat}"
        )
        try:
            body = self.session.get(
                url,
                params={"overview": "full", "geometries": "geojson"},
                timeout=settings.ROUTING_TIMEOUT_SECONDS,
            ).json()
        except requests.RequestException as exc:
            raise RoutingUnavailable("The routing service did not respond.") from exc

        if body.get("code") == "NoRoute":
            raise NoRouteFound("No drivable route between these locations.")
        if body.get("code") != "Ok":
            raise RoutingUnavailable(f"The routing service failed: {body.get('message', body)}")

        route = body["routes"][0]
        return Route(
            coordinates=np.array(route["geometry"]["coordinates"]),
            distance_miles=route["distance"] / METERS_PER_MILE,
            duration_seconds=route["duration"],
        )


@cache
def get_provider() -> RoutingProvider:
    return import_string(settings.ROUTING_PROVIDER)()
