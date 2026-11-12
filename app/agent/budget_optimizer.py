from typing import List
from app.models.flight import FlightOption
from app.models.hotel import HotelOption
from app.models.package import TripPackage

class BudgetOptimizer:
    """
    Pairs flight options and verified hotel options, verifies strict budget constraints,
    and ranks valid packages by rating, savings, and value.
    """
    @staticmethod
    def build_and_rank_packages(
        flights: List[FlightOption],
        hotels: List[HotelOption],
        total_budget: float = 30000.0,
        require_beach_view: bool = True,
        require_free_cancellation: bool = True
    ) -> List[TripPackage]:
        valid_packages: List[TripPackage] = []
        pkg_counter = 1

        for flight in flights:
            for hotel in hotels:
                # 1. Enforce Beach View constraint
                if require_beach_view and not hotel.has_beach_view:
                    continue

                # 2. Enforce Free Cancellation constraint
                if require_free_cancellation and not hotel.cancellation_verification.is_free_cancellation:
                    continue

                # 3. Enforce Budget constraint
                total_cost = flight.price + hotel.total_price
                if total_cost > total_budget:
                    continue

                savings = total_budget - total_cost

                # Determine package character
                if savings > 8000:
                    badge = "Best Budget Value"
                elif hotel.rating >= 4.5:
                    badge = "Premium Beachfront Experience"
                else:
                    badge = "Recommended Balance"

                pkg = TripPackage(
                    package_id=f"PKG_00{pkg_counter}",
                    title=f"{hotel.name} + {flight.airline} Flight",
                    flight=flight,
                    hotel=hotel,
                    flight_cost=flight.price,
                    hotel_cost=hotel.total_price,
                    total_cost=total_cost,
                    budget_limit=total_budget,
                    savings=savings,
                    meets_all_constraints=True,
                    cancellation_highlight=hotel.cancellation_verification.deadline_description,
                    beach_view_highlight=hotel.beach_view_excerpt,
                    why_recommended=f"{badge}: Saves ₹{savings:,.0f} with verified direct beach view and free cancellation."
                )
                valid_packages.append(pkg)
                pkg_counter += 1

        # Rank by a composite score of hotel rating and budget adherence
        valid_packages.sort(
            key=lambda p: (p.hotel.rating * 1000) + p.savings,
            reverse=True
        )

        return valid_packages

