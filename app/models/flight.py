from pydantic import BaseModel, Field
from typing import Optional

class FlightSearchQuery(BaseModel):
    origin: str = Field(description="Departure airport code, e.g. 'BOM'")
    destination: str = Field(description="Arrival airport code, e.g. 'GOI' or 'GOX'")
    departure_date: Optional[str] = Field(default=None, description="Departure date YYYY-MM-DD")
    return_date: Optional[str] = Field(default=None, description="Return date YYYY-MM-DD")
    cabin_class: str = Field(default="ECONOMY", description="Cabin class: ECONOMY, BUSINESS")
    max_price: Optional[float] = Field(default=None, description="Max acceptable flight price")

class FlightOption(BaseModel):
    flight_id: str
    airline: str
    flight_number: str
    origin: str
    destination: str
    departure_time: str
    arrival_time: str
    duration: str
    cabin_class: str = "ECONOMY"
    stops: int = 0
    price: float
    currency: str = "INR"
    is_round_trip: bool = True
    provider: str = "Amadeus / IndiGo / Air India"

