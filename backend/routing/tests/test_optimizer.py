import random

import numpy as np
import pytest
from scipy.optimize import linprog

from routing.services.optimizer import Candidate, UnreachableGap, plan_purchases

RANGE = 500
MPG = 10


def plan(stations, trip_miles, initial_fuel_miles=RANGE):
    candidates = [Candidate(key, mile, price) for key, (mile, price) in enumerate(stations)]
    return plan_purchases(candidates, trip_miles, RANGE, MPG, initial_fuel_miles)


def summary(purchases):
    return [(p.key, round(p.gallons, 6), p.cost) for p in purchases]


def test_trip_within_initial_range_needs_no_stop():
    assert plan([(100, 3.0), (250, 2.5)], trip_miles=400) == []


def test_single_stop_buys_only_what_the_trip_needs():
    assert summary(plan([(300, 3.0)], trip_miles=700)) == [(0, 20.0, 60.0)]


def test_skips_expensive_station_when_cheaper_one_is_reachable():
    assert summary(plan([(100, 4.0), (300, 3.0)], trip_miles=750)) == [(1, 25.0, 75.0)]


def test_buys_just_enough_to_reach_a_cheaper_station():
    purchases = plan([(50, 4.0), (250, 3.0)], trip_miles=600, initial_fuel_miles=100)
    assert summary(purchases) == [(0, 15.0, 60.0), (1, 35.0, 105.0)]


def test_fills_up_when_everything_ahead_costs_more():
    purchases = plan([(400, 3.0), (800, 5.0)], trip_miles=1300)
    assert summary(purchases) == [(0, 40.0, 120.0), (1, 40.0, 200.0)]


def test_station_order_does_not_matter():
    purchases = plan([(800, 5.0), (400, 3.0)], trip_miles=1300)
    assert [p.key for p in purchases] == [1, 0]


def test_gap_after_a_station_is_reported():
    with pytest.raises(UnreachableGap) as raised:
        plan([(300, 3.0)], trip_miles=1000)
    assert (raised.value.from_mile, raised.value.to_mile) == (300, 1000)


def test_gap_from_the_origin_is_reported():
    with pytest.raises(UnreachableGap) as raised:
        plan([(450, 3.0)], trip_miles=900, initial_fuel_miles=200)
    assert (raised.value.from_mile, raised.value.to_mile) == (0, 450)


def cheapest_cost_by_lp(stations, trip_miles, initial_fuel_miles):
    stations = sorted(stations)
    miles = np.array([mile for mile, _ in stations] + [trip_miles])
    bought_before = np.tri(len(miles), len(stations), k=-1)
    bought_through = np.tri(len(stations), len(stations))
    result = linprog(
        c=[price / MPG for _, price in stations],
        A_ub=np.vstack((-bought_before, bought_through)),
        b_ub=np.concatenate((initial_fuel_miles - miles, RANGE - initial_fuel_miles + miles[:-1])),
    )
    return result.fun if result.success else None


def test_matches_linear_programming_optimum_on_random_trips():
    rng = random.Random(7)
    feasible = 0
    for _ in range(300):
        trip_miles = rng.uniform(50, 2500)
        initial_fuel_miles = rng.choice([RANGE, rng.uniform(0, RANGE)])
        stations = [
            (round(rng.uniform(0, trip_miles), 1), round(rng.uniform(2.5, 4.5), 3))
            for _ in range(rng.randint(1, 14))
        ]
        expected = cheapest_cost_by_lp(stations, trip_miles, initial_fuel_miles)
        if expected is None:
            with pytest.raises(UnreachableGap):
                plan(stations, trip_miles, initial_fuel_miles)
            continue
        feasible += 1
        purchases = plan(stations, trip_miles, initial_fuel_miles)
        assert sum(p.gallons * p.price for p in purchases) == pytest.approx(expected, abs=1e-4)
    assert feasible > 50
