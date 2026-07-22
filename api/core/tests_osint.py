"""OSINT enricher-registry tests: classify, fuse, cache, fusion-event, graph."""
from unittest import mock

from django.test import TestCase

from core.events import A2AEvent
from core.footprint import classify
from core.models import OsintCache, TrustEvent
from core.osint import registry
from core.osint.base import EnrichResult


class ClassifyTest(TestCase):
    def test_kinds(self):
        self.assertEqual(classify("+91 98123 45678"), "phone")
        self.assertEqual(classify("a@b.com"), "email")
        self.assertEqual(classify("9812345678@okhdfcbank"), "upi")
        self.assertEqual(classify("185.220.101.1"), "ip")
        self.assertEqual(classify("someuser"), "username")


def _fake_high(identifier, ctx):
    return EnrichResult(
        risk=0.8, findings=["fake high-risk finding"], attributes={"a": 1},
        sources=["FakeSrc"], nodes=[{"id": "n1", "label": "N1", "type": "breach", "risk": 0.8}],
        edges=[{"src": identifier, "dst": "n1", "rel": "exposed_in"}],
        event=A2AEvent(module="osint", signal="breach_exposure", identifier=identifier, confidence=0.8),
    )


class RegistryTest(TestCase):
    def setUp(self):
        self._orig = registry.ENRICHERS
        registry.ENRICHERS = [("fake", {"email"}, _fake_high)]

    def tearDown(self):
        registry.ENRICHERS = self._orig

    def test_fuse_and_graph(self):
        fp = registry.aggregate("x@y.com", "email")
        self.assertEqual(fp["risk_score"], 0.8)
        self.assertEqual(fp["verdict"], "scam")
        self.assertIn("FakeSrc", fp["sources"])
        # center node + enricher node
        self.assertGreaterEqual(len(fp["graph"]["nodes"]), 2)
        self.assertEqual(len(fp["graph"]["edges"]), 1)

    def test_emits_fusion_event(self):
        before = TrustEvent.objects.filter(module="osint").count()
        registry.aggregate("z@y.com", "email")
        self.assertEqual(TrustEvent.objects.filter(module="osint").count(), before + 1)

    def test_cache_hit(self):
        registry.aggregate("c@y.com", "email")
        self.assertTrue(OsintCache.objects.filter(kind="email", identifier="c@y.com").exists())
        with mock.patch.object(registry, "_safe") as safe:
            fp = registry.aggregate("c@y.com", "email")
            self.assertTrue(fp["cached"])
            safe.assert_not_called()  # served from cache, no enrichers run
