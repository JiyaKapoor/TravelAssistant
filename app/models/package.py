from pydantic import BaseModel, Field
from typing import List
from app.models.flight import FlightOption
from app.models.hotel import HotelOption

class TripPackage(BaseModel):
    package_id: str
    title: str
    flight: FlightOption
    hotel: HotelOption
    flight_cost: float
    hotel_cost: float
    total_cost: float
    budget_limit: float
    savings: float
    meets_all_constraints: bool = True
    cancellation_highlight: str
    beach_view_highlight: str
    why_recommended: str

class ItinerarySummary(BaseModel):
    query: str
    total_budget: float
    currency: str = "INR"
    packages: List[TripPackage]
    best_package: TripPackage
    markdown_report: str

