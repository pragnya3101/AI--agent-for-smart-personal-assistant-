import sys

from groq import Groq

import config
import edge_voice as voice
import memory
import skills
from web_search import is_web_search_query, search_web


SYSTEM_PROMPT = f"""
You are {config.JARVIS_NAME}, a smart AI assistant.
Reply shortly.
"""


def get_groq_client():
    if not config.GROQ_API_KEY:
        raise RuntimeError("GROQ_API_KEY is missing. Add it to your .env file.")

    return Groq(api_key=config.GROQ_API_KEY)


def ask_ai(prompt):
    try:
        client = get_groq_client()
        response = client.chat.completions.create(
            model=config.GROQ_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
        )
        return response.choices[0].message.content
    except Exception as e:
        print(e)
        return "AI failed."


def respond(user_input, chat_history):
    normalized_input = user_input.lower().strip()

    if normalized_input in {"exit", "quit", "goodbye", "bye"}:
        return "Goodbye", True, chat_history

    skill_response = skills.handle_command(normalized_input)

    if skill_response == "EXIT":
        memory.save_memory(chat_history)
        return "Goodbye", True, chat_history

    if skill_response == "CLEAR_MEMORY":
        memory.clear_memory()
        return "Memory cleared", False, []

    if skill_response:
        return skill_response, False, chat_history

    if is_web_search_query(normalized_input):
        return search_web(normalized_input), False, chat_history

    response = ask_ai(user_input)
    chat_history = memory.add_to_memory(chat_history, "user", user_input)
    chat_history = memory.add_to_memory(chat_history, "assistant", response)
    return response, False, chat_history


def run_will(text_mode=False):
    print("=" * 40)
    print("      WILL AI ASSISTANT")
    print("=" * 40)

    voice.speak("Hello. I am Will.")
    chat_history = memory.load_memory()

    while True:
        if text_mode:
            try:
                user_input = input("You: ").lower().strip()
            except EOFError:
                break
        else:
            user_input = voice.listen()

        if not user_input:
            continue

        if not text_mode:
            print(f"You: {user_input}")

        response, should_stop, chat_history = respond(user_input, chat_history)
        voice.speak(response)

        if should_stop:
            break


if __name__ == "__main__":
    run_will(text_mode="--text" in sys.argv)
