# 🌴 Agentic Travel Assistant

A goal-oriented AI Travel Assistant designed to parse complex natural language prompts, query travel tools via the **Model Context Protocol (MCP)**, inspect unstructured room views & legal cancellation policies in-context, enforce hard budget limits (e.g. `<= ₹30,000`), and trigger a **Human Interrupt** whenever critical information is missing.

---

## 🏗️ Architecture & State Machine

```
User Prompt:
"Plan a trip to Goa including Economy flights and hotels with a Beach view that offer a free cancellation under 30000"
                              │
                              ▼
                ┌───────────────────────────┐
                │ 1. Intent & Constraint    │
                │    Parser (Planner)       │
                └─────────────┬─────────────┘
                              │
                              ▼
               ┌─────────────────────────────┐
               │  2. Missing Critical Info?   │
               │     (Human Interrupt Gate)  │
               └──────────────┬──────────────┘
                     YES      │      NO
        ┌─────────────────────┴──────────────────┐
        ▼                                        ▼
┌───────────────────────────┐         ┌─────────────────────────┐
│ ⏸️ AWAITING_HUMAN_INPUT    │         │ 3. Parallel MCP Calls   │
│ Prompt: "What departure   │         │    • search_flights()   │
│ city are you flying from?"│         │    • search_hotels()    │
└─────────────┬─────────────┘         └────────────┬────────────┘
              │ (User replies: "Mumbai")           │
              └────────────────────────────────────┘
                                                   │
                                                   ▼
                                      ┌─────────────────────────┐
                                      │ 4. In-Context Evaluator │
                                      │    • Verify Beach View  │
                                      │    • Verify Free Cancel │
                                      └────────────┬────────────┘
                                                   │
                                                   ▼
                                      ┌─────────────────────────┐
                                      │ 5. Budget Optimizer     │
                                      │    Flight + Hotel       │
                                      │    <= ₹30,000           │
                                      └────────────┬────────────┘
                                                   │
                                                   ▼
                                      ┌─────────────────────────┐
                                      │ 6. Itinerary Synthesizer│
                                      │    Report & Citations   │
                                      └─────────────────────────┘
```

---

## 🌟 Key Features

1. **Human-in-the-Loop Interrupt**: If the prompt is missing vital information (e.g., origin departure city), the agent halts its workflow, creates an interactive interruption prompt, and waits for human input before continuing.
2. **MCP Tool Integration**: Modular Model Context Protocol server exposing `search_flights`, `search_hotels`, and `get_hotel_details`.
3. **In-Context Semantic Reasoning**: 
   - Rejects hotels that claim "beach view" but are actually inland, pool, or garden views (e.g. *Fairfield by Marriott Anjuna*).
   - Rejects non-refundable promotional rates even if they have great views (e.g. *Goa Marriott Miramar*).
   - Verifies 100% full-refund cancellation deadlines.
4. **Constraint & Budget Optimization**: Strictly verifies `flight_cost + hotel_cost <= 30000` and ranks qualifying packages by savings and customer ratings.

---

## 📂 Project Structure

```text
TravelAssistant/
│
├── requirements.txt            # Lightweight dependencies (Pydantic, FastAPI, Streamlit)
├── .env.example                # API key template (Gemini, Amadeus)
├── run_demo.py                 # Interactive CLI demonstration with Human Interrupt
│
├── mcp_server/                 # Model Context Protocol layer
│   ├── server.py               # MCP Server definition & tool registry
│   ├── tools/
│   │   ├── flight_tools.py     # Search flight routes & cabin classes
│   │   └── hotel_tools.py      # Search hotels & fetch full text policies
│   └── data/
│       ├── raw_flights.json    # Flight routes (BOM, DEL, BLR -> GOI/GOX)
│       └── raw_hotels.json     # Goa hotels with room & policy text
│
├── app/
│   ├── main.py                 # FastAPI REST API entrypoint
│   ├── core/
│   │   └── state.py            # AgentState schema & AgentStatus enum
│   ├── models/                 # Pydantic validation contracts
│   │   ├── trip_request.py     # User query & constraints schema
│   │   ├── flight.py           # FlightOption schema
│   │   ├── hotel.py            # HotelOption & Cancellation schema
│   │   └── package.py          # Combined trip package schema
│   ├── services/               # External providers & Geo resolution
│   │   ├── geo_service.py      # Dynamic City ➔ IATA Airport Code Resolver
│   │   └── amadeus_service.py  # Amadeus Self-Service API live client
│   └── agent/
│       ├── planner.py          # Production Entity Parser (LLM Schema + Grammar)
│       ├── evaluator.py        # In-context policy & view inspector
│       ├── budget_optimizer.py # Combined cost validator & ranker
│       ├── synthesizer.py      # Formats executive report with citations
│       └── orchestrator.py     # State machine coordinating the flow
│
├── frontend/
│   └── app.py                  # Streamlit Interactive Web Dashboard
│
└── tests/
    └── test_agent.py           # Full test suite (Extraction, Interrupts, Budget, Policies)
```

---

## 🚀 Quickstart

### 1. Run the Interactive CLI Demo
```bash
python run_demo.py
```
This tests the exact prompt:  
`"Plan a trip to Goa including Economy flights and hotels with a Beach view that offer a free cancellation under 30000"`

You will see:
1. The **Human Interrupt** fire because the origin departure city was omitted.
2. The user providing `Mumbai (BOM)`.
3. The MCP tools executing and candidate hotels being evaluated in-context.
4. The final verified itinerary synthesized within budget!

### 2. Launch the Streamlit Web UI
```bash
streamlit run frontend/app.py
```
Open [http://localhost:8501](http://localhost:8501) in your browser to interact with the visual trip cards, budget meters, and interruption modals.

### 3. Launch the FastAPI REST Server
```bash
uvicorn app.main:app --reload
```
Interactive Swagger docs available at [http://localhost:8000/docs](http://localhost:8000/docs).

### 4. Run Automated Test Suite
```bash
python tests/test_agent.py
```

