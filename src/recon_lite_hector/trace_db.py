"""Compatibility re-exports for legacy Hector modules."""

from recon_lite.trace_db import (
    BanditArmSummary,
    EpisodeRecord,
    EpisodeSummary,
    TickRecord,
    TraceDB,
    outcome_to_score,
    pack_fingerprint,
)

__all__ = [
    "BanditArmSummary",
    "EpisodeRecord",
    "EpisodeSummary",
    "TickRecord",
    "TraceDB",
    "outcome_to_score",
    "pack_fingerprint",
]
