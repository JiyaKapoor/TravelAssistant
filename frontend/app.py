"""
Streamlit Web UI for Agentic Travel Assistant with Human Interrupt & MCP Tool Integration.
"""
import streamlit as st
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.agent.orchestrator import TravelAgent
from app.core.state import AgentStatus

st.set_page_config(
    page_title="AI Travel Assistant - Goa Trip Planner",
    page_icon="🌴",
    layout="wide"
)

# Initialize Agent in session state
if "agent" not in st.session_state:
    st.session_state.agent = TravelAgent()
if "current_state" not in st.session_state:
    st.session_state.current_state = None

st.title("🌴 Agentic Travel Assistant")
st.caption("Powered by MCP Tools, In-Context Policy Reasoning & Human-in-the-Loop Interrupts")

# Sidebar Configuration
with st.sidebar:
    st.header("⚙️ Agent Controls")
    st.markdown("""
    **Active Capabilities:**
    -  **MCP Server Tools**: Flights & Hotels
    -  **In-Context Policy Inspection**: 
      - Real Beach View Verification
      - 100% Free Cancellation Guarantee
    - ⏸️ **Human Interrupt**: Automatically halts when critical data is omitted
    - 💰 **Budget Enforcer**: Flight + Hotel <= ₹30,000
    """)
    if st.button("Reset Session"):
        st.session_state.current_state = None
        st.rerun()

# Prompt Input
default_query = "Plan a trip to Goa including Economy flights and hotels with a Beach view that offer a free cancellation under 30000"
user_prompt = st.text_area("Your Travel Request:", value=default_query, height=75)

col_btn, _ = st.columns([1, 4])
with col_btn:
    start_plan = st.button("🚀 Plan My Trip", type="primary")

if start_plan and user_prompt:
    with st.spinner("Agent is analyzing your request..."):
        st.session_state.current_state = st.session_state.agent.run(user_prompt)

# Render Human Interrupt Modal / Warning if triggered
state = st.session_state.current_state

if state and state.status == AgentStatus.AWAITING_HUMAN_INPUT:
    st.warning("### ⏸️ Human Interrupt: Missing Critical Information")
    st.markdown(f"**Agent Message:** {state.interrupt_question}")
    
    with st.form("human_input_form"):
        user_reply_parts = []
        
        if "origin" in state.missing_fields:
            origin_choice = st.selectbox(
                "Departure City / Airport:",
                ["Mumbai (BOM)", "Delhi (DEL)", "Bangalore (BLR)", "Custom City"]
            )
            if origin_choice == "Custom City":
                custom_origin = st.text_input("Enter your origin city or airport code:", "Mumbai")
                user_reply_parts.append(custom_origin)
            else:
                user_reply_parts.append(origin_choice)

        if "total_budget" in state.missing_fields:
            budget_input = st.text_input("Total Target Budget (e.g., 30000, 25k, $1,500):", "30000")
            user_reply_parts.append(budget_input)

        if not state.missing_fields:
            general_reply = st.text_input("Your Response:", "")
            user_reply_parts.append(general_reply)

        submit_answer = st.form_submit_button("Continue Workflow ➔")

        if submit_answer and user_reply_parts:
            combined_reply = " ".join(user_reply_parts)
            with st.spinner(f"Resuming agent with: {combined_reply}..."):
                st.session_state.current_state = st.session_state.agent.resume_with_human_input(
                    session_id=state.session_id,
                    user_answer=combined_reply
                )
                st.rerun()

# Render Results when Completed
if state and state.status == AgentStatus.COMPLETED:
    st.success("✅ Agent execution complete! All constraints verified and optimized.")

    # Top Metrics
    best = state.packages[0]
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Trip Cost", f"₹{best.total_cost:,.0f}")
    m2.metric("Budget Remaining (Savings)", f"₹{best.savings:,.0f}", delta=f"₹{best.savings:,.0f}")
    m3.metric("Flight Fares", f"₹{best.flight_cost:,.0f}")
    m4.metric("Hotel Total (3 Nights)", f"₹{best.hotel_cost:,.0f}")

    # Tabs for Itinerary vs Agent Trace
    tab_report, tab_packages, tab_logs = st.tabs(["📄 Full Itinerary", "📦 All Qualifying Packages", "🧠 Agent Reasoning Trace"])

    with tab_report:
        st.markdown(state.final_itinerary)

    with tab_packages:
        for pkg in state.packages:
            with st.expander(f"⭐ {pkg.title} — Total: ₹{pkg.total_cost:,.0f} (Saves ₹{pkg.savings:,.0f})", expanded=(pkg.package_id == "PKG_001")):
                col_fl, col_ht = st.columns(2)
                with col_fl:
                    st.subheader("✈️ Flight")
                    st.write(f"**Airline:** {pkg.flight.airline} ({pkg.flight.flight_number})")
                    st.write(f"**Route:** {pkg.flight.origin} ➔ {pkg.flight.destination}")
                    st.write(f"**Departure:** {pkg.flight.departure_time} | **Cabin:** {pkg.flight.cabin_class}")
                    st.write(f"**Round-trip Price:** ₹{pkg.flight.price:,.0f}")
                with col_ht:
                    st.subheader("🏨 Hotel")
                    st.write(f"**Hotel:** {pkg.hotel.name} ({pkg.hotel.rating} ⭐)")
                    st.write(f"**Area:** {pkg.hotel.area}")
                    st.write(f"**Total Stay Cost:** ₹{pkg.hotel.total_price:,.0f} ({pkg.hotel.nights} Nights)")
                    st.info(f"**Beach View Evidence:**\n*{pkg.hotel.beach_view_excerpt}*")
                    st.success(f"**Cancellation Policy:**\n*{pkg.hotel.cancellation_verification.deadline_description}*")

    with tab_logs:
        st.subheader("Agent Audit Trail & State Transitions")
        for log in state.audit_log:
            st.code(log, language="bash")

