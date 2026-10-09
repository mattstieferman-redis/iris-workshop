"""Test configuration: never download a model or call a model API.

Embeddings use the deterministic "hash" model, and no real API key is needed because the tests do
not call the LLM. These must be set before backend modules are imported.
"""

import os

os.environ["EMBEDDING_MODEL"] = "hash"
os.environ.setdefault("ANTHROPIC_API_KEY", "test-key")
