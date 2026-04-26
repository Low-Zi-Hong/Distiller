import json

lengths = []

with open("my_distilled_data.jsonl", encoding="utf-8") as f:
    for line in f:
        data = json.loads(line)
        for msg in data["messages"]:
            if msg["role"] == "assistant":
                lengths.append(len(msg["content"].split()))

print("Avg length:", sum(lengths)/len(lengths))
print("Short %:", sum(1 for x in lengths if x < 4)/len(lengths))