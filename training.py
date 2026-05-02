# train_unsloth.py

from unsloth import FastLanguageModel
import torch
from datasets import load_dataset
from transformers import TrainingArguments
from trl import SFTTrainer

# ======================
# Config
# ======================

model_name = "unsloth/llama-3-8b-Instruct-bnb-4bit"
max_seq_length = 1024
dtype = None  # auto
load_in_4bit = True

# ======================
# Load model
# ======================

model, tokenizer = FastLanguageModel.from_pretrained(
    model_name = model_name,
    max_seq_length = max_seq_length,
    dtype = dtype,
    load_in_4bit = load_in_4bit,
)

# ======================
# LoRA setup (IMPORTANT)
# ======================

model = FastLanguageModel.get_peft_model(
    model,
    r = 16,  # increase for quality (8–32 range)
    target_modules = [
        "q_proj", "k_proj", "v_proj", "o_proj",
        "gate_proj", "up_proj", "down_proj",
    ],
    lora_alpha = 32,
    lora_dropout = 0.05,
    bias = "none",
    use_gradient_checkpointing = "unsloth",
    random_state = 3407,
)

# ======================
# Load dataset
# ======================

dataset = load_dataset("json", data_files="dataset.jsonl", split="train")

# ======================
# Formatting (CRITICAL)
# ======================

def format_chat(example):
    messages = example["messages"]

    system_prompt = {
        "role": "system",
        "content": (
            "You are RL (EnderRL), a tech-obsessed guy who loves Minecraft servers, "
            "gaming, making sarcastic jokes, and sometimes talks shit humorously."
        )
    }

    messages = [system_prompt] + messages

    text = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=False,
    )
    return {"text": text}

dataset = dataset.map(format_chat)

# ======================
# Training
# ======================

trainer = SFTTrainer(
    model = model,
    tokenizer = tokenizer,
    train_dataset = dataset,
    dataset_text_field = "text",
    max_seq_length = max_seq_length,
    packing = False,  # better GPU usage
    args = TrainingArguments(
        per_device_train_batch_size = 1,
        gradient_accumulation_steps = 8,

        warmup_steps = 100,
        num_train_epochs = 3,  # increase later if needed

        learning_rate = 2e-4,
        fp16 = not torch.cuda.is_bf16_supported(),
        bf16 = torch.cuda.is_bf16_supported(),

        logging_steps = 10,
        optim = "adamw_8bit",

        weight_decay = 0.01,
        lr_scheduler_type = "cosine",

        seed = 3407,
        output_dir = "outputs",
    ),
)

# ======================
# Train
# ======================

trainer.train()

# ======================
# Save LoRA
# ======================

model.save_pretrained("lora_model")
tokenizer.save_pretrained("lora_model")