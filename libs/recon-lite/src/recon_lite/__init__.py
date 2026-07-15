"""
Core ReCoN (Request-Confirmation Network) library.

This package provides the domain-agnostic ReCoN components that can be used for
hierarchical planning and execution tasks.
"""

from .__version__ import __version__
from .causal_rent import (
    CandidateRentStats,
    CausalRentConfig,
    ExperienceReservoirConfig,
    LifetimeDecisionRecord,
    LifetimeDecisionReservoir,
    LifetimeReservoirMutation,
    record_supports_candidate,
)
from .engine import ActivationMode, EngineConfig, ReConEngine
from .episodic_composition import (
    DecisionTrace,
    EpisodicCompositionConfig,
    EpisodicCompositionPolicy,
    GraphBackedCompositionChannel,
)
from .formal_engine import EdgeMessage, FormalMessage, FormalReConEngine
from .choice_genome import (
    AnonymousChoiceEmission,
    AnonymousChoiceGenome,
    AnonymousChoiceOption,
)
from .frame_context import (
    ChildResponse,
    DreamStateLeakError,
    FrameContext,
    FrameEffectFirewall,
    FrameKind,
    VirtualFrameEvaluation,
    VirtualFrameExecutor,
    VirtualFrameSideEffectError,
    child_response_terminal,
    prediction_residual_terminal,
    prediction_surprise_terminal,
)
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
from .robust_policy import (
    GraphBackedRobustActionPolicy,
    RobustActionPolicyConfig,
)
from .trace_db import LearningEvent

__all__ = [
    "__version__",
    "ActivationMode",
    "AnonymousChoiceEmission",
    "AnonymousChoiceGenome",
    "AnonymousChoiceOption",
    "CandidateRentStats",
    "CausalRentConfig",
    "EdgeMessage",
    "EngineConfig",
    "DecisionTrace",
    "EpisodicCompositionConfig",
    "EpisodicCompositionPolicy",
    "ExperienceReservoirConfig",
    "FormalMessage",
    "FormalReConEngine",
    "FrameContext",
    "FrameEffectFirewall",
    "FrameKind",
    "Graph",
    "GraphBackedCompositionChannel",
    "LearningEvent",
    "LifetimeDecisionRecord",
    "LifetimeDecisionReservoir",
    "LifetimeReservoirMutation",
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
    "GraphBackedRobustActionPolicy",
    "RobustActionPolicyConfig",
    "RunLogger",
    "ChildResponse",
    "DreamStateLeakError",
    "VirtualFrameEvaluation",
    "VirtualFrameExecutor",
    "VirtualFrameSideEffectError",
    "child_response_terminal",
    "prediction_residual_terminal",
    "prediction_surprise_terminal",
    "record_supports_candidate",
]
