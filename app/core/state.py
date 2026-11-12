from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from app.models.trip_request import TripConstraints
from app.models.flight import FlightOption
from app.models.hotel import HotelOption
from app.models.package import TripPackage

class AgentStatus(str, Enum):
    IDLE = "IDLE"
    PARSING = "PARSING"
    AWAITING_HUMAN_INPUT = "AWAITING_HUMAN_INPUT"  # Human Interrupt trigger
    SEARCHING_TOOLS = "SEARCHING_TOOLS"
    EVALUATING_POLICIES = "EVALUATING_POLICIES"
    OPTIMIZING_BUDGET = "OPTIMIZING_BUDGET"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class AgentState(BaseModel):
    session_id: str
    status: AgentStatus = AgentStatus.IDLE
    original_prompt: str
    constraints: Optional[TripConstraints] = None
    
    # Human Interrupt fields
    missing_fields: List[str] = Field(default_factory=list)
    interrupt_question: Optional[str] = None
    interrupt_context: Dict[str, Any] = Field(default_factory=dict)
    
    # Tool Execution outputs
    raw_flights: List[Dict[str, Any]] = Field(default_factory=list)
    raw_hotels: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Verified Candidates
    verified_flights: List[FlightOption] = Field(default_factory=list)
    verified_hotels: List[HotelOption] = Field(default_factory=list)
    
    # Final Output
    packages: List[TripPackage] = Field(default_factory=list)
    final_itinerary: Optional[str] = None
    audit_log: List[str] = Field(default_factory=list)

    def log(self, message: str):
        self.audit_log.append(message)

