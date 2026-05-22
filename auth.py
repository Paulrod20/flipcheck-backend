import httpx
import base64
import os
import time

EBAY_APP_ID = os.getenv("EBAY_APP_ID")
EBAY_CERT_ID = os.getenv("EBAY_CERT_ID")

_token_cache: dict = {}

async def get_ebay_access_token():
    if _token_cache.get("token") and time.time() < _token_cache.get("expires_at", 0):
        return _token_cache["token"]

    credentials = f"{EBAY_APP_ID}:{EBAY_CERT_ID}"
    encoded_credentials = base64.b64encode(credentials.encode()).decode()
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.ebay.com/identity/v1/oauth2/token",
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "Authorization": f"Basic {encoded_credentials}"
            },
            data={"grant_type": "client_credentials", "scope": "https://api.ebay.com/oauth/api_scope"}
        )
        response.raise_for_status()
        token_data = response.json()
        _token_cache["token"] = token_data["access_token"]
        _token_cache["expires_at"] = time.time() + token_data.get("expires_in", 7200) - 60
        return _token_cache["token"]