from typing import Dict, Any, Tuple, Optional
from app.models.hotel import HotelOption, CancellationPolicyVerification

class InContextEvaluator:
    """
    Performs in-context reasoning on raw hotel room descriptions and cancellation policies.
    Eliminates the need for a Vector DB by directly inspecting the unstructured text
    returned by the MCP tools.
    """
    @staticmethod
    def evaluate_room_view(room_type: str, room_description: str) -> Tuple[bool, str]:
        """
        Inspects room description to verify if it has an authentic beach/sea view.
        Distinguishes between authentic beach views and deceptive pool/inland views.
        """
        full_text = f"{room_type}. {room_description}".lower()

        # Disqualify inland or non-beach views
        disqualifiers = ["pool view", "garden view", "courtyard pool", "lake view", "inland"]
        if any(d in full_text for d in disqualifiers) and not any(p in full_text for p in ["beachfront", "beach view", "arabian sea"]):
            return False, f"Room faces pool/garden/inland ({room_type}). No direct beach view."

        # Verify authentic beach markers
        qualifiers = [
            "beachfront", "facing the ocean", "panoramic views of the arabian sea",
            "full beach view", "sweeping views of candolim beach", "waterfront",
            "sea facing", "sea and bay view"
        ]
        
        for q in qualifiers:
            if q in full_text:
                return True, room_description

        return False, "Could not verify direct beach view from room description."

    @staticmethod
    def evaluate_cancellation_policy(cancellation_text: str) -> CancellationPolicyVerification:
        """
        Inspects cancellation policy terms to verify if 100% free cancellation is guaranteed.
        Rejects non-refundable or penalty rates.
        """
        text_lower = cancellation_text.lower()

        if "non-refundable" in text_lower or "100% will be charged" in text_lower or "no refund" in text_lower:
            return CancellationPolicyVerification(
                is_free_cancellation=False,
                deadline_description="Non-refundable policy. Full charge applies on cancellation.",
                policy_excerpt=cancellation_text,
                rag_confidence=1.0
            )

        if "free cancellation" in text_lower or "free of charge" in text_lower:
            deadline = "Free cancellation before arrival"
            if "72 hours" in text_lower:
                deadline = "Free cancellation up to 72 hours before check-in (100% full refund)"
            elif "48 hours" in text_lower:
                deadline = "Free cancellation up to 48 hours before check-in (100% full refund)"
            elif "24 hours" in text_lower:
                deadline = "Free cancellation up to 24 hours prior to arrival (100% full refund)"

            return CancellationPolicyVerification(
                is_free_cancellation=True,
                deadline_description=deadline,
                policy_excerpt=cancellation_text,
                rag_confidence=1.0
            )

        return CancellationPolicyVerification(
            is_free_cancellation=False,
            deadline_description="Standard cancellation fees may apply.",
            policy_excerpt=cancellation_text,
            rag_confidence=0.7
        )

    @classmethod
    def evaluate_hotel(cls, raw_hotel: Dict[str, Any], nights: int = 3) -> Optional[HotelOption]:
        """
        Evaluates a candidate hotel against beach view and cancellation requirements.
        Returns a validated HotelOption model.
        """
        has_beach_view, beach_excerpt = cls.evaluate_room_view(
            raw_hotel["room_type"],
            raw_hotel["room_description"]
        )
        cancellation_verif = cls.evaluate_cancellation_policy(
            raw_hotel["cancellation_terms"]
        )

        total_price = raw_hotel["price_per_night"] * nights

        return HotelOption(
            hotel_id=raw_hotel["hotel_id"],
            name=raw_hotel["name"],
            area=raw_hotel["area"],
            rating=raw_hotel["star_rating"],
            price_per_night=raw_hotel["price_per_night"],
            nights=nights,
            total_price=total_price,
            currency="INR",
            has_beach_view=has_beach_view,
            beach_view_excerpt=beach_excerpt,
            cancellation_verification=cancellation_verif,
            amenities=raw_hotel["amenities"],
            description=raw_hotel["room_description"]
        )

