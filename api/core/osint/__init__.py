"""OSINT enricher registry — pluggable, concurrent, self-healing footprint enrichment."""
from .registry import aggregate

__all__ = ["aggregate"]
