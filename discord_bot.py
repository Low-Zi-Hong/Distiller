import discord
import requests
import os
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
OLLAMA_URL = "https://competition-showed-sticker-paperback.trycloudflare.com/api/generate"
MODEL_NAME = "mytwin"

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

# 🔥 核心改动：用字典记录每个人的专属对话历史
# 格式: { 用户ID: "历史记录字符串" }
user_histories = {}

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
            
            # 如果是新用户，初始化他的记忆库
            if user_id not in user_histories:
                user_histories[user_id] = ""
            
            current_history = user_histories[user_id]

            # ==========================================
            # 1. 记忆压缩系统 (你超棒的 Idea)
            # ==========================================
            if len(current_history) > 1000:
                print(f"🧹 记忆过长，正在压缩 {message.author.name} 的对话...")
                summary_prompt = "Please summarize the conversation below in under 50 words, keeping the main context:\n" + current_history
                
                sum_resp = requests.post(OLLAMA_URL, json={
                    "model": MODEL_NAME,
                    "prompt": summary_prompt,
                    "stream": False
                })
                # 正确提取总结的文字
                summary_text = sum_resp.json().get('response', '')
                current_history = f"[之前的对话总结: {summary_text}]\n"

            # ==========================================
            # 2. 拼接新对话并请求 AI
            # ==========================================
            # 清理掉 @ 机器人的无用字符
            clean_msg = message.content.replace(f'<@!{client.user.id}>', '').replace(f'<@{client.user.id}>', '').strip()
            
            # 加上 User 和 Twin 的前缀，让模型知道谁在说话
            current_history += f"User: {clean_msg}\nTwin:"
            
            response = requests.post(OLLAMA_URL, json={
                "model": MODEL_NAME,
                "prompt": current_history,
                "stream": False
            })
            
            answer = response.json().get('response', '我断网了...')

            # ==========================================
            # 3. 存储 AI 的回答并更新记忆
            # ==========================================
            current_history += f" {answer}\n"
            user_histories[user_id] = current_history # 存回字典里

            await message.reply(answer)

client.run(TOKEN)