# Local AI Setup (Ollama)

1. The docker compose includes `ollama` service.
2. On first `make dev`, it may take time to download the default model (llama3.2:1b recommended for CPU/Windows dev ~1.3GB).
3. If /ready or health indicates not ready, exec:
   docker compose exec ollama ollama pull llama3.2:1b
   docker compose exec ollama ollama pull nomic-embed-text
4. Verify: curl http://localhost:11434/api/tags
5. In .env set AI_CHAT_MODEL / AI_EMBEDDING_MODEL if you pull different ones.
6. vLLM: point AI_BASE_URL to your vLLM OpenAI-compatible endpoint and use AI_PROVIDER=vllm (or openai compat).

Never commit keys. External only after explicit consent in UI.
