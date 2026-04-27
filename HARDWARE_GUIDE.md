# Local RAG: Hardware & Model Configurations Guide

When running Local LLMs and Vector Databases, your hardware dictates which models you can run effectively. This guide will help you choose the best LLM (via Ollama) and Embedding model based on your system's specifications.

> **💡 Rule of Thumb:** 
> - **RAM/VRAM** determines **how large** of a model you can load.
> - **GPU/CPU speed** determines **how fast** it generates tokens.
> - **SSD vs HDD** determines **how fast** the model loads into memory initially.

---

## 🖥️ CPU-Only Setups (No Dedicated GPU)

If you don't have a GPU, inference will be handled by your system's CPU and RAM. It will be slower than a GPU, but completely functional.

### 1. The 16GB RAM Setup (Minimum Recommended)
This is the baseline for most modern laptops.
* **LLM Recommendations:** `mistral:7b`, `llama3:8b`, `phi3:14b` (using Q4 or Q5 quantization).
* **Embeddings:** `all-MiniLM-L6-v2` (Very fast and lightweight).
* **Expected Speed:** 5-10 tokens per second.

### 2. The 32GB RAM Setup
Great for running slightly larger models or running 7B-8B models without any quantization (Q8) for maximum intelligence.
* **LLM Recommendations:** `mixtral:8x7b` (Q3/Q4 - slow but smart), `command-r:35b` (Q4), `llama3:8b` (Q8).
* **Embeddings:** `nomic-embed-text` or `bge-m3`.
* **Expected Speed:** 3-7 tokens per second for larger models.

### 3. The 64GB RAM Setup
Now you can start running "Large" tier models, though CPU generation will be quite slow.
* **LLM Recommendations:** `llama3:70b` (Q4), `qwen2:72b` (Q4), `mixtral:8x22b` (Q3).
* **Embeddings:** `mxbai-embed-large`.
* **Expected Speed:** 1-3 tokens per second (Heavy CPU load).

### 4. The 128GB - 256GB RAM Setup (Workstation/Server)
You can run almost any open-source model currently available locally.
* **LLM Recommendations:** `llama3:70b` (Q8 - uncompressed), `wizardlm2:8x22b` (Q8).
* **Embeddings:** Any high-dimensional embedding model.
* **Expected Speed:** Will still be bottlenecked by CPU memory bandwidth (2-5 tokens/sec).

---

## 🎮 GPU-Accelerated Setups (NVIDIA / Apple Silicon)

If you have a dedicated GPU (or Apple M-series Unified Memory), generation speed increases drastically. Models must fit entirely inside the VRAM (Video RAM) to get the maximum speed boost.

### 1. 8GB VRAM (e.g., RTX 3060, RTX 4060)
* **LLM Recommendations:** `llama3:8b`, `mistral:7b`, `gemma:7b`.
* **Strategy:** These models fit perfectly into 8GB VRAM, giving you blazing fast inference (40-60+ tokens per second).

### 2. 16GB VRAM (e.g., RTX 4080, Mac M1/M2/M3 with 16GB)
* **LLM Recommendations:** `mixtral:8x7b` (Q4), `command-r:35b` (Q3), `phi3:14b` (Q8).
* **Strategy:** You can run "Mixture of Experts" models like Mixtral or larger dense models at lower precision.

### 3. 24GB VRAM (e.g., RTX 3090, RTX 4090)
* **LLM Recommendations:** `command-r:35b` (Q8), `mixtral:8x7b` (Q6).
* **Strategy:** The sweet spot for AI enthusiasts. You can run highly capable 30B+ parameter models at incredible speeds.

### 4. 48GB+ VRAM / Apple 64GB+ Unified Memory (e.g., Dual 3090s, Mac Studio)
* **LLM Recommendations:** `llama3:70b` (Q4/Q5), `command-r-plus:104b` (Q4).
* **Strategy:** Unlocks the ability to run 70B+ parameter models natively on GPU. These models rival GPT-4 in capability.

---

## 💾 Storage Considerations

Regardless of your RAM or GPU, **you absolutely MUST use an SSD** (preferably NVMe).

* **NVMe M.2 SSD (Recommended):** Models will load into RAM/VRAM in 2 to 10 seconds.
* **SATA SSD (Acceptable):** Models will load in 10 to 30 seconds.
* **HDD (Not Recommended):** Loading a 40GB model from a spinning hard drive can take 5+ minutes just to start the chat. Avoid this.

---

> [!NOTE]
> **Disclaimer:** All the token generation speeds and RAM/VRAM requirements mentioned in this guide are estimates collected from web sources and community benchmarks. They have not been independently tested by our team and may vary based on your specific hardware setup.
