"""Number-check tests: normalisation, known-scam, graph linkage, clean number."""
from django.test import TestCase

from core.number_intel import check_number, normalize


class NumberIntelTest(TestCase):
    def test_normalize_indian(self):
        self.assertEqual(normalize("98123 45678"), "+919812345678")
        self.assertEqual(normalize("0091 9812345678"), "+919812345678")

    def test_known_scam_and_graph_linkage(self):
        out = check_number("+919812345678")
        self.assertEqual(out["verdict"], "scam")
        self.assertGreaterEqual(out["risk_score"], 0.6)
        self.assertTrue(out["reasons"])
        self.assertTrue(out["recommended_actions"])

    def test_foreign_number_flagged_suspicious(self):
        out = check_number("+1 202 555 0100")
        self.assertIn(out["verdict"], {"suspicious", "scam"})

    def test_clean_indian_number_low_risk(self):
        out = check_number("+919123456780")
        self.assertEqual(out["verdict"], "safe")
