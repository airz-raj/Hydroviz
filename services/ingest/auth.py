import os
import sys
import httpx
from datetime import datetime, timedelta

# Ensure shared modules (and env loader) are available
sys.path.insert(0, '/shared')
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'shared')))
try:
    import env_loader
except ImportError:
    pass

class CDSEAuth:
    def __init__(self):
        self._client_id = None
        self._client_secret = None
        self.token_url = "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token"
        self._access_token = None
        self._expires_at = None

    @property
    def client_id(self) -> str:
        if self._client_id is not None:
            return self._client_id
        return os.getenv("CDSE_CLIENT_ID", "")

    @client_id.setter
    def client_id(self, val: str):
        self._client_id = val

    @property
    def client_secret(self) -> str:
        if self._client_secret is not None:
            return self._client_secret
        return os.getenv("CDSE_CLIENT_SECRET", "")

    @client_secret.setter
    def client_secret(self, val: str):
        self._client_secret = val

    def is_configured(self) -> bool:
        try:
            from shared.env_loader import load_env
            load_env()
        except Exception:
            pass
        cid = self.client_id
        csec = self.client_secret
        if not cid or not csec:
            return False
        if "your_client_id_here" in cid or "your_client_secret_here" in csec:
            return False
        return True

    def get_token(self) -> str:
        if not self.is_configured():
            raise ValueError("CDSE credentials not configured in .env (CDSE_CLIENT_ID / CDSE_CLIENT_SECRET)")
            
        now = datetime.now()
        # Add 60s buffer for expiration
        if self._access_token and self._expires_at and now < (self._expires_at - timedelta(seconds=60)):
            return self._access_token

        data = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret
        }
        
        try:
            response = httpx.post(self.token_url, data=data, timeout=12.0)
            if response.status_code in (401, 403):
                raise PermissionError(
                    f"CDSE Authentication Rejected (HTTP {response.status_code}): "
                    f"Invalid CDSE_CLIENT_ID or CDSE_CLIENT_SECRET. Please check your credentials at dataspace.copernicus.eu."
                )
            response.raise_for_status()
            body = response.json()
            self._access_token = body["access_token"]
            self._expires_at = now + timedelta(seconds=body.get("expires_in", 3600))
            return self._access_token
        except httpx.HTTPStatusError as e:
            raise PermissionError(f"CDSE Authentication Failed (HTTP {e.response.status_code}): {e.response.text[:150]}")
        except httpx.RequestError as e:
            raise ConnectionError(f"CDSE Connection Failed: Unable to reach {self.token_url} ({str(e)})")

# Singleton instance
auth_manager = CDSEAuth()
