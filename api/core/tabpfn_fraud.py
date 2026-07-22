"""TabPFN fraud scorer — real ML, zero training.

TabPFN is a pretrained tabular foundation model: it classifies in a single
forward pass (in-context), so there is no gradient training. We fit it once on a
small labelled table of account-profile features (graph linkage + reports) and
predict a fraud probability for a queried identifier. Runs via the hosted
tabpfn-client (no local GPU). Behind ``TABPFN_API_KEY``; returns None on any
failure so ``fraud_graph`` keeps its deterministic + rule-based self-heal paths.
"""
from __future__ import annotations

import logging

from django.conf import settings

logger = logging.getLogger("ecoti.tabpfn")

FEATURES = ["cluster_size", "num_districts", "num_transfers", "watchlist", "reported_count"]

_clf = None
_tried = False
_pred_cache: dict[tuple, float] = {}  # feature-vector -> prob (predict is a network call)


def _training_table():
    import numpy as np

    rng = np.random.default_rng(42)
    n = 120
    # Fraud profiles: large multi-district mule clusters, watchlisted, reported.
    fraud = np.column_stack([
        rng.integers(4, 15, n),   # cluster_size
        rng.integers(2, 4, n),    # num_districts
        rng.integers(3, 14, n),   # num_transfers
        rng.integers(0, 2, n),    # watchlist
        rng.integers(1, 12, n),   # reported_count
    ])
    # Legit profiles: isolated, single/no district, never reported.
    legit = np.column_stack([
        rng.integers(0, 2, n),
        rng.integers(0, 1, n),
        rng.integers(0, 2, n),
        np.zeros(n, dtype=int),
        rng.integers(0, 1, n),
    ])
    X = np.vstack([fraud, legit]).astype(float)
    y = np.array([1] * n + [0] * n)
    return X, y


def _classifier():
    global _clf, _tried
    if _tried:
        return _clf
    _tried = True
    token = getattr(settings, "TABPFN_API_KEY", "")
    if not token:
        return None
    try:
        import tabpfn_client
        from tabpfn_client import TabPFNClassifier

        tabpfn_client.set_access_token(token)
        X, y = _training_table()
        clf = TabPFNClassifier()
        clf.fit(X, y)
        _clf = clf
        logger.info("TabPFN fraud classifier ready")
    except Exception as exc:  # pragma: no cover - network/optional
        logger.warning("TabPFN unavailable: %s", exc)
        _clf = None
    return _clf


def score(features: dict) -> float | None:
    """Fraud probability in [0,1], or None if TabPFN is unavailable."""
    clf = _classifier()
    if clf is None:
        return None
    key = tuple(float(features.get(f, 0)) for f in FEATURES)
    if key in _pred_cache:
        return _pred_cache[key]
    try:
        import numpy as np

        p = round(float(clf.predict_proba(np.array([key], dtype=float))[0][1]), 2)
        _pred_cache[key] = p
        return p
    except Exception as exc:  # pragma: no cover
        logger.warning("TabPFN predict failed: %s", exc)
        return None
