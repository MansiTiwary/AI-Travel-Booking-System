import os
from tavily import TavilyClient
from dotenv import load_dotenv

load_dotenv()

client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))


def tavily_search(query: str) -> str:
    try:
        response = client.search(query=query, max_results=5)
    except Exception as e:
        return f"Hotel search failed: {str(e)}"

    results = []

    for i, r in enumerate(response.get("results", []), 1):
        title   = r.get("title", "Unknown")
        url     = r.get("url", "")
        snippet = r.get("content", "").strip()

        if len(snippet) > 300:
            snippet = snippet[:300].rsplit(" ", 1)[0] + "..."

        results.append(
            f"{i}. {title}\n"
            f"   🔗 {url}\n"
            f"   {snippet}\n"
        )

    if not results:
        return "No hotel results found for the given query."

    return "\n\n".join(results)