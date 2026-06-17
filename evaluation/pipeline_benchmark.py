"""
Benchmark harness for the AI Travel Booking System (LangGraph pipeline).

Runs a batch of test queries straight through your compiled LangGraph app
(the same `app` object from main.py) and measures, per query and aggregated:

  - End-to-end response time
  - Per-agent latency: flight_agent, hotel_agent, itinerary_agent, final_agent
  - Tool/API success rate for AviationStack (flight_tool) and Tavily (tavily_tool),
    inferred from whether their returned text looks like an error
  - LLM call count (already tracked in your state as `llm_calls`)
  - A completeness/"accuracy" heuristic: does the final itinerary actually
    contain a flight section, hotel section, day-wise plan, INR budget, tips
  - Optional: an LLM-as-judge quality score (uses your existing Groq `llm`
    client to rate relevance / completeness / currency compliance 1-5).
    This costs one extra Groq call per query, so it's off by default.

Run with:
    python evaluation/pipeline_benchmark.py

Run this from your project root (where main.py lives), with your usual
.env in place (GROQ_API_KEY, DATABASE_URL, TAVILY_API_KEY, AVIATIONSTACK_API_KEY),
since it imports main.py directly and reuses your real Postgres-checkpointed graph.
"""

import json
import re
import statistics
import sys
import time
import uuid
from pathlib import Path

# Make sure the project root (parent of this evaluation/ folder) is on sys.path
# so `from main import ...` works no matter where you launch the script from.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from langchain_core.messages import HumanMessage

from main import app as travel_graph, llm  # reuse your real pipeline + LLM client

# ---------------------------------------------------------------------------
# Config — edit these
# ---------------------------------------------------------------------------
TEST_QUERIES = [
    "Plan a 5-day trip to Goa under ₹30,000",
    "Find the cheapest flights from Mumbai to Dubai",
    "Suggest hotels near Marina Bay Sands in Singapore",
    "Create a 7-day itinerary for Japan",
    "Plan a solo trip to Manali for 4 days under ₹15,000",
]

ENABLE_LLM_JUDGE = False  # set True for a real quality score (costs extra LLM calls)

NODE_LABELS = ["flight_agent", "hotel_agent", "itinerary_agent", "final_agent"]

COMPLETENESS_CHECKS = [
    ("has_flight_section", r"flight"),
    ("has_hotel_section", r"hotel|accommodation"),
    ("has_day_plan", r"day\s*\d"),
    ("has_inr_budget", r"₹|inr|rupee"),
    ("has_tips_section", r"tip"),
]

FAILURE_MARKERS = ["failed", "error", "no flight data found", "no results"]

JUDGE_PROMPT = """Rate this travel itinerary on a scale of 1-5 for each criterion below.

User request: {query}

Itinerary:
{itinerary}

Criteria:
- relevance: does it actually answer the user's request?
- completeness: does it include flights, hotel, a day-wise plan, and a budget?
- currency_compliance: are all prices shown in INR (₹)?

Respond with ONLY a JSON object, no other text:
{{"relevance": <1-5>, "completeness": <1-5>, "currency_compliance": <1-5>}}
"""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def check_tool_failure(text: str) -> bool:
    low = (text or "").lower()
    return any(marker in low for marker in FAILURE_MARKERS)


def completeness_score(final_text: str) -> dict:
    low = (final_text or "").lower()
    result = {name: bool(re.search(pattern, low)) for name, pattern in COMPLETENESS_CHECKS}
    result["score"] = round(sum(result.values()) / len(COMPLETENESS_CHECKS), 3)
    return result


def llm_judge_score(query: str, itinerary: str) -> dict:
    try:
        resp = llm.invoke(JUDGE_PROMPT.format(query=query, itinerary=itinerary[:4000]))
        text = resp.content.strip()
        text = text[text.find("{"): text.rfind("}") + 1]
        scores = json.loads(text)
        scores["avg"] = round(sum(v for v in scores.values() if isinstance(v, (int, float))) / 3, 2)
        return scores
    except Exception as e:
        return {"error": str(e)}


def percentile(values: list, p: float) -> float:
    if not values:
        return 0.0
    s = sorted(values)
    idx = int(p * (len(s) - 1))
    return s[idx]


# ---------------------------------------------------------------------------
# Core run
# ---------------------------------------------------------------------------
def run_single_query(query: str) -> dict:
    thread_id = f"bench_{uuid.uuid4().hex[:8]}"
    config = {"configurable": {"thread_id": thread_id}}

    state_input = {
        "messages": [HumanMessage(content=query)],
        "user_query": query,
        "flights_result": "",
        "hotel_results": "",
        "itinerary": "",
        "llm_calls": 0,
    }

    node_timings = {}
    t_start = time.perf_counter()
    t_prev = t_start

    for event in travel_graph.stream(state_input, config=config):
        node_name = list(event.keys())[0] if event else None
        t_now = time.perf_counter()
        if node_name in NODE_LABELS:
            node_timings[node_name] = round(t_now - t_prev, 3)
        t_prev = t_now

    total_time = round(time.perf_counter() - t_start, 3)

    final_state = travel_graph.get_state(config).values
    flights_result = final_state.get("flights_result", "")
    hotel_results = final_state.get("hotel_results", "")
    itinerary = final_state.get("itinerary", "")

    record = {
        "query": query,
        "total_time_sec": total_time,
        "node_timings_sec": node_timings,
        "llm_calls": final_state.get("llm_calls", 0),
        "api_status": {
            "flight_api_success": not check_tool_failure(flights_result),
            "hotel_api_success": not check_tool_failure(hotel_results),
        },
        "completeness": completeness_score(itinerary),
        "itinerary_chars": len(itinerary),
    }

    if ENABLE_LLM_JUDGE:
        record["llm_judge"] = llm_judge_score(query, itinerary)

    return record


def summarize(results: list) -> dict:
    total_times = [r["total_time_sec"] for r in results]
    flight_success = [r["api_status"]["flight_api_success"] for r in results]
    hotel_success = [r["api_status"]["hotel_api_success"] for r in results]
    completeness_scores = [r["completeness"]["score"] for r in results]

    def pct(bools):
        return round(100 * sum(bools) / len(bools), 1) if bools else 0.0

    per_node = {}
    for node in NODE_LABELS:
        node_times = [r["node_timings_sec"].get(node) for r in results if r["node_timings_sec"].get(node) is not None]
        if node_times:
            per_node[node] = {
                "avg_sec": round(statistics.mean(node_times), 3),
                "p95_sec": round(percentile(node_times, 0.95), 3),
            }

    summary = {
        "num_queries": len(results),
        "response_time_sec": {
            "avg": round(statistics.mean(total_times), 3),
            "median": round(statistics.median(total_times), 3),
            "p95": round(percentile(total_times, 0.95), 3),
            "min": round(min(total_times), 3),
            "max": round(max(total_times), 3),
        },
        "per_node_latency_sec": per_node,
        "api_success_rate_pct": {
            "flight_api": pct(flight_success),
            "hotel_api": pct(hotel_success),
        },
        "avg_completeness_score": round(statistics.mean(completeness_scores), 3),
        "avg_llm_calls": round(statistics.mean([r["llm_calls"] for r in results]), 2),
    }

    if ENABLE_LLM_JUDGE:
        judge_avgs = [r["llm_judge"]["avg"] for r in results if "llm_judge" in r and "avg" in r["llm_judge"]]
        if judge_avgs:
            summary["avg_llm_judge_score"] = round(statistics.mean(judge_avgs), 2)

    return summary


def main():
    print(f"Running benchmark on {len(TEST_QUERIES)} queries...\n")
    results = []
    for i, q in enumerate(TEST_QUERIES, 1):
        print(f"[{i}/{len(TEST_QUERIES)}] {q}")
        try:
            r = run_single_query(q)
            results.append(r)
            print(f"    -> {r['total_time_sec']}s | completeness={r['completeness']['score']} | llm_calls={r['llm_calls']}")
        except Exception as e:
            print(f"    -> FAILED: {e}")
            results.append({
                "query": q,
                "total_time_sec": None,
                "node_timings_sec": {},
                "llm_calls": 0,
                "api_status": {"flight_api_success": False, "hotel_api_success": False},
                "completeness": {"score": 0},
                "itinerary_chars": 0,
                "error": str(e),
            })

    valid_results = [r for r in results if r.get("total_time_sec") is not None]
    summary = summarize(valid_results) if valid_results else {}

    report = {"results": results, "summary": summary}
    out_path = Path(__file__).parent / "benchmark_report.json"
    out_path.write_text(json.dumps(report, indent=2))

    print("\n" + "=" * 50)
    print("SUMMARY")
    print("=" * 50)
    print(json.dumps(summary, indent=2))
    print(f"\nFull report saved to {out_path}")


if __name__ == "__main__":
    main()
