import json
import asyncio
from typing import AsyncGenerator
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
# pyrefly: ignore [missing-import]
from sse_starlette.sse import EventSourceResponse

# Import our LangGraph app and HumanMessage from the existing backend
from main import app as travel_graph
from langchain_core.messages import HumanMessage
from datetime import datetime

app = FastAPI(title="AI Travel API")

# Add CORS so our React frontend can communicate with this backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class PlanRequest(BaseModel):
    query: str
    traveler_name: str = ""
    trip_style: str = ""

def make_thread_id():
    return f"traveler_{datetime.now().strftime('%Y%m%d%H%M%S')}"

async def run_pipeline_stream(full_query: str) -> AsyncGenerator[dict, None]:
    thread_id = make_thread_id()
    config = {"configurable": {"thread_id": thread_id}}

    state_input = {
        "messages": [HumanMessage(content=full_query)],
        "user_query": full_query,
        "flights_result": "",
        "hotel_results": "",
        "itinerary": "",
        "llm_calls": 0,
    }

    # Run langgraph stream. Note: we use sync stream here and yield asynchronously.
    # Depending on langgraph setup, a stream might block if not run in executor,
    # but for simplicity we wrap it in a non-blocking way if possible, or just iterate.
    # In a real app we might use app.astream() if the nodes are async, 
    # but since tools and nodes in main.py are sync, we'll iterate using asyncio.to_thread 
    # or just iterate directly if it's fast enough. Let's iterate directly as it's a prototype.
    
    # We will send Server-Sent Events (SSE)
    yield {
        "event": "step",
        "data": json.dumps({"step": 1, "message": "Searching live flight data..."})
    }
    
    for event in travel_graph.stream(state_input, config=config):
        node_name = list(event.keys())[0] if event else None
        
        step_idx = 0
        message = ""
        if node_name == "flight_agent":
            step_idx = 2
            message = "Finding best hotels..."
        elif node_name == "hotel_agent":
            step_idx = 3
            message = "Crafting your itinerary..."
        elif node_name == "itinerary_agent":
            step_idx = 4
            message = "Generating final travel plan..."
        
        if step_idx > 0:
            yield {
                "event": "step",
                "data": json.dumps({"step": step_idx, "message": message})
            }
            await asyncio.sleep(0.1) # Yield control to event loop

    # Get final state
    final_state = travel_graph.get_state(config).values
    
    # Clean messages for JSON serialization (remove Langchain message objects)
    messages_log = []
    for msg in final_state.get("messages", []):
        role = "ai" if getattr(msg, "type", "") == "ai" else "user"
        messages_log.append({"role": role, "content": msg.content})

    result_data = {
        "itinerary": final_state.get("itinerary", ""),
        "flights_result": final_state.get("flights_result", ""),
        "hotel_results": final_state.get("hotel_results", ""),
        "llm_calls": final_state.get("llm_calls", 0),
        "messages": messages_log,
        "thread_id": thread_id
    }

    yield {
        "event": "complete",
        "data": json.dumps(result_data)
    }

@app.post("/api/plan")
async def plan_trip(request: Request, body: PlanRequest):
    """
    Using POST but responding with an SSE stream. 
    Standard EventSource doesn't support POST, but we can use fetch + handling streams on client.
    However, SSE Starlette works well if the client uses fetch to read the stream.
    For standard EventSource, we usually need GET.
    We will use a GET endpoint with query params for pure standard EventSource compatibility.
    """
    pass # Replaced by GET endpoint below

@app.get("/api/plan/stream")
async def plan_trip_stream(request: Request, query: str, traveler_name: str = "", trip_style: str = ""):
    full_query = query.strip()
    if traveler_name.strip() and trip_style.strip():
        full_query = f"[Traveler: {traveler_name.strip()}, Style: {trip_style}] {full_query}"
        
    return EventSourceResponse(run_pipeline_stream(full_query))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
