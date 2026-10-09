"""Simple RAG service for the active domain."""

from __future__ import annotations

import json
from typing import Any, AsyncIterator
from uuid import uuid4

from langchain_core.messages import HumanMessage, SystemMessage
from redisvl.index import SearchIndex
from redisvl.query import VectorQuery

from backend.app.core.domain_loader import get_active_domain
from backend.app.embeddings import aembed_query
from backend.app.llm import build_chat_model, message_text
from backend.app.llm_errors import classify_llm_exception
from backend.app.redis_connection import RESILIENT_CONNECTION_KWARGS, build_redis_url, create_redis_client
from backend.app.settings import Settings


def _discover_index(settings: Settings, *, name_contains: str) -> str:
    """Find the domain-configured vector index name dynamically via FT._LIST.

    Scopes to the current surface ID to avoid matching stale indexes from
    previous surfaces.
    """
    client = create_redis_client(settings)
    indexes = client.execute_command("FT._LIST")
    surface_id = settings.ctx_surface_id or ""
    needle = name_contains.lower()
    for idx in indexes:
        name = idx if isinstance(idx, str) else idx.decode()
        if surface_id and surface_id not in name:
            continue
        if needle in name.lower():
            return name
    raise RuntimeError(
        f"No matching search index found for '{name_contains}'. Run setup/load first."
    )


def _first_field(result: dict[str, Any], fields: list[str]) -> str:
    for field in fields:
        value = result.get(field)
        if value:
            return str(value)
    return ""


class SimpleRAGService:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.domain = get_active_domain(settings)
        self._chat_model: Any = None
        self._index: SearchIndex | None = None
        self._index_name: str | None = None

    def _get_index(self) -> SearchIndex:
        if self._index is None:
            rag = self.domain.manifest.rag
            self._index_name = _discover_index(self.settings, name_contains=rag.index_name_contains)
            self._index = SearchIndex.from_existing(
                self._index_name,
                redis_url=build_redis_url(self.settings),
                connection_kwargs=RESILIENT_CONNECTION_KWARGS,
            )
        return self._index

    async def _embed(self, text: str) -> list[float]:
        return await aembed_query(text)

    def _model(self) -> Any:
        if self._chat_model is None:
            self._chat_model = build_chat_model(self.settings)
        return self._chat_model

    def _search_documents(self, embedding: list[float]) -> list[dict[str, Any]]:
        rag = self.domain.manifest.rag
        query = VectorQuery(
            vector=embedding,
            vector_field_name=rag.vector_field,
            return_fields=rag.return_fields,
            num_results=rag.num_results,
        )
        try:
            return self._get_index().query(query)
        except (ConnectionError, TimeoutError, OSError):
            self._index = None
            return self._get_index().query(query)

    async def stream_answer(self, question: str, timer: Any) -> AsyncIterator[str]:
        """Embed the question, search domain documents, stream a one-shot LLM answer."""
        rag = self.domain.manifest.rag
        tool_run_id = str(uuid4())

        yield _sse("status", text="Embedding query…", ts=timer.elapsed_ms())
        try:
            embedding = await self._embed(question)
        except Exception as exc:
            error_code, msg = classify_llm_exception(exc)
            yield _sse("error", errorCode=error_code, message=msg, ts=timer.elapsed_ms())
            return

        yield _sse("status", text=rag.status_text, ts=timer.elapsed_ms())
        yield _sse("tool-call", runId=tool_run_id, toolName=rag.tool_name,
                    toolKind="internal_function",
                    payload={"query": question, "num_results": rag.num_results},
                    ts=timer.elapsed_ms())

        timer.lap_ms()
        try:
            results = self._search_documents(embedding)
            search_duration = timer.lap_ms()
        except Exception as exc:
            search_duration = timer.lap_ms()
            yield _sse("tool-result", runId=tool_run_id, toolName=rag.tool_name,
                        toolKind="internal_function",
                        payload={"error": str(exc), "results": []},
                        durationMs=search_duration, ts=timer.elapsed_ms())
            yield _sse("text-delta",
                        delta="Simple RAG is not available right now because the vector search index is not ready.")
            return

        search_payload = [
            {k: v for k, v in r.items() if k != rag.vector_field} for r in results
        ]
        yield _sse("tool-result", runId=tool_run_id, toolName=rag.tool_name,
                    toolKind="internal_function",
                    payload={"results": search_payload},
                    durationMs=search_duration, ts=timer.elapsed_ms())

        yield _sse("status",
                    text=f"Found {len(results)} matching documents. {rag.generating_text}",
                    ts=timer.elapsed_ms())

        context_chunks: list[str] = []
        for r in results:
            title = _first_field(r, rag.title_fields) or "Document"
            label = _first_field(r, rag.label_fields)
            body = _first_field(r, rag.body_fields) or json.dumps(r, ensure_ascii=False)
            chunk = f"**{title}**"
            if label:
                chunk += f" ({label})"
            chunk += f":\n{body}"
            context_chunks.append(chunk)

        context_text = "\n\n".join(context_chunks)
        system_prompt = f"{rag.answer_system_prompt}\n\n--- DOMAIN DOCUMENTS ---\n{context_text}\n--- END ---"
        try:
            async for chunk in self._model().astream(
                [SystemMessage(content=system_prompt), HumanMessage(content=question)]
            ):
                delta = message_text(chunk.content)
                if delta:
                    yield _sse("text-delta", delta=delta)
        except Exception as exc:
            error_code, msg = classify_llm_exception(exc)
            yield _sse("error", errorCode=error_code, message=msg, ts=timer.elapsed_ms())


def _sse(event_type: str, **fields: Any) -> str:
    return f"data: {json.dumps({'type': event_type, **fields})}\n\n"
