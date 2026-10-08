import pytest
from services.ingest.cache import tile_cache

def test_cache_generate_key():
    key = tile_cache.generate_key("tile123", "s1_post")
    assert key == "tile:tile123:s1_post"
