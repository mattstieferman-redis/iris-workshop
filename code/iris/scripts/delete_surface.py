"""List and delete the Context Surfaces that belong to this demo.

Every `make setup` creates a NEW Context Surface and never removes the old one, and the admin key
is shared by everyone on the account (hundreds of surfaces from other people). So this tool only
touches surfaces it can tie to this checkout or this Redis database:

  * the surface in .env (CTX_SURFACE_ID),
  * surfaces recorded in .surface-ledger.json when `make setup` created them, and
  * surfaces that own search indexes (idx:<surface id>:...) in THIS Redis database.

Anything else needs an explicit --id plus --force.

Usage:
    python scripts/delete_surface.py --list             # show the surfaces tied to this demo
    python scripts/delete_surface.py                    # delete the surface in .env
    python scripts/delete_surface.py --old              # delete earlier surfaces (not the current one)
    python scripts/delete_surface.py --id <uuid> [--force]
Add --dry-run to see what would happen, and --yes to skip the confirmation prompt.

Deleting a surface also removes its search indexes from Redis, so the app stops working until you
run `make setup` again. Your Redis data and memories are not touched.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx
from dotenv import dotenv_values

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app.settings import ENV_PATH, get_settings  # noqa: E402

LEDGER_PATH = ROOT / ".surface-ledger.json"
_INDEX_RE = re.compile(r"^idx:([0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}):")


# ── pure helpers (unit tested) ────────────────────────────────────────────────

def surface_ids_from_index_names(index_names: list[str]) -> set[str]:
    """Surface IDs that own at least one search index (idx:<surface id>:...)."""
    return {m.group(1).lower() for name in index_names if (m := _INDEX_RE.match(name))}


@dataclass(frozen=True)
class Ownership:
    current_id: str
    ledger_ids: frozenset[str]
    index_ids: frozenset[str]

    def reason(self, surface_id: str) -> str | None:
        """Why this surface counts as belonging to this demo, or None if it does not."""
        sid = surface_id.lower()
        if sid == self.current_id.lower() and sid:
            return "current (.env)"
        if sid in self.ledger_ids:
            return "created by this checkout"
        if sid in self.index_ids:
            return "owns indexes in this Redis"
        return None


def clear_surface_env(text: str) -> str:
    """Blank CTX_SURFACE_ID and MCP_AGENT_KEY in .env text (same as the Makefile does)."""
    for key in ("CTX_SURFACE_ID", "MCP_AGENT_KEY"):
        text = re.sub(rf"^{key}=.*$", f"{key}=", text, flags=re.MULTILINE)
    return text


def confirmed(count: int, *, yes: bool, interactive: bool, ask=input) -> bool:
    if yes:
        return True
    if not interactive:
        print("Refusing to delete without --yes (no terminal available to confirm).")
        return False
    return ask(f"Delete {count} surface(s)? [y/N] ").strip().lower() in ("y", "yes")


# ── ledger ────────────────────────────────────────────────────────────────────

def read_ledger(path: Path = LEDGER_PATH) -> list[dict[str, Any]]:
    try:
        data = json.loads(path.read_text())
        return data if isinstance(data, list) else []
    except (FileNotFoundError, ValueError):
        return []


def record_surface(surface_id: str, name: str, path: Path = LEDGER_PATH) -> None:
    """Remember a surface this checkout created (called by setup_surface.py)."""
    entries = [e for e in read_ledger(path) if e.get("id") != surface_id]
    entries.append({"id": surface_id, "name": name, "created_at": datetime.now(timezone.utc).isoformat()})
    path.write_text(json.dumps(entries, indent=2) + "\n")


def forget_surface(surface_id: str, path: Path = LEDGER_PATH) -> None:
    entries = read_ledger(path)
    kept = [e for e in entries if e.get("id") != surface_id]
    if len(kept) != len(entries):
        path.write_text(json.dumps(kept, indent=2) + "\n")


# ── Context Surfaces admin API ────────────────────────────────────────────────

def _headers(admin_key: str) -> dict[str, str]:
    return {"Content-Type": "application/json", "X-API-Key": admin_key}


def describe_surface(api_url: str, admin_key: str, surface_id: str) -> dict[str, Any] | None:
    response = httpx.get(f"{api_url}/api/v1/context-surfaces/{surface_id}", headers=_headers(admin_key), timeout=30.0)
    if response.status_code == 404:
        return None
    response.raise_for_status()
    return response.json()


def delete_surface(api_url: str, admin_key: str, surface_id: str) -> str:
    """Delete one surface. Returns 'deleted' or 'already gone'."""
    response = httpx.delete(f"{api_url}/api/v1/context-surfaces/{surface_id}", headers=_headers(admin_key), timeout=60.0)
    if response.status_code == 404:
        return "already gone"
    if response.status_code not in (200, 202, 204):
        raise RuntimeError(f"HTTP {response.status_code}: {response.text[:200]}")
    return "deleted"


def redis_index_names() -> list[str]:
    from backend.app.redis_connection import create_redis_client

    client = create_redis_client(get_settings())
    return [n.decode() if isinstance(n, bytes) else n for n in client.execute_command("FT._LIST")]


# ── command ───────────────────────────────────────────────────────────────────

def _ownership(current_id: str) -> Ownership:
    return Ownership(
        current_id=current_id,
        ledger_ids=frozenset(str(e.get("id", "")).lower() for e in read_ledger()),
        index_ids=frozenset(surface_ids_from_index_names(redis_index_names())),
    )


def _row(info: dict[str, Any] | None, surface_id: str, reason: str | None) -> str:
    if info is None:
        return f"  {surface_id}  (not found in the account)  [{reason or 'unrelated'}]"
    created = str(info.get("created_at", ""))[:19].replace("T", " ")
    return f"  {surface_id}  {info.get('name', '?')}  created {created}  {info.get('status', '')}  [{reason or 'NOT tied to this demo'}]"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--list", action="store_true", help="show the surfaces tied to this demo and exit")
    parser.add_argument("--old", action="store_true", help="delete earlier surfaces tied to this demo, keeping the current one")
    parser.add_argument("--id", action="append", default=[], metavar="UUID", help="delete this surface (repeatable)")
    parser.add_argument("--force", action="store_true", help="allow --id for a surface not tied to this demo")
    parser.add_argument("--yes", action="store_true", help="do not ask for confirmation")
    parser.add_argument("--dry-run", action="store_true", help="show what would be deleted, delete nothing")
    parser.add_argument("--keep-env", action="store_true", help="do not blank CTX_SURFACE_ID / MCP_AGENT_KEY in .env")
    parser.add_argument("--hint", action="store_true", help="print a one-line reminder if earlier surfaces exist, then exit")
    args = parser.parse_args(argv)

    settings = get_settings()
    if not settings.ctx_admin_key:
        print("CTX_ADMIN_KEY is not set in .env")
        return 1
    from context_surfaces import config as cs_config

    api_url = str(cs_config.api_url).rstrip("/")
    env = dotenv_values(ENV_PATH) if ENV_PATH.exists() else {}
    current_id = (env.get("CTX_SURFACE_ID") or "").strip()
    own = _ownership(current_id)
    tied = sorted(({current_id.lower()} if current_id else set()) | set(own.ledger_ids) | set(own.index_ids))

    if args.list or args.hint:
        old = [sid for sid in tied if sid != current_id.lower()]
        if args.hint:
            if old:
                print(f"Note: {len(old)} earlier Context Surface(s) from this demo still exist. Remove them with: make delete-old-surfaces")
            return 0
        print(f"Surfaces tied to this demo ({len(tied)}); the account has many others that are never touched:")
        for sid in tied:
            print(_row(describe_surface(api_url, settings.ctx_admin_key, sid), sid, own.reason(sid)))
        if not tied:
            print("  (none)")
        return 0

    # Decide what to delete.
    targets: list[str] = []
    if args.id:
        targets = [sid.strip().lower() for sid in args.id]
    elif args.old:
        targets = [sid for sid in tied if sid != current_id.lower()]
    elif current_id:
        targets = [current_id.lower()]
    else:
        print("No CTX_SURFACE_ID in .env, nothing to delete. Use --list, --old or --id.")
        return 0

    plan: list[tuple[str, dict[str, Any] | None, str | None]] = []
    for sid in targets:
        reason = own.reason(sid)
        if reason is None and not args.force:
            print(f"Refusing to delete {sid}: it is not tied to this demo or this Redis database. Use --force if you are sure.")
            return 2
        plan.append((sid, describe_surface(api_url, settings.ctx_admin_key, sid), reason))

    if not plan:
        print("Nothing to delete.")
        return 0
    print("Surfaces to delete:")
    for sid, info, reason in plan:
        print(_row(info, sid, reason))
    deletes_current = any(sid == current_id.lower() for sid, _, _ in plan)
    if deletes_current:
        print("This includes the current surface: the app will stop working until you run `make setup` again.")
    if args.dry_run:
        print("Dry run: nothing deleted.")
        return 0
    if not confirmed(len(plan), yes=args.yes, interactive=sys.stdin.isatty()):
        print("Cancelled.")
        return 1

    failures = 0
    for sid, _, _ in plan:
        try:
            outcome = delete_surface(api_url, settings.ctx_admin_key, sid)
            print(f"  {sid}: {outcome}")
            forget_surface(sid)
        except Exception as exc:  # report and continue with the rest
            failures += 1
            print(f"  {sid}: FAILED ({exc})")

    if deletes_current and not failures and not args.keep_env and ENV_PATH.exists():
        ENV_PATH.write_text(clear_surface_env(ENV_PATH.read_text()))
        print("Cleared CTX_SURFACE_ID and MCP_AGENT_KEY in .env.")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
