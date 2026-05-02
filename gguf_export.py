import argparse
from unsloth import FastLanguageModel
from pathlib import Path
import os

def main():
    parser = argparse.ArgumentParser(description="数字孪生 GGUF 导出脚本")
    # 默认指向你刚才训练保存的 LoRA 文件夹
    parser.add_argument("--folder", type=str, default="lora_model", help="LoRA 适配器文件夹路径")
    parser.add_argument("--output", type=str, default="final_model", help="导出的文件夹名称")
    args = parser.parse_args()

    lora_path = Path(args.folder)
    
    if not lora_path.exists():
        print(f"❌ 错误：找不到文件夹 {lora_path}，请确认路径是否正确。")
        return

    # 1. 加载模型
    # 注意：max_seq_length 最好与你训练时保持一致
    print(f"🔄 正在从 {lora_path} 加载模型...")
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name = str(lora_path), 
        max_seq_length = 2048,
        load_in_4bit = True,
    )

    # 2. 导出 GGUF
    # quantization_method "q4_k_m" 是目前 Ollama 用户最常用的 4-bit 格式
    print("📦 正在炼制 GGUF 文件...")
    print("⚠️  提示：这一步非常消耗内存（RAM），如果报错请关闭浏览器等占用内存的程序。")

    try:
        model.save_pretrained_gguf(
            args.output, 
            tokenizer, 
            quantization_method = "q8_0" # q4_k_m, q5_k_m, q8_0
        )
        print(f"✅ 导出成功！")
        print(f"📂 你的 GGUF 文件就在这里: {os.path.abspath(args.output)}")
    except Exception as e:
        print(f"❌ 导出失败: {e}")

if __name__ == "__main__":
    main()