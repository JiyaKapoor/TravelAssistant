"""
Interactive CLI Runner demonstrating the complete Agentic Travel Assistant workflow
with Human-in-the-Loop Interrupt, MCP Tools, and In-Context Policy Inspection.
"""
import sys
from app.agent.orchestrator import TravelAgent
from app.core.state import AgentStatus

def main():
    agent = TravelAgent()

    print("=" * 80)
    print("🌍 AGENTIC TRAVEL ASSISTANT: MULTI-DESTINATION PLANNER")
    print("=" * 80)

    # Use command-line argument if provided, otherwise test prompt
    if len(sys.argv) > 1:
        user_prompt = " ".join(sys.argv[1:])
    else:
        user_prompt = (
            "Plan a trip to Goa including Economy flights and hotels with a "
            "Beach view that offer a free cancellation under 30000"
        )

    print(f"\n[User Request]: \"{user_prompt}\"\n")

    # Step 1: Run Agent Initial Step
    state = agent.run(user_prompt)

    # Step 2: Handle Human Interrupt loop (supports multiple missing fields if needed)
    while state.status == AgentStatus.AWAITING_HUMAN_INPUT:
        print("\n" + "!" * 80)
        print("⏸️  [HUMAN-IN-THE-LOOP INTERRUPT TRIGGERED]")
        print(f"Missing Fields: {', '.join(state.missing_fields)}")
        print(f"Agent Question:\n{state.interrupt_question}")
        print("!" * 80)

        # Check if running interactively in terminal
        if sys.stdin.isatty():
            try:
                user_reply = input("\n👉 Enter your answer: ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\nOperation cancelled by user.")
                sys.exit(0)
        else:
            # Automated fallback for headless/CI runs
            user_reply = "Mumbai (BOM)"
            print(f"\n[Auto-Supplying Answer for Headless Run]: '{user_reply}'")

        # Step 3: Resume Agent Execution with user input
        print("\n▶️  Resuming Agent Workflow with provided input...\n")
        state = agent.resume_with_human_input(
            session_id=state.session_id,
            user_answer=user_reply
        )

    # Step 4: Display Agent Execution Audit Trail
    print("-" * 80)
    print("📋 AGENT AUDIT LOG & REASONING TRACE:")
    print("-" * 80)
    for log_entry in state.audit_log:
        print(f"  {log_entry}")
    print("-" * 80)

    # Step 5: Display Final Synthesized Report
    print("\n" + "=" * 80)
    print("📄 FINAL VERIFIED ITINERARY REPORT:")
    print("=" * 80)
    print(state.final_itinerary)
    print("=" * 80)

if __name__ == "__main__":
    main()
