from ddgs import DDGS


def search_web(query):
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=3))

        if not results:
            return "No results found."

        answer_parts = []

        for result in results:
            body = result.get("body", "")

            if body:
                answer_parts.append(body)

        return " ".join(answer_parts)[:400]
    except Exception as e:
        print(e)
        return "Web search failed."


def is_web_search_query(text):
    text = text.lower()
    keywords = [
        "what is",
        "who is",
        "tell me about",
        "search",
        "find",
        "where is",
    ]

    return any(keyword in text for keyword in keywords)