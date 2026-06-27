import feedparser
import os
from ddgs import DDGS
from urllib.parse import quote_plus


NEWS_TOPICS = {
    "india": "India latest news",
    "indian": "India latest news",
    "telangana": "Telangana latest news",
    "hyderabad": "Hyderabad Telangana latest news",
    "technology": "India technology news",
    "tech": "India technology news",
    "sports": "India sports news",
}


def _disable_broken_proxy():
    for name in (
        "HTTP_PROXY",
        "HTTPS_PROXY",
        "http_proxy",
        "https_proxy",
        "ALL_PROXY",
        "all_proxy",
    ):
        os.environ.pop(name, None)


def get_news(topic="india", limit=5):
    _disable_broken_proxy()

    topic = (topic or "india").strip().lower()
    query = NEWS_TOPICS.get(topic, topic)

    if topic in {"top", "headlines", "general"}:
        url = "https://news.google.com/rss?hl=en-IN&gl=IN&ceid=IN:en"
    else:
        url = f"https://news.google.com/rss/search?q={quote_plus(query)}&hl=en-IN&gl=IN&ceid=IN:en"

    try:
        feed = feedparser.parse(url)
        headlines = []
        seen = set()

        for entry in feed.entries:
            title = entry.title.strip()
            key = title.lower()
            if title and key not in seen:
                headlines.append(title)
                seen.add(key)
            if len(headlines) >= limit:
                break

        if headlines:
            return headlines
    except Exception as e:
        print(e)

    try:
        with DDGS() as ddgs:
            results = ddgs.news(query, region="in-en", max_results=limit)

        return [
            result["title"].strip()
            for result in results
            if result.get("title")
        ][:limit]
    except Exception as e:
        print(e)
        return []


def read_news_aloud(speak, topic="india"):
    headlines = get_news(topic=topic)

    if not headlines:
        speak("News is not available right now.")
        return

    speak(". ".join(headlines))
