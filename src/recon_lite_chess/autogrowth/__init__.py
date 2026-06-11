"""Learning-first KRK autogrowth utilities."""

from .evaluate import (
    ArmMetrics,
    EvaluationConfig,
    EvaluationResult,
    evaluate_arm,
    evaluate_baseline_and_sham,
)
from .experiment import (
    AutogrowthExperimentConfig,
    AutogrowthExperimentResult,
    run_autogrowth_experiment,
)
from .features import (
    FORBIDDEN_LEARNER_TERMS,
    extract_learner_features,
    make_trace_record,
    validate_learner_record,
)
from .mining import (
    CandidateMiningConfig,
    CandidateMiningResult,
    mine_triplet_candidates_from_artifact,
    mine_triplet_candidates_from_records,
)
from .positions import (
    KRKPositionSet,
    can_mate_in_one,
    generate_position_sets,
    is_valid_krk_seed,
)
from .sandbox import (
    SandboxConfig,
    SandboxMetrics,
    SandboxResult,
    evaluate_candidate_sandbox,
    evaluate_sandbox_arm,
    load_selected_candidate,
)
from .traces import (
    TraceCollectionConfig,
    TraceCollectionResult,
    collect_trace_records,
)

__all__ = [
    "ArmMetrics",
    "AutogrowthExperimentConfig",
    "AutogrowthExperimentResult",
    "CandidateMiningConfig",
    "CandidateMiningResult",
    "EvaluationConfig",
    "EvaluationResult",
    "FORBIDDEN_LEARNER_TERMS",
    "KRKPositionSet",
    "SandboxConfig",
    "SandboxMetrics",
    "SandboxResult",
    "TraceCollectionConfig",
    "TraceCollectionResult",
    "can_mate_in_one",
    "collect_trace_records",
    "evaluate_arm",
    "evaluate_baseline_and_sham",
    "evaluate_candidate_sandbox",
    "evaluate_sandbox_arm",
    "extract_learner_features",
    "generate_position_sets",
    "is_valid_krk_seed",
    "load_selected_candidate",
    "make_trace_record",
    "mine_triplet_candidates_from_artifact",
    "mine_triplet_candidates_from_records",
    "run_autogrowth_experiment",
    "validate_learner_record",
]
