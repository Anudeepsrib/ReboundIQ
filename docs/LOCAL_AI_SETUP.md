# Local AI Setup (Ollama)

1. The docker compose includes `ollama` service (auto-pulls default models on start via entrypoint; health waits until llama3.2:1b present in /api/tags).
2. On first `make dev`, it may take time to download the default model (llama3.2:1b recommended for CPU/Windows dev ~1.3GB).
3. If /ready or /api/v1/ai/status or /api/v1/ai/test-conn indicates degraded (no model), exec:
   docker compose exec ollama ollama pull llama3.2:1b
   docker compose exec ollama ollama pull nomic-embed-text
4. Verify models: curl http://localhost:11434/api/tags
   or inside: docker compose exec ollama ollama list
5. In .env set AI_CHAT_MODEL / AI_EMBEDDING_MODEL if you pull different ones (re-pull + restart api for health).
6. Local conn test (from api): GET /api/v1/ai/test-conn  (lists models, checks presence, runs smoke chat).
7. vLLM: point AI_BASE_URL to your vLLM OpenAI-compatible endpoint and use AI_PROVIDER=vllm (or openai compat).

## Windows / WSL2 / Docker Desktop Notes
- Use Docker Desktop with WSL2 backend (recommended) or native Windows containers (less common for Linux images).
- On first boot or after `docker compose down -v`, Ollama image pull + model download can take 5-15+ minutes on CPU/Windows. Do not interrupt.
- Models stored in named volume `ollamadata` (persists across restarts).
- If curl not in PATH on host, use `docker compose exec ollama curl ...` or PowerShell Invoke-WebRequest equivalent.
- For non-Docker local dev: install Ollama from https://ollama.com , `ollama serve`, pull models, set AI_BASE_URL=http://localhost:11434 in .env (api runs with uvicorn).
- GPU: if NVIDIA + CUDA on WSL2, ollama may auto use; for dev stick to CPU small models.
- Firewall / port: ensure 11434, 5432, 6379, 8000, 3000, 9000/9001 free or remapped.
- MinIO console at http://localhost:9001 (user/pass from .env.example).
- After `make dev` (detached), use `docker compose ps` and `docker compose logs -f api` to monitor.
- `make down` cleans volumes (removes data; use without -v to keep dbs).

Never commit keys. External only after explicit consent in UI.
