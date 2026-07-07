"""RAG tests: ingest bundled corpus, retrieve relevant chunk, answer grounded."""
from django.test import TestCase

from rag.corpus import SEED_ADVISORIES
from rag.ingest import ingest_document
from rag.models import AdvisoryChunk
from rag.retrieve import ask, retrieve


class RagTest(TestCase):
    def setUp(self):
        for doc in SEED_ADVISORIES:
            ingest_document(**doc)

    def test_corpus_ingested(self):
        self.assertGreaterEqual(AdvisoryChunk.objects.count(), len(SEED_ADVISORIES))

    def test_retrieve_returns_ranked_hits(self):
        hits = retrieve("Can CBI arrest me over a video call?")
        self.assertTrue(hits)
        self.assertIn("score", hits[0])
        # scores are sorted descending
        self.assertGreaterEqual(hits[0]["score"], hits[-1]["score"])

    def test_ask_is_grounded_with_sources(self):
        out = ask("What should I do if I get a digital arrest call?")
        self.assertTrue(out["grounded"])
        self.assertTrue(out["sources"])
        self.assertTrue(out["answer"])
