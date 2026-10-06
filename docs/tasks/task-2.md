# Task 2: Look Inside Redis

## Goal

See what the demo stored in Redis, and how Agent Memory changes the agent's answers.

## Instructions

### Step 1: Browse the data

1. Open **Redis Insight** from the ☰ menu.
2. Add a connection to your Redis Cloud database, using the `REDIS_*` values from `iris/.env`.
3. Look for keys starting with `reddash_` (orders, drivers, restaurants, policies). These are what Context Retriever exposes to the agent.

### Step 2: Teach the agent something

1. In the App, say **"Please remember that I'm allergic to peanuts."**
2. Start a new conversation and ask **"What restaurants would you recommend?"**
3. Check the **Agent Memory** section of the activity panel. The agent should find your stored preference.

### Step 3: Read the seeded memories

`make setup` seeded two long-term memories. Find them in `iris/domains/reddash/domain.py` (search for `seed_memories`).

## What You Learned

✅ Where the demo data lives in Redis  
✅ How long-term memory persists across conversations  

---

**Next:** [Task 3: Change the Domain](/tasks/task-3.md)
