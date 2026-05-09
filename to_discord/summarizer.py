import asyncio
from openai import OpenAI
from config import DEEPSEEK_API_KEY, DEEPSEEK_MODEL, MAX_STORED_FACTS

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

Tasks:
1. Write a concise updated summary (3-5 sentences) merging old + new.
2. List any important NEW facts about the user (name, preferences, topics discussed).
   Format: FACTS: fact1 | fact2 | ...
   Write FACTS: none  if nothing new.

Updated summary:"""

    response = _client.chat.completions.create(
        model=SUMMARIZE_MODEL,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=500,
        temperature=0.3,
    )

    text = response.choices[0].message.content.strip()
    lines = text.split("\n")
    facts_line    = next((l for l in lines if l.startswith("FACTS:")), "FACTS: none")
    summary_lines = [l for l in lines if not l.startswith("FACTS:")]

    memory.summary = "\n".join(summary_lines).strip()

    raw_facts = facts_line.replace("FACTS:", "").strip()
    if raw_facts.lower() != "none":
        new_facts = [f.strip() for f in raw_facts.split("|") if f.strip()]
        memory.facts.extend(new_facts)
        memory.facts = memory.facts[-MAX_STORED_FACTS:]

    memory.short_term.clear()
    memory.save()

async def summarize_and_compress(memory):
    await asyncio.to_thread(_run_summarize, memory)