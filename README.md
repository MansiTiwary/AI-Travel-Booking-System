# ✈️ AI Travel Booking System

A Multi-Agent AI Travel Booking System that automates end-to-end travel planning through collaborative AI agents. The platform leverages LangGraph, Groq-powered LLaMA 3.3 70B, PostgreSQL, Tavily Search, and AviationStack APIs to provide intelligent flight recommendations, hotel suggestions, personalized itineraries, and optimized travel plans.

---

## 🚀 Project Overview

Planning a trip often requires users to browse multiple platforms for flights, accommodations, destination research, and itinerary creation. This project simplifies the process using a Multi-Agent AI architecture where specialized agents collaborate to generate a complete travel plan from a single natural language request.

### Example Queries

* Plan a 5-day trip to Bali under ₹50,000.
* Find the cheapest flights from Mumbai to Dubai.
* Suggest hotels near Marina Bay Sands in Singapore.
* Create a 7-day itinerary for Japan.
* Recommend a solo travel destination for December.

---

## ✨ Key Features

### 🤖 Multi-Agent Architecture

The system uses specialized AI agents that work together to accomplish complex travel-planning tasks.

### ✈️ Flight Search Agent

* Searches available flights
* Compares routes and airlines
* Identifies cost-effective options
* Retrieves real-time flight information

### 🏨 Hotel Recommendation Agent

* Searches accommodations based on user preferences
* Filters by budget, location, and ratings
* Provides personalized recommendations

### 🗺️ Itinerary Planning Agent

* Creates day-wise travel schedules
* Suggests attractions and activities
* Optimizes travel plans based on trip duration

### 📋 Final Planning Agent

* Aggregates outputs from all agents
* Generates a complete travel package
* Provides estimated trip costs
* Creates final travel recommendations

### 💬 Natural Language Interaction

Users can communicate with the system using conversational language without navigating multiple booking platforms.

---

## 🏗️ System Architecture

```text
                    User Request
                          │
                          ▼
                  Supervisor Agent
                          │
         ┌────────────────┼────────────────┐
         ▼                ▼                ▼
  Flight Agent      Hotel Agent     Itinerary Agent
         │                │                │
         └────────────────┴────────────────┘
                          │
                          ▼
                     Final Agent
                          │
                          ▼
                  Complete Travel Plan
```

---

## 🔄 Agent Workflow

### Step 1: User Request

```text
Plan a 5-day trip to Goa under ₹30,000
```

### Step 2: Supervisor Agent

* Understands user intent
* Extracts travel requirements
* Assigns tasks to specialized agents

### Step 3: Flight Agent

* Retrieves flight information
* Compares options
* Returns best flight recommendations

### Step 4: Hotel Agent

* Searches hotels
* Applies budget filters
* Returns ranked accommodations

### Step 5: Itinerary Agent

* Generates travel schedule
* Suggests attractions
* Creates day-wise plans

### Step 6: Final Agent

* Consolidates outputs
* Calculates estimated costs
* Produces final travel package

---

## 🛠️ Technology Stack

### AI & Agent Framework

* LangGraph
* Groq
* LLaMA 3.3 70B

### Backend

* Python
* FastAPI

### Database

* PostgreSQL

### APIs

* AviationStack API
* Tavily Search API

### Data Storage

* PostgreSQL

### Development Tools

* Git
* GitHub

---

## 📂 Project Structure

```text
ai-travel-booking-system/
│
├── agents/
│   ├── flight_agent.py
│   ├── hotel_agent.py
│   ├── itinerary_agent.py
│   ├── final_agent.py
│   └── supervisor_agent.py
│
├── api/
│   ├── routes.py
│   └── schemas.py
│
├── database/
│   ├── models.py
│   ├── connection.py
│   └── migrations/
│
├── services/
│   ├── aviationstack_service.py
│   ├── tavily_service.py
│   └── llm_service.py
│
├── graph/
│   └── travel_workflow.py
│
├── frontend/
│   └── streamlit_app.py
│
├── requirements.txt
├── README.md
└── .gitignore
```

---

## 🎯 Core Components

### Supervisor Agent

Responsible for:

* Intent analysis
* Task delegation
* Workflow orchestration

### Flight Agent

Responsible for:

* Flight discovery
* Airline comparison
* Route optimization

### Hotel Agent

Responsible for:

* Accommodation search
* Budget filtering
* Hotel recommendations

### Itinerary Agent

Responsible for:

* Attraction planning
* Schedule generation
* Activity recommendations

### Final Agent

Responsible for:

* Response aggregation
* Cost estimation
* Travel plan generation

---

## 📊 Database Design

### Users

```sql
user_id
name
email
preferences
```

### Travel Requests

```sql
request_id
user_id
destination
budget
duration
travel_dates
```

### Travel Plans

```sql
plan_id
request_id
flight_details
hotel_details
itinerary
total_cost
created_at
```

---

## 🔥 Advanced Features

### Personalized Recommendations

* Budget-aware planning
* Preference-based suggestions
* Travel history analysis

### Real-Time Travel Information

* Flight availability
* Airline details
* Destination research

### Intelligent Decision Making

* Multi-agent collaboration
* Context-aware planning
* Cost optimization

---

## 🎓 Learning Outcomes

* Multi-Agent AI Systems
* Agent Orchestration with LangGraph
* LLM Integration using Groq
* Workflow Automation
* API Integration
* PostgreSQL Database Design
* FastAPI Development
* Enterprise System Architecture

---

## 🔮 Future Enhancements

* Flight Booking Integration
* Hotel Booking Integration
* Visa Requirement Assistant
* Travel Expense Tracker
* Voice-Based Travel Assistant
* Multi-Language Support
* Travel Recommendation Engine
* AI Travel Concierge

---

## 📌 Project Status

🚧 Beta Version – Under Active Development

This project is being developed to demonstrate advanced Multi-Agent AI architectures, enterprise-grade backend development, and real-world travel automation workflows using state-of-the-art large language models.

---

## 👩‍💻 Author

**Mansi Tiwary**  | **Yash Gupta**

Aspiring Software Engineer | Generative AI Enthusiast | Backend Developer

---

## 📜 License

© 2026 Mansi Tiwary and Yash Gupta . All Rights Reserved.

This project and its source code may not be copied, modified, distributed, or used for commercial purposes without explicit written permission from the author.
