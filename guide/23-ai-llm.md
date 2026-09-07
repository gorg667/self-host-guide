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

## Chat front-ends

- **Open WebUI** — the ChatGPT-like interface for local models and the community standard: multi-user with roles, model switching, conversation history, **RAG over uploaded documents and web pages**, web search integration (SearXNG, others), image generation hooks (ComfyUI/Automatic1111), voice input/output (Whisper/TTS), tool/function calling, "pipelines" and plugins, prompt library, OIDC login, and connections to any OpenAI-compatible API alongside Ollama (so one UI fronts local *and* hosted models). Actively developed to a fault — features arrive weekly. ~500 MB–1 GB RAM. **The recommendation.** Note the licence moved from MIT to a custom licence with a branding clause in 2025; free for self-hosting.
- **LibreChat** — a polished multi-provider chat UI (OpenAI, Anthropic, Google, Ollama, any OpenAI-compatible) with agents, RAG, plugins, conversation search, and a strong multi-user story; MIT. Slightly more "many providers, one UI" than "local-first." Excellent; a close second.
- **AnythingLLM** — RAG-centric: workspaces of documents with chat over them, agents, many vector DBs and providers, a desktop app too. Good for "chat with my document collection" as the primary use.
- **Lobe Chat**, **Chatbot UI**, **Hollama** (minimal), **Enchanted** (iOS/macOS native for Ollama), **Msty** (desktop), **Reins** (mobile for Ollama), **Ollama's own app** (2025, desktop), **SillyTavern** (roleplay-oriented), **Hoarder/Karakeep**, **Perplexica** (below).

## Retrieval-augmented generation (RAG) over your own data

RAG lets a model answer questions from *your* documents: chunk them, embed them into a vector store, retrieve relevant chunks for each question, and give them to the model as context. In practice at home:

- **Open WebUI's built-in RAG** (upload documents or point at a folder; uses a local embedding model via Ollama — `nomic-embed-text`, `bge-m3`, `mxbai-embed-large`) covers most needs without any extra service.
- **AnythingLLM** for a more document-centric workflow.
- **Paperless-AI / Paperless-GPT** for asking questions of your Paperless archive ([Chapter 17](17-files-sync-documents.md)).
- **Khoj** (a personal AI over your notes — Obsidian/Markdown/PDF/Notion — with chat, search, and an agent framework; self-hostable), **Danswer/Onyx** (enterprise-grade search-and-chat over many connectors — heavy), **Dify** and **Flowise** and **Langflow** (visual builders for LLM apps and RAG pipelines — for people building rather than just using), **n8n's AI nodes** ([Chapter 22](22-dev-git-automation.md)).
- Vector stores if you build your own: **Qdrant**, **Chroma**, **Weaviate**, **Milvus**, **pgvector** in Postgres ([Chapter 26](26-databases-backing-services.md)) — pgvector is the pragmatic home choice.

Realistic expectations: RAG over a few thousand well-formatted documents with a 14–32 B model is genuinely useful; over a messy 200 GB archive it needs tuning (chunking, hybrid search with a keyword index, reranking) and patience.

## Coding assistants

- **Editor integration**: **Continue** (VS Code/JetBrains — open source, points at Ollama/llama.cpp/vLLM for chat, autocomplete, and edits), **Cline / Roo Code** (agentic coding in VS Code; local models work but the 8–32 B ones lag hosted frontier models at agentic tasks), **Tabby** (a self-hosted GitHub-Copilot-style server with its own IDE extensions and code indexing — the most complete self-hosted Copilot replacement), **llama.vscode**, **Aider** (terminal pair-programmer; any model), **OpenCode**/**Crush** and other terminal agents.
- **Models**: Qwen2.5-Coder / Qwen3-Coder, DeepSeek-Coder-V2, Codestral, StarCoder2, and the general models (Llama 3.x, Gemma 3, Mistral) all code competently at 14–32 B. Autocomplete wants a *small fast* model (1.5–7 B); chat/edit wants the biggest you can fit.

## Image generation

**Stable Diffusion** (1.5, SDXL, SD 3.5), **FLUX.1** (dev/schnell — the 2024–2025 quality leader among open weights), **Qwen-Image**, **HiDream**, and video models (**Wan**, **HunyuanVideo**, **LTX**) run locally on a GPU with 8–24 GB VRAM (FLUX dev wants 12+ GB at FP8; quantised GGUF variants run on less).

- **ComfyUI** — the node-graph workflow tool that has become the standard: every model, every technique (ControlNet, LoRA, inpainting, upscaling, IP-Adapter, video), workflows shared as JSON/embedded in images, an enormous custom-node ecosystem, and a learning curve. Run as a container with the GPU; **ComfyUI-Manager** for nodes; keep it LAN/VPN-only (arbitrary custom nodes execute code).
- **Stable Diffusion WebUI (Automatic1111)** — the original tabbed UI, still widely used, less actively developed; **Forge** and **reForge** are faster forks; **SD.Next** is the most actively maintained fork with broad model support; **Fooocus** is the "Midjourney-simple" UI (less updated); **InvokeAI** is the polished professional-style app with a unified canvas; **SwarmUI** wraps ComfyUI in a friendlier front-end.
- Integrations: Open WebUI can call ComfyUI/A1111 for image generation from chat; Immich uses CLIP (not generation); **Stable Diffusion in Home Assistant** for generated dashboard art is a thing people do.

## Speech

- **Speech-to-text**: **Whisper** (OpenAI's open model) via **faster-whisper** (CTranslate2, 4× faster), **whisper.cpp** (CPU/Metal), **WhisperX** (word timestamps, diarisation), **Speaches** (formerly faster-whisper-server — an OpenAI-compatible API for STT *and* TTS, the clean way to serve it), **Wyoming faster-whisper** (Home Assistant add-on), **Vosk** (tiny, offline, lower accuracy), **NVIDIA Parakeet/Canary** (very fast, English-strong), **Moonshine**. Use cases: HA voice, meeting transcription (**Scriberr** and **Whishper** are self-hosted transcription apps with UIs), subtitles (**Bazarr** can use Whisper via **whisper-asr-webservice**; **Subgen**), voice notes.
- **Text-to-speech**: **Piper** (fast, light, many voices, the HA default), **Kokoro** (2025 — remarkably natural for 82 M parameters, runs on CPU; **Kokoro-FastAPI** serves it OpenAI-style), **XTTS-v2**/**Coqui** (voice cloning; heavier), **F5-TTS**, **Chatterbox**, **OpenedAI-Speech** (OpenAI-compatible TTS wrapper), **Mimic 3**, **Orpheus**. For HA announcements and audiobook generation, Piper or Kokoro.
- **Full voice pipelines**: HA Assist ([Chapter 19](19-home-automation.md)); Open WebUI's voice mode with Whisper + Kokoro; **LocalAI** bundling both.

## Private search: SearXNG

**SearXNG** is a self-hosted **metasearch engine**: it queries Google, Bing, DuckDuckGo, Brave, Wikipedia, and 200+ other engines on your behalf, aggregates and deduplicates results, and returns them with no tracking, no ads, and no profile — the engines see your server's IP, not your identity. Fast, light (~100 MB), configurable per-engine, with a JSON API that **Open WebUI, Perplexica, LibreChat, and n8n** use for web-augmented answers. Set it as your browser's default search; run it LAN/VPN-only or rate-limited if public (public instances attract bot traffic and get your IP blocked by Google). **Whoogle** (a Google-only proxy) and **4get** are alternatives; **Perplexica** and **Morphic** are self-hosted Perplexity-style "answer engines" that combine SearXNG with a local LLM for cited answers — Perplexica + Ollama + SearXNG is a genuinely useful stack.

## Integrations across the lab

Where a local model earns its keep:

- **Home Assistant**: the Ollama integration as a conversation agent for Assist — natural-language control ("make it cosy in here"), with **exposed entities** as tools; also summarising camera events (LLM Vision), writing notifications, and generating dashboard text. A 7–14 B model is enough.
- **Paperless-ngx**: **Paperless-AI**/**Paperless-GPT** auto-title, tag, and extract correspondents; ask questions of your archive.
- **Immich**: not an LLM, but its CLIP and face models run on the same GPU; larger CLIP models (ViT-L, ViT-H) improve search noticeably if you have the VRAM.
- **Frigate**: **GenAI** integration describes detected objects/events in natural language via Ollama; semantic search embeddings.
- **Karakeep/Linkwarden**: auto-tagging and summaries of saved links.
- **Nextcloud Assistant**: local LLM via the Ollama/OpenAI-compatible backend for summaries, translations, and text generation inside Nextcloud.
- **n8n / Windmill**: LLM nodes for classification, extraction, and summarisation in workflows — morning briefings from RSS, invoice parsing, ticket triage.
- **Obsidian** (Copilot/Smart Connections plugins pointed at Ollama), **Joplin**, **Trilium** — note-taking with local AI.
- **Jellyfin/Plex**: subtitle generation via Whisper; **Recommendarr** for recommendations.
- **Email**: local spam/priority classification, drafting replies (via n8n or Stalwart hooks).

## Operational notes

- **Models are large** — 5–40 GB each; a 1 TB NVMe fills quickly. Keep them on fast local storage and prune.
- **GPU sharing**: NVIDIA lets many containers use one GPU (VRAM permitting); Ollama unloads idle models to make room. Set `OLLAMA_MAX_LOADED_MODELS` and keep-alive deliberately. Intel iGPUs share `/dev/dri` among containers naturally.
- **Power**: an idle 3090 is 20 W; add a "suspend the GPU box when idle, wake-on-LAN on request" automation if the machine is separate ([Chapter 29](29-power-cost-environment.md)).
- **Security**: never expose Ollama's API (no auth by default) or ComfyUI (arbitrary code via custom nodes) beyond LAN/VPN; put Open WebUI behind forward-auth/OIDC; treat prompt injection via RAG'd documents as real if the model has tools.
- **Model choice changes monthly.** As of 2026 the dependable families for general use are Llama 3.x/4, Qwen 3, Gemma 3, Mistral Small/Medium, DeepSeek (R1/V3 distils), Phi-4, GLM; for vision, Qwen-VL, Gemma 3, Llama 3.2 Vision, Pixtral; for embeddings, bge-m3, nomic-embed, Qwen3-Embedding. Check r/LocalLLaMA and the Open LLM Leaderboard rather than trusting any static list.
- **Licences**: most open-weight models have permissive or "open with acceptable-use" licences (Llama's has a 700 M-user clause irrelevant to you; Gemma's has usage terms; Qwen and Mistral Small are Apache 2.0). Fine for personal use; read them if you build a product.

## Recommendations

- **Hardware**: an RTX 3090/4090 (24 GB) if you are serious; a 16 GB card (4060 Ti/5060 Ti) for a solid start; a Mac Mini/Studio with 64 GB+ if you want big models at low power; CPU-only on a mini PC is fine for HA intents and tagging with 3–8 B models.
- **Stack**: Ollama + Open WebUI + SearXNG, behind the proxy with OIDC; llama.cpp when you want to squeeze more out of one model; vLLM for concurrency.
- **Models**: a 14–32 B general model at Q4 for chat, a 7–8 B for HA and automations, `bge-m3`/`nomic-embed-text` for embeddings, Whisper (via Speaches) + Kokoro/Piper for voice.
- **Images**: ComfyUI with FLUX.1-dev or SDXL; SwarmUI or InvokeAI if you want friendlier.
- **Integrate**: HA Assist, Paperless-AI, Frigate GenAI, n8n. That is where "I run an LLM" becomes "my house is smarter."

## Checklist

- [ ] GPU (or Mac/CPU plan) sized against the models you actually want to run; VRAM arithmetic done.
- [ ] Ollama (or llama.cpp/vLLM) running with the GPU visible inside the container (`nvidia-smi`/`rocm-smi`/`intel_gpu_top` from the host shows load when generating).
- [ ] Open WebUI behind the reverse proxy with OIDC/forward-auth; signups disabled; API endpoints not exposed publicly.
- [ ] Context length set appropriately (`num_ctx`/Modelfile); keep-alive tuned; models on fast storage with a pruning habit.
- [ ] SearXNG running and wired into Open WebUI (and your browser).
- [ ] At least one integration live (HA conversation agent, Paperless-AI, or an n8n workflow).
- [ ] Whisper + a TTS engine serving HA Assist if you use voice.
- [ ] ComfyUI (if run) reachable only via LAN/VPN; custom nodes reviewed before install.
- [ ] Power behaviour of the GPU box understood and, if separate, suspended when idle.
