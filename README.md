# Distiller

A pipeline to distill your personal chat history into a localized AI "Digital Twin."

---

## Description

**Distiller** is a comprehensive toolset designed to extract, process, and fine-tune Large Language Models (LLMs) using your own conversation data. By leveraging **Unsloth** for fast 4-bit LoRA fine-tuning, the project transforms raw exports from WhatsApp or Discord into a structured "Messages" format that teaches a model (like Qwen2) to mimic your specific tone, vocabulary, and response logic. The final model can be exported to GGUF format and deployed as a personalized Discord bot through a local Ollama instance.

---

## Getting Started

### Dependencies

* **OS**: Windows 10/11 (with WSL2) or Linux.
* **Hardware**: NVIDIA GPU (12GB+ VRAM recommended for 7B models).
* **Python**: 3.10 or 3.11.
* **Key Libraries**: `unsloth`, `torch`, `discord.py`, `python-dotenv`, `requests`, and `datasets`.

### Installing

1.  **Clone the Repository**:
    ```bash
    git clone https://github.com/Low-Zi-Hong/Distiller.git
    cd Distiller
    ```
2.  **Install Dependencies**:
    It is recommended to use `uv` for faster installation:
    ```bash
    uv pip install unsloth torch datasets transformers trl python-dotenv discord requests
    ```
3.  **Environment Setup**:
    Create a `.env` file in the root directory (this file is ignored by `.gitignore` to keep your secrets safe).
    ```env
    DISCORD_TOKEN=your_discord_bot_token_here
    ```

### Executing program

1.  **Data Processing**:
    Place your WhatsApp `.txt` export in the `raw/` folder. Run the processor to generate a training-ready JSONL file:
    ```bash
    python process_data.py --name "Your Name" --context 5
    ```
2.  **Fine-Tuning**:
    Start the local training process. This script uses 4-bit quantization to save VRAM.
    ```bash
    python train.py --data "YourName_distilled_data.jsonl"
    ```
3.  **Exporting to GGUF**:
    Convert the trained LoRA adapter into a GGUF file for use with Ollama.
    ```bash
    python save_gguf.py --folder "my_lora_adapter" --output "final_model"
    ```
4.  **Running the Discord Bot**:
    Ensure your model is loaded in Ollama, then start the bot:
    ```bash
    python discord_bot.py
    ```

---

## Help

* **ModuleNotFoundError**: Ensure you have installed `python-dotenv` if the bot fails to start.
* **CUDA Issues**: If training fails to detect your GPU, verify that your PyTorch version matches your CUDA toolkit.
* **Privacy**: The `.gitignore` is pre-configured to ignore all `raw/` folders and `*.jsonl` files to ensure your private chat history is never pushed to a public repository.

---

## Authors

* **Low Zi Hong**

---

## Version History

* **0.1**
    * Initial Release: Added WhatsApp/Discord processors, Unsloth trainer, and GGUF exporter.

---

## License

This project is licensed under the MIT License - see the LICENSE file for details.

---

## Acknowledgments

* [Unsloth](https://github.com/unslothai/unsloth) for providing the ultra-fast fine-tuning framework.
* [Ollama](https://ollama.com/) for the seamless local LLM serving infrastructure.
* [Qwen Team](https://github.com/QwenLM/Qwen2) for the high-performance base model.