from pydantic import BaseModel, Field
from typing import List, Optional

class HotelSearchQuery(BaseModel):
    destination: str = Field(description="Destination city or area, e.g. 'Goa'")
    check_in_date: Optional[str] = Field(default=None, description="Check-in date YYYY-MM-DD")
    check_out_date: Optional[str] = Field(default=None, description="Check-out date YYYY-MM-DD")
    nights: int = Field(default=3, description="Number of nights")
    requires_beach_view: bool = Field(default=True, description="Strict requirement for beach/ocean view")
    requires_free_cancellation: bool = Field(default=True, description="Strict requirement for free cancellation")
    max_price: Optional[float] = Field(default=None, description="Maximum total price for stay")

class CancellationPolicyVerification(BaseModel):
    is_free_cancellation: bool
    deadline_description: str
    policy_excerpt: str
    rag_confidence: float = 0.95

class HotelOption(BaseModel):
    hotel_id: str
    name: str
    area: str
    rating: float
    price_per_night: float
    nights: int = 3
    total_price: float
    currency: str = "INR"
    has_beach_view: bool
    beach_view_excerpt: str
    cancellation_verification: CancellationPolicyVerification
    amenities: List[str]
    description: str

