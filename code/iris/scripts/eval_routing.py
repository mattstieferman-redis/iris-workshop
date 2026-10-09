"""Check a domain's guardrail and tool-route thresholds against its example messages.

Run this after changing the embedding model (EMBEDDING_MODEL), a route's references or a distance
threshold. It builds temporary Redis indexes with the same embedding model the app uses, scores the
messages in domains/<domain>/routing_eval.json, prints what went wrong, and drops the temporary indexes.

    python scripts/eval_routing.py [--domain reddash] [--eval-file my_messages.json] [--verbose]

Reports:
  guardrail   attacks that get through, legitimate messages that are blocked or flagged as injection
  tool routes questions whose expected tool group was NOT matched, plus how many groups match on average
              (fewer groups means fewer tools sent to the model, more means more tokens)
Exit code is 1 if any attack gets through or any legitimate message is flagged as injection.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from redisvl.extensions.router import Route, SemanticRouter  # noqa: E402
from redisvl.extensions.router.schema import RoutingConfig  # noqa: E402

from backend.app.core.domain_loader import load_domain  # noqa: E402
from backend.app.embeddings import get_vectorizer  # noqa: E402
from backend.app.redis_connection import build_redis_url, create_redis_client  # noqa: E402
from backend.app.settings import get_settings  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--domain", default=None)
    parser.add_argument("--eval-file", default=None, help="use these messages instead of domains/<domain>/routing_eval.json")
    parser.add_argument("--verbose", action="store_true", help="print every message, not only the problems")
    args = parser.parse_args()

    settings = get_settings()
    domain_id = args.domain or settings.demo_domain
    domain = load_domain(domain_id)
    eval_path = Path(args.eval_file) if args.eval_file else ROOT / "domains" / domain_id / "routing_eval.json"
    if not eval_path.exists():
        print(f"No {eval_path} for this domain; nothing to evaluate.")
        return 0
    data = json.loads(eval_path.read_text())
    vectorizer = get_vectorizer()
    redis_url = build_redis_url(settings)
    suffix = f"-eval-{int(time.time())}"
    created: list[str] = []
    failed = False
    print(f"Embedding model: {settings.embedding_model} ({vectorizer.dims} dims)")

    try:
        guard = domain.manifest.guardrail
        if guard:
            name = guard.router_name + suffix
            created.append(name)
            router = SemanticRouter(
                name=name, vectorizer=vectorizer,
                routes=[Route(name=r.name, references=r.references, distance_threshold=r.distance_threshold) for r in guard.routes],
                routing_config=RoutingConfig(aggregation_method="min"), redis_url=redis_url, overwrite=True,
            )

            def check(text: str) -> tuple[bool, str | None, float | None]:
                match = router(text)
                return match.name == guard.allowed_route_name, match.name, match.distance

            print(f"\nGuardrail '{guard.router_name}'")
            through = flagged = blocked_wrongly = labeled = 0
            for text in data.get("attacks", []):
                allowed, route, dist = check(text)
                labeled += route == "prompt_injection"
                if allowed:
                    through += 1
                    print(f"  ATTACK GOT THROUGH  {route} d={dist:.2f}  {text}")
                elif args.verbose:
                    print(f"  blocked ({route})  {text}")
            for text in data.get("legit", []):
                allowed, route, dist = check(text)
                if route == "prompt_injection":
                    flagged += 1
                    print(f"  LEGIT FLAGGED AS INJECTION  d={dist:.2f}  {text}")
                elif not allowed:
                    blocked_wrongly += 1
                    print(f"  legit blocked by '{route}'  {text}")
                elif args.verbose:
                    print(f"  allowed  {text}")
            n_a, n_l = len(data.get("attacks", [])), len(data.get("legit", []))
            print(f"  attacks blocked: {n_a - through}/{n_a} ({labeled} with the injection message)")
            print(f"  legitimate allowed: {n_l - flagged - blocked_wrongly}/{n_l} (flagged as injection: {flagged}, blocked otherwise: {blocked_wrongly})")
            failed = failed or through > 0 or flagged > 0

        tools = domain.manifest.tool_routing
        if tools and data.get("tool_routes"):
            name = tools.router_name + suffix
            created.append(name)
            router = SemanticRouter(
                name=name, vectorizer=vectorizer,
                routes=[Route(name=r.name, references=r.references, distance_threshold=r.distance_threshold) for r in tools.routes],
                routing_config=RoutingConfig(aggregation_method="min", max_k=tools.max_routes), redis_url=redis_url, overwrite=True,
            )
            print(f"\nTool routes '{tools.router_name}'")
            missed = fallbacks = total_matched = 0
            for case in data["tool_routes"]:
                matched = [m.name for m in router.route_many(case["question"], max_k=tools.max_routes) if m.name]
                total_matched += len(matched)
                fallbacks += not matched
                ok = any(route in matched for route in case["expected_any"])
                if not ok:
                    missed += 1
                    print(f"  MISSED  expected {case['expected_any']}, matched {matched or 'nothing (all tools sent)'}  {case['question']}")
                elif args.verbose:
                    print(f"  ok  {matched}  {case['question']}")
            n = len(data["tool_routes"])
            print(f"  expected group matched: {n - missed}/{n} | all-tools fallback: {fallbacks} | avg groups per question: {total_matched / n:.1f}")
    finally:
        client = create_redis_client(settings)
        for name in created:
            try:
                client.execute_command("FT.DROPINDEX", name, "DD")
            except Exception:
                pass
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
