"""RAG corpus over MHA / I4C / RBI / Sanchar Saathi fraud advisories.

Embeddings are stored as JSON and scored with Python cosine similarity — this
runs identically on sqlite (local) and Postgres (VM), for any embedding
dimension, with zero extra infra. For a large corpus, swap ``embedding`` for a
``pgvector.django.VectorField`` + a CosineDistance index (the Postgres image
already ships pgvector); retrieval in ``rag/retrieve.py`` is the only call site.
"""
from django.db import models


class AdvisorySource(models.Model):
    """One ingested advisory document (from Firecrawl or the bundled corpus)."""

    title = models.CharField(max_length=300)
    url = models.URLField(blank=True, default="")
    authority = models.CharField(max_length=80, default="")  # I4C / RBI / MHA ...
    origin = models.CharField(max_length=20, default="seed")  # seed | firecrawl
    fetched_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.authority}: {self.title}"


class AdvisoryChunk(models.Model):
    """A retrievable chunk of an advisory with its embedding vector."""

    source = models.ForeignKey(AdvisorySource, on_delete=models.CASCADE, related_name="chunks")
    ordinal = models.IntegerField(default=0)
    text = models.TextField()
    embedding = models.JSONField(default=list)  # list[float]

    class Meta:
        ordering = ["source_id", "ordinal"]

    def __str__(self):
        return f"{self.source.title} #{self.ordinal}"
