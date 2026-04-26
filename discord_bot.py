import discord
import requests
import json
import os
from dotenv import load_dotenv

load_dotenv() # 自动加载 .env 里的变量
TOKEN = os.getenv("DISCORD_TOKEN") # 这样代码里就没有明文密钥了
# 配置
OLLAMA_URL = "https://competition-showed-sticker-paperback.trycloudflare.com/api/generate"
MODEL_NAME = "mytwin"

intents = discord.Intents.default()
intents.message_content = True # 必须开启，否则收不到消息内容
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f'已登录为 {client.user}，你的数字孪生已上线！')

@client.event
async def on_message(message):
    # 不回应机器人自己的消息
    if message.author == client.user:
        return

    # 只有在私聊或被 @ 时才回应（防止频道刷屏）
    if client.user.mentioned_in(message) or isinstance(message.channel, discord.DMChannel):
        async with message.channel.typing(): # 显示“正在输入...”
            prompt = message.content.replace(f'<@!{client.user.id}>', '').strip()
            
            # 调用本地 Ollama
            response = requests.post(OLLAMA_URL, json={
                "model": MODEL_NAME,
                "prompt": prompt,
                "stream": False
            })
            
            answer = response.json().get('response', '我断网了...')
            await message.reply(answer)

client.run(TOKEN)