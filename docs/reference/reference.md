# Reference & Resources

## Quick Links

- [Redis Iris](https://redis.io/iris/)
- [Context Retriever](https://redis.io/docs/latest/develop/ai/context-engine/context-retriever/)
- [Agent Memory](https://redis.io/docs/latest/develop/ai/context-engine/agent-memory/)
- [LangCache](https://redis.io/docs/latest/develop/ai/context-engine/langcache/)

## Terminal Commands

Run these in the Terminal panel (they start in `/code/iris`):

| Command | What it does |
|---------|--------------|
| `make domains` | List available demo domains |
| `make setup` | Generate data, load Redis, seed memory and cache |
| `make reset` | Reload data for the current domain |
| `make seed-memories` | Re-seed long-term memories |
| `make seed-langcache` | Re-seed the semantic cache |
| `make create-domain DOMAIN=x` | Scaffold a new domain |
| `uv run python scripts/measure_tokens.py "question"` | Measure OpenAI tokens per model call (set `TOOL_ROUTING_ENABLED=false` to compare) |
| `pytest` | Run the unit tests |

## Where Things Run

| Piece | Where |
|-------|-------|
| Chat UI (Vite) | `web` container, `/app/` |
| API (FastAPI) | `backend` container, `/api/` |
| Terminal | `web` container, `/terminal/` |

## What the Prompt-Injection Guardrail Covers

The `prompt_injection` route blocks messages that look like attacks: overriding instructions, extracting the system prompt, jailbreak role-play, fake "system" or "admin" messages, and asking for other customers' data. It checks the **latest user message** against example attacks, so it is a first line of defense, not a complete one:

- A new phrasing that is far from every example can slip through, so add examples as you see new attacks. In our tests, 36 of 36 attack phrasings were blocked and none of 63 legitimate questions were flagged as injection.
- It does not inspect text that comes back from tools or memory (indirect injection), and it looks at one message at a time, so an attack split across several messages is not caught.
- The agent itself is also limited to the signed-in customer's identity, which is what actually protects other customers' data.

## Known Issues

- Some tests depend on test order. If `pytest` reports OpenAI 401 errors in the data generator tests, run the failing test file on its own.
- `tests/test_healthcare_domain.py::test_generate_demo_data_jsonl_valid` fails: it expects an `id` field that the generator does not write.

## Keyboard Shortcuts in VS Code

| Action | Windows/Linux | Mac |
|--------|---------------|-----|
| Save | Ctrl+S | Cmd+S |
| Find | Ctrl+F | Cmd+F |
| Command Palette | Ctrl+Shift+P | Cmd+Shift+P |
