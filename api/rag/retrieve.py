"""Retrieval + answer synthesis (the advisory copilot).

Embed the question, rank chunks by cosine similarity (Python — swap for a
pgvector CosineDistance query for scale), then answer with the cloud reasoning
tier (Kimi long-context / Groq), grounded in the retrieved advisories with
citations. Degrades to an extractive answer when no LLM key is configured.
"""
from __future__ import annotations

import math
import re

from core import llm
from django.conf import settings

from .models import AdvisoryChunk

TOP_K = 4

_STOP = {
    "the", "a", "an", "is", "are", "i", "me", "my", "to", "of", "and", "in", "on",
    "for", "do", "if", "it", "this", "that", "what", "how", "should", "can", "will",
    "you", "your", "get", "got", "over", "am", "was", "with", "by", "or", "be",
}


def _tokens(text: str) -> set[str]:
    return {t for t in re.findall(r"[a-z0-9]+", (text or "").lower()) if t not in _STOP and len(t) > 1}


def _cosine(a: list[float], b: list[float]) -> float:
    if not a or not b:
        return 0.0
    n = min(len(a), len(b))
    a, b = a[:n], b[:n]
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    return dot / (na * nb) if na and nb else 0.0


def _embeddings_are_semantic() -> bool:
    """Stub embeddings are hash-based (no meaning); only trust cosine when a real
    embedding backend (HF / Ollama) is configured."""
    return bool(getattr(settings, "HF_TOKEN", "")) or llm.provider() == "ollama"


def retrieve(question: str, k: int = TOP_K) -> list[dict]:
    q_tokens = _tokens(question)
    semantic = _embeddings_are_semantic()
    qvec = llm.embed(question) if semantic else None

    scored = []
    for ch in AdvisoryChunk.objects.select_related("source").all():
        # Lexical overlap coefficient — meaningful with zero real models.
        c_tokens = _tokens(ch.text)
        inter = len(q_tokens & c_tokens)
        lexical = inter / (math.sqrt(len(q_tokens) or 1) * math.sqrt(len(c_tokens) or 1))
        if semantic and qvec is not None:
            score = 0.5 * lexical + 0.5 * _cosine(qvec, ch.embedding)
        else:
            score = lexical
        scored.append((score, ch))
    scored.sort(key=lambda t: t[0], reverse=True)
    out = []
    for score, ch in scored[:k]:
        out.append({
            "score": round(score, 4),
            "text": ch.text,
            "title": ch.source.title,
            "authority": ch.source.authority,
            "url": ch.source.url,
        })
    return out


def ask(question: str, k: int = TOP_K) -> dict:
    hits = retrieve(question, k)
    if not hits:
        return {"answer": "No advisories ingested yet. Run `manage.py ingest_advisories`.",
                "sources": [], "grounded": False}

    context = "\n\n".join(
        f"[{i+1}] ({h['authority']}) {h['title']}\n{h['text']}" for i, h in enumerate(hits)
    )
    system = (
        "You are EcoTi's fraud-advisory copilot for India. Answer ONLY from the "
        "provided official advisories (I4C/MHA/RBI/DoT). Be concise, practical and "
        "protective of the citizen. Cite sources as [n]. If unsure, tell the user to "
        "call 1930."
    )
    prompt = f"Question: {question}\n\nAdvisories:\n{context}\n\nAnswer with citations:"
    answer = llm.complete(prompt, system=system)

    # If no real LLM is configured the stub echoes the prompt; fall back to the
    # top advisory as an extractive answer so the copilot is always useful.
    if answer.startswith("[stub-verdict]"):
        answer = (
            f"{hits[0]['text']}\n\n(Source: [1] {hits[0]['authority']} — {hits[0]['title']}. "
            f"For help, call the 1930 cyber helpline.)"
        )

    return {
        "answer": answer,
        "sources": [
            {"n": i + 1, "authority": h["authority"], "title": h["title"],
             "url": h["url"], "score": h["score"]}
            for i, h in enumerate(hits)
        ],
        "grounded": True,
    }
