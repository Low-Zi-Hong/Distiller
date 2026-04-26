import re
import json
import argparse
from pathlib import Path

def whatsapp_to_messages(file_path, my_name, context_len=5, output_file=None):
    if output_file is None:
        output_file = f"{my_name}_chat_format.jsonl"
        
    pattern = r'^(\d{2}/\d{2}/\d{2,4},\s\d{2}:\d{2})\s-\s([^:]+):\s(.*)'
    all_messages = []
    
    # --- 第一步：解析全文 ---
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line: continue
            
            match = re.match(pattern, line)
            if match:
                timestamp, sender, content = match.groups()
                if "<Media omitted>" in content or "omitted" in content:
                    continue
                all_messages.append({"sender": sender, "content": content})
            else:
                if all_messages:
                    all_messages[-1]["content"] += " " + line

    # --- 第二步：转换成 Messages 格式 ---
    data = []
    for i in range(len(all_messages)):
        msg = all_messages[i]
        
        # 当说话人是你时，我们以此为结尾生成一条对话流
        if msg["sender"] == my_name and msg["content"] != "You deleted this message" and msg["content"] != "This message was deleted":
            start_idx = max(0, i - context_len)
            window = all_messages[start_idx : i + 1] # 包含当前这一条
            
            if len(window) < 2: continue # 如果只有你自己说话，跳过
            
            messages_list = []
            for m in window:
                # 逻辑：如果是你，就是 assistant；如果是别人，就是 user
                role = "assistant" if m["sender"] == my_name else "user"
                messages_list.append({
                    "role": role,
                    "content": m["content"]
                })
            
            # 存入新格式：{"messages": [...]}
            data.append({"messages": messages_list})

    # --- 第三步：追加保存 ---
    with open(output_file, 'a', encoding='utf-8') as f:
        for entry in data:
            f.write(json.dumps(entry, ensure_ascii=False) + '\n')
    
    print(f"✅ 处理完成: {Path(file_path).name} -> 提取了 {len(data)} 条对话流")

def main():
    parser = argparse.ArgumentParser(description="WhatsApp 数据蒸馏工具 (Messages 格式)")
    parser.add_argument("--name", type=str, required=True, help="你在聊天记录里的名字")
    parser.add_argument("--input", type=str, default="C:/Users/lozho/Desktop/mydata/raw/", help="数据源文件夹")
    parser.add_argument("--context", type=int, default=5, help="上下文长度")
    
    args = parser.parse_args()
    data_folder = Path(args.input)
    
    if not data_folder.exists():
        print(f"❌ 找不到路径: {data_folder}")
        return

    print(f"🚀 开始炼制 {args.name} 的数字灵魂 (Context: {args.context})...")

    for item in data_folder.iterdir():
        if item.is_dir():
            # 假设结构是 /raw/folder/folder.txt
            txt_path = item / f"{item.name}.txt"
            if txt_path.exists():
                whatsapp_to_messages(
                    str(txt_path), 
                    my_name=args.name, 
                    context_len=args.context,
                    output_file=f"{args.name}_distilled_data.jsonl"
                )

if __name__ == "__main__":
    main()