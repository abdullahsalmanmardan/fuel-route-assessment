# Fuel route planner

Django API that plans a drive between two US locations and picks the cheapest
places to refuel along it, using the supplied OPIS price list.

## Setup

With Docker:

```
cp .env.example .env
docker compose up --build
```

The image runs the migrations and the station import at build time, so the
container is ready as soon as it starts.

Without Docker:

```
cd backend
python3.12 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
python manage.py migrate
python manage.py import_stations
python manage.py runserver
```

## Usage

```
curl "http://127.0.0.1:8000/api/route/?start=New%20York,%20NY&finish=Los%20Angeles,%20CA"
```

`start` and `finish` take `City, ST` or `lat,lng`. The response holds the route
as a GeoJSON LineString, the ordered fuel stops (station, mile marker, price,
gallons, cost), total gallons and total cost.

Open http://127.0.0.1:8000/map/ to see the same result on a map, or
http://127.0.0.1:8000/api/docs/ to try the endpoint in Swagger UI.

| Status | Meaning |
| --- | --- |
| 400 | Unknown city, bad format, or a point outside the USA |
| 422 | No drivable route, or a stretch longer than the vehicle range with no station |
| 502 | The routing service failed or timed out |

## How it works

1. `import_stations` loads the CSV once. The file has no coordinates, so each
   station is placed at its city, looked up in a bundled GeoNames extract.
   Duplicate OPIS IDs keep the lowest price. Canadian rows are skipped.
2. A request resolves both locations locally and makes one call to OSRM for the
   route. Repeat requests are served from cache with no external call.
3. The route is sampled every half mile. Stations within 10 miles of it become
   candidates, each with a mile marker.
4. A greedy pass over the candidates gives the minimum fuel cost: when a cheaper
   station is within range, buy just enough to reach it, otherwise fill up and
   move to the cheapest one in range. A test checks it against a linear
   programming solution on random trips.

Outside the OSRM call, a coast-to-coast request takes about 5 ms.

## Assumptions

- The vehicle starts with a full tank, so the first 500 miles cost nothing. The
  total is fuel bought on the way. Set `VEHICLE_INITIAL_FUEL_FRACTION=0` to
  start empty.
- The vehicle may arrive with an empty tank.
- Stations sit on the route; the detour to reach one is not counted.

## Trade-offs

- Station positions are city centres, so a stop can be a few miles from its
  real location.
- The plan minimises cost only. Where prices rise steadily it can produce
  several small top-ups rather than fewer, larger stops.
- The USA check for `lat,lng` input uses bounding boxes, which also cover
  border areas of Canada and Mexico.
- The public OSRM server is rate limited and has no uptime guarantee. Point
  `OSRM_BASE_URL` at another instance, or set `ROUTING_PROVIDER` to another
  class with the same `route()` method.

## Settings

Environment variables, with defaults (`.env.example` lists them for Docker): `VEHICLE_RANGE_MILES=500`,
`VEHICLE_MPG=10`, `VEHICLE_INITIAL_FUEL_FRACTION=1`, `STATION_CORRIDOR_MILES=10`,
`OSRM_BASE_URL`, `ROUTING_PROVIDER`, `ROUTING_TIMEOUT_SECONDS=15`,
`ROUTE_CACHE_SECONDS=3600`, `FUEL_PRICES_CSV`, `DJANGO_SECRET_KEY`,
`DJANGO_DEBUG`, `DJANGO_ALLOWED_HOSTS`.

## Tests

```
pytest
ruff check . && ruff format --check .
```

`geo/data/us_places.csv.gz` is derived from the GeoNames US dump (CC BY 4.0)
with `python -m scripts.build_gazetteer US.txt`.
