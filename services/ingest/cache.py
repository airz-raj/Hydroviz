import redis
import json
import os
from typing import Dict, Any, Optional

class TileCache:
    def __init__(self):
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        self.client = redis.from_url(redis_url)
        
    def generate_key(self, tile_id: str, data_type: str) -> str:
        """
        Generate a cache key for a specific tile and data type.
        Example: tile:12345:s1_post
        """
        return f"tile:{tile_id}:{data_type}"
        
    def mark_ready(self, tile_id: str, data_type: str, metadata: Dict[str, Any]):
        """
        Mark a tile as downloaded and ready in the shared volume.
        """
        key = self.generate_key(tile_id, data_type)
        metadata["status"] = "ready"
        self.client.set(key, json.dumps(metadata))
        
    def get_status(self, tile_id: str, data_type: str) -> Optional[Dict[str, Any]]:
        """
        Get the status of a specific tile.
        """
        key = self.generate_key(tile_id, data_type)
        val = self.client.get(key)
        if val:
            return json.loads(val)
        return None

# Singleton cache client
tile_cache = TileCache()
