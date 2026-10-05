from dataclasses import dataclass

import numpy as np
from scipy.spatial import cKDTree

from geo.coordinates import to_xyz
from stations.index import StationIndex

from .optimizer import Candidate
from .providers import Route

SAMPLE_SPACING_MILES = 0.5


@dataclass(frozen=True)
class RouteSamples:
    coordinates: np.ndarray
    xyz: np.ndarray
    miles: np.ndarray


def sample_route(route: Route) -> RouteSamples:
    xyz = to_xyz(route.coordinates[:, 1], route.coordinates[:, 0])
    steps = np.linalg.norm(np.diff(xyz, axis=0), axis=1)
    miles = np.concatenate(([0.0], np.cumsum(steps)))
    if miles[-1]:
        miles *= route.distance_miles / miles[-1]

    marks = np.append(np.arange(0, miles[-1], SAMPLE_SPACING_MILES), miles[-1])
    lng = np.interp(marks, miles, route.coordinates[:, 0])
    lat = np.interp(marks, miles, route.coordinates[:, 1])
    return RouteSamples(np.column_stack((lng, lat)), to_xyz(lat, lng), marks)


def stations_along(
    samples: RouteSamples, index: StationIndex, corridor_miles: float
) -> list[Candidate]:
    offsets, nearest = cKDTree(samples.xyz).query(index.xyz, distance_upper_bound=corridor_miles)
    return [
        Candidate(key=int(i), mile=float(samples.miles[nearest[i]]), price=float(index.prices[i]))
        for i in np.flatnonzero(np.isfinite(offsets))
    ]
