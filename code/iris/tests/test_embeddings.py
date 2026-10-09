import math

import pytest

from backend.app import embeddings
from backend.app.settings import DEFAULT_EMBEDDING_DIM, DEFAULT_EMBEDDING_MODEL


def test_defaults_are_the_small_local_model():
    assert DEFAULT_EMBEDDING_MODEL == "sentence-transformers/all-MiniLM-L6-v2"
    assert DEFAULT_EMBEDDING_DIM == 384
    assert embeddings.EMBEDDING_DIM == DEFAULT_EMBEDDING_DIM


def test_hash_vectors_are_deterministic_unit_length_and_the_right_size():
    a = embeddings.embed_query("Where is my order?")
    b = embeddings.embed_query("Where is my order?")
    c = embeddings.embed_query("A different sentence")
    assert a == b and a != c
    assert len(a) == embeddings.EMBEDDING_DIM
    assert math.isclose(sum(v * v for v in a), 1.0, rel_tol=1e-6)


def test_embed_documents_batches_and_handles_empty():
    assert embeddings.embed_documents([]) == []
    docs = embeddings.embed_documents(["one", "two"])
    assert len(docs) == 2 and docs[0] == embeddings.embed_query("one")


def test_domain_vector_fields_follow_the_configured_size():
    from domains.reddash.generated_models import Policy

    assert f"vector_dim={embeddings.EMBEDDING_DIM}" in open("domains/reddash/generated_models.py").read()
    assert Policy is not None


def test_dimension_mismatch_explains_how_to_fix_it(monkeypatch):
    class FakeVectorizer:
        dims = 768

        def __init__(self, model):
            self.model = model

    embeddings.get_vectorizer.cache_clear()
    monkeypatch.setenv("EMBEDDING_MODEL", "some/other-model")
    monkeypatch.setattr("redisvl.utils.vectorize.HFTextVectorizer", FakeVectorizer)
    monkeypatch.setattr(embeddings, "get_settings", lambda: __import__("backend.app.settings", fromlist=["Settings"]).Settings(_env_file=None, embedding_model="some/other-model", embedding_dim=384))
    with pytest.raises(RuntimeError) as err:
        embeddings.get_vectorizer()
    assert "768" in str(err.value) and "make generate-models" in str(err.value)
    embeddings.get_vectorizer.cache_clear()
