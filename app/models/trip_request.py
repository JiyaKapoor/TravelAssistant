from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date

class TripConstraints(BaseModel):
    destination: str = Field(default=None, description="Target destination city/region, e.g. 'Goa'")
    origin: str= Field(default=None, description="Departure airport code or city, e.g. 'BOM'")
    start_date: date= Field(default=None, description="Trip start date")
    end_date: date = Field(default=None, description="Trip return date")
    nights: int = Field(default=None, description="Number of nights for stay")
    passengers: int = Field(default=1, description="Number of passengers")
    
    # Flight Preferences
    cabin_class: Optional[str] = Field(default="ECONOMY", description="Cabin class: ECONOMY, PREMIUM_ECONOMY, BUSINESS, FIRST")
    
    # Hotel Preferences - Populated ONLY if parsed from the prompt
    hotel_preferences: List[str] = Field(
        default_factory=list,
        description="Explicit user hotel preferences (e.g. ['beach view']). Empty if not mentioned."
    )
    free_cancellation_required: bool = Field(
        default=False,
        description="Strict requirement for free cancellation. True ONLY if explicitly requested."
    )
    
    # Budget Constraints - No silent default! Must be provided or requested via Human Interrupt
    total_budget: Optional[float] = Field(
        default=None,
        description="Total budget cap for flight + hotel. None if omitted in prompt."
    )
    currency: str = Field(default="INR", description="Currency symbol or 3-letter code")

class ParsedTripRequest(BaseModel):
    raw_prompt: str
    constraints: TripConstraints
    missing_fields: List[str] = Field(
        default_factory=list,
        description="Critical fields (e.g. ['origin', 'total_budget']) requiring Human Interrupt"
    )
    assumptions_made: List[str] = Field(default_factory=list)
