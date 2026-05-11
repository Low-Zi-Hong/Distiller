import asyncio
from openai import OpenAI
from config import DEEPSEEK_API_KEY, DEEPSEEK_MODEL

_client = OpenAI(
    api_key=DEEPSEEK_API_KEY,
    base_url="https://api.deepseek.com/v1",
)

def _run_summarize(memory):
    turns_text = "\n".join(
        f"{m['role'].upper()}: {m['content']}"
        for m in memory.short_term
    )
    existing = memory.summary or "None yet."

    prompt = f"""You are a memory compression assistant.

Existing summary:
{existing}

New conversation turns:
{turns_text}

Write a concise updated summary (3-5 sentences) merging the old summary with the new turns.
Return only the summary text, nothing else."""

    response = _client.chat.completions.create(
        model=DEEPSEEK_MODEL,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=300,
        temperature=0.3,
    )

    memory.summary = response.choices[0].message.content.strip()
    memory.short_term.clear()
    memory.save()

async def summarize_and_compress(memory):
    await asyncio.to_thread(_run_summarize, memory)