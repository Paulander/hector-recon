"""Import-stable outer laboratory graph for future V2 harnesses.

The consumed V2 discriminator created its graph while the runner was
``__main__``.  This subclass deliberately has a permanent import path.  It does
not change the graph, learner, or authority implementation.
"""

from __future__ import annotations

from .native_prospective_evidence_v2_science import OpaqueChessEcologyGraph


class ImportStableOpaqueChessEcologyGraph(OpaqueChessEcologyGraph):
    """The old opaque ecology graph with a stable pickle module identity."""


__all__ = ["ImportStableOpaqueChessEcologyGraph"]
