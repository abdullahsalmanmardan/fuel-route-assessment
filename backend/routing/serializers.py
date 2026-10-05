from rest_framework import serializers

from geo import usa
from geo.coordinates import Coordinate
from geo.gazetteer import find_place


class LocationField(serializers.CharField):
    default_error_messages = {
        "format": 'Use "lat,lng" or "City, ST".',
        "unknown": "No US city found with this name.",
        "outside": "Location must be inside the USA.",
    }

    def to_internal_value(self, data) -> Coordinate:
        head, comma, tail = super().to_internal_value(data).rpartition(",")
        if not comma:
            self.fail("format")
        try:
            point = Coordinate(float(head), float(tail))
        except ValueError:
            return find_place(head, tail) or self.fail("unknown")
        if not usa.contains(point):
            self.fail("outside")
        return point


class RouteQuerySerializer(serializers.Serializer):
    start = LocationField(help_text='"City, ST" or "lat,lng", for example "New York, NY".')
    finish = LocationField(help_text='"City, ST" or "lat,lng", for example "34.05,-118.24".')

    def validate(self, attrs):
        if attrs["start"] == attrs["finish"]:
            raise serializers.ValidationError("Start and finish must be different locations.")
        return attrs


class RoundedFloatField(serializers.FloatField):
    def __init__(self, places: int, **kwargs):
        self.places = places
        super().__init__(**kwargs)

    def to_representation(self, value):
        return round(float(value), self.places)


class CoordinateSerializer(serializers.Serializer):
    lat = serializers.FloatField()
    lng = serializers.FloatField()


class FuelStopSerializer(serializers.Serializer):
    name = serializers.CharField(source="station.name")
    address = serializers.CharField(source="station.address")
    city = serializers.CharField(source="station.city")
    state = serializers.CharField(source="station.state")
    lat = serializers.FloatField(source="station.latitude")
    lng = serializers.FloatField(source="station.longitude")
    mile = RoundedFloatField(1, source="purchase.mile")
    price = RoundedFloatField(3, source="purchase.price")
    gallons = RoundedFloatField(2, source="purchase.gallons")
    cost = RoundedFloatField(2, source="purchase.cost")


class TripPlanSerializer(serializers.Serializer):
    start = CoordinateSerializer()
    finish = CoordinateSerializer()
    distance_miles = RoundedFloatField(1)
    duration_minutes = RoundedFloatField(0)
    total_gallons = RoundedFloatField(2)
    total_cost = RoundedFloatField(2)
    stops = FuelStopSerializer(many=True)
    route = serializers.JSONField(help_text="GeoJSON LineString of the route.")
