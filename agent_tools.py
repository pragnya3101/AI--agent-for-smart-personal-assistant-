"""
agent_tools.py
Defines tool schemas for Groq function-calling and dispatches calls
to your existing skill functions. This replaces ad-hoc regex parsing
with LLM-driven structured intent extraction.
"""

import json
import skills
import spotify_control
import messenger
import news_reader

# ---- Tool schemas (OpenAI/Groq function-calling format) ----
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "send_email",
            "description": "Send an email to a known contact.",
            "parameters": {
                "type": "object",
                "properties": {
                    "contact": {"type": "string", "description": "Contact name, e.g. amma, akka, pragnya"},
                    "subject": {"type": "string"},
                    "body": {"type": "string"},
                },
                "required": ["contact", "body"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "send_whatsapp",
            "description": "Send a WhatsApp message to a known contact.",
            "parameters": {
                "type": "object",
                "properties": {
                    "contact": {"type": "string"},
                    "message": {"type": "string"},
                },
                "required": ["contact", "message"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "play_music",
            "description": "Play a song on Spotify, or open Spotify with no song.",
            "parameters": {
                "type": "object",
                "properties": {
                    "song": {"type": "string", "description": "Song name; empty string to just open Spotify"},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "control_music",
            "description": "Pause music or skip to next song.",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {"type": "string", "enum": ["pause", "next"]},
                },
                "required": ["action"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_news",
            "description": "Get top news headlines for a topic.",
            "parameters": {
                "type": "object",
                "properties": {
                    "topic": {
                        "type": "string",
                        "enum": ["india", "telangana", "hyderabad", "technology", "sports"],
                    },
                },
                "required": ["topic"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "system_info",
            "description": "Get system info: battery percent, take a screenshot, or check internet speed.",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {"type": "string", "enum": ["battery", "screenshot", "speed", "time"]},
                },
                "required": ["action"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "control_volume",
            "description": "Set, raise, lower, mute, or unmute system volume.",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {"type": "string", "enum": ["set", "up", "down", "mute", "unmute"]},
                    "level": {"type": "integer", "description": "Only for action=set, 0-100"},
                },
                "required": ["action"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "open_website",
            "description": "Open a website in the default browser.",
            "parameters": {
                "type": "object",
                "properties": {"site": {"type": "string"}},
                "required": ["site"],
            },
        },
    },
]


def execute_tool_call(name, arguments_json):
    """Dispatch a single tool call (from Groq) to the real skill function."""
    try:
        args = json.loads(arguments_json) if arguments_json else {}
    except json.JSONDecodeError:
        args = {}

    if name == "send_email":
        return messenger.send_email(
            args.get("contact", ""), args.get("subject", "Message from Will"), args.get("body", "")
        )

    if name == "send_whatsapp":
        return messenger.send_whatsapp(args.get("contact", ""), args.get("message", ""))

    if name == "play_music":
        song = args.get("song", "")
        return spotify_control.play_song(song) if song else spotify_control.open_spotify()

    if name == "control_music":
        action = args.get("action")
        if action == "pause":
            return spotify_control.pause_music()
        if action == "next":
            return spotify_control.next_song()
        return "Say pause or next"

    if name == "get_news":
        topic = args.get("topic", "india")
        headlines = news_reader.get_news(topic=topic, limit=5)
        return ". ".join(headlines) if headlines else "News is not available right now"

    if name == "system_info":
        action = args.get("action")
        if action == "battery":
            return skills.get_battery()
        if action == "screenshot":
            return skills.take_screenshot()
        if action == "speed":
            return skills.check_speed()
        if action == "time":
            return skills.get_time()
        return "Unknown system action"

    if name == "control_volume":
        action = args.get("action")
        if action == "set":
            return skills.set_volume(int(args.get("level", 50)))
        if action == "up":
            return skills.change_volume(10)
        if action == "down":
            return skills.change_volume(-10)
        if action == "mute":
            return skills.set_mute(True)
        if action == "unmute":
            return skills.set_mute(False)
        return "Unknown volume action"

    if name == "open_website":
        site = args.get("site", "")
        url = skills._normalize_site_url(site)
        if not url:
            return "Say the website name, for example: open google.com"
        import webbrowser
        webbrowser.open(url)
        return f"Opening {url}"

    return f"Unknown tool: {name}"