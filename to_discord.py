import discord
import json
import os
import requests
import asyncio

# =========================
# CONFIG
# =========================

DISCORD_TOKEN = "TOKEN"
OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL_NAME = "Magikarp"

MEMORY_DIR = "memory_Magikarp"
os.makedirs(MEMORY_DIR, exist_ok=True)

MAX_RECENT_MESSAGES = 20  # before summarizing

SYSTEM_PROMPT = (
    "You are Magikarp, good at therapy people, very good at creative stuff and chatting."
    "Sometimes lazy and get annoyed"
)

# =========================
# DISCORD SETUP
# =========================

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

# =========================
# MEMORY FUNCTIONS
# =========================

def get_memory_path(channel_id):
    return os.path.join(MEMORY_DIR, f"{channel_id}.json")

def load_memory(channel_id):
    path = get_memory_path(channel_id)
    if not os.path.exists(path):
        return {"summary": "", "recent": []}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_memory(channel_id, memory):
    with open(get_memory_path(channel_id), "w", encoding="utf-8") as f:
        json.dump(memory, f, ensure_ascii=False, indent=2)

# =========================
# OLLAMA CALL
# =========================

def ask_ollama(messages):
    response = requests.post(
        OLLAMA_URL,
        json={
            "model": MODEL_NAME,
            "messages": messages,
            "stream": False
        }
    )
    return response.json()["message"]["content"]

# =========================
# PROMPT BUILDER
# =========================

def build_messages(memory, user_name, user_msg):
    messages = []

    # System prompt
    messages.append({"role": "system", "content": SYSTEM_PROMPT})

    # Memory summary
    if memory["summary"]:
        messages.append({
            "role": "system",
            "content": f"Previous conversation summary:\n{memory['summary']}"
        })

    # Recent conversation
    for msg in memory["recent"]:
        role = "assistant" if msg["user"] == "Magikarp" else "user"
        messages.append({
            "role": role,
            "content": f"{msg['user']}: {msg['content']}"
        })

    # Current user input
    messages.append({
        "role": "user",
        "content": f"{user_name}: {user_msg}"
    })

    return messages

# =========================
# SUMMARIZATION
# =========================

def summarize_memory(memory):
    convo = "\n".join(
        [f"{m['user']}: {m['content']}" for m in memory["recent"]]
    )

    prompt = [
        {"role": "system", "content": "Summarize this conversation for memory."},
        {"role": "user", "content": convo}
    ]

    summary = ask_ollama(prompt)

    # Merge summaries
    memory["summary"] = (memory["summary"] + "\n" + summary).strip()

    # Keep last few messages
    memory["recent"] = memory["recent"][-5:]

# =========================
# MAIN LOGIC
# =========================

@client.event
async def on_ready():
    print(f"Logged in as {client.user}")

@client.event
async def on_message(message):
    if message.author.bot:
        return

    # Trigger: mention or reply to bot
    if client.user in message.mentions or message.reference:
        
        channel_id = str(message.channel.id)
        memory = load_memory(channel_id)

        user_name = message.author.display_name
        user_msg = message.content

        # Add user message
        memory["recent"].append({
            "user": user_name,
            "content": user_msg
        })

        # Build prompt
        messages = build_messages(memory, user_name, user_msg)

        # Typing indicator
        async with message.channel.typing():
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None, ask_ollama, messages
            )

        # Save bot reply
        memory["recent"].append({
            "user": "Magikarp",
            "content": response
        })

        # Summarize if needed
        if len(memory["recent"]) > MAX_RECENT_MESSAGES:
            summarize_memory(memory)

        save_memory(channel_id, memory)

        await message.reply(response)

# =========================
# RUN
# =========================

client.run(DISCORD_TOKEN)