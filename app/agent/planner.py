import os
import re
import json
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv

from app.models.trip_request import TripConstraints, ParsedTripRequest
from app.services.geo_service import GeoService

load_dotenv()

EXTRACTION_SYSTEM_PROMPT = """You are an expert travel intent parser. 
Extract structured travel constraints from the user request into valid JSON matching the schema below.

JSON Schema:
{
  "destination": "Destination city/country or null if omitted",
  "origin": "Departure city or airport code if explicitly mentioned, or null if omitted",
  "cabin_class": "ECONOMY" | "PREMIUM_ECONOMY" | "BUSINESS" | "FIRST",
  "hotel_preferences": ["only", "amenities", "explicitly", "mentioned", "e.g.", "beach view"],
  "free_cancellation_required": true | false,
  "total_budget": float or null if not mentioned,
  "currency": "INR" | "USD" | "EUR"
}

Strict Rules:
1. DO NOT assume or invent default values. If origin is not mentioned, return "origin": null.
2. If total budget is not mentioned, return "total_budget": null.
3. For hotel_preferences, include ONLY features explicitly requested (e.g. if user didn't mention beach view, return []).
4. For free_cancellation_required, return true ONLY if explicitly mentioned (e.g. "free cancellation", "refundable"), else false.
5. Output ONLY the JSON object.
"""

class TravelPlanner:
    """
    Production-grade Intent & Constraint Extractor.
    Extracts explicit user intent without silent defaults.
    Flags missing critical fields (destination, origin, total_budget) for Human-in-the-Loop Interrupt.
    """

    @classmethod
    def parse_prompt(cls, prompt: str) -> ParsedTripRequest:
        api_key = os.getenv("GEMINI_API_KEY")
        
        # 1. Attempt LLM Structured Extraction if API Key is configured
        if api_key and api_key != "your_gemini_api_key_here":
            try:
                return cls._parse_with_llm(prompt, api_key)
            except Exception:
                pass
        return None
        

    @classmethod
    def _parse_with_llm(cls, prompt: str, api_key: str) -> ParsedTripRequest:
        from google import genai
        client = genai.Client(api_key=api_key)
        
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config={
                "system_instruction": EXTRACTION_SYSTEM_PROMPT,
                "response_mime_type": "application/json"
            }
        )
        
        raw_json = json.loads(response.text)
        
        # Resolve destination & origin with GeoService
        raw_dest = raw_json.get("destination")
        dest_geo = GeoService.resolve_location(raw_dest) if raw_dest else None
        dest_name = dest_geo["name"] if dest_geo else raw_dest
        
        raw_origin = raw_json.get("origin")
        origin_geo = GeoService.resolve_location(raw_origin) if raw_origin else None
        origin_code = origin_geo["primary_iata"] if origin_geo else None

        raw_budget = raw_json.get("total_budget")
        budget = float(raw_budget) if raw_budget is not None else None

        # Determine missing critical fields for Human Interrupt
        missing_fields = []
        if not dest_name:
            missing_fields.append("destination")
        if not origin_code:
            missing_fields.append("origin")
        if budget is None:
            missing_fields.append("total_budget")

        constraints = TripConstraints(
            destination=dest_name,
            origin=origin_code,
            cabin_class=raw_json.get("cabin_class", "ECONOMY"),
            hotel_preferences=raw_json.get("hotel_preferences", []),
            free_cancellation_required=bool(raw_json.get("free_cancellation_required", False)),
            total_budget=budget,
            currency=raw_json.get("currency", "INR")
        )

        return ParsedTripRequest(
            raw_prompt=prompt,
            constraints=constraints,
            missing_fields=missing_fields,
            assumptions_made=[]
        )
