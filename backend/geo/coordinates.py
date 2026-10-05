from dataclasses import dataclass

import numpy as np

EARTH_RADIUS_MILES = 3958.8
METERS_PER_MILE = 1609.344


@dataclass(frozen=True)
class Coordinate:
    lat: float
    lng: float


def to_xyz(lat: np.ndarray, lng: np.ndarray) -> np.ndarray:
    lat, lng = np.radians(lat), np.radians(lng)
    cos_lat = np.cos(lat)
    return EARTH_RADIUS_MILES * np.column_stack(
        (cos_lat * np.cos(lng), cos_lat * np.sin(lng), np.sin(lat))
    )
