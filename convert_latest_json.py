import json
import re
from pathlib import Path
import random

# =========================
# CONFIG
# =========================
MY_ID = "820075754846289930"
INPUT_FOLDER = "F:/Appdata/Local/train/process"
OUTPUT_FILE = "F:/Appdata/Local/train/my_distilled_data.jsonl"

CONTEXT_LIMIT = 4

LOW_QUALITY = {
    "lol", "lmao", "ok", "okay", "k", "bruh",
    "nah", "ye", "yeah", "yep", "nope"
}

# =========================
# CLEANING
# =========================
def clean_text(text):
    if not text:
        return ""

    text = re.sub(r'http\S+', '', text)
    text = re.sub(r'<@\d+>', '', text)
    text = text.strip()

    return text


# =========================
# CONTEXT QUALITY CHECK
# =========================
def has_meaningful_context(context):
    # at least one message that isn't tiny
    return any(len(m["content"].split()) >= 6 for m in context)


# =========================
# SHORT REPLY LOGIC (KEY)
# =========================
def allow_short_reply(text, context):
    words = text.split()

    # long replies always allowed
    if len(words) >= 4:
        return True

    # short replies allowed ONLY if context is meaningful
    return has_meaningful_context(context)

# =========================
# RANDOMNESS???
# =========================

def allow_short_reply(text, context):
    words = text.split()

    if len(words) >= 4:
        return True

    if not has_meaningful_context(context):
        return False

    # 🔥 key fix: only keep SOME short replies
    return random.random() < 0.3

# =========================
# MAIN PROCESS
# =========================
print("🔥 Processing Discord dataset (v3)...")

total_saved = 0

with open(OUTPUT_FILE, 'w', encoding='utf-8') as out_f:

    for json_file in Path(INPUT_FOLDER).glob("*.json"):
        print(f"Processing: {json_file.name}")

        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            messages = data.get('messages', data)

        context = []

        for msg in messages:
            author_id = str(msg['author']['id'])
            raw = msg.get('content', '')
            content = clean_text(raw)

            if not content:
                continue

            is_me = author_id == MY_ID
            role = "assistant" if is_me else "user"

            # =========================
            # FILTER OTHER USERS HARDER
            # =========================
            if not is_me:
                # remove super short noise
                if len(content.split()) < 3:
                    continue

                # remove low quality single words
                if content.lower() in LOW_QUALITY:
                    continue

            # add to context
            context.append({
                "role": role,
                "content": content
            })

            if len(context) > CONTEXT_LIMIT:
                context.pop(0)

            # =========================
            # SAVE WHEN YOU REPLY
            # =========================
            if is_me:

                # need at least 1 user message before
                if len(context) < 2:
                    context = []
                    continue

                # separate context and reply
                reply = context[-1]
                prev_context = context[:-1]

                # filter context quality
                filtered_context = [
                    m for m in prev_context
                    if len(m["content"].split()) >= 3
                ]

                if not filtered_context:
                    context = []
                    continue

                # key logic: allow short replies ONLY with good context
                if not allow_short_reply(reply["content"], filtered_context):
                    context = []
                    continue

                entry = {
                    "messages": filtered_context + [reply]
                }

                # save
                out_f.write(json.dumps(entry, ensure_ascii=False) + '\n')
                total_saved += 1

                # slight bias toward longer replies
                if len(reply["content"].split()) >= 6:
                    out_f.write(json.dumps(entry, ensure_ascii=False) + '\n')
                    total_saved += 1

                # reset after reply
                context = []

print(f"\n✅ Done. Saved {total_saved} conversations.")