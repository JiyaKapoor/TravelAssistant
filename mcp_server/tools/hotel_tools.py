import json
from pathlib import Path
from typing import List, Dict, Any, Optional

DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "raw_hotels.json"

def _load_hotels() -> List[Dict[str, Any]]:
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def search_hotels(
    destination: str = "Goa",
    nights: int = 3,
    max_total_budget: Optional[float] = None
) -> List[Dict[str, Any]]:
    """
    Search available hotels for a destination.
    Returns summaries of matching hotels with prices calculated for the total stay.
    """
    hotels = _load_hotels()
    candidates = []
    
    dest_lower = destination.lower()
    for h in hotels:
        # Match destination
        if dest_lower not in h["area"].lower() and dest_lower not in "goa":
            continue
            
        total_price = h["price_per_night"] * nights
        if max_total_budget and total_price > max_total_budget:
            continue
            
        candidates.append({
            "hotel_id": h["hotel_id"],
            "name": h["name"],
            "area": h["area"],
            "star_rating": h["star_rating"],
            "price_per_night": h["price_per_night"],
            "nights": nights,
            "total_price": total_price,
            "room_type": h["room_type"],
            "amenities": h["amenities"]
        })
        
    return candidates

def get_hotel_details(hotel_id: str) -> Optional[Dict[str, Any]]:
    """
    Fetch comprehensive unstructured hotel details:
    - Exact room view description
    - Complete cancellation policy terms and conditions
    - Full list of amenities and property tags
    """
    hotels = _load_hotels()
    for h in hotels:
        if h["hotel_id"].upper() == hotel_id.upper():
            return h
    return None

