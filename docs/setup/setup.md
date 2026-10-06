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
| `OPENAI_API_KEY` | OpenAI |
| `REDIS_HOST`, `REDIS_PORT`, `REDIS_PASSWORD`, `REDIS_SSL` | Redis Cloud database |
| `CTX_ADMIN_KEY` | Context Surfaces (Context Retriever) |
| `MEMORY_API_BASE_URL`, `MEMORY_STORE_ID`, `MEMORY_API_KEY` | Agent Memory |
| `LANGCACHE_HOST`, `LANGCACHE_CACHE_ID`, `LANGCACHE_API_KEY` | LangCache |

Leave `MCP_AGENT_KEY` and `CTX_SURFACE_ID` empty. The next step fills them in.

> The demo starts even before any credentials are set. Until `OPENAI_API_KEY` is added, the chat replies with a message saying so. The backend restarts automatically whenever `.env` changes.

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
- **"RateLimitError" in the chat:** your OpenAI organization hit its tokens-per-minute limit. Every model call carries the tool definitions, and one question makes 3–6 calls. Measured on the Reddash demo with `gpt-4o-mini`, one question used about 8,000–61,000 tokens with semantic tool routing on (the default) and about 32,000–98,000 with it off (`TOOL_ROUTING_ENABLED=false`); see [Task 4](/tasks/task-4.md). A key limited to 30k tokens per minute cannot run the agent even with routing, so for a workshop budget tens of thousands of tokens per question and multiply by the questions your attendees ask in the same minute. Cached and blocked questions use few or no tokens. Switching `OPENAI_CHAT_MODEL` in `.env` changes cost and which rate-limit bucket you use, but not the token count.
- **Frontend logs:** `tail -f /tmp/vite.log` in the Terminal panel.

Tip: to look at the data the demo loaded, add the same Redis database in **Redis Insight**. [Task 2](/tasks/task-2.md) has the steps.

Ready? Start [Task 1](/tasks/task-1.md).
