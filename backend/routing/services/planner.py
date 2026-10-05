from dataclasses import dataclass

from django.conf import settings

from geo.coordinates import Coordinate
from stations.index import get_station_index
from stations.models import Station

from .corridor import sample_route, stations_along
from .optimizer import Purchase, plan_purchases
from .providers import get_provider


@dataclass(frozen=True)
class FuelStop:
    station: Station
    purchase: Purchase


@dataclass(frozen=True)
class TripPlan:
    start: Coordinate
    finish: Coordinate
    distance_miles: float
    duration_minutes: float
    path: list[list[float]]
    stops: list[FuelStop]

    @property
    def route(self) -> dict:
        return {"type": "LineString", "coordinates": self.path}

    @property
    def total_gallons(self) -> float:
        return sum(stop.purchase.gallons for stop in self.stops)

    @property
    def total_cost(self) -> float:
        return round(sum(stop.purchase.cost for stop in self.stops), 2)


def plan_trip(start: Coordinate, finish: Coordinate) -> TripPlan:
    route = get_provider().route(start, finish)
    samples = sample_route(route)
    index = get_station_index()

    purchases = plan_purchases(
        stations_along(samples, index, settings.STATION_CORRIDOR_MILES),
        trip_miles=route.distance_miles,
        range_miles=settings.VEHICLE_RANGE_MILES,
        mpg=settings.VEHICLE_MPG,
        initial_fuel_miles=settings.VEHICLE_RANGE_MILES * settings.VEHICLE_INITIAL_FUEL_FRACTION,
    )
    return TripPlan(
        start=start,
        finish=finish,
        distance_miles=route.distance_miles,
        duration_minutes=route.duration_seconds / 60,
        path=samples.coordinates.round(5).tolist(),
        stops=[FuelStop(index.stations[p.key], p) for p in purchases],
    )
