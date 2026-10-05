from django.urls import path
from django.views.generic import RedirectView, TemplateView

from .views import RouteView

urlpatterns = [
    path("", RedirectView.as_view(pattern_name="map")),
    path("api/route/", RouteView.as_view(), name="route"),
    path("map/", TemplateView.as_view(template_name="routing/map.html"), name="map"),
]
