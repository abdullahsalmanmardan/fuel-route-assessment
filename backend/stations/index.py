from dataclasses import dataclass
from functools import cache

import numpy as np

from geo.coordinates import to_xyz

from .models import Station


@dataclass(frozen=True)
class StationIndex:
    stations: tuple[Station, ...]
    prices: np.ndarray
    xyz: np.ndarray


@cache
def get_station_index() -> StationIndex:
    stations = tuple(Station.objects.order_by("id"))
    return StationIndex(
        stations=stations,
        prices=np.array([float(s.price) for s in stations]),
        xyz=to_xyz(
            np.array([s.latitude for s in stations]),
            np.array([s.longitude for s in stations]),
        ),
    )
