import numpy as np

from geo.coordinates import EARTH_RADIUS_MILES
from routing.services.providers import Route

LATITUDE = 40.0


def straight_route(west: float, east: float, points: int = 2000) -> Route:
    lngs = np.linspace(west, east, points)
    miles = EARTH_RADIUS_MILES * np.cos(np.radians(LATITUDE)) * np.radians(east - west)
    return Route(
        coordinates=np.column_stack((lngs, np.full(points, LATITUDE))),
        distance_miles=float(miles),
        duration_seconds=float(miles) * 60,
    )
