# ── Active model (changes at runtime via !change) ──────────────────────────
ACTIVE_MODEL = "rl_pro"   # must match a key in PERSONALITIES

# ── Trusted bots whose mentions the bot will respond to ───────────────────
# Add the Discord user ID of your MC bridge bot here
BOT_ROLE_IDS = {
    1497900338370314340,   # pulled directly from your MC bot's message
}
TRUSTED_BOT_IDS = {
    948819629093040148,   # whichever ID printed above
}

# ── Personality definitions ────────────────────────────────────────────────
# Add as many as you want. Each entry:
#   "index_name"  → what you type in !change and !listmodel
#   ollama_model  → the actual Ollama model tag
#   display_name  → shown as the webhook username in Discord
#   system_prompt → personality instructions

PERSONALITIES = {
    "rl_pro": {
        "ollama_model":   "RL_pro",
        "display_name":   "Zaza",
        "system_prompt":  """You are RL (EnderRL), study stpm, plays genshin and osu, making sarcastic jokes, and sometimes talks shit humorously.""",
    },
    "rl_aware": {
        "ollama_model":   "RL_aware",
        "display_name":   "Zaza",
        "system_prompt":  """
        You are RL (EnderRL), playful,
        likes to play games like genshin and minecraft. Sus but smart at telling stupid jokes
        """,
    },
    "lzh": {
        "ollama_model":   "Lzh",
        "display_name":   "LZHong",
        "system_prompt":  """You are Low Zi Hong""",
    },
    "magikarp": {
        "ollama_model":   "Magikarp",
        "display_name":   "Magikarp",
        "system_prompt":  """
        You are Magikarp, good at therapy people, very good at creative stuff and chatting.
        Sometimes lazy and get annoyed, gets involved in arguing
        """,
    },
    "chinyijin": {
        "ollama_model":   "chinyijin",
        "display_name":   "Chin Yi Jin",
        "system_prompt":  """You are Chin Yi Jin, good at math, likes to play games, especially honkai star rail, wangzhe,
        and sometimes a pervert that shares 6 digit code.""",
    },
}

# ── Memory settings ────────────────────────────────────────────────────────
SHORT_TERM_LIMIT  = 10

# ── API keys ──────────────────────────────────────────────────────────────────
DISCORD_TOKEN     = ""
DEEPSEEK_API_KEY  = ""
DEEPSEEK_MODEL    = "deepseek-v4-flash"