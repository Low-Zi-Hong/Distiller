import discord
import requests
import os
import json
from dotenv import load_dotenv
from pathlib import Path
import aiohttp

useDeepSeek = False

user_histories = {}

load_dotenv()
#deal with memory here
data_folder = Path("Bot_Memory")
data_folder.mkdir(exist_ok=True)


for json_file in data_folder.rglob("*.json"):
    with open(json_file, 'r', encoding='utf-8') as f:
        try:
            data = json.load(f)
            user_id = int(json_file.stem)
            user_histories[user_id] = data
        except Exception as e:
            print(f"❌ 读取失败 {json_file.name}: {e}")
    print(f"✅ 成功加载了 {len(user_histories)} 个用户的记忆！")

def save_memory(user_id):
    """Saves a specific user's history to their JSON file."""
    file_path = data_folder / f"{user_id}.json"
    
    with open(file_path, 'w', encoding='utf-8') as f:
        # indent=4 makes the JSON file pretty and readable for humans
        json.dump(user_histories[user_id], f, ensure_ascii=False, indent=4)

#deepseek
deepseek_token = os.getenv("DEEPSEEK_TOKEN")
DEEPSEEK_URL = "https://api.deepseek.com/chat/completions"
payload={}

"""
headers = {
  'Accept': 'application/json',
  'Authorization': "Bearer " + deepseek_token
}

response_deepseek = requests.request("GET", DEEKSEEK_URL, headers=headers, data=payload)
"""

#Ollama

TOKEN = os.getenv("DISCORD_TOKEN")
OLLAMA_URL = "http://127.0.0.1:11434/api/chat"
MODEL_NAME = "lzhModel"

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

# 🔥 核心改动：用字典记录每个人的专属对话历史
# 格式: { 用户ID: "历史记录字符串" }

# Helper to keep the list clean
def add_to_memory(user_id, role, content):
    if user_id not in user_histories:
        user_histories[user_id] = []
    
    user_histories[user_id].append({"role": role, "content": content})

async def summarise_memory(message,us):
    print(f"🧹 Memory full for {message.author.name}, compressing...")
    # You'd send the list to a summarizer here, then reset the list
    # For now, let's just keep the last 10 to keep it simple

    #using deepseek to compress
    ds_payload = {
        "messages": [
            {
            "content": "You are a summariser. Summerise the below conversation to a short description about what is going on.",
            "role": "system"
            }
        ] + us[user_id],
        "model": "deepseek-v4-flash",
        "thinking": {
            "type": "enabled"
        },
        "reasoning_effort": "high",
        "max_tokens": 4096,
        "response_format": {
            "type": "text"
        },
        "stop": None,
        "stream": False,
        "stream_options": None,
        "temperature": 1,
        "top_p": 1,
        "tools": None,
        "tool_choice": "none",
        "logprobs": False,
        "top_logprobs": None
        }
    ds_headers = {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    'Authorization': 'Bearer ' + deepseek_token
    }

    #ds_response = requests.request("POST", DEEKSEEK_URL, headers=ds_headers, data=ds_payload)

    async with aiohttp.ClientSession() as session:
                async with session.post(DEEPSEEK_URL, headers=ds_headers, json=ds_payload) as ds_response:
                    resp_json = await ds_response.json()

    print(json.dumps(resp_json))
    memory = [{"role" : "assistant", "content" : resp_json.get("choices",[{}])[0].get("message",{}).get("content","")}] +  us[user_id][-4:]
    return memory

@client.event
async def on_ready():
    print(f'已登录为 {client.user}，你的带记忆数字孪生已上线！')

@client.event
async def on_message(message):
    global user_histories

    if message.author == client.user:
        return

    if client.user.mentioned_in(message) or isinstance(message.channel, discord.DMChannel):
        async with message.channel.typing():
            user_id = message.author.id
            

            if user_id not in user_histories:
                user_histories[user_id] = []

            # 1. Memory Compression (Check number of messages, e.g., > 20 messages)
            if len(user_histories[user_id]) > 20:
                if(useDeepSeek):
                    user_histories[user_id] = await summarise_memory(message,user_histories)
                else:
                    response = requests.post(OLLAMA_URL, json={
                        "model": MODEL_NAME,
                        "messages":  {
                            "content": "You are a summariser. Summerise the below conversation to a short description about what is going on.",
                            "role": "system"
                            } + user_histories[user_id],
                        "stream": False
                    memory = [{"role" : "assistant", "content" : response.json().get("message",{}).get("content",{})}] +  us[user_id][-4:]
                    user_histories[user_id] = memory
            })


            # 2. Add the NEW message from the user
            clean_msg = message.content.replace(f'<@!{client.user.id}>', '').replace(f'<@{client.user.id}>', '').strip()
            # We tag the name so the model knows who is talking (as we discussed)
            add_to_memory(user_id, "user", clean_msg)
            
            response = requests.post(OLLAMA_URL, json={
                "model": MODEL_NAME,
                "messages": user_histories[user_id],
                "stream": False
            })

            #print("promt: \t" +json.dumps(user_histories[user_id]))

            
            answer = response.json().get('message', {}).get('content',{})


            #print("response: \t" + json.dumps(response.json()))
            # ==========================================
            # 3. 存储 AI 的回答并更新记忆
            # ==========================================
            add_to_memory(user_id, "assistant", answer)

            if answer == "":
                answer = "no response from model!"

            save_memory(user_id)

            await message.reply(answer)

client.run(TOKEN)