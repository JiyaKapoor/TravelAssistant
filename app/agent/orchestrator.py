import uuid
import re
from typing import Dict, Any, Optional, List
from app.core.state import AgentState, AgentStatus
from app.agent.planner import TravelPlanner
from app.agent.evaluator import InContextEvaluator
from app.agent.budget_optimizer import BudgetOptimizer
from app.agent.synthesizer import ItinerarySynthesizer
from app.services.geo_service import GeoService
from mcp_server.server import mcp_server

class TravelAgent:
    """
    Goal-oriented Agentic Travel Assistant with Human-in-the-Loop Interrupt.
    
    Workflow:
    1. Parse Prompt -> Extract structured constraints without assuming silent defaults.
    2. Human Interrupt Gate -> If ANY critical info (destination, origin, total_budget, nights)
       is missing, pause and ask targeted clarification questions.
    3. Tool Execution via MCP -> Concurrently search flights and candidate hotels.
    4. In-Context Evaluation -> Inspect raw hotel room descriptions and cancellation clauses
       strictly based on user preferences.
    5. Budget Optimization -> Validate flight + hotel <= budget and rank packages.
    6. Synthesis -> Generate final verified itinerary report.
    """
    def __init__(self):
        self.sessions: Dict[str, AgentState] = {}

    def run(self, prompt: str, session_id: Optional[str] = None) -> AgentState:
        session_id = session_id or str(uuid.uuid4())[:8]
        state = AgentState(session_id=session_id, original_prompt=prompt)
        self.sessions[session_id] = state

        state.log(f"[Agent] Received prompt: '{prompt}'")
        state.status = AgentStatus.PARSING

        # 1. Parse prompt into constraints without synthetic defaults
        parsed = TravelPlanner.parse_prompt(prompt)
        state.constraints = parsed.constraints
        c = parsed.constraints
        
        budget_str = f"₹{c.total_budget:,.0f}" if c.total_budget else "Not specified"
        state.log(f"[Planner] Parsed destination='{c.destination}', origin='{c.origin}', budget={budget_str}, preferences={c.hotel_preferences}, free_cancellation={c.free_cancellation_required}")

        # 2. HUMAN INTERRUPT GATE: Check for missing critical fields
        missing = parsed.missing_fields
        if missing:
            state.status = AgentStatus.AWAITING_HUMAN_INPUT
            state.missing_fields = missing
            state.interrupt_question = self._build_interrupt_question(c.destination, missing)
            state.log(f"[Interrupt] Triggered Human Interrupt for missing fields: {missing}")
            return state

        return self._execute_agentic_flow(state)

    def _build_interrupt_question(self, destination: Optional[str], missing_fields: List[str]) -> str:
        """Constructs friendly, targeted human-in-the-loop clarification questions."""
        dest_display = destination or "your destination"
        
        if "origin" in missing_fields and "total_budget" in missing_fields:
            return (
                f"✈️ I'd love to help plan your trip to {dest_display}! "
                f"To find the best flights and accommodations, could you please share:\n"
                f"1. Which departure city or airport will you be flying from?\n"
                f"2. What is your target total budget for flights and hotel?"
            )
        elif "origin" in missing_fields:
            return (
                f"✈️ Which departure city or airport will you be flying from to {dest_display}? "
                f"(e.g., Mumbai / BOM, Delhi / DEL, Bangalore / BLR)"
            )
        elif "total_budget" in missing_fields:
            return (
                f"💰 What is your maximum target budget for this trip to {dest_display}? "
                f"(e.g., under ₹30,000, 25k, $1,500)"
            )
        elif "destination" in missing_fields:
            return "🌍 Where would you like to travel to? (e.g., Goa, Paris, Bali, Tokyo)"
            
        return "Could you please provide the missing travel details to continue?"

    def resume_with_human_input(self, session_id: str, user_answer: str) -> AgentState:
        """
        Resumes agent execution after human provides missing critical information.
        """
        state = self.sessions.get(session_id)
        if not state:
            raise ValueError(f"Session {session_id} not found.")

        state.log(f"[Human Input] User responded: '{user_answer}'")
        c = state.constraints

        # 1. Resolve Origin if it was missing
        if "origin" in state.missing_fields:
            # Check for city names or airport codes
            matched_geo = GeoService.resolve_location(user_answer)
            if matched_geo and matched_geo.get("primary_iata"):
                c.origin = matched_geo["primary_iata"]
                state.missing_fields.remove("origin")
                state.log(f"[Agent] Origin resolved to '{c.origin}'.")

        # 2. Resolve Budget if it was missing
        if "total_budget" in state.missing_fields:
            budget_match = re.search(r"(?:[₹$€£]|rs\.?|inr|usd)?\s*([0-9]+(?:,[0-9]+)*(?:\.[0-9]+)?)\s*(k|thousand|lakh|m)?", user_answer, re.IGNORECASE)
            if budget_match:
                amt = float(budget_match.group(1).replace(",", ""))
                multiplier = (budget_match.group(2) or "").lower()
                if multiplier in ["k", "thousand"]:
                    amt *= 1000
                elif multiplier == "lakh":
                    amt *= 100000
                elif multiplier == "m":
                    amt *= 1000000
                c.total_budget = amt
                state.missing_fields.remove("total_budget")
                state.log(f"[Agent] Total budget resolved to ₹{c.total_budget:,.0f}.")

        # 3. Check if anything is still missing
        if state.missing_fields:
            state.status = AgentStatus.AWAITING_HUMAN_INPUT
            state.interrupt_question = self._build_interrupt_question(c.destination, state.missing_fields)
            state.log(f"[Interrupt] Still awaiting: {state.missing_fields}")
            return state

        state.interrupt_question = None
        state.log("[Agent] All critical fields resolved. Resuming workflow...")
        return self._execute_agentic_flow(state)

    def _execute_agentic_flow(self, state: AgentState) -> AgentState:
        c = state.constraints
        state.status = AgentStatus.SEARCHING_TOOLS
        state.log(f"[Tools] Calling MCP tools: search_flights(origin='{c.origin}', dest='{c.destination}') and search_hotels(dest='{c.destination}')")

        # 3. Tool Calls via MCP Server
        raw_flights = mcp_server.search_flights(
            origin=c.origin,
            destination=c.destination,
            cabin_class=c.cabin_class,
            max_price=c.total_budget
        )
        raw_hotels = mcp_server.search_hotels(
            destination=c.destination,
            nights=c.nights,
            max_total_budget=c.total_budget
        )

        state.raw_flights = raw_flights
        state.raw_hotels = raw_hotels
        state.log(f"[Tools] MCP returned {len(raw_flights)} flight options and {len(raw_hotels)} candidate hotels.")

        # 4. In-Context Evaluation & Inspection based on USER'S ACTUAL CONSTRAINTS
        state.status = AgentStatus.EVALUATING_POLICIES
        state.log("[Evaluator] Inspecting raw hotel room view descriptions and cancellation terms...")

        evaluated_hotels = []
        for h in raw_hotels:
            full_details = mcp_server.get_hotel_details(h["hotel_id"])
            if not full_details:
                continue

            evaluated_hotel = InContextEvaluator.evaluate_hotel(full_details, nights=c.nights)
            evaluated_hotels.append(evaluated_hotel)

        state.verified_hotels = evaluated_hotels

        from app.models.flight import FlightOption
        flight_models = [FlightOption(**f) for f in raw_flights]
        state.verified_flights = flight_models

        # 5. Budget Optimization: Enforce constraints ONLY IF requested
        state.status = AgentStatus.OPTIMIZING_BUDGET
        require_beach = "beach view" in c.hotel_preferences
        require_free_cancel = c.free_cancellation_required

        state.log(f"[Optimizer] Enforcing budget <= ₹{c.total_budget:,.0f} | Beach View filter: {require_beach} | Free Cancellation filter: {require_free_cancel}")

        valid_packages = BudgetOptimizer.build_and_rank_packages(
            flights=flight_models,
            hotels=evaluated_hotels,
            total_budget=c.total_budget,
            require_beach_view=require_beach,
            require_free_cancellation=require_free_cancel
        )

        state.packages = valid_packages
        state.log(f"[Optimizer] Found {len(valid_packages)} qualifying packages matching user constraints under budget.")

        # 6. Synthesis
        state.status = AgentStatus.COMPLETED
        report = ItinerarySynthesizer.generate_report(
            prompt=state.original_prompt,
            constraints=c,
            packages=valid_packages
        )
        state.final_itinerary = report
        state.log("[Agent] Successfully synthesized final itinerary report.")

        return state
