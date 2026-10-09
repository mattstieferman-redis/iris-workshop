# Setup Guide

## Finding Your Code

In VS Code the demo lives in `iris/`:

```
iris/
├── backend/    FastAPI app and LangGraph agent
├── domains/    One folder per demo (reddash, electrohub, ...)
├── frontend/   React chat UI
├── scripts/    Data generation, loading and seeding
└── .env        Your credentials (created on first start)
```

## 1. Add Your Credentials

Open `iris/.env` and fill in the values provided for the workshop:

| Variable(s) | Service |
|-------------|---------|
| `ANTHROPIC_API_KEY` (plus `ANTHROPIC_BASE_URL` and `LLM_MODEL` if you use Amazon Bedrock) | Claude, the agent's model |
| `REDIS_HOST`, `REDIS_PORT`, `REDIS_PASSWORD`, `REDIS_SSL` | Redis Cloud database |
| `CTX_ADMIN_KEY` | Context Surfaces (Context Retriever) |
| `MEMORY_API_BASE_URL`, `MEMORY_STORE_ID`, `MEMORY_API_KEY` | Agent Memory |
| `LANGCACHE_HOST`, `LANGCACHE_CACHE_ID`, `LANGCACHE_API_KEY` | LangCache |

Leave `MCP_AGENT_KEY` and `CTX_SURFACE_ID` empty. The next step fills them in.

No embeddings key is needed: the guardrail, tool routing and Simple RAG use a small embedding model that runs inside the container. The first start downloads it (about 90 MB), so give the backend a minute.

> The demo starts even before any credentials are set. Until `ANTHROPIC_API_KEY` is added, the chat replies with a message saying so. The backend restarts automatically whenever `.env` changes.

## 2. Load the Data

Open the **Terminal** panel and run:

```bash
make setup
```

This generates the Reddash data, loads it into Redis, creates a Context Surface, and seeds Agent Memory and LangCache. It takes a minute or two. **It flushes the Redis database you configured.**

## 3. Check That It Works

Open the **App** panel and ask *"Why is my order running late?"*. Then confirm the backend sees every service:

```bash
curl -s backend:8040/api/health
```

`mcp_enabled`, `memory_enabled`, `langcache_enabled` and `guardrail_enabled` should all be `true`.

## Troubleshooting

- **App shows errors / 502:** the backend is still starting or waiting for credentials. Check the container logs (`docker compose logs backend`).
- **Agent has no tools after a restart:** run `make reset` to reload the data.
- **"rate limited" in the chat:** your Claude key hit its tokens-per-minute limit. Every model call carries the tool definitions (about 25,000 tokens for all 57 on Claude Haiku 4.5), and one question makes 2 to 4 calls. Measured on five sample questions, semantic tool routing (on by default) used 14,000 to 29,000 tokens per question, against 52,000 to 107,000 with it off (`TOOL_ROUTING_ENABLED=false`); see [Task 4](/tasks/task-4.md). For a workshop, budget tens of thousands of tokens per question and multiply by the questions your attendees ask in the same minute. Cached and blocked questions use few or no tokens.
- **First start is slow / "could not load the embedding model":** the embedding model downloads from Hugging Face on first use. Check the backend can reach huggingface.co; it is cached afterwards.
- **Frontend logs:** `tail -f /tmp/vite.log` in the Terminal panel.

Tip: to look at the data the demo loaded, import the generated `iris/redis-insight-import.json` into **Redis Insight**. [Task 2](/tasks/task-2.md) has the steps.

Ready? Start [Task 1](/tasks/task-1.md).
