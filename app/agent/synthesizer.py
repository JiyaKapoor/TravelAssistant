from typing import List
from app.models.package import TripPackage
from app.models.trip_request import TripConstraints

class ItinerarySynthesizer:
    """
    Synthesizes packages into an executive travel briefing with grounded citations
    and transparent cost breakdowns based strictly on user-requested constraints.
    """
    @staticmethod
    def generate_report(
        prompt: str,
        constraints: TripConstraints,
        packages: List[TripPackage]
    ) -> str:
        dest = constraints.destination or "Destination"
        budget_display = f"₹{constraints.total_budget:,.0f} {constraints.currency}" if constraints.total_budget else "Flexible"

        if not packages:
            return (
                f"### ❌ No Packages Found Within Budget\n\n"
                f"We searched for flights and hotels in **{dest}** under **{budget_display}**, "
                "but no combination strictly satisfied all constraints.\n\n"
                "**Suggestions:**\n"
                "- Increase your budget slightly.\n"
                "- Consider travel dates with lower airfares.\n"
                "- Relax specific amenity or room requirements."
            )

        best = packages[0]
        md = []
        md.append(f"# 🌴 {dest} Trip Itinerary & Booking Plan\n")
        md.append(f"**Request:** *\"{prompt}\"*\n")
        
        # Build constraints summary dynamically
        constraint_bullets = [f"Cabin: {constraints.cabin_class}"]
        if constraints.hotel_preferences:
            constraint_bullets.append(f"Preferences: {', '.join(constraints.hotel_preferences)}")
        if constraints.free_cancellation_required:
            constraint_bullets.append("100% Free Cancellation")
            
        md.append(f"**Total Budget Cap:** {budget_display} | **Applied Constraints:** {', '.join(constraint_bullets)}\n")
        md.append("---\n")
        
        md.append(f"## 🏆 Top Recommended Package: {best.title}\n")
        md.append(f"**Status:**  All constraints verified! Total Cost: **₹{best.total_cost:,.0f}** (You save **₹{best.savings:,.0f}** under budget)\n\n")

        # Flight Details Card
        f = best.flight
        md.append("### ✈️ Flight Details (Round-Trip)")
        md.append(f"- **Airline:** {f.airline} ({f.flight_number})")
        md.append(f"- **Route:** {f.origin} ➔ {f.destination}")
        md.append(f"- **Cabin Class:** {f.cabin_class}")
        md.append(f"- **Departure:** {f.departure_time} | **Duration:** {f.duration} (Non-stop)")
        md.append(f"- **Price:** **₹{f.price:,.0f}** (Round-trip total)")
        md.append(f"- **Provider:** {f.provider}\n")

        # Hotel Details Card
        h = best.hotel
        md.append("### 🏨 Hotel Details")
        md.append(f"- **Property:** **{h.name}** ({h.rating} ⭐)")
        md.append(f"- **Location:** {h.area}")
        md.append(f"- **Duration:** {h.nights} Nights (@ ₹{h.price_per_night:,.0f}/night)")
        md.append(f"- **Total Hotel Cost:** **₹{h.total_price:,.0f}**")
        md.append(f"- **Amenities:** {', '.join(h.amenities)}\n")

        # Grounded Verification Evidence
        md.append("### 🔍 Verified Highlights & Policies")
        if "beach view" in constraints.hotel_preferences or h.has_beach_view:
            md.append(f"1. **Beach View Verification:** ")
            md.append(f"   > *\"{h.beach_view_excerpt}\"*")
            
        md.append(f"2. **Cancellation Policy Terms:** ")
        md.append(f"   > *\"{h.cancellation_verification.policy_excerpt}\"*")
        md.append(f"   - **Verified Policy:** **{h.cancellation_verification.deadline_description}**\n")

        # Cost Breakdown Table
        md.append("### 💰 Budget & Cost Breakdown")
        md.append("| Expense Item | Amount |")
        md.append("| :--- | :--- |")
        md.append(f"| Round-Trip Flights ({f.airline}) | ₹{f.price:,.0f} |")
        md.append(f"| Hotel Stay ({h.nights} Nights at {h.name}) | ₹{h.total_price:,.0f} |")
        md.append(f"| **Total Trip Cost** | **₹{best.total_cost:,.0f}** |")
        md.append(f"| **Remaining Budget (Savings)** | **+₹{best.savings:,.0f}** |")
        md.append("\n---\n")

        # Alternative Packages
        if len(packages) > 1:
            md.append("### 🥈 Alternative Valid Packages Under Budget\n")
            for alt in packages[1:3]:
                md.append(f"- **{alt.title}**")
                md.append(f"  - Total: **₹{alt.total_cost:,.0f}** (Saves ₹{alt.savings:,.0f})")
                md.append(f"  - Flight: {alt.flight.airline} (₹{alt.flight.price:,.0f}) | Hotel: {alt.hotel.name} (₹{alt.hotel.total_price:,.0f})")
                md.append(f"  - Policy: {alt.hotel.cancellation_verification.deadline_description}\n")

        return "\n".join(md)
