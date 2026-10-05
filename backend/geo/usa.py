from .coordinates import Coordinate

# (south, north, west, east): contiguous states, Alaska, Hawaii
BOUNDS = (
    (24.4, 49.4, -124.9, -66.9),
    (51.2, 71.5, -179.2, -129.9),
    (18.9, 22.3, -160.3, -154.8),
)


def contains(point: Coordinate) -> bool:
    return any(
        south <= point.lat <= north and west <= point.lng <= east
        for south, north, west, east in BOUNDS
    )
