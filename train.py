import argparse
import torch
from pathlib import Path
from datasets import load_dataset
from unsloth import FastLanguageModel
from trl import SFTTrainer
from transformers import TrainingArguments

def main():
    parser = argparse.ArgumentParser(description="数字孪生本地训练脚本")
    # 修正：如果你设置了 default，通常就不设 required=True，方便直接运行
    parser.add_argument("--data", type=str, default="my_distilled_data.jsonl", help="你的 JSONL 语料路径")
    args = parser.parse_args()

    data_path = Path(args.data)
    if not data_path.exists():
        print(f"❌ 找不到数据文件: {data_path}")
        return

    # 1. 加载模型 (针对 12GB VRAM 优化)
    max_seq_length = 2048 # 你的聊天记录带 Context，设长一点比较稳
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name = "unsloth/qwen2-7b-instruct-bnb-4bit",
        max_seq_length = max_seq_length,
        load_in_4bit = True,
    )

    # 2. 添加 LoRA 适配器
    model = FastLanguageModel.get_peft_model(
        model,
        r = 16, 
        target_modules = ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
        lora_alpha = 16,
        lora_dropout = 0,
        bias = "none",
    )

    # 3. 加载并处理数据
    dataset = load_dataset("json", data_files=str(data_path), split="train")
    
    # 测试阶段取 100 条，正式跑记得删掉这一行
    dataset = dataset.shuffle(seed=42).select(range(min(100, len(dataset))))

    def format_chat(example):
        # 使用 Qwen2 官方模板将 messages 列表转为纯文本
        text = tokenizer.apply_chat_template(
            example["messages"],
            tokenize = False,
            add_generation_prompt = False # 训练时不需要生成提示符
        )
        return {"text": text}

    dataset = dataset.map(format_chat, num_proc=2)

    # 4. 设置训练器
    trainer = SFTTrainer(
        model = model,
        tokenizer = tokenizer,
        train_dataset = dataset,
        dataset_text_field = "text",
        max_seq_length = max_seq_length,
        dataset_num_proc = 2,
        packing = True, # 开启 packing 可以让 12GB 显存训练效率更高
        args = TrainingArguments(
            per_device_train_batch_size = 2, # 12GB 卡设为 2 比较保险
            gradient_accumulation_steps = 4, # 累积 4 步，等效 Batch Size = 8
            warmup_steps = 5,
            max_steps = 100, 
            learning_rate = 2e-4,
            fp16 = not torch.cuda.is_bf16_supported(),
            bf16 = torch.cuda.is_bf16_supported(),
            logging_steps = 1,
            optim = "adamw_8bit", # 使用 8bit 优化器省显存
            weight_decay = 0.01,
            lr_scheduler_type = "linear",
            seed = 3407,
            output_dir = "outputs",
        ),
    )

    # 开始炼丹
    print("🚀 启动本地训练...")
    trainer.train()

    # 5. 保存 LoRA 适配器 (不导出 GGUF)
    # 这样训练完后，文件夹里会出现 adapter_model.bin 等文件
    model.save_pretrained("my_lora_adapter")
    tokenizer.save_pretrained("my_lora_adapter")
    print("✅ 训练完成，LoRA 权重已保存至 my_lora_adapter 文件夹")

if __name__ == "__main__":
    main()