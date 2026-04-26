import json
import re
from pathlib import Path

MY_ID = "820075754846289930"
INPUT_FOLDER = "F:/Appdata/Local/train/process"
OUTPUT_FILE = "F:/Appdata/Local/train/my_distilled_data.jsonl"

CONTEXT_LIMIT = 4
MIN_LENGTH = 3

def clean_text(text):
    if not text:
        return ""

    text = re.sub(r'http\S+', '', text)
    text = re.sub(r'<@\d+>', '', text)
    text = text.strip()

    LOW_QUALITY = {
    "lol", "lmao", "ok", "okay", "k", "bruh",
    "nah", "ye", "yeah", "yep", "nope", "hmm", "mmh", "waw", "o", ":snas:"
}

    # filter junk
    if author_id != MY_ID:
        if len(text.split()) < 2:
            return ""
    
    if re.fullmatch(r'[\W_]+', text):
        return ""


    if text.lower() in LOW_QUALITY:
        return ""

    if text.startswith(('!', '/', '$')):
        return ""

    return text


print("🔥 Processing Discord data...")

for json_file in Path(INPUT_FOLDER).glob("*.json"):
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
        messages = data.get('messages', data)

    context = []

    with open(OUTPUT_FILE, 'a', encoding='utf-8') as out_f:
        for msg in messages:
            author_id = str(msg['author']['id'])
            content = clean_text(msg.get('content', ''))

            if not content:
                continue

            role = "assistant" if author_id == MY_ID else "user"

            context.append({
                "role": role,
                "content": content
            })

            # keep context small
            if len(context) > CONTEXT_LIMIT:
                context.pop(0)

            # only save when YOU reply
            if role == "assistant":
                # ensure last message is assistant
                if len(context) >= 2:
                    entry = {
                        "messages": context.copy()
                    }
                    out_f.write(json.dumps(entry, ensure_ascii=False) + '\n')

                # reset after response (important!)
                context = []

print("✅ Done.")
