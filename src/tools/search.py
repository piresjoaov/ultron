from ddgs import DDGS

def web_search(query: str, max_results: int = 3) -> str:
    try:
        if not query or not query.strip():
            return "Error: 'query' parameter cannot be empty."

        safe_max_results = max(1, min(max_results, 5))

        with DDGS() as ddgs:
            raw_results = list(ddgs.text(query, max_results=safe_max_results))

        if not raw_results:
            return f"No results found on the web for '{query}'."

        formatted = [f"Search results for '{query}':"]
        for idx, item in enumerate(raw_results, start=1):
            title = item.get("title", "No title")
            snippet = item.get("body", "No description available.")
            link = item.get("href", "No link available.")
            formatted.append(f"{idx}. {title}\n   Snippet: {snippet}\n   URL: {link}")

        return "\n\n".join(formatted)

    except Exception as e:
        return f"Error while performing web search: {str(e)}"