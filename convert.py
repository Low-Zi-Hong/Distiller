import json
import glob

MY_USER_ID = "820075754846289930"

def clean_text(text):
    text = text.strip()
    if not text:
        return None
    # Optional: remove emoji-only messages
    if text.startswith(":") and text.endswith(":"):
        return None
    return text

def process_file(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    messages = data["messages"]

    processed = []
    last_role = None
    buffer = ""

    # Step 1: merge consecutive messages
    merged = []

    for msg in messages:
        content = clean_text(msg["content"])
        if not content:
            continue

        role = "assistant" if msg["author"]["id"] == MY_USER_ID else "user"

        if role == last_role:
            buffer += "\n" + content
        else:
            if buffer:
                merged.append({"role": last_role, "content": buffer})
            buffer = content
            last_role = role

    if buffer:
        merged.append({"role": last_role, "content": buffer})

    # Step 2: create pairs
    pairs = []
    for i in range(len(merged) - 1):
        if merged[i]["role"] == "user" and merged[i+1]["role"] == "assistant":
            pairs.append({
                "messages": [
                    {"role": "user", "content": merged[i]["content"]},
                    {"role": "assistant", "content": merged[i+1]["content"]}
                ]
            })

    return pairs


# Process all JSON files
all_data = []

for file in glob.glob("process/*.json"):
    all_data.extend(process_file(file))

# Save JSONL
with open("dataset.jsonl", "w", encoding="utf-8") as f:
    for item in all_data:
        f.write(json.dumps(item, ensure_ascii=False) + "\n")

print(f"Saved {len(all_data)} training samples.")