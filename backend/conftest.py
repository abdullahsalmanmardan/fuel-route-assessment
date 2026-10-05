import pytest
from django.core.cache import cache

from stations.index import get_station_index


@pytest.fixture(autouse=True)
def fresh_caches():
    cache.clear()
    get_station_index.cache_clear()
