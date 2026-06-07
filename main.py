import os
import operator
from typing import TypedDict, Annotated

# ✅ Load .env FIRST
from dotenv import load_dotenv
load_dotenv()

# pyrefly: ignore [missing-import]
import psycopg                                  # ✅ MUST be psycopg v3, NOT psycopg2
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.postgres import PostgresSaver
from langchain_core.messages import AnyMessage, HumanMessage, AIMessage, SystemMessage
from langchain_groq import ChatGroq

from tools.flight_tool import search_flights
from tools.tavily_tool import tavily_search

# ── LLM ──────────────────────────────────────────────────────────────────────
llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    api_key=os.getenv("GROQ_API_KEY"),
)

# ── Database ──────────────────────────────────────────────────────────────────
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL not set. Check your .env file.")


# ── State ─────────────────────────────────────────────────────────────────────
class TravelState(TypedDict):
    messages:       Annotated[list[AnyMessage], operator.add]
    user_query:     str
    flights_result: str
    hotel_results:  str
    itinerary:      str
    llm_calls:      int


# ── Agent 1 : Flights ─────────────────────────────────────────────────────────
def flight_agent(state: TravelState) -> dict:
    flight_data = search_flights(state["user_query"])
    return {
        "flights_result": flight_data,
        "messages": [AIMessage(content="✈ Flight data fetched successfully.")],
        "llm_calls": state.get("llm_calls", 0) + 1,
    }


# ── Agent 2 : Hotels ──────────────────────────────────────────────────────────
def hotel_agent(state: TravelState) -> dict:
    hotel_result = tavily_search(f"Best hotels and accommodations for {state['user_query']} with prices in Indian Rupees (INR)")
    return {
        "hotel_results": hotel_result,
        "messages": [AIMessage(content="🏨 Hotel information fetched successfully.")],
        "llm_calls": state.get("llm_calls", 0) + 1,
    }


# ── Agent 3 : Itinerary ───────────────────────────────────────────────────────
def itinerary_agent(state: TravelState) -> dict:
    prompt = f"""
You are an expert travel planner. Using the flight and hotel information below,
create a detailed, day-by-day travel itinerary for the user's query.

User Query     : {state['user_query']}
Flight Results : {state['flights_result']}
Hotel Results  : {state['hotel_results']}

Please generate a comprehensive itinerary that includes:
- Flight details (departure, arrival, airline, timings)
- Hotel recommendations (name, location, why it's good)
- Day-by-day activities and must-see attractions
- Estimated budget breakdown (CRITICAL: ALL prices and budgets MUST be in Indian Rupees, INR, ₹. Convert any foreign currencies to INR)
- Practical travel tips and recommendations
"""
    response = llm.invoke([
        SystemMessage(content="You are an expert travel planner. Create detailed, practical, exciting travel itineraries. You MUST use Indian Rupees (INR, ₹) for all prices and budgets."),
        HumanMessage(content=prompt),
    ])
    return {
        "itinerary": response.content,
        "messages": [response],
        "llm_calls": state.get("llm_calls", 0) + 1,
    }


# ── Agent 4 : Final ───────────────────────────────────────────────────────────
def final_agent(state: TravelState) -> dict:
    final_prompt = f"""
You are a luxury travel concierge. Write a polished, well-structured final travel plan.

User Request : {state['user_query']}

--- FLIGHTS ---
{state['flights_result']}

--- HOTELS ---
{state['hotel_results']}

--- DRAFT ITINERARY ---
{state['itinerary']}

Write the final plan with clear sections:
1. Trip Overview
2. Flight Details
3. Accommodation
4. Day-by-Day Itinerary
5. Budget Estimate (CRITICAL: Ensure ALL prices and budget estimates are EXCLUSIVELY in Indian Rupees, INR, ₹. Convert from USD if needed.)
6. Essential Travel Tips

Make it exciting, practical, and easy to follow.
"""
    response = llm.invoke([
        SystemMessage(content="You are a luxury travel concierge. Deliver a polished, professional travel plan. Format all financial values, prices, and budgets in Indian Rupees (INR, ₹) only."),
        HumanMessage(content=final_prompt),
    ])
    return {
        "itinerary": response.content,
        "messages": [response],
        "llm_calls": state.get("llm_calls", 0) + 1,
    }


# ── Graph ─────────────────────────────────────────────────────────────────────
def build_app():
    graph = StateGraph(TravelState)

    graph.add_node("flight_agent",    flight_agent)
    graph.add_node("hotel_agent",     hotel_agent)
    graph.add_node("itinerary_agent", itinerary_agent)
    graph.add_node("final_agent",     final_agent)

    graph.add_edge(START,             "flight_agent")
    graph.add_edge("flight_agent",    "hotel_agent")
    graph.add_edge("hotel_agent",     "itinerary_agent")
    graph.add_edge("itinerary_agent", "final_agent")
    graph.add_edge("final_agent",     END)

    # ✅ psycopg v3 connection — PostgresSaver requires this, NOT psycopg2
    conn = psycopg.connect(DATABASE_URL, autocommit=True)
    checkpointer = PostgresSaver(conn)
    checkpointer.setup()

    return graph.compile(checkpointer=checkpointer)


app = build_app()


# ── CLI ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    user_input = input("Enter your travel request: ").strip()
    if not user_input:
        print("No input provided. Exiting.")
        exit(1)

    print("\n⏳ Running 4 AI agents...\n")
    result = app.invoke(
        {
            "messages":       [HumanMessage(content=user_input)],
            "user_query":     user_input,
            "flights_result": "",
            "hotel_results":  "",
            "itinerary":      "",
            "llm_calls":      0,
        },
        config={"configurable": {"thread_id": "cli_user"}},
    )
    print("=" * 60)
    print("✈  FINAL TRAVEL PLAN")
    print("=" * 60)
    print(result["itinerary"])
    print(f"\n✅ Completed in {result['llm_calls']} LLM calls.")