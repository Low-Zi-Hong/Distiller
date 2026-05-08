import discord
import requests
import os
import json
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
OLLAMA_URL = "https://competition-showed-sticker-paperback.trycloudflare.com/api/chat"
MODEL_NAME = "mytwin"

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

# 🔥 核心改动：用字典记录每个人的专属对话历史
# 格式: { 用户ID: "历史记录字符串" }
user_histories = {}

# Helper to keep the list clean
def add_to_memory(user_id, role, content):
    if user_id not in user_histories:
        user_histories[user_id] = []
    
    user_histories[user_id].append({"role": role, "content": content})

@client.event
async def on_ready():
    print(f'已登录为 {client.user}，你的带记忆数字孪生已上线！')

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if client.user.mentioned_in(message) or isinstance(message.channel, discord.DMChannel):
        async with message.channel.typing():
            user_id = message.author.id
            

            if user_id not in user_histories:
                user_histories[user_id] = []

            # 1. Memory Compression (Check number of messages, e.g., > 20 messages)
            if len(user_histories[user_id]) > 20:
                print(f"🧹 Memory full for {message.author.name}, compressing...")
                # You'd send the list to a summarizer here, then reset the list
                # For now, let's just keep the last 10 to keep it simple
                user_histories[user_id] = user_histories[user_id][-10:]

            # 2. Add the NEW message from the user
            clean_msg = message.content.replace(f'<@!{client.user.id}>', '').replace(f'<@{client.user.id}>', '').strip()
            # We tag the name so the model knows who is talking (as we discussed)
            add_to_memory(user_id, "user", clean_msg)
            
            response = requests.post(OLLAMA_URL, json={
                "model": MODEL_NAME,
                "prompt": user_histories[user_id],
                "stream": False,
                "options": {
                    "stop": ["User:", "\nUser:", "Assistant:", "\nAssistant:"] 
                }
            })
            
            answer = response.json().get('message', {}, '我断网了...')

            # ==========================================
            # 3. 存储 AI 的回答并更新记忆
            # ==========================================
            add_to_memory(user_id, "assistant", answer)

            await message.reply(answer)

client.run(TOKEN)