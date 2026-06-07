
import os
from typing import TypedDict, Annotated
import operator

# pyrefly: ignore [missing-import]
import psycopg
# pyrefly: ignore [missing-import]
from langgraph.graph import StateGraph, START, END
# pyrefly: ignore [missing-import]
from langgraph.checkpoint.postgres import PostgresSaver
# pyrefly: ignore [missing-import]
from langchain_core.messages import (
    AnyMessage,
    HumanMessage,
    AIMessage,
    SystemMessage,
)

# pyrefly: ignore [missing-import]
from langchain_groq import ChatGroq


from tools.tavily_tool import tavily_search
from tools.flight_tool import search_flights

# pyrefly: ignore [missing-import]
from dotenv import load_dotenv
load_dotenv()
#llm connected
llm = ChatGroq(
    model="llama3.3-70b-versatile"
)
# database connected
DATABASE_URL = os.getenv("DATABASE_URL")
#yaha we are creating state 
class TravelState(TypedDict): #dictionary type main data rakhenge state main
    messages: Annotated[list[AnyMessage], operator.add] #har type ka message add hoga
    #puranan saara message rahega and ek ke niche ek aayega list append hote rahega
    user_query: str  #mera message user ka 
    flights_result: str #Flight Search Agent ka result
    hotel_results: str  #Hotel Recommendation Agent ka result
    itinerary: str     #Itinerary Planning Agent ka result
    llm_calls: int     #LLM calls count
    #keys : format . har agent ka ek key hai 

    #aab agents banega har particular kaam ka 4 agents
    #AGENT 1:

def flight_agent(state :TravelState):
    query = state["user_query"]
    flight_data = search_flights(query)  #flight search tool 
    return { #update kiya result
        "flights_result" : flight_data,
        "messages": [
            AIMessage(content=f"Flight Result Fetched")
        ],
        "llm_calls" : state.get("llm_calls", 0) + 1
    }
    
#hotel ko search karega : AGENT 2

def hotel_agent(state :TravelState):
    query = f"Best hotels for {state['user_query']}"
    hotel_result = tavily_search(query)  #hotel search tool 
    return { #update kiya result
        "hotel_results" : hotel_result,
        "messages": [
            AIMessage(content=f"Hotel Information Fetched")
        ],
        "llm_calls" : state.get("llm_calls", 0) + 1
    }
#Itinerary ko search karega : AGENT 3

def itinerary_agent(state :TravelState):
    prompt = f"""
    You are an expert travel planner. Using the flight and hotel information below, create
    a detailed, day-by-day travel itinerary for the user's query.
    Create a travel itinerary.
    User Query: {state['user_query']}

    Hotel Results: {state['hotel_results']}

    Flight Results: {state['flight_results']}

    Please generate a comprehensive itinerary that includes: 
    - Flight details (departure, arrival, airline)
    - Hotel recommendations (name, location)
    - Daily activities and attractions
    - Estimated budget breakdown
    - Travel tips and recommendations
    """

    response = llm.invoke(
        [
            SystemMessage(content="You are an expert travel planner. Create a detailed travel itinerary."),
            HumanMessage(content=prompt),
        ]
    )
    return {
        "itinerary": response.content,
        "messages": [response],
        "llm_calls" : state.get("llm_calls", 0) + 1
    }
#final agent: AGENT 4

def final_agent(state: TravelState):
    final_prompt = f"""
    You are an expert travel planner. Using the flight and hotel information below, create
    a detailed, day-by-day travel itinerary for the user's query.
    Flights: 
    {state['flights_result']}

    Hotels:
    {state['hotel_results']}

    Itinerary:
    {state['itinerary']}

    Please generate a comprehensive itinerary that includes: 
    - Flight details (departure, arrival, airline)
    - Hotel recommendations (name, location)
    - Daily activities and attractions
    - Estimated budget breakdown
    - Travel tips and recommendations
    """
    response = llm.invoke(
        [
            HumanMessage(content=final_prompt),
        ]
    )
    return {
        "itinerary": response.content,
        "messages": [response],
        "llm_calls" : state.get("llm_calls", 0) + 1
    }

#Creating the graph
graph = StateGraph(TravelState)
#Adding nodes 
graph.add_node("flight_agent", flight_agent)
graph.add_node("hotel_agent", hotel_agent)
graph.add_node("itinerary_agent", itinerary_agent)
graph.add_node("final_agent", final_agent)

graph.add_edge(START, "flight_agent")
graph.add_edge("flight_agent", "hotel_agent")
graph.add_edge("hotel_agent", "itinerary_agent")
graph.add_edge("itinerary_agent", "final_agent")
graph.add_edge("final_agent", END)

_conn = psycopg.connect(
    DATABASE_URL,
    autocommit=True
)

checkpointer = PostgresSaver(_conn)
checkpointer.setup()


#Compile the graph
app = graph.compile(checkpointer=checkpointer)

if __name__ == "__main__":
    config = {
        "configurable": {
            "thread_id": "user_mansi"
        }
    }
    user_input = input("Enter Travel Request: ")
    result = app.invoke(
        {
            "messages": [
                HumanMessage(content=user_input)
            ],
            "user_query" : user_input,
            "flights_result" : "",
            "hotel_results" : "",
            "itinerary" : "",
            "llm_calls" : 0          
        },
        config=config
    )
    print("\nFINAL RESPONSE:\n")

    for msg in result['messages']:
        print(msg.content)