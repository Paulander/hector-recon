"""Terminal-kind lifecycle policy for TG26x native autogrowth runs."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from recon_lite import NodeType
from recon_lite_hector.nodes.stem_cell import StemCellState

from .native_single_graph_curriculum import NativeReConKRKGraph


@dataclass(frozen=True)
class TerminalKindPolicy:
    expected_activation_frequency: str
    inactivity_decay_rate: float
    minimum_exposures_before_pruning: int
    confirmation_threshold: float
    false_positive_penalty: float
    false_positive_penalty_delay_exposures: int
    false_negative_penalty: float
    m4_promotion_threshold: float
    survival_utility_formula: str
    pruning_reason: str


TERMINAL_LIFECYCLE_POLICY: dict[str, TerminalKindPolicy] = {
    "environment_feature_terminal": TerminalKindPolicy(
        expected_activation_frequency="medium_to_high",
        inactivity_decay_rate=0.030,
        minimum_exposures_before_pruning=8,
        confirmation_threshold=0.45,
        false_positive_penalty=0.055,
        false_positive_penalty_delay_exposures=0,
        false_negative_penalty=0.25,
        m4_promotion_threshold=0.70,
        survival_utility_formula="local_weight + 0.35*precision + 0.10*coverage - false_positive_penalty*false_positives - decay",
        pruning_reason="low precision/coverage after sufficient exposure",
    ),
    "action_delta_terminal": TerminalKindPolicy(
        expected_activation_frequency="medium",
        inactivity_decay_rate=0.020,
        minimum_exposures_before_pruning=10,
        confirmation_threshold=0.50,
        false_positive_penalty=0.080,
        false_positive_penalty_delay_exposures=0,
        false_negative_penalty=0.30,
        m4_promotion_threshold=0.72,
        survival_utility_formula="local_weight + 0.45*precision + 0.20*contrast - false_positive_penalty*false_positives - decay",
        pruning_reason="poor good-vs-bad legal-action contrast",
    ),
    "projection_or_conjunction_terminal": TerminalKindPolicy(
        expected_activation_frequency="low_to_medium",
        inactivity_decay_rate=0.012,
        minimum_exposures_before_pruning=14,
        confirmation_threshold=0.58,
        false_positive_penalty=0.070,
        false_positive_penalty_delay_exposures=2,
        false_negative_penalty=0.35,
        m4_promotion_threshold=0.78,
        survival_utility_formula="local_weight + 0.55*precision_gain + 0.15*coverage - 0.08*complexity - false_positive_penalty*false_positives - decay",
        pruning_reason="does not improve precision over child/shared atoms",
    ),
    "internal_attention_terminal": TerminalKindPolicy(
        expected_activation_frequency="low_to_medium",
        inactivity_decay_rate=0.006,
        minimum_exposures_before_pruning=20,
        confirmation_threshold=0.62,
        false_positive_penalty=0.045,
        false_positive_penalty_delay_exposures=8,
        false_negative_penalty=0.65,
        m4_promotion_threshold=0.82,
        survival_utility_formula="local_weight + 0.50*attention_precision + 0.25*saved_checks - 0.20*missed_true_positive_rate - delayed_false_positive_penalty - decay",
        pruning_reason="attention does not reduce checks or preserve true positives after exposure",
    ),
    "handoff_gate_terminal": TerminalKindPolicy(
        expected_activation_frequency="low",
        inactivity_decay_rate=0.005,
        minimum_exposures_before_pruning=24,
        confirmation_threshold=0.65,
        false_positive_penalty=0.040,
        false_positive_penalty_delay_exposures=10,
        false_negative_penalty=0.85,
        m4_promotion_threshold=0.84,
        survival_utility_formula="local_weight + 0.55*handoff_precision + 0.25*reply_check_reduction - 0.30*false_negative_rate - delayed_false_positive_penalty - decay",
        pruning_reason="handoff gate fails to preserve conversion or reduce unnecessary continuation checks",
    ),
    "chain_confidence_terminal": TerminalKindPolicy(
        expected_activation_frequency="low",
        inactivity_decay_rate=0.006,
        minimum_exposures_before_pruning=20,
        confirmation_threshold=0.65,
        false_positive_penalty=0.050,
        false_positive_penalty_delay_exposures=6,
        false_negative_penalty=0.55,
        m4_promotion_threshold=0.84,
        survival_utility_formula="local_weight + 0.55*chain_precision + 0.20*reply_coverage - false_positive_penalty*false_positives - decay",
        pruning_reason="chain confidence fails heldout continuation confirmation",
    ),
    "veto_or_safety_terminal": TerminalKindPolicy(
        expected_activation_frequency="rare",
        inactivity_decay_rate=0.002,
        minimum_exposures_before_pruning=30,
        confirmation_threshold=0.55,
        false_positive_penalty=0.020,
        false_positive_penalty_delay_exposures=12,
        false_negative_penalty=0.90,
        m4_promotion_threshold=0.80,
        survival_utility_formula="local_weight + 0.35*safety_precision - 0.60*false_negative_rate - mild_false_positive_penalty - decay",
        pruning_reason="safety veto misses catastrophic cases after sufficient exposure",
    ),
    "actuator_terminal": TerminalKindPolicy(
        expected_activation_frequency="environment_affordance_dependent",
        inactivity_decay_rate=0.000,
        minimum_exposures_before_pruning=50,
        confirmation_threshold=0.35,
        false_positive_penalty=0.100,
        false_positive_penalty_delay_exposures=0,
        false_negative_penalty=0.20,
        m4_promotion_threshold=0.70,
        survival_utility_formula="legal_confirm_rate + causal_contribution - illegal_or_unsafe_penalty",
        pruning_reason="consistently illegal, unsafe, or non-causal",
    ),
}


def apply_terminal_lifecycle(
    graph: NativeReConKRKGraph,
    *,
    heldout_confirmed: bool,
    prune: bool = True,
    promote: bool = True,
) -> dict[str, Any]:
    stats = _initial_stats()
    pruned_by_kind = {kind: 0 for kind in TERMINAL_LIFECYCLE_POLICY}
    promoted_by_kind = {kind: 0 for kind in TERMINAL_LIFECYCLE_POLICY}
    for node in graph.graph.nodes.values():
        if node.ntype != NodeType.TERMINAL:
            continue
        kind = classify_terminal_kind(node.meta)
        policy = TERMINAL_LIFECYCLE_POLICY[kind]
        exposures = _exposures(node.meta)
        confirmations = int(node.meta.get("confirm_count", 0)) + int(node.meta.get("handoff_positive_count", 0))
        false_positives = int(node.meta.get("false_positive_count", 0)) + int(node.meta.get("handoff_negative_count", 0))
        false_negatives = int(node.meta.get("false_negative_count", 0)) + int(node.meta.get("handoff_false_negative_count", 0))
        precision = confirmations / max(1, confirmations + false_positives)
        coverage = min(1.0, exposures / max(1, policy.minimum_exposures_before_pruning))
        decay = policy.inactivity_decay_rate * max(0, policy.minimum_exposures_before_pruning - exposures)
        contrast = max(0.0, float(node.meta.get("positive_correlation", 0.0)) - float(node.meta.get("negative_correlation", 0.0)))
        saved_checks = float(node.meta.get("handoff_positive_count", 0)) / max(1, exposures)
        missed_true_positive_rate = false_negatives / max(1, exposures)
        delayed_false_positives = max(0, false_positives - policy.false_positive_penalty_delay_exposures)
        utility = (
            float(node.meta.get("local_weight", 0.0))
            + 0.35 * precision
            + 0.10 * coverage
            + 0.15 * contrast
            + (0.15 * saved_checks if kind in {"internal_attention_terminal", "handoff_gate_terminal"} else 0.0)
            - policy.false_positive_penalty * delayed_false_positives
            - policy.false_negative_penalty * missed_true_positive_rate
            - decay
        )
        node.meta["terminal_lifecycle_kind"] = kind
        node.meta["lifecycle_policy"] = asdict(policy)
        node.meta["lifecycle_exposures"] = exposures
        node.meta["lifecycle_precision"] = round(precision, 6)
        node.meta["lifecycle_survival_utility"] = round(utility, 6)
        node.meta["lifecycle_confirmation_threshold"] = policy.confirmation_threshold
        node.meta["lifecycle_pruning_reason"] = policy.pruning_reason
        if (
            prune
            and kind != "actuator_terminal"
            and exposures >= policy.minimum_exposures_before_pruning
            and precision < policy.confirmation_threshold
            and utility < 0.0
        ):
            node.meta["tier"] = "dead"
            node.meta["stem_cell_state"] = StemCellState.PRUNED.name
            node.meta["quarantine_reason"] = policy.pruning_reason
            graph.pruned_terminal_ids.add(node.nid)
            pruned_by_kind[kind] += 1
        elif promote and heldout_confirmed and exposures >= policy.minimum_exposures_before_pruning and utility >= policy.m4_promotion_threshold:
            node.meta["tier"] = "mature"
            node.meta["stem_cell_state"] = StemCellState.MATURE.name
            node.meta["mature_reason"] = "tg26x_terminal_kind_lifecycle_heldout_confirmation"
            promoted_by_kind[kind] += 1
        item = stats[kind]
        item["count"] += 1
        item["avg_exposures"] += exposures
        item["avg_precision"] += precision
        item["avg_survival_utility"] += utility
        item["pruned_count"] += int(node.meta.get("stem_cell_state") == StemCellState.PRUNED.name)
        item["mature_count"] += int(node.meta.get("stem_cell_state") == StemCellState.MATURE.name)
    for item in stats.values():
        count = max(1, int(item["count"]))
        item["avg_exposures"] = round(float(item["avg_exposures"]) / count, 6)
        item["avg_precision"] = round(float(item["avg_precision"]) / count, 6)
        item["avg_survival_utility"] = round(float(item["avg_survival_utility"]) / count, 6)
    return {
        "policy": {kind: asdict(policy) for kind, policy in TERMINAL_LIFECYCLE_POLICY.items()},
        "terminal_kind_stats": stats,
        "m4_promotion_count_by_terminal_kind": promoted_by_kind,
        "pruning_count_by_terminal_kind": pruned_by_kind,
        "heldout_confirmed": heldout_confirmed,
        "pruning_enabled": prune,
        "promotion_enabled": promote,
    }


def classify_terminal_kind(meta: dict[str, Any]) -> str:
    terminal_kind = str(meta.get("terminal_kind", ""))
    role = str(meta.get("role", ""))
    key = str(meta.get("terminal_key", ""))
    if terminal_kind == "actuator_affordance" or "actuator" in role:
        return "actuator_terminal"
    if terminal_kind in {"continuation_attention_gate"} or role in {"handoff_affordance_positive", "continuation_attention_gate"}:
        return "handoff_gate_terminal"
    if terminal_kind in {"same_graph_continuation_confirmation", "chain_evidence_quorum"} or "chain" in role:
        return "chain_confidence_terminal"
    if "veto" in role or "safety" in role:
        return "veto_or_safety_terminal"
    if role == "projection_feature" or "projection" in role or key.startswith("projection:") or ":pair:" in key:
        return "projection_or_conjunction_terminal"
    if role in {"delta_feature"} or key.startswith("action_pattern:") or key.startswith("delta_terminal:"):
        return "action_delta_terminal"
    if role in {"quorum_evidence_terminal"} or terminal_kind == "evidence_quorum":
        return "internal_attention_terminal"
    return "environment_feature_terminal"


def _exposures(meta: dict[str, Any]) -> int:
    return (
        int(meta.get("request_exposures", 0))
        + int(meta.get("activation_count", 0))
        + int(meta.get("handoff_affordance_exposure_count", 0))
    )


def _initial_stats() -> dict[str, dict[str, Any]]:
    return {
        kind: {
            "count": 0,
            "avg_exposures": 0.0,
            "avg_precision": 0.0,
            "avg_survival_utility": 0.0,
            "pruned_count": 0,
            "mature_count": 0,
            "policy": asdict(policy),
        }
        for kind, policy in TERMINAL_LIFECYCLE_POLICY.items()
    }
