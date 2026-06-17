"""
Load / availability test for your running FastAPI server (api.py).

This tests the system the way a real client would: over HTTP, hitting the
actual SSE endpoint, optionally with several requests in flight at once.
It measures:

  - HTTP-level success rate (did the request complete with a 200 and reach
    the "complete" SSE event, vs. timing out or erroring)
  - Per-request response time (time to receive the final "complete" event)
  - Throughput: requests handled per second under your chosen concurrency

Prereqs:
    pip install httpx
    Start your API first, in another terminal:
        python api.py
    (or: uvicorn api:app --reload)

Run with:
    python evaluation/api_load_test.py
"""

import asyncio
import json
import statistics
import time

import httpx

BASE_URL = "http://127.0.0.1:8000"

TEST_QUERIES = [
    "Plan a 3-day trip to Jaipur under ₹20,000",
    "Find flights from Delhi to Bangalore",
    "Suggest a budget itinerary for Pondicherry",
]

CONCURRENCY = 3   # how many requests in flight at once
ROUNDS = 2        # how many times to repeat the query list (total requests = len(queries) * ROUNDS)
TIMEOUT_SEC = 60.0


async def call_once(client: httpx.AsyncClient, query: str) -> dict:
    t0 = time.perf_counter()
    completed = False
    status_code = None
    error = None
    try:
        async with client.stream(
            "GET", "/api/plan/stream",
            params={"query": query},
            timeout=TIMEOUT_SEC,
        ) as resp:
            status_code = resp.status_code
            async for line in resp.aiter_lines():
                if line.startswith("event: complete") or '"itinerary"' in line:
                    completed = True
    except Exception as e:
        error = str(e)

    return {
        "query": query,
        "status_code": status_code,
        "completed": completed,
        "elapsed_sec": round(time.perf_counter() - t0, 3),
        "error": error,
    }


async def main():
    queries = TEST_QUERIES * ROUNDS
    sem = asyncio.Semaphore(CONCURRENCY)

    async def bound_call(client, q):
        async with sem:
            return await call_once(client, q)

    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        t_start = time.perf_counter()
        results = await asyncio.gather(*(bound_call(client, q) for q in queries))
        total_wall_time = time.perf_counter() - t_start

    successes = [r for r in results if r["completed"] and r["status_code"] == 200]
    times = [r["elapsed_sec"] for r in successes]

    summary = {
        "total_requests": len(results),
        "successful_requests": len(successes),
        "api_success_rate_pct": round(100 * len(successes) / len(results), 1) if results else 0,
        "concurrency": CONCURRENCY,
        "total_wall_time_sec": round(total_wall_time, 3),
        "throughput_req_per_sec": round(len(results) / total_wall_time, 3) if total_wall_time else 0,
        "response_time_sec": {
            "avg": round(statistics.mean(times), 3) if times else None,
            "p95": round(sorted(times)[int(0.95 * (len(times) - 1))], 3) if times else None,
            "max": round(max(times), 3) if times else None,
        },
        "failures": [r for r in results if not (r["completed"] and r["status_code"] == 200)],
    }

    print(json.dumps({"results": results, "summary": summary}, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
