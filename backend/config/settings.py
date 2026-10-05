import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


def env(name: str, default: str) -> str:
    return os.environ.get(name, default)


SECRET_KEY = env("DJANGO_SECRET_KEY", "dev-only-not-for-production")
DEBUG = env("DJANGO_DEBUG", "false").lower() == "true"
ALLOWED_HOSTS = env("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1,0.0.0.0").split(",")

INSTALLED_APPS = [
    "rest_framework",
    "drf_spectacular",
    "stations",
    "routing",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.middleware.common.CommonMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "APP_DIRS": True,
    }
]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    }
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
USE_TZ = True

# OpenStreetMap tiles are refused when the browser sends no Referer.
SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"

REST_FRAMEWORK = {
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
    "DEFAULT_AUTHENTICATION_CLASSES": [],
    "UNAUTHENTICATED_USER": None,
    "EXCEPTION_HANDLER": "routing.errors.exception_handler",
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

SPECTACULAR_SETTINGS = {
    "TITLE": "Fuel route planner",
    "DESCRIPTION": "Plans a drive between two US locations with the cheapest fuel stops.",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
}

FUEL_PRICES_CSV = Path(
    env("FUEL_PRICES_CSV", str(BASE_DIR.parent / "documents" / "fuel-prices-for-be-assessment.csv"))
)

VEHICLE_RANGE_MILES = float(env("VEHICLE_RANGE_MILES", "500"))
VEHICLE_MPG = float(env("VEHICLE_MPG", "10"))
VEHICLE_INITIAL_FUEL_FRACTION = float(env("VEHICLE_INITIAL_FUEL_FRACTION", "1"))
STATION_CORRIDOR_MILES = float(env("STATION_CORRIDOR_MILES", "10"))

ROUTING_PROVIDER = env("ROUTING_PROVIDER", "routing.services.providers.OSRMProvider")
OSRM_BASE_URL = env("OSRM_BASE_URL", "https://router.project-osrm.org")
ROUTING_TIMEOUT_SECONDS = float(env("ROUTING_TIMEOUT_SECONDS", "15"))
ROUTE_CACHE_SECONDS = int(env("ROUTE_CACHE_SECONDS", "3600"))
