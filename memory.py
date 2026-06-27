import json
import os

MEMORY_FILE = "memory.json"
MAX_MEMORY_ITEMS = 100


def load_memory():
    if not os.path.exists(MEMORY_FILE):
        return []

    try:
        with open(MEMORY_FILE, "r", encoding="utf-8") as file:
            return json.load(file)
    except (json.JSONDecodeError, OSError):
        return []


def save_memory(memory):
    with open(MEMORY_FILE, "w", encoding="utf-8") as file:
        json.dump(memory, file, indent=2)


def add_to_memory(memory, role, content):
    memory.append({"role": role, "content": content})
    if len(memory) > MAX_MEMORY_ITEMS:
        memory = memory[-MAX_MEMORY_ITEMS:]
    save_memory(memory)
    return memory


def clear_memory():
    save_memory([])


def get_messages_for_groq(memory):
    return [
        {"role": item["role"], "content": item["content"]}
        for item in memory
        if item.get("role") in {"user", "assistant"} and item.get("content")
    ]


def get_messages_for_ollama(memory):
    # Kept for the existing UI code path. The shape is also accepted by Groq.
    return get_messages_for_groq(memory)
