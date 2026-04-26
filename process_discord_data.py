import json
import re
import os
import argparse
from pathlib import Path

def clean_text(text):
    if not text: return ""
    # 过滤指令、链接和 Discord 内部标记
    if text.startswith(('!', '/', '$', '<:')): return ""
    text = re.sub(r'http\S+', '', text)
    # 去掉像 <@123...> 这样的艾特，保持纯净文本
    text = re.sub(r'<@\d+>', '', text)
    return text.strip()

def discord_to_messages(json_file, my_ids, context_len=5, output_file="distilled_data.jsonl"):
    with open(json_file, 'r', encoding='utf-8') as f:
        try:
            data = json.load(f)
            # 兼容不同层级的导出格式
            raw_messages = data.get('messages', data) if isinstance(data, dict) else data
        except Exception as e:
            print(f"❌ 读取失败 {json_file.name}: {e}")
            return 0

    # --- 第一步：清洗并拍平所有有效消息 ---
    all_cleaned_msgs = []
    for msg in raw_messages:
        # 获取 author id (兼容不同的层级结构)
        author_info = msg.get('author', {})
        current_author_id = str(author_info.get('id', msg.get('authorId', '')))
        
        raw_content = msg.get('content', '')
        content = clean_text(raw_content)
        
        # 只要有文本内容就存入列表
        if content:
            all_cleaned_msgs.append({
                "sender_id": current_author_id,
                "content": content
            })

    # --- 第二步：使用滑动窗口提取 Messages 对话流 ---
    data_pairs = []
    for i in range(len(all_cleaned_msgs)):
        msg = all_cleaned_msgs[i]
        
        # 只有当说话人是你（主号或小号）时，才生成一条训练数据
        if msg["sender_id"] in my_ids:
            start_idx = max(0, i - context_len)
            window = all_cleaned_msgs[start_idx : i + 1] # 包含你当前说的话
            
            # 如果只有你自己单机说话，没有上下文，则跳过
            if len(window) < 2: continue 
            
            messages_list = []
            for m in window:
                # 判断角色：如果是你的 ID 就是 assistant，别人就是 user
                role = "assistant" if m["sender_id"] in my_ids else "user"
                messages_list.append({
                    "role": role,
                    "content": m["content"]
                })
            
            data_pairs.append({"messages": messages_list})

    # --- 第三步：追加保存 ---
    if data_pairs:
        with open(output_file, 'a', encoding='utf-8') as f:
            for entry in data_pairs:
                f.write(json.dumps(entry, ensure_ascii=False) + '\n')
                
    return len(data_pairs)

def main():
    parser = argparse.ArgumentParser(description="Discord 数据蒸馏工具 (Messages 格式)")
    parser.add_argument("--id", type=str, default="950697325838340107", help="你的主 Discord ID")
    parser.add_argument("--id2", type=str, default="1140597224762523738", help="你的小号 Discord ID")
    parser.add_argument("--input", type=str, default="C:/Users/lozho/Desktop/mydata/raw", help="Discord JSON 文件夹路径")
    parser.add_argument("--output", type=str, default="Low_Zi_Hong_distilled_data.jsonl", help="输出文件名")
    parser.add_argument("--context", type=int, default=5, help="上下文长度 (默认 5)")
    
    args = parser.parse_args()
    
    # 将多个 ID 放入列表方便匹配
    my_ids = [args.id]
    if args.id2:
        my_ids.append(args.id2)
        
    input_folder = Path(args.input)
    
    if not input_folder.exists():
        print(f"❌ 找不到路径: {input_folder}")
        return

    print(f"🔥 开始解析 DiscordChatExporter 导出的 JSON...")
    print(f"   - 目标 ID: {my_ids}")
    print(f"   - 输出文件: {args.output}")
    
    file_exists = os.path.exists(args.output)
    if file_exists:
        print(f"⚠️ 发现已存在的 {args.output}，将开启“追加模式”。")

    total_extracted = 0
    # 递归搜索所有 .json 文件（哪怕藏在子文件夹里也能找到）
    for json_file in input_folder.rglob("*.json"):
        # 忽略掉不是对话内容的杂碎文件 (比如 package.json 等)
        if "package" in json_file.name.lower(): continue 
        
        print(f"正在炼制频道: {json_file.name}...", end="")
        count = discord_to_messages(
            json_file=json_file, 
            my_ids=my_ids, 
            context_len=args.context, 
            output_file=args.output
        )
        total_extracted += count
        print(f" 提取了 {count} 对")

    print(f"\n✅ 炼制完成！共提取了 {total_extracted} 对“灵魂对话”。")

if __name__ == "__main__":
    main()