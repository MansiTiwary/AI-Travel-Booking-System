import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("AVIATIONSTACK_API_KEY")


def search_flights(query: str) -> str:
    url = "https://api.aviationstack.com/v1/flights"

    params = {
        "access_key": API_KEY,
        "limit": 5,
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
    except requests.exceptions.RequestException as e:
        return f"Flight search failed: {str(e)}"

    if "error" in data:
        return f"AviationStack error: {data['error'].get('message', 'Unknown error')}"

    flights = []

    if "data" in data and data["data"]:
        for flight_item in data["data"][:5]:
            airline   = flight_item.get("airline", {}).get("name", "Unknown Airline")
            departure = flight_item.get("departure", {}).get("airport", "Unknown Airport")
            dep_iata  = flight_item.get("departure", {}).get("iata", "")
            dep_time  = flight_item.get("departure", {}).get("scheduled", "N/A")
            arrival   = flight_item.get("arrival", {}).get("airport", "Unknown Airport")
            arr_iata  = flight_item.get("arrival", {}).get("iata", "")
            arr_time  = flight_item.get("arrival", {}).get("scheduled", "N/A")
            status    = flight_item.get("flight_status", "Unknown")
            flight_no = flight_item.get("flight", {}).get("iata", "N/A")

            flights.append(
                f"✈ Flight : {flight_no}\n"
                f"  Airline   : {airline}\n"
                f"  Departure : {departure} ({dep_iata})  —  {dep_time}\n"
                f"  Arrival   : {arrival} ({arr_iata})  —  {arr_time}\n"
                f"  Status    : {status}\n"
            )

    if not flights:
        return "No flight data found for the given query."

    return "\n".join(flights)