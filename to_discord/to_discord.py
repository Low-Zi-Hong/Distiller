import discord
import ollama
import asyncio

import config
from config import PERSONALITIES, DISCORD_TOKEN
from memory import UserMemory
from summarizer import summarize_and_compress

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

# ── Runtime state ──────────────────────────────────────────────────────────
_active_key: str = config.ACTIVE_MODEL
_memories: dict[tuple, UserMemory] = {}

# ── Helpers ────────────────────────────────────────────────────────────────
def get_personality() -> dict:
    return PERSONALITIES[_active_key]

def get_memory(user_id: str) -> UserMemory:
    model = get_personality()["ollama_model"]
    key = (user_id, model)
    if key not in _memories:
        _memories[key] = UserMemory(user_id, model)
    return _memories[key]

def should_respond(message: discord.Message) -> bool:
    
    if client.user in message.mentions:
        return True
    if (
        message.reference
        and message.reference.resolved
        and isinstance(message.reference.resolved, discord.Message)
        and message.reference.resolved.author == client.user
    ):
        return True
    return False

def clean_content(message: discord.Message) -> str:
    content = message.content
    for token in (f"<@{client.user.id}>", f"<@!{client.user.id}>"):
        content = content.replace(token, "")
    return content.strip()

def split_message(text: str, limit: int = 1990) -> list[str]:
    """
    Split a long response into chunks under the Discord character limit.
    Tries to break on newlines first so sentences/paragraphs stay intact,
    falls back to hard splitting if no newline exists in range.
    """
    chunks = []
    while len(text) > limit:
        # Try to find the last newline within the limit
        split_at = text.rfind("\n", 0, limit)
        if split_at == -1:
            # No newline found — hard split at limit
            split_at = limit
        chunks.append(text[:split_at].strip())
        text = text[split_at:].strip()
    if text:
        chunks.append(text)
    return chunks

async def send_reply_chunked(message: discord.Message, text: str, delay: float = 1.5):
    """
    Reply to a message with the first chunk, then send the rest as
    follow-up messages with a short delay between each to avoid rate limits.
    """
    chunks = split_message(text)

    if not chunks:
        return

    # First chunk as a proper reply so the thread context is clear
    await message.reply(chunks[0])

    # Remaining chunks sent as regular channel messages, spaced out
    for chunk in chunks[1:]:
        await asyncio.sleep(delay)
        await message.channel.send(chunk)

# ── Commands ───────────────────────────────────────────────────────────────
async def cmd_listmodel(message: discord.Message):
    lines = ["**Available personalities:**\n"]
    for key, p in PERSONALITIES.items():
        marker = " ◀ active" if key == _active_key else ""
        lines.append(f"`{key}` — **{p['display_name']}** | model: `{p['ollama_model']}`{marker}")
    await message.reply("\n".join(lines))

async def cmd_currentmodel(message: discord.Message):
    p = get_personality()
    await message.reply(
        f"Currently running **{p['display_name']}** "
        f"(`{_active_key}` → `{p['ollama_model']}`)"
    )

async def cmd_change(message: discord.Message, args: list[str]):
    global _active_key
    if not args:
        await message.reply("Usage: `!change <name>` — use `!listmodel` to see options.")
        return
    name = args[0].lower()
    if name not in PERSONALITIES:
        valid = ", ".join(f"`{k}`" for k in PERSONALITIES)
        await message.reply(f"Unknown model `{name}`. Valid options: {valid}")
        return
    _active_key = name
    p = PERSONALITIES[name]
    await message.reply(
        f"Switched to **{p['display_name']}** (`{p['ollama_model']}`). "
    )

async def cmd_memory(message: discord.Message):
    user_id = str(message.author.id)
    mem     = get_memory(user_id)

    parts = []

    if mem.summary:
        parts.append(f"**Long-term summary:**\n{mem.summary}")
    else:
        parts.append("**Long-term summary:** none yet.")

    if mem.short_term:
        recent_lines = [
            f"[{m['role']}]: {m['content'][:80]}{'...' if len(m['content']) > 80 else ''}"
            for m in mem.short_term
        ]
        parts.append("**Recent turns (short-term):**\n" + "\n".join(recent_lines))
    else:
        parts.append("**Recent turns (short-term):** none.")

    await send_reply_chunked(message, "\n\n".join(parts))

async def cmd_memoryclear(message: discord.Message):
    user_id = str(message.author.id)
    mem     = get_memory(user_id)
    p       = get_personality()
    mem.clear()
    await message.reply(
        f"Memory cleared between you with **{p['display_name']}**. "
    )

# ── Main event ─────────────────────────────────────────────────────────────
@client.event
async def on_ready():
    p = get_personality()
    print(f"Online as {client.user}  |  active: {_active_key} ({p['ollama_model']})")

@client.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return

    content = message.content.strip()

    # ── commands ───────────────────────────────────────────────
    if content.startswith("!listmodel"):
        await cmd_listmodel(message)
        return

    if content.startswith("!currentmodel"):
        await cmd_currentmodel(message)
        return

    if content.startswith("!change"):
        args = content.split()[1:]
        await cmd_change(message, args)
        return

    if content.startswith("!memory") and not content.startswith("!memoryclear"):
        await cmd_memory(message)
        return

    if content.startswith("!memoryclear"):
        await cmd_memoryclear(message)
        return

    # ── conversation ───────────────────────────────────────────
    if not should_respond(message):
        return

    user_msg = clean_content(message)
    if not user_msg:
        return

    user_id     = str(message.author.id)
    mem         = get_memory(user_id)
    personality = get_personality()

    mem.add_turn("user", user_msg)

    if mem.is_full():
        async with message.channel.typing():
            await summarize_and_compress(mem)

    context = mem.build_context(personality["system_prompt"])

    async with message.channel.typing():
        response = await asyncio.to_thread(
            ollama.chat,
            model=personality["ollama_model"],
            messages=context,
        )

    reply_text = response["message"]["content"]
    mem.add_turn("assistant", reply_text)
    mem.save()

    await send_reply_chunked(message, reply_text)

client.run(DISCORD_TOKEN)