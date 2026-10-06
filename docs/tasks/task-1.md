# Task 1: Meet the Agent

## Goal

Run the demo's scripted path and see which Iris component handles each message.

## Instructions

1. In the **App** panel, ask **"Why is my order running late?"**
2. Open the **Redis Iris** activity panel on the right. You should see **Semantic Routing** allow the question and **LangCache** report a hit. This question is pre-seeded in the cache.
3. Ask a question the cache has not seen: **"What is the status of my most recent order and who is the driver?"**
4. Watch the activity panel. This time the agent searches memory and calls **Context Retriever** tools (such as `filter_order`) against the data in Redis.
5. Ask **"Write me a poem about the stock market."** and watch **Semantic Routing** block it.

## Challenge

Open `iris/domains/reddash/docs/demo_paths.md` and run the flagship path "Late Order Investigation". Which tools does the agent call for each follow-up?

## What You Learned

✅ Off-topic questions never reach the LLM  
✅ Repeated questions are answered from the semantic cache  
✅ Other questions use memory and Context Retriever tools  

---

**Next:** [Task 2: Look Inside Redis](/tasks/task-2.md)
