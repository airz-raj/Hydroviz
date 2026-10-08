import os
import httpx
from datetime import datetime, timedelta

class CDSEAuth:
    def __init__(self):
        self.client_id = os.getenv("CDSE_CLIENT_ID")
        self.client_secret = os.getenv("CDSE_CLIENT_SECRET")
        self.token_url = "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token"
        self._access_token = None
        self._expires_at = None

    def get_token(self) -> str:
        if not self.client_id or not self.client_secret:
            raise ValueError("CDSE_CLIENT_ID and CDSE_CLIENT_SECRET must be set")
            
        now = datetime.now()
        # Add 60s buffer for expiration
        if self._access_token and self._expires_at and now < (self._expires_at - timedelta(seconds=60)):
            return self._access_token

        data = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret
        }
        
        response = httpx.post(self.token_url, data=data)
        response.raise_for_status()
        
        body = response.json()
        self._access_token = body["access_token"]
        self._expires_at = now + timedelta(seconds=body["expires_in"])
        
        return self._access_token

# Singleton instance
auth_manager = CDSEAuth()
