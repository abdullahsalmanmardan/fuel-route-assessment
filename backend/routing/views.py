from django.conf import settings
from django.core.cache import cache
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework.response import Response
from rest_framework.views import APIView

from geo.coordinates import Coordinate

from .serializers import RouteQuerySerializer, TripPlanSerializer
from .services.planner import plan_trip


def cache_key(start: Coordinate, finish: Coordinate) -> str:
    return f"route:{start.lat:.3f},{start.lng:.3f}:{finish.lat:.3f},{finish.lng:.3f}"


class RouteView(APIView):
    @extend_schema(
        summary="Plan a route with the cheapest fuel stops",
        parameters=[RouteQuerySerializer],
        responses={
            200: TripPlanSerializer,
            400: OpenApiResponse(description="Unknown city, bad format, or outside the USA."),
            422: OpenApiResponse(description="No drivable route, or no station within range."),
            502: OpenApiResponse(description="The routing service failed or timed out."),
        },
    )
    def get(self, request):
        query = RouteQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        start, finish = query.validated_data["start"], query.validated_data["finish"]

        payload = cache.get_or_set(
            cache_key(start, finish),
            lambda: TripPlanSerializer(plan_trip(start, finish)).data,
            settings.ROUTE_CACHE_SECONDS,
        )
        return Response(payload)
