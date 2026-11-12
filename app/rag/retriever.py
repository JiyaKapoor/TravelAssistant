from typing import Tuple, Dict, Any
from app.rag.vector_store import TravelVectorStore
from app.models.hotel import CancellationPolicyVerification

class HotelSemanticRetriever:
    """
    Semantic Retriever for Agentic RAG verification:
    1. Verifies if room actually has a beach/sea view.
    2. Parses and verifies free cancellation terms.
    """
    def __init__(self, vector_store: TravelVectorStore = None):
        self.vector_store = vector_store or TravelVectorStore()

    def verify_beach_view(self, hotel_id: str) -> Tuple[bool, str, float]:
        """
        Queries room view descriptions using semantic similarity.
        Returns: (has_beach_view, excerpt, confidence_score)
        """
        results = self.vector_store.query_semantic(
            query="direct beach ocean sea panoramic waves beachfront view balcony",
            doc_type="room_view",
            hotel_id=hotel_id,
            top_k=1
        )
        if not results:
            return False, "No room view data found.", 0.0

        top = results[0]
        text_lower = top["text"].lower()

        # Reject explicitly inland / non-beach views
        if any(neg in text_lower for neg in ["inland", "lake view", "pool view", "garden view"]) and not any(pos in text_lower for pos in ["beachfront", "beach view", "sea facing", "ocean"]):
            return False, top["text"], top["score"]

        # Check positive beach markers
        has_beach = any(marker in text_lower for marker in [
            "beachfront", "sea facing", "ocean cottage", "panoramic views of the arabian sea",
            "full beach view", "sweeping views of candolim beach", "waterfront", "sea and bay view"
        ])
        
        return has_beach, top["text"], top["score"]

    def verify_free_cancellation(self, hotel_id: str) -> CancellationPolicyVerification:
        """
        Queries and evaluates cancellation policy chunks.
        Returns: CancellationPolicyVerification model with verified status and excerpt.
        """
        results = self.vector_store.query_semantic(
            query="free cancellation 100% full refund zero penalty",
            doc_type="cancellation_policy",
            hotel_id=hotel_id,
            top_k=1
        )
        if not results:
            return CancellationPolicyVerification(
                is_free_cancellation=False,
                deadline_description="No policy found",
                policy_excerpt="Unavailable",
                rag_confidence=0.0
            )

        top = results[0]
        text = top["text"]
        text_lower = text.lower()

        # Check for explicit non-refundable keywords
        if "non-refundable" in text_lower or "100% will be charged" in text_lower:
            return CancellationPolicyVerification(
                is_free_cancellation=False,
                deadline_description="Non-refundable booking",
                policy_excerpt=text,
                rag_confidence=0.98
            )

        # Check for free cancellation confirmation
        is_free = "free cancellation" in text_lower or "free of charge" in text_lower
        
        # Extract deadline description
        deadline = "Free cancellation before check-in"
        if "72 hours" in text_lower:
            deadline = "Free cancellation up to 72 hours before arrival (100% refund)"
        elif "48 hours" in text_lower:
            deadline = "Free cancellation up to 48 hours before check-in (100% refund)"
        elif "24 hours" in text_lower:
            deadline = "Free cancellation up to 24 hours prior to check-in"

        return CancellationPolicyVerification(
            is_free_cancellation=is_free,
            deadline_description=deadline,
            policy_excerpt=text,
            rag_confidence=0.95
        )

