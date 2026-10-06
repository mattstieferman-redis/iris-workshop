# Task 2: Look Inside Redis

## Goal

See what the demo stored in Redis, and how Agent Memory changes the agent's answers.

## Instructions

### Step 1: Browse the data

Redis Insight does not know about your database yet. The demo stores its data in the Redis database from `iris/.env`, not in the workshop's local Redis container, so you add it once:

1. Open **Redis Insight** from the ☰ menu.
2. The first time, it shows an **EULA and Privacy settings** dialog. Read it, choose your privacy settings, and accept the terms to continue. (*Encrypt sensitive information* is unavailable in this environment; your connection details stay in this workshop environment only.)
3. Click **Add Redis database** and enter the values from `iris/.env`:

   | Insight field | `.env` value |
   |---------------|--------------|
   | Host | `REDIS_HOST` |
   | Port | `REDIS_PORT` |
   | Username | `REDIS_USERNAME` (usually `default`) |
   | Password | `REDIS_PASSWORD` |
   | Use TLS | on only if `REDIS_SSL=true` |

4. Open the database and look for keys starting with `reddash_` (orders, drivers, restaurants, policies). These are what Context Retriever exposes to the agent. The **Search** tab lists the indexes that make them queryable.

> If the database looks empty, check that you connected to the database in `.env` and that `make setup` finished. The local "redis" container is not used by the demo.

### Step 2: See memory change an answer

`make setup` seeded two long-term memories for the demo customer: *prefers contactless delivery* and *likes spicy food*.

1. In a new conversation ask: **"Given what you know about me, look at my recent orders and tell me what I should reorder tonight and how it should be delivered."**
2. In the activity panel, open **Agent Memory**. The agent searches long-term memory and uses the delivery preference in its answer.
3. Now tell the agent **"Please remember that I'm allergic to shellfish."** and ask **"What am I allergic to?"** in the same conversation. This uses short-term (session) memory.

> Long-term memory writes are intentionally not done by the agent's `remember_customer_detail` tool in this demo (the activity panel marks it as blocked). Long-term memories come from the seeded data and from Agent Memory's own extraction, so a new fact is not guaranteed to appear in the next conversation.

### Step 3: Read the seeded memories

Find them in `iris/domains/reddash/domain.py` (search for `seed_memories`).

## What You Learned

✅ Where the demo data lives in Redis  
✅ How long-term and short-term memory each shape the agent's answers  

---

**Next:** [Task 3: Change the Domain](/tasks/task-3.md)
