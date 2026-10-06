# Task 4: Save Tokens with Semantic Tool Routing

## Goal

Cut the cost of every agent question by sending the LLM only the tools it needs, chosen with **Semantic Routing**.

## Why it matters

The Reddash agent has 57 tools. Every time it calls the model, all the tool definitions are sent along: about **15,000 tokens per call**, and one question makes 3-6 calls. Most questions only need a few of those tools.

Semantic tool routing fixes that. A second semantic router (stored in Redis, like the guardrail) matches the question against groups of example questions and attaches only the matching group's tools. It reuses the embedding the guardrail already computed, so it adds a Redis vector search and no extra OpenAI call. If nothing matches, every tool is attached, so routing can save tokens but never removes the agent's ability to answer.

## Instructions

### Step 1: Measure without routing

In the **Terminal** panel run:

```bash
TOOL_ROUTING_ENABLED=false uv run python scripts/measure_tokens.py "I reported a missing item last week - was that resolved?"
```

Note the **input tokens per call** and the **TOTAL tokens**. (This makes real OpenAI calls and uses your key's quota.)

### Step 2: Measure with routing

```bash
TOOL_ROUTING_ENABLED=true uv run python scripts/measure_tokens.py "I reported a missing item last week - was that resolved?"
```

The question now matches the `support_tickets` route, so only 11 of 57 tools are sent. In our test the total dropped from about **47,000** to about **11,000** tokens.

### Step 3: Watch it in the app

Ask the same question in the **App** panel and open **Tool selection · ROUTE** under *Semantic Routing* in the activity panel. It shows the matched route, its distance, and how many tools were selected.

### Step 4: Read the routes

Open `iris/domains/reddash/domain.py` and find `tool_routing`. Each route has:

- `references`: example questions that describe the route
- `tools`: the tools to attach (names or `*` patterns)
- `distance_threshold`: how close a question must be to match (lower is stricter)

`always_on` lists tools sent with every call (user profile, time, memory).

### Step 5: Experiment

Try one of these, save, and wait a few seconds for the backend to reload and rebuild the router:

1. Ask a question in your own words, such as "Did you ever sort out my complaint?". Does it route correctly? Add a reference phrase to the route if not.
2. Lower a `distance_threshold` until a question stops matching. What does the activity panel show? (No match means every tool is attached.)
3. Remove `filter_supportticket` from the `support_tickets` route and ask the missing-item question again. This is the risk of routing: the agent can't use a tool it was never shown.

## Challenge

Add a route for a new kind of question, for example one about restaurants only, with 5-6 references. Measure the question before and after with `scripts/measure_tokens.py`.

## What You Learned

✅ Tool definitions are a big, repeated token cost for agents  
✅ Semantic routing can pick tools per question, using the same embeddings and Redis as the guardrail  
✅ The trade-off: tighter routes save more tokens but risk hiding a tool the agent needs  

---

**Happy building!** See the [Reference](/reference/reference.md) for links and commands.
