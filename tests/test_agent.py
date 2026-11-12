"""
Unit and Integration Tests for Agentic Travel Assistant.
"""
import pytest
from app.agent.orchestrator import TravelAgent
from app.agent.planner import TravelPlanner
from app.agent.evaluator import InContextEvaluator
from app.agent.budget_optimizer import BudgetOptimizer
from app.core.state import AgentStatus
from app.models.flight import FlightOption
from app.models.hotel import HotelOption, CancellationPolicyVerification

def test_planner_parsing():
    prompt = "Plan a trip to Goa from Delhi including Economy flights and hotels with a Beach view that offer a free cancellation under 25000"
    parsed = TravelPlanner.parse_prompt(prompt)
    c = parsed.constraints

    assert c.destination == "Goa"
    assert c.origin == "DEL"
    assert c.cabin_class == "ECONOMY"
    assert c.total_budget == 25000.0
    assert c.free_cancellation_required is True
    assert "beach view" in c.hotel_preferences

def test_generalized_destinations_without_hardcoding():
    # Test Paris with London origin and EUR budget
    prompt_paris = "Plan a trip to Paris from London with budget of 2000 EUR"
    p1 = TravelPlanner.parse_prompt(prompt_paris)
    assert p1.constraints.destination == "Paris"
    assert p1.constraints.origin == "LHR"
    assert p1.constraints.total_budget == 2000.0
    assert p1.constraints.currency == "EUR"

    # Test Tokyo with Business Class and Lakh budget
    prompt_tokyo = "Fly to Tokyo in business class under 1.5 lakh"
    p2 = TravelPlanner.parse_prompt(prompt_tokyo)
    assert p2.constraints.destination == "Tokyo"
    assert "origin" in p2.missing_fields  # Origin was omitted, triggers interrupt
    assert p2.constraints.cabin_class == "BUSINESS"
    assert p2.constraints.total_budget == 150000.0

    # Test Bali with USD budget
    prompt_bali = "Vacation in Bali under $1,800"
    p3 = TravelPlanner.parse_prompt(prompt_bali)
    assert p3.constraints.destination == "Bali"
    assert p3.constraints.total_budget == 1800.0
    assert p3.constraints.currency == "USD"


def test_human_interrupt_triggered_when_origin_missing():
    agent = TravelAgent()
    prompt = "Plan a trip to Goa including Economy flights and hotels with a Beach view that offer a free cancellation under 30000"
    state = agent.run(prompt)

    # Must halt at Human Interrupt gate
    assert state.status == AgentStatus.AWAITING_HUMAN_INPUT
    assert "origin" in state.missing_fields
    assert state.interrupt_question is not None
    assert "departure city" in state.interrupt_question.lower()

def test_resume_after_human_interrupt():
    agent = TravelAgent()
    prompt = "Plan a trip to Goa including Economy flights and hotels with a Beach view that offer a free cancellation under 30000"
    state = agent.run(prompt)

    assert state.status == AgentStatus.AWAITING_HUMAN_INPUT

    # Resume with human input
    resumed_state = agent.resume_with_human_input(
        session_id=state.session_id,
        user_answer="Mumbai"
    )

    assert resumed_state.status == AgentStatus.COMPLETED
    assert resumed_state.constraints.origin == "BOM"
    assert len(resumed_state.packages) > 0
    assert resumed_state.final_itinerary is not None

    # Verify best package cost <= 30000
    best = resumed_state.packages[0]
    assert best.total_cost <= 30000.0
    assert best.hotel.has_beach_view is True
    assert best.hotel.cancellation_verification.is_free_cancellation is True

def test_human_interrupt_when_budget_missing():
    agent = TravelAgent()
    prompt = "Plan a trip to Goa from Mumbai with a beach view hotel"
    state = agent.run(prompt)

    # Must halt because budget was omitted
    assert state.status == AgentStatus.AWAITING_HUMAN_INPUT
    assert "total_budget" in state.missing_fields
    assert state.interrupt_question is not None
    assert "target budget" in state.interrupt_question.lower()

def test_human_interrupt_when_both_origin_and_budget_missing():
    agent = TravelAgent()
    prompt = "Plan a trip to Goa with a beach view hotel"
    state = agent.run(prompt)

    # Must halt because both origin and budget are omitted
    assert state.status == AgentStatus.AWAITING_HUMAN_INPUT
    assert "origin" in state.missing_fields
    assert "total_budget" in state.missing_fields
    assert "1. Which departure city" in state.interrupt_question

def test_optional_preferences_and_cancellation():
    prompt = "Plan a trip to Goa from Mumbai under 25000"
    parsed = TravelPlanner.parse_prompt(prompt)
    c = parsed.constraints

    assert c.destination == "Goa"
    assert c.origin == "BOM"
    assert c.total_budget == 25000.0
    assert c.hotel_preferences == []  # Not requested!
    assert c.free_cancellation_required is False  # Not requested!

def test_evaluator_rejects_pool_view():
    has_beach, excerpt = InContextEvaluator.evaluate_room_view(
        room_type="Deluxe Pool View Room",
        room_description="Courtyard swimming pool and tropical gardens 2.5 km inland from beach."
    )
    assert has_beach is False

def test_evaluator_rejects_non_refundable():
    verif = InContextEvaluator.evaluate_cancellation_policy(
        "NON-REFUNDABLE SPECIAL PROMO: Cancellation fee is 100% of total reservation."
    )
    assert verif.is_free_cancellation is False

def test_budget_optimizer_strict_filter():
    flight = FlightOption(
        flight_id="F1",
        airline="TestAir",
        flight_number="TA-101",
        origin="BOM",
        destination="GOI",
        departure_time="10:00",
        arrival_time="11:00",
        duration="1h",
        price=10000.0
    )
    # Expensive hotel that breaches 30k combined
    hotel_over = HotelOption(
        hotel_id="H_EXP",
        name="Expensive Resort",
        area="Goa",
        rating=4.5,
        price_per_night=8000.0,
        nights=3,
        total_price=24000.0,  # 10,000 + 24,000 = 34,000 > 30,000
        has_beach_view=True,
        beach_view_excerpt="Direct ocean view",
        cancellation_verification=CancellationPolicyVerification(
            is_free_cancellation=True,
            deadline_description="Free cancel",
            policy_excerpt="Free cancel"
        ),
        amenities=["Beach"],
        description="Beach resort"
    )

    packages = BudgetOptimizer.build_and_rank_packages(
        flights=[flight],
        hotels=[hotel_over],
        total_budget=30000.0
    )

    # Must be filtered out because 34,000 > 30,000
    assert len(packages) == 0

if __name__ == "__main__":
    test_planner_parsing()
    test_generalized_destinations_without_hardcoding()
    test_human_interrupt_triggered_when_origin_missing()
    test_human_interrupt_when_budget_missing()
    test_human_interrupt_when_both_origin_and_budget_missing()
    test_optional_preferences_and_cancellation()
    test_resume_after_human_interrupt()
    test_evaluator_rejects_pool_view()
    test_evaluator_rejects_non_refundable()
    test_budget_optimizer_strict_filter()
    print("✅ All unit and integration tests passed successfully!")

