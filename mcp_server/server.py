"""
Travel MCP Server: Exposes flight search and hotel inspection tools.
Supports both direct Python execution and Model Context Protocol (MCP) tool exposure.
"""
from typing import List, Dict, Any, Optional
from mcp_server.tools.flight_tools import search_flights
from mcp_server.tools.hotel_tools import search_hotels, get_hotel_details
from app.models.flight import FlightOption

class TravelMCPServer:
    """
    Model Context Protocol server for travel queries.
    Provides tools for flight lookup, hotel catalog discovery, and policy inspection.
    """
    def __init__(self):
        self.tools = {
            "search_flights": self.search_flights,
            "search_hotels": self.search_hotels,
            "get_hotel_details": self.get_hotel_details,
        }

    def search_flights(
        self,
        origin: str = "BOM",
        destination: str = "GOI",
        cabin_class: str = "ECONOMY",
        max_price: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """Search flight routes matching origin, destination, cabin class, and budget."""
        results = search_flights(
            origin=origin,
            destination=destination,
            cabin_class=cabin_class,
            max_price=max_price
        )
        return [f.model_dump() for f in results]

    def search_hotels(
        self,
        destination: str = "Goa",
        nights: int = 3,
        max_total_budget: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """Search hotel candidates for a given destination and stay duration."""
        return search_hotels(
            destination=destination,
            nights=nights,
            max_total_budget=max_total_budget
        )

    def get_hotel_details(self, hotel_id: str) -> Optional[Dict[str, Any]]:
        """Fetch complete room description and legal cancellation policy text for a hotel."""
        return get_hotel_details(hotel_id=hotel_id)

    def list_tools(self) -> List[Dict[str, Any]]:
        """Returns standard MCP tool metadata."""
        return [
            {
                "name": "search_flights",
                "description": "Find flight options by origin, destination, cabin class (e.g. ECONOMY), and price.",
                "parameters": {
                    "origin": "Airport code (e.g., BOM)",
                    "destination": "Airport code (e.g., GOI/GOX)",
                    "cabin_class": "ECONOMY or BUSINESS",
                    "max_price": "Maximum flight price"
                }
            },
            {
                "name": "search_hotels",
                "description": "Find available hotels for a destination with price calculated for total nights.",
                "parameters": {
                    "destination": "City name (e.g., Goa)",
                    "nights": "Number of nights (default: 3)",
                    "max_total_budget": "Maximum total hotel cost"
                }
            },
            {
                "name": "get_hotel_details",
                "description": "Retrieve full room view description and cancellation policy fine print for verification.",
                "parameters": {
                    "hotel_id": "Hotel ID, e.g. HOTEL_001"
                }
            }
        ]

# Global singleton server instance
mcp_server = TravelMCPServer()

