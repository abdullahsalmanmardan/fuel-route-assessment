from bisect import bisect_right
from collections.abc import Iterable
from dataclasses import dataclass
from math import inf


@dataclass(frozen=True)
class Candidate:
    key: int
    mile: float
    price: float


@dataclass(frozen=True)
class Purchase:
    key: int
    mile: float
    price: float
    gallons: float

    @property
    def cost(self) -> float:
        return round(self.gallons * self.price, 2)


class UnreachableGap(Exception):
    def __init__(self, from_mile: float, to_mile: float):
        self.from_mile = from_mile
        self.to_mile = to_mile
        super().__init__(
            f"No fuel station within range between mile {from_mile:.0f} and mile {to_mile:.0f}."
        )


def plan_purchases(
    candidates: Iterable[Candidate],
    trip_miles: float,
    range_miles: float,
    mpg: float,
    initial_fuel_miles: float,
) -> list[Purchase]:
    origin = Candidate(key=-1, mile=0.0, price=0.0)
    destination = Candidate(key=-1, mile=trip_miles, price=-inf)
    nodes = [origin, *sorted(candidates, key=lambda c: c.mile), destination]
    miles = [node.mile for node in nodes]

    purchases = []
    fuel = initial_fuel_miles
    i = 0
    while i < len(nodes) - 1:
        here = nodes[i]
        reach = range_miles if i else fuel
        ahead = range(i + 1, bisect_right(miles, here.mile + reach))
        if not ahead:
            raise UnreachableGap(here.mile, nodes[i + 1].mile)

        target = next((j for j in ahead if nodes[j].price < here.price), None)
        if target is None:
            target = min(ahead, key=lambda j: nodes[j].price)
            wanted = reach
        else:
            wanted = nodes[target].mile - here.mile

        if wanted > fuel:
            purchases.append(Purchase(here.key, here.mile, here.price, (wanted - fuel) / mpg))
            fuel = wanted
        fuel -= nodes[target].mile - here.mile
        i = target

    return purchases
