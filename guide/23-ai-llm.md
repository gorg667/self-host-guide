# Local AI: LLMs, Image Generation, Speech, and Search

Running AI models on your own hardware went from a curiosity to a legitimate self-hosting category between 2023 and 2026. Open-weight language models now rival the hosted giants for everyday tasks; image generation runs on a mid-range GPU; speech-to-text and text-to-speech are fast and free; and the tooling to serve all of it — Ollama, Open WebUI, llama.cpp, vLLM, ComfyUI, Whisper — is mature. This chapter explains how to size hardware for models (the VRAM arithmetic that decides everything), compares the inference servers and chat front-ends, covers image generation, speech, retrieval-augmented generation over your own documents, coding assistants, private search with SearXNG, and the practical integrations with the rest of the lab — Home Assistant, Paperless, Immich, Frigate — that make a local model genuinely useful rather than a toy.

## Why run models locally

- **Privacy**: your documents, photos, conversations, and code never leave the house. For a household's medical letters, finances, and personal notes, this is the whole argument.
- **Cost**: zero per-token; a GPU pays for itself against API bills quickly if you use models heavily — and is free to experiment with.
- **Control**: no content filters you did not choose, no model deprecations, no rate limits, no terms-of-service changes, works offline.
- **Integration**: local models can be wired into Home Assistant, Paperless, Immich, n8n, and your editor without sending anything to a third party.

The honest counterpoint: the very largest hosted frontier models remain more capable than anything that fits on consumer hardware, and for hard reasoning or the newest capabilities a hosted API may still be the right tool. Local models in the 8–70 B parameter range are excellent at summarisation, drafting, translation, Q&A over documents, classification, coding assistance, and home-automation intent — which covers most of what most people do.

## Hardware and the VRAM arithmetic

The single number that determines what you can run is **GPU memory (VRAM)**. Models are measured in parameters (B = billions); each parameter takes space depending on **quantisation** — the precision it is stored at:

| Precision | Bytes per parameter | 8B model | 14B | 32B | 70B |
|---|---|---|---|---|---|
| FP16/BF16 (full) | 2 | 16 GB | 28 GB | 64 GB | 140 GB |
| Q8 (8-bit) | ~1.1 | 9 GB | 15 GB | 34 GB | 75 GB |
| **Q4_K_M / Q4 (4-bit)** — the sweet spot | ~0.6 | **5 GB** | **9 GB** | **20 GB** | **40 GB** |
| Q2–Q3 | ~0.4 | 3.5 GB | 6 GB | 13 GB | 28 GB (degraded) |

Add **context** (the conversation and documents in the prompt): the KV cache for a long context can add several GB — 8K tokens is modest, 32K+ meaningful, 128K substantial. Rule of thumb: **model size at Q4 + 2–4 GB for context and overhead** must fit in VRAM for full-speed generation. Models that do not fit spill to system RAM (Ollama/llama.cpp do this automatically) and slow down by an order of magnitude — usable for batch jobs, painful for chat.

**Quality at 4-bit** is remarkably close to full precision for models above ~7 B; below Q4 degradation becomes noticeable. Q4_K_M or Q5_K_M GGUF quants are the community default; Q6/Q8 if you have the room.

**Practical tiers (2026):**

| Hardware | VRAM | Comfortable models | Notes |
|---|---|---|---|
| CPU only (mini PC, 16–32 GB RAM) | — | 1–8 B at Q4, slowly (2–10 tokens/s) | Fine for HA intents, tagging, small summaries. Memory bandwidth is the limit; dual-channel DDR5 helps. |
| Intel Arc A770 16 GB / B580 12 GB | 12–16 GB | 8–14 B | Works via IPEX-LLM/SYCL/Vulkan with less polish than CUDA; improving. |
| RTX 3060 12 GB / 4060 Ti 16 GB / 5060 Ti 16 GB | 12–16 GB | 8–14 B comfortably; 24–32 B tightly at Q3–Q4 | The value entry points. 16 GB is meaningfully better than 12. |
| RTX 3090 / 4090 / 5090 (24–32 GB) | 24–32 GB | **32 B at Q4 with room**; 70 B at Q2–Q3 | The used 3090 (~USD 600–800) is the perennial home-lab pick. |
| 2× 24 GB cards | 48 GB | 70 B at Q4 | Tensor parallel via vLLM/exllama, or layer split via llama.cpp. |
| AMD RX 7900 XTX 24 GB | 24 GB | Same as 3090 | ROCm works for Ollama/llama.cpp/vLLM/ComfyUI; more friction than CUDA; cheaper. |
| Apple Silicon Mac (Mini/Studio) | Unified 32–192 GB | Up to 70–120 B at Q4 on high-memory configs | Excellent tokens/s for the power; the unconventional but very effective LLM server. MLX and llama.cpp. |
| Strix Halo mini PCs (Ryzen AI Max+ 395, 64–128 GB unified) | Up to ~96 GB for GPU | 70 B at Q4 | 2025's interesting x86 alternative to a Mac for big models; ROCm/Vulkan. |
| NVIDIA DGX Spark / GB10 boxes | 128 GB unified | 70–120 B | Expensive; purpose-built. |

**Other considerations:** PCIe bandwidth barely matters for single-card inference (x4 is fine — a card in an SFF's second slot works); **power** — a 3090 idles at ~20 W and pulls 350 W generating (undervolt/power-limit to ~250 W loses little); **cooling** in a case that was not designed for it; **the GPU can be in a separate machine** that other services call over the network, and that machine can suspend when idle; **Frigate, Immich ML, and Jellyfin transcoding** can share the same GPU with the LLM if VRAM allows (NVIDIA only via the container toolkit; Intel via `/dev/dri` — one GPU, many containers).

## Inference servers

The server loads the model and exposes an API (almost always **OpenAI-compatible** — `/v1/chat/completions` — which every client speaks).

### Ollama

The **default** for home use: a single binary/container that downloads models from its library by name (`ollama pull llama3.3`, `qwen3:32b`, `gemma3`, `mistral-small`, `deepseek-r1`, `phi4`, and hundreds more, plus any GGUF from Hugging Face), manages them, loads/unloads on demand, runs multiple models, serves an OpenAI-compatible API, supports NVIDIA (CUDA), AMD (ROCm), Apple (Metal), Intel (via a fork/Vulkan), and CPU, handles vision models, embeddings, tool calling, structured outputs, and automatic GPU/CPU layer split. Built on llama.cpp. It made local LLMs a one-command affair and nearly every self-hosted app that integrates with a local model integrates with Ollama first.

**Watch out for:** default context window is small (2K–4K) unless you set `num_ctx` or create a Modelfile — many "the model forgot what I said" complaints are this; it is slightly slower and less tunable than raw llama.cpp or vLLM; model library tags are sometimes ambiguous about quantisation (check the tag's details); keep-alive defaults unload models after 5 minutes (set `OLLAMA_KEEP_ALIVE=-1` or a longer time for latency).

```yaml
services:
  ollama:
    image: ollama/ollama:latest
    container_name: ollama
    restart: unless-stopped
    volumes: ["/mnt/fast/ollama:/root/.ollama"]     # models are large (5–40 GB each); fast SSD
    environment:
      OLLAMA_KEEP_ALIVE: 30m
      OLLAMA_NUM_PARALLEL: "2"
      OLLAMA_FLASH_ATTENTION: "1"
    ports: ["127.0.0.1:11434:11434"]
    deploy:
      resources:
        reservations:
          devices: [{ driver: nvidia, count: all, capabilities: [gpu] }]
    # AMD: image: ollama/ollama:rocm  + devices: ["/dev/kfd", "/dev/dri"]
  open-webui:
    image: ghcr.io/open-webui/open-webui:main
    container_name: open-webui
    restart: unless-stopped
    depends_on: [ollama]
    environment:
      OLLAMA_BASE_URL: http://ollama:11434
      WEBUI_URL: https://chat.example.com
      ENABLE_SIGNUP: "false"
    volumes: ["./open-webui:/app/backend/data"]
    networks: [proxy, default]
```

### llama.cpp (llama-server)

The C/C++ inference engine underneath Ollama, LM Studio, and much else. Its own `llama-server` exposes an OpenAI-compatible API with **full control** over every parameter (context, batch, threads, GPU layers, KV cache quantisation, speculative decoding, grammar-constrained output), supports every GGUF model the day it appears, runs on CUDA/ROCm/Metal/Vulkan/SYCL/CPU, and is often 10–30% faster than Ollama for the same model. No model library or management — you download GGUFs yourself. **Pick it if** you want maximum performance and control from one model at a time; **llama-swap** adds on-demand model switching in front of it.

### vLLM

The production inference server: **PagedAttention**, continuous batching, tensor parallelism across GPUs, and very high throughput for many simultaneous requests. It runs Hugging Face safetensors models (FP16, AWQ, GPTQ, FP8 quants — GGUF support is secondary) and wants the whole model in VRAM. For a single user chatting, it offers little over llama.cpp; for serving a household plus automations plus a coding assistant concurrently, or running two GPUs as one, it is the right tool. Heavier to set up; NVIDIA-first with AMD support.

### Others

**LocalAI** (an all-in-one OpenAI-compatible server for LLMs, embeddings, image generation, TTS, STT, with a model gallery — the "everything behind one API" option, somewhat heavier and less polished than the specialists), **LM Studio** (desktop app with a server mode — excellent on a Mac or Windows PC, not a headless service), **Text Generation WebUI (oobabooga)** (the Swiss Army knife with every backend and a dense UI; for tinkerers), **TabbyAPI/ExLlamaV2** and **exllamav3** (the fastest NVIDIA-only engines for EXL2/EXL3 quants — power users), **SGLang** (vLLM competitor), **MLX-LM** (Apple Silicon native), **Aphrodite**, **KoboldCpp** (llama.cpp with a story/roleplay UI), **Jan** (desktop), **GPT4All** (desktop), **Xinference**, **TGI** (Hugging Face's server). For most home labs: **Ollama**, with llama.cpp when you want to tune.
