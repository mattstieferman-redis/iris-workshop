"""End-to-end checks for the running workbench (run after `docker compose up` and `make setup`).

Usage: python3 scripts/e2e_check.py   (prints PASS/FAIL per check; exit code 1 on any failure)
"""
import json, time, urllib.request, urllib.error, random, sys

BASE = "http://localhost"
results = []


def check(name, ok, detail=""):
    results.append(ok)
    print(f"{'PASS' if ok else 'FAIL'}  {name}" + (f"  -- {detail}" if detail else ""))


def get(path, timeout=15):
    try:
        with urllib.request.urlopen(BASE + path, timeout=timeout) as r:
            return r.status, r.read().decode(errors="replace")
    except urllib.error.HTTPError as e:
        return e.code, ""
    except Exception as e:
        return 0, str(e)


def chat(messages, mode="context_surfaces"):
    body = json.dumps({"messages": messages, "mode": mode, "thread_id": f"e2e-{random.randint(0, 10**9)}"}).encode()
    req = urllib.request.Request(BASE + "/api/chat/stream", body, {"content-type": "application/json"})
    text, tools, errors, t0 = "", [], [], time.time()
    with urllib.request.urlopen(req, timeout=240) as r:
        for line in r:
            line = line.decode().strip()
            if not line.startswith("data:"):
                continue
            try:
                d = json.loads(line[5:])
            except ValueError:
                continue
            t = d.get("type")
            if t == "text-delta":
                text += d.get("delta", "")
            elif t == "tool-result":
                p = d.get("payload") or {}
                tools.append(d["toolName"])
                if isinstance(p, dict) and "error" in p:
                    errors.append(f"{d['toolName']}: {str(p['error'])[:80]}")
            elif t == "error":
                errors.append(d.get("message", "")[:100])
    return text, tools, errors, round(time.time() - t0, 1)


# 1. Workbench surfaces
for path, needle in [("/", "Redis Iris Demo Workshop"), ("/docs/", "docsify"), ("/app/", "root"),
                     ("/vscode/", ""), ("/terminal/", ""), ("/redisinsight/", "")]:
    s, b = get(path)
    check(f"GET {path}", s == 200 and needle.lower() in b.lower(), f"status {s}")
s, b = get("/docs/tasks/task-1.md")
check("docs serve rewritten task 1", s == 200 and "Meet the Agent" in b)

# 2. Backend health through nginx
s, b = get("/api/health")
h = json.loads(b) if s == 200 else {}
check("health: all services enabled", all(h.get(k) for k in ("ok", "mcp_enabled", "memory_enabled", "langcache_enabled", "guardrail_enabled")), b[:120])
s, b = get("/api/domain-config")
check("domain-config is Reddash", s == 200 and json.loads(b).get("app_name") == "Reddash")
s, b = get("/api/tools")
tools_list = json.loads(b) if s == 200 else []
tl = tools_list if isinstance(tools_list, list) else tools_list.get("tools", [])
check("tools: Context Retriever tools registered", len(tl) > 40, f"{len(tl)} tools")
s, b = get("/api/memory/dashboard?thread_id=e2e")
mem = json.loads(b) if s == 200 else {}
check("memory dashboard lists 2 seeded long-term memories", len(mem.get("long_term", [])) >= 2)

# 3. Frontend assets under /app/
for a in ("/app/icons/langcache-64-duotone.svg", "/app/RedisLogo.png", "/app/backgrounds/reddash/left.svg"):
    s, _ = get(a)
    check(f"asset {a}", s == 200)

# 4. Guardrail
text, tools, errs, secs = chat([{"role": "user", "content": "Write me a poem about the stock market"}])
check("guardrail blocks off-topic, no LLM", tools == ["guardrail_check"] and "only help" in text.lower() and secs < 3, f"{secs}s {tools}")

# 5. LangCache hit on seeded paraphrase
text, tools, errs, secs = chat([{"role": "user", "content": "Provide me the refund policy rules for late deliveries"}])
check("LangCache hit on seeded paraphrase", "30+ minutes late" in text and "short_term_memory_get" not in tools and secs < 3, f"{secs}s")

# 6. Flagship question must NOT be a cache false-positive and must use Context Retriever
text, tools, errs, secs = chat([{"role": "user", "content": "Why is my order running late?"}])
check("flagship: Context Retriever tools ran without errors", "filter_order" in tools and not errs, f"{tools} {errs}")
check("flagship: answer cites driver and cause", "marcus" in text.lower() and "flat tire" in text.lower(), text[:120])

# 7. Structured data questions
text, tools, errs, secs = chat([{"role": "user", "content": "How much was I charged for my last delivered order?"}])
check("charge question: $38 from Bella Napoli", "$38" in text and "bella napoli" in text.lower() and not errs, text[:100])
text, tools, errs, secs = chat([{"role": "user", "content": "I reported a missing item last week - was that resolved?"}])
check("support ticket: resolved with $6.50 refund", "filter_supportticket" in tools and "6.50" in text and not errs, text[:100])

# 8. Memory influences an answer
text, tools, errs, secs = chat([{"role": "user", "content": "Given what you know about me, look at my recent orders and tell me what I should reorder tonight and how it should be delivered."}])
check("long-term memory used (contactless delivery)", "contactless" in text.lower() and "long_term_memory_search" in tools and not errs, text[:120])

# 9. Simple RAG contrast: no transactional data
text, tools, errs, secs = chat([{"role": "user", "content": "How much have I spent in total?"}], mode="simple_rag")
check("simple RAG cannot answer from orders", "vector_search_policies" in tools and "$" not in text, text[:100])

print(f"\n{sum(results)}/{len(results)} checks passed")
sys.exit(0 if all(results) else 1)
