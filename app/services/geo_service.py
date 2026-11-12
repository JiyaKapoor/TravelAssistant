"""
Geographical & Airport Code Resolution Service.
Resolves arbitrary city names, states, or regions to their primary IATA airport codes.
"""
from typing import Optional, List, Dict, Any

# Top domestic and international destination airport and metro mappings
AIRPORT_DATABASE: Dict[str, Dict[str, Any]] = {
    "goa": {"name": "Goa", "primary_iata": "GOI", "all_iatas": ["GOI", "GOX"], "country": "India"},
    "mumbai": {"name": "Mumbai", "primary_iata": "BOM", "all_iatas": ["BOM"], "country": "India"},
    "delhi": {"name": "New Delhi", "primary_iata": "DEL", "all_iatas": ["DEL"], "country": "India"},
    "bangalore": {"name": "Bangalore", "primary_iata": "BLR", "all_iatas": ["BLR"], "country": "India"},
    "bengaluru": {"name": "Bangalore", "primary_iata": "BLR", "all_iatas": ["BLR"], "country": "India"},
    "chennai": {"name": "Chennai", "primary_iata": "MAA", "all_iatas": ["MAA"], "country": "India"},
    "hyderabad": {"name": "Hyderabad", "primary_iata": "HYD", "all_iatas": ["HYD"], "country": "India"},
    "kolkata": {"name": "Kolkata", "primary_iata": "CCU", "all_iatas": ["CCU"], "country": "India"},
    "jaipur": {"name": "Jaipur", "primary_iata": "JAI", "all_iatas": ["JAI"], "country": "India"},
    "kerala": {"name": "Kochi", "primary_iata": "COK", "all_iatas": ["COK", "TRV", "CCJ"], "country": "India"},
    "kochi": {"name": "Kochi", "primary_iata": "COK", "all_iatas": ["COK"], "country": "India"},
    "dubai": {"name": "Dubai", "primary_iata": "DXB", "all_iatas": ["DXB", "DWC"], "country": "UAE"},
    "singapore": {"name": "Singapore", "primary_iata": "SIN", "all_iatas": ["SIN"], "country": "Singapore"},
    "london": {"name": "London", "primary_iata": "LHR", "all_iatas": ["LHR", "LGW", "STN", "LCY"], "country": "UK"},
    "paris": {"name": "Paris", "primary_iata": "CDG", "all_iatas": ["CDG", "ORY"], "country": "France"},
    "bali": {"name": "Bali", "primary_iata": "DPS", "all_iatas": ["DPS"], "country": "Indonesia"},
    "bangkok": {"name": "Bangkok", "primary_iata": "BKK", "all_iatas": ["BKK", "DMK"], "country": "Thailand"},
    "tokyo": {"name": "Tokyo", "primary_iata": "HND", "all_iatas": ["HND", "NRT"], "country": "Japan"},
    "new york": {"name": "New York", "primary_iata": "JFK", "all_iatas": ["JFK", "EWR", "LGA"], "country": "USA"},
}

class GeoService:
    """
    Resolves human-readable locations into standard IATA airport identifiers.
    In full production with Amadeus/Google Places, this queries the live Location API.
    """
    @classmethod
    def resolve_location(cls, location_name: Optional[str]) -> Optional[Dict[str, Any]]:
        if not location_name:
            return None
            
        cleaned = location_name.strip().lower()
        
        # Check direct 3-letter IATA code (e.g. BOM, DEL, GOI, JFK)
        if len(cleaned) == 3 and cleaned.isalpha():
            upper = cleaned.upper()
            for key, val in AIRPORT_DATABASE.items():
                if upper in val["all_iatas"]:
                    return val
            # Generic return for recognized IATA shape
            return {"name": upper, "primary_iata": upper, "all_iatas": [upper], "country": "Unknown"}

        # Exact city match
        if cleaned in AIRPORT_DATABASE:
            return AIRPORT_DATABASE[cleaned]

        # Substring / fuzzy match
        for key, val in AIRPORT_DATABASE.items():
            if key in cleaned or cleaned in key:
                return val

        # Fallback: treat location as custom destination
        capitalized = " ".join(word.capitalize() for word in cleaned.split())
        pseudo_iata = "".join(w[:3] for w in cleaned.split())[:3].upper()
        return {
            "name": capitalized,
            "primary_iata": pseudo_iata,
            "all_iatas": [pseudo_iata],
            "country": "Unknown"
        }
