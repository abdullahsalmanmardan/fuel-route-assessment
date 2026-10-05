import logging

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler

from .services.optimizer import UnreachableGap
from .services.providers import NoRouteFound, RoutingUnavailable

logger = logging.getLogger(__name__)

STATUS_CODES = {
    RoutingUnavailable: status.HTTP_502_BAD_GATEWAY,
    NoRouteFound: status.HTTP_422_UNPROCESSABLE_ENTITY,
    UnreachableGap: status.HTTP_422_UNPROCESSABLE_ENTITY,
}


def exception_handler(exc, context):
    code = STATUS_CODES.get(type(exc))
    if code is None:
        return drf_exception_handler(exc, context)
    if code >= status.HTTP_500_INTERNAL_SERVER_ERROR:
        logger.warning("Routing request failed", exc_info=exc)
    return Response({"detail": str(exc)}, status=code)
