# Task 2: Look Inside Redis

## Goal

See what the demo stored in Redis, and how Agent Memory changes the agent's answers.

## Instructions

### Step 1: Browse the data

Redis Insight does not know about your database yet. The demo stores its data in the Redis database from `iris/.env`, not in the workshop's local Redis container. A connection file for it is generated from your `.env` (when the backend starts, and by `make setup`), so you can import it:

1. In the **Code** panel, find `iris/redis-insight-import.json`. Right-click it and choose **Download...** (it is created once `REDIS_HOST` is set in `.env`; run `make insight-import` in the Terminal to regenerate it).
2. Open **Redis Insight** from the ☰ menu. The first time, it shows an **EULA and Privacy settings** dialog. Read it, choose your privacy settings, and accept the terms to continue. (*Encrypt sensitive information* is unavailable in this environment, so your connection details stay in this workshop environment only.)
3. Click **Add Redis database**, then **Import from file**, and choose the file you downloaded.
4. Open **Iris demo database**. Look for keys starting with `reddash_` (orders, drivers, restaurants, policies). These are what Context Retriever exposes to the agent. The **Search** tab lists the indexes that make them queryable.

The file contains your Redis password, so keep it private (it is gitignored and not shared).

> If you would rather type the connection in: **Add Redis database**, then **Connection settings**, with Host `REDIS_HOST`, Port `REDIS_PORT`, Username `REDIS_USERNAME` (usually `default`), Password `REDIS_PASSWORD`, and TLS on only if `REDIS_SSL=true`.
>
> If the database looks empty, check that you connected to the database in `.env` and that `make setup` finished. The local "redis" container is not used by the demo.

### Step 2: See memory change an answer

`make setup` seeded two long-term memories for the demo customer: *prefers contactless delivery* and *likes spicy food*.

1. In a new conversation ask: **"Given what you know about me, look at my recent orders and tell me what I should reorder tonight and how it should be delivered."**
2. In the activity panel, open **Agent Memory**. The agent searches long-term memory and uses the delivery preference in its answer.
3. Now tell the agent **"Please remember that I'm allergic to shellfish."** In the activity panel the `remember_customer_detail` tool saves it to long-term memory (look for **Long-term memory · CREATE**).
4. Start a **new conversation** and ask **"What am I allergic to?"**. The agent finds the saved memory, even though this is a different session.
5. Try a general question such as **"What should I order tonight?"**. Long-term memory is found by similarity to your message, so a question with nothing about allergies in it may not bring up the allergy. Why is that, and how would you make sure the agent always considers it?

Saving the same fact twice updates one memory instead of creating a duplicate. You can see all of the customer's memories in the **All Context** tab, or in Redis Insight under the `memory:` keys.

### Step 3: Read the seeded memories

Find them in `iris/domains/reddash/domain.py` (search for `seed_memories`).

## What You Learned

✅ Where the demo data lives in Redis  
✅ How long-term and short-term memory each shape the agent's answers  

---

**Next:** [Task 3: Change the Domain](/tasks/task-3.md)
