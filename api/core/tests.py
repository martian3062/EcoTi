"""Core tests: event schema, correlator >=2-signal fusion, planner self-heal."""
from agents import citizen_shield, fraud_graph, scam_call
from django.test import TestCase, override_settings
from orchestrator import correlator, planner

from core.events import A2AEvent
from core.script_bank import match_script


class EventSchemaTest(TestCase):
    def test_a2a_event_jsonable(self):
        e = A2AEvent(module="scam_call", signal="x", confidence=0.7, identifier="+91999")
        d = e.model_dump_jsonable()
        self.assertEqual(d["module"], "scam_call")
        self.assertIsInstance(d["ts"], str)


class CorrelatorFusionTest(TestCase):
    def test_two_independent_signals_fuse(self):
        ident = "+919812345678"
        # Signal 1: scam_call
        s = scam_call.run({"identifier": ident, "audio_ref": "demo_scam_call.wav"})
        fused1 = correlator.ingest(s["event"])
        self.assertIsNone(fused1)  # only one module so far

        # Signal 2: fraud_graph -> should fuse (>= 2 independent modules)
        g = fraud_graph.run({"identifier": ident})
        fused2 = correlator.ingest(g["event"])
        self.assertIsNotNone(fused2)
        self.assertGreaterEqual(len(fused2.modules), 2)


class PlannerSelfHealTest(TestCase):
    @override_settings(FORCE_GNN_FAILURE=True)
    def test_fraud_graph_reroutes_to_rule_based(self):
        out = planner.run_agent("fraud_graph", {"identifier": "+919812345678"})
        self.assertEqual(out.get("_route"), "fallback")
        self.assertEqual(out.get("_fallback_used"), "rule_based_linkage")
        self.assertEqual(out["event"].payload["method"], "rule_based_fallback")


class P1CoreTest(TestCase):
    def test_script_bank_detects_digital_arrest(self):
        match = match_script(
            "This is CBI. Aadhaar money laundering digital arrest. "
            "Do not disconnect, stay on video and transfer to RBI account."
        )
        self.assertEqual(match["pattern_id"], "digital_arrest_v1")
        self.assertGreaterEqual(match["score"], 0.9)

    def test_shield_supports_all_demo_languages(self):
        for lang in citizen_shield.LANGS:
            out = citizen_shield.run(
                {
                    "identifier": "+919812345678",
                    "message": "CBI digital arrest. Transfer to RBI account now.",
                    "lang": lang,
                    "edge": True,
                }
            )
            self.assertEqual(out["lang"], lang)
            self.assertEqual(out["event"].route, "edge")
            self.assertTrue(out["advisory"])

    def test_p1_core_demo_endpoint(self):
        response = self.client.post(
            "/api/demo/p1-core",
            {
                "identifier": "+919812345678",
                "lang": "hi",
                "transcript": "CBI digital arrest. Aadhaar case. Transfer to RBI account now.",
            },
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["scam_call"]["verdict"], "scam")
        self.assertEqual(body["citizen_shield"]["verdict"], "scam")
        self.assertTrue(body["offline_proof"]["network_required"] is False)
