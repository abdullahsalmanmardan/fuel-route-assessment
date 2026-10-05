import numpy as np
import pytest

from geo.coordinates import to_xyz
from routing.services.corridor import sample_route, stations_along
from routing.services.providers import Route
from stations.index import StationIndex

from .factories import LATITUDE, straight_route

MILES_PER_DEGREE_LAT = 69.1


def index_of(positions):
    lats, lngs = zip(*positions, strict=True)
    return StationIndex(
        stations=(),
        prices=np.arange(3.0, 3.0 + len(positions)),
        xyz=to_xyz(np.array(lats), np.array(lngs)),
    )


def test_samples_cover_the_whole_route():
    route = straight_route(-100, -99)
    samples = sample_route(route)

    assert samples.miles[0] == 0
    assert samples.miles[-1] == pytest.approx(route.distance_miles)
    assert np.diff(samples.miles).max() <= 0.5
    assert samples.coordinates[0].tolist() == [-100, LATITUDE]
    assert samples.coordinates[-1].tolist() == [-99, LATITUDE]


def test_sparse_geometry_is_sampled_at_the_same_spacing():
    samples = sample_route(straight_route(-100, -99, points=2))

    assert np.diff(samples.miles).max() <= 0.5
    assert samples.coordinates[len(samples.miles) // 2, 0] == pytest.approx(-99.5, abs=0.01)


def test_zero_length_route_has_a_single_mile_marker():
    route = Route(np.array([[-100.0, LATITUDE], [-100.0, LATITUDE]]), 0.0, 0.0)

    samples = sample_route(route)

    assert samples.miles.tolist() == [0.0]
    assert stations_along(samples, index_of([(LATITUDE, -100.0)]), 10)[0].mile == 0


def test_keeps_stations_inside_the_corridor_with_their_mile_marker():
    route = straight_route(-100, -99)
    index = index_of(
        [
            (LATITUDE, -99.5),
            (LATITUDE + 5 / MILES_PER_DEGREE_LAT, -99.75),
            (LATITUDE + 30 / MILES_PER_DEGREE_LAT, -99.5),
        ]
    )

    candidates = stations_along(sample_route(route), index, corridor_miles=10)

    assert [c.key for c in candidates] == [0, 1]
    assert candidates[0].mile == pytest.approx(route.distance_miles / 2, abs=0.5)
    assert candidates[1].mile == pytest.approx(route.distance_miles / 4, abs=0.5)
    assert candidates[1].price == 4.0
