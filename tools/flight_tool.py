import os
import requests
# pyrefly: ignore [missing-import]
from dotenv import load_dotenv #API key load ke liye 

load_dotenv() #API KEY LOAD HOGA 

API_KEY = os.getenv("AVIATIONSTACK_API_KEY")


def search_flights(query): #yaha user ka query input banega
    url = "https://api.aviationstack.com/v1/flights"

    params = {
        "access_key" : API_KEY,
        "limit": 5, #5 results dega
    }
   
    response = requests.get(url, params=params)    
    
    data = response.json()
    
    flight = []

    if "data" in data:
        
        for flight in data["data"][:5]:

            airline = flight.get("airline", {}).get("name", "Unknown")
            
            departure = flight.get(
                "departure", {}
            ).get("airport", "Unknown")

            arrival = flight.get(
                "arrival", {}
            ).get("airport", "Unknown")

            status = flight.get("flight_status", "Unknown")

            flight.append(
                f"""
Airline: {airline}
Departure: {departure}
Arrival: {arrival}
Status: {status}
"""
            )
    
    return "\n".join(flight)  