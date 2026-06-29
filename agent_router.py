"""
agent_router.py
Uses Groq function-calling to decide whether user input maps to an
action (tool call) or a normal conversational reply. This replaces
relying purely on regex in skills.py for ambiguous phrasing.
"""

import config
from groq import Groq
from agent_tools import TOOLS, execute_tool_call

SYSTEM_PROMPT = f"""You are {config.JARVIS_NAME}, a smart AI assistant.
If the user's request matches one of the available tools, call it.
Only call a tool when you're confident about the action and arguments.
Otherwise, just reply normally and briefly.
"""


def get_client():
    if not config.GROQ_API_KEY:
        raise RuntimeError("GROQ_API_KEY is missing. Add it to your .env file.")
    return Groq(api_key=config.GROQ_API_KEY)


def route(user_input, chat_history=None):
    """
    Returns (response_text, tool_was_used: bool)
    """
    client = get_client()
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    if chat_history:
        messages.extend(chat_history[-6:])  # keep recent context small
    messages.append({"role": "user", "content": user_input})

    try:
        response = client.chat.completions.create(
            model=config.GROQ_MODEL,
            messages=messages,
            tools=TOOLS,
            tool_choice="auto",
        )
    except Exception as e:
        print(e)
        return "AI failed.", False

    message = response.choices[0].message

    if message.tool_calls:
        results = []
        for call in message.tool_calls:
            result = execute_tool_call(call.function.name, call.function.arguments)
            results.append(result)
        return ". ".join(r for r in results if r), True

    return message.content or "I didn't quite get that.", False