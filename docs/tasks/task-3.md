# Task 3: Change the Domain

## Goal

Edit the Reddash domain and see the result in the running app.

## Instructions

### Step 1: Change the starter prompts

1. In VS Code open `iris/domains/reddash/domain.py`.
2. Find `starter_prompts` and change the text of one prompt.
3. Save. The backend reloads on its own, so refresh the **App** panel to see the new prompt.

### Step 2: Tune the guardrail

1. In the same file find the `off_topic` guardrail route and its `references` list.
2. Add a new off-topic example, such as `"Tell me a joke"`.
3. Save, wait for the backend to restart, and ask the agent for a joke. It should be blocked.
4. Run `uv run python scripts/eval_routing.py` to confirm your change did not let an attack through or block a normal question.
5. Find the `prompt_injection_route()` entry in the same list. It comes from `backend/app/core/guardrail_presets.py` and holds example attacks (ignore-your-instructions, reveal-your-prompt, jailbreaks, asking for another customer's data). Add an attack phrasing of your own, then check it gets blocked.

### Step 3: Switch domains

1. In `iris/.env` set `DEMO_DOMAIN=electrohub`.
2. In the Terminal run `make setup`. **This flushes the Redis database.**
3. Refresh the App panel for a different company, data, and logo.

## Challenge

Scaffold your own domain with `make create-domain DOMAIN=my-domain`.

## What You Learned

✅ A domain is a set of Python files: schema, data, prompt, guardrails  
✅ Switching verticals needs no change to the Iris pipeline  

---

**Next:** [Task 4: Save Tokens with Tool Routing](/tasks/task-4.md)
