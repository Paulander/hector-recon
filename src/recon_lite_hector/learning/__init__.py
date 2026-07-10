"""Learning subpackage for structure learning and plasticity."""

from .m5_structure import (
    StructureLearner,
    AffordanceSpike,
    PromotionResult,
    PruningResult,
    create_pattern_sensor,
)
from .intrinsic_credit import (
    CausalCredit,
    CompetenceGateConfig,
    CompetenceGateExample,
    CompetenceSignal,
    CompetenceValueState,
    CreditEvent,
    IntrinsicCreditConfig,
    IntrinsicCreditEngine,
    OutcomeCalibratedCompetenceGate,
    Responsibility,
    apply_credit_event_to_edges,
)

__all__ = [
    "StructureLearner",
    "AffordanceSpike",
    "PromotionResult",
    "PruningResult",
    "create_pattern_sensor",
    "CausalCredit",
    "CompetenceGateConfig",
    "CompetenceGateExample",
    "CompetenceSignal",
    "CompetenceValueState",
    "CreditEvent",
    "IntrinsicCreditConfig",
    "IntrinsicCreditEngine",
    "OutcomeCalibratedCompetenceGate",
    "Responsibility",
    "apply_credit_event_to_edges",
]
