"""Engine selection helpers for Hector experiments."""

from __future__ import annotations

from typing import Literal, Optional

from recon_lite import FormalReConEngine, ReConEngine
from recon_lite.engine import EngineConfig, GatingSchedule
from recon_lite.graph import Graph


EngineMode = Literal["pragmatic", "formal"]


def create_recon_engine(
    graph: Graph,
    *,
    mode: EngineMode = "pragmatic",
    gating_schedule: Optional[GatingSchedule] = None,
    config: Optional[EngineConfig] = None,
    validate_pairs: bool = True,
):
    """Create a ReCoN executor without changing legacy default behavior.

    ``pragmatic`` returns the existing high-level engine with SubgraphLock and
    continuous-activation support. ``formal`` returns the article-style
    symbolic message-passing executor and validates paired SUB/SUR and POR/RET
    links by default.
    """
    if mode == "pragmatic":
        return ReConEngine(graph, gating_schedule=gating_schedule, config=config)
    if mode == "formal":
        return FormalReConEngine(graph, validate_pairs=validate_pairs)
    raise ValueError(f"Unknown ReCoN engine mode: {mode!r}")
