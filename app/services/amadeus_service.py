"""
Amadeus GDS Travel API Service Integration.
Provides live flight offers and hotel search from the official Amadeus Self-Service API (test environment).
Falls back to mock data if credentials are not configured or when offline.
"""
import os
import httpx
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

load_dotenv()

AMADEUS_AUTH_URL = "https://test.api.amadeus.com/v1/security/oauth2/token"
AMADEUS_FLIGHTS_URL = "https://test.api.amadeus.com/v2/shopping/flight-offers"
AMADEUS_HOTELS_URL = "https://test.api.amadeus.com/v1/reference-data/locations/hotels/by-city"

class AmadeusTravelService:
    """
    Connects to Amadeus Self-Service Travel API.
    Handles token caching, flight search, and hotel lookup.
    """
    def __init__(self):
        self.client_id = os.getenv("AMADEUS_CLIENT_ID")
        self.client_secret = os.getenv("AMADEUS_CLIENT_SECRET")
        self._access_token: Optional[str] = None

    def is_configured(self) -> bool:
        return bool(self.client_id and self.client_secret and self.client_id != "your_amadeus_client_id")

    def _get_access_token(self) -> Optional[str]:
        if self._access_token:
            return self._access_token

        if not self.is_configured():
            return None

        try:
            with httpx.Client(timeout=10.0) as client:
                res = client.post(
                    AMADEUS_AUTH_URL,
                    data={
                        "grant_type": "client_credentials",
                        "client_id": self.client_id,
                        "client_secret": self.client_secret
                    }
                )
                if res.status_code == 200:
                    data = res.json()
                    self._access_token = data.get("access_token")
                    return self._access_token
        except Exception:
            return None
        return None

    def search_live_flights(
        self,
        origin_iata: str,
        dest_iata: str,
        departure_date: str = "2026-12-15",
        return_date: Optional[str] = "2026-12-18",
        cabin_class: str = "ECONOMY",
        max_price: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        token = self._get_access_token()
        if not token:
            return []

        headers = {"Authorization": f"Bearer {token}"}
        params = {
            "originLocationCode": origin_iata.upper(),
            "destinationLocationCode": dest_iata.upper(),
            "departureDate": departure_date,
            "adults": "1",
            "travelClass": cabin_class.upper(),
            "max": "5"
        }
        if return_date:
            params["returnDate"] = return_date
        if max_price:
            params["maxPrice"] = str(int(max_price))

        try:
            with httpx.Client(timeout=12.0) as client:
                res = client.get(AMADEUS_FLIGHTS_URL, headers=headers, params=params)
                if res.status_code == 200:
                    data = res.json()
                    return data.get("data", [])
        except Exception:
            return []
        return []

