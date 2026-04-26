import re
import json
from pathlib import Path

import argparse

# --- 运行部分 ---
data_folder = "C:/Users/lozho/Desktop/mydata/raw/"
my_name = "Low Zi Hong"

def main():
    # 1. 创建解析器
    parser = argparse.ArgumentParser(description="WhatsApp 数据蒸馏工具")
    
    # 2. 定义你想接收的参数
    parser.add_argument("--name", type=str, required=True, help="你在聊天记录里的名字")
    #parser.add_argument("--context", type=int, default=5, help="上下文长度 (默认 5)")
    parser.add_argument("--input", type=str, default="C:/Users/lozho/Desktop/mydata/raw/", help="数据文件夹路径")

    # 3. 解析参数
    args = parser.parse_args()

    data_folder = args.input
    my_name = args.name

    # 4. 使用这些参数
    print(f"🚀 开始炼制！名字: {args.name}, Input: {args.input}")

def whatsapp_to_instruction(file_path, my_name, context_len=5, output_file="my_distilled_data.jsonl"):
    # 匹配格式: 25/04/2026, 10:00 - 姓名: 内容
    pattern = r'^(\d{2}/\d{2}/\d{2,4},\s\d{2}:\d{2})\s-\s([^:]+):\s(.*)'
    
    all_messages = []
    
    # --- 第一步：解析全文，处理换行，存入列表 ---
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line: continue
            
            match = re.match(pattern, line)
            if match:
                timestamp, sender, content = match.groups()
                # 过滤掉媒体文件提示
                if "<Media omitted>" in content or "omitted" in content:
                    continue
                all_messages.append({"sender": sender, "content": content})
            else:
                # 处理多行消息：合并到上一条
                if all_messages:
                    all_messages[-1]["content"] += " " + line

    # --- 第二步：使用滑动窗口提取带 Context 的对话对 ---
    data = []
    for i in range(len(all_messages)):
        msg = all_messages[i]
        
        # 只有当说话人是你时，才生成一个训练条目
        if msg["sender"] == my_name:
            # 抓取当前消息之前的 context_len 条记录
            start_idx = max(0, i - context_len)
            context_msgs = all_messages[start_idx : i]
            
            if not context_msgs: continue # 如果你开场第一句话，没上下文，跳过
            
            # 将上下文格式化： "姓名: 内容" 拼接起来
            # 这样模型能学会区分是谁在说话
            instruction_list = [f"{m['sender']}: {m['content']}" for m in context_msgs]
            instruction_text = "\n".join(instruction_list)
            
            data.append({
                "instruction": instruction_text,
                "input": "",
                "output": msg["content"]
            })

    # --- 第三步：追加保存 ---
    with open(output_file, 'a', encoding='utf-8') as f:
        for entry in data:
            f.write(json.dumps(entry, ensure_ascii=False) + '\n')
    
    print(f"源文件 {Path(file_path).name}: 提取了 {len(data)} 组带上下文的对话。")



if __name__ == "__main__":
    main()
    for item in Path(data_folder).iterdir():
        # 假设你的文件夹结构是 /raw/folder/folder.txt
        txt_path = item / f"{item.name}.txt"
        if txt_path.exists():
            whatsapp_to_instruction(str(txt_path), my_name=my_name, context_len=5)