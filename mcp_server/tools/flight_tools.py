import json
from pathlib import Path
from typing import List, Optional
from app.models.flight import FlightOption

DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "raw_flights.json"

def search_flights(
    origin: str = "BOM",
    destination: str = "GOI",
    cabin_class: str = "ECONOMY",
    max_price: Optional[float] = None
) -> List[FlightOption]:
    """
    Search available flights matching origin, destination, cabin class, and budget.
    """
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        flights_raw = json.load(f)

    results: List[FlightOption] = []
    
    # Destination mapping (GOI or GOX are both Goa)
    dest_keys = [destination.upper()]
    if destination.upper() in ["GOA", "GOI", "GOX"]:
        dest_keys = ["GOI", "GOX", "GOA"]

    for item in flights_raw:
        # Check origin match
        if item["origin"].upper() != origin.upper():
            continue
            
        # Check destination match
        if item["destination"].upper() not in dest_keys:
            continue
            
        # Check cabin class
        if cabin_class and item["cabin_class"].upper() != cabin_class.upper():
            continue
            
        # Check price limit
        if max_price and item["round_trip_price"] > max_price:
            continue

        results.append(FlightOption(
            flight_id=item["flight_id"],
            airline=item["airline"],
            flight_number=item["flight_number"],
            origin=f"{item['origin_city']} ({item['origin']})",
            destination=f"{item['destination_city']} ({item['destination']})",
            departure_time=item["departure_time"],
            arrival_time=item["arrival_time"],
            duration=item["duration"],
            cabin_class=item["cabin_class"],
            stops=item["stops"],
            price=item["round_trip_price"],
            currency=item["currency"],
            is_round_trip=True,
            provider=item["provider"]
        ))
        
    return results

