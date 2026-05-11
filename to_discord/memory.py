import json
import os
from collections import deque
from config import SHORT_TERM_LIMIT

MEMORY_DIR = "memories"
os.makedirs(MEMORY_DIR, exist_ok=True)

class UserMemory:
    def __init__(self, user_id: str, model_name: str):
        self.user_id    = user_id
        self.model_name = model_name
        self.short_term: deque = deque(maxlen=SHORT_TERM_LIMIT)
        self.summary: str      = ""
        self._load()

    def _path(self) -> str:
        folder = os.path.join(MEMORY_DIR, self._safe_name(self.model_name))
        os.makedirs(folder, exist_ok=True)
        return os.path.join(folder, f"{self.user_id}.json")

    @staticmethod
    def _safe_name(name: str) -> str:
        return "".join(c if c.isalnum() or c in "-_" else "_" for c in name)

    def _load(self):
        if os.path.exists(self._path()):
            data = json.load(open(self._path()))
            self.summary = data.get("summary", "")
            for msg in data.get("recent", []):
                self.short_term.append(msg)

    def save(self):
        json.dump(
            {
                "model":   self.model_name,
                "summary": self.summary,
                "recent":  list(self.short_term),
            },
            open(self._path(), "w"),
            indent=2,
        )

    def clear(self):
        """Wipe all memory for this user under the current model."""
        self.summary = ""
        self.short_term.clear()
        if os.path.exists(self._path()):
            os.remove(self._path())

    def add_turn(self, role: str, content: str):
        self.short_term.append({"role": role, "content": content})

    def is_full(self) -> bool:
        return len(self.short_term) >= SHORT_TERM_LIMIT

    def build_context(self, system_prompt: str) -> list[dict]:
        messages = []

        system_parts = [system_prompt]
        if self.summary:
            system_parts.append(f"[Memory — past summary]\n{self.summary}")

        messages.append({"role": "system", "content": "\n\n".join(system_parts)})
        messages.extend(list(self.short_term))
        return messages