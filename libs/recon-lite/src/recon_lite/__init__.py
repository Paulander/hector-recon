"""
Core ReCoN (Request-Confirmation Network) library.

This package provides the domain-agnostic ReCoN components that can be used for
hierarchical planning and execution tasks.
"""

from .__version__ import __version__
from .engine import ActivationMode, EngineConfig, ReConEngine
from .episodic_composition import (
    DecisionTrace,
    EpisodicCompositionConfig,
    EpisodicCompositionPolicy,
    GraphBackedCompositionChannel,
)
from .formal_engine import EdgeMessage, FormalMessage, FormalReConEngine
from .graph import Graph, LinkType, Node, NodeState, NodeType
from .logger import RunLogger
from .online_composition import (
    CompositeCandidate,
    OnlineCompositionConfig,
    OnlinePairCompositionLearner,
)
from .robust_return import (
    ReturnEstimate,
    RobustReturnConfig,
    RobustReturnMemory,
)
from .trace_db import LearningEvent

__all__ = [
    "__version__",
    "ActivationMode",
    "EdgeMessage",
    "EngineConfig",
    "DecisionTrace",
    "EpisodicCompositionConfig",
    "EpisodicCompositionPolicy",
    "FormalMessage",
    "FormalReConEngine",
    "Graph",
    "GraphBackedCompositionChannel",
    "LearningEvent",
    "LinkType",
    "Node",
    "NodeState",
    "NodeType",
    "CompositeCandidate",
    "OnlineCompositionConfig",
    "OnlinePairCompositionLearner",
    "ReConEngine",
    "ReturnEstimate",
    "RobustReturnConfig",
    "RobustReturnMemory",
    "RunLogger",
]
