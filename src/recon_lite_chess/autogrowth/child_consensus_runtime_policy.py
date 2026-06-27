"""Feature-flagged child-consensus runtime policy.

The default policy is intentionally parent-only.  Child consensus can affect a
selection only when a caller explicitly selects one of the experimental policies
and supplies generic parent/child evidence.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal


ChildConsensusRuntimePolicyName = Literal[
    "parent_only",
    "child_shadow_only",
    "child_consensus_canary_balanced",
    "child_consensus_canary_failclosed",
    "no_child_canary_harness_control",
]


DEFAULT_CHILD_CONSENSUS_RUNTIME_POLICY: ChildConsensusRuntimePolicyName = "parent_only"


@dataclass(frozen=True)
class ChildConsensusRuntimeDecision:
    policy_name: ChildConsensusRuntimePolicyName
    final_selected_move: str
    parent_selected_move: str
    child_selected_move: str | None
    child_changed_selected_move: bool
    child_can_influence: bool
    child_shadow_active: bool
    gate_opened: bool
    consensus_active: bool
    gate_reason: str
    child_used_in_main_runtime: bool
    child_used_in_experimental_runtime: bool
    child_used_in_shadow_only: bool
    fail_closed: bool


def decide_child_consensus_runtime(
    *,
    policy_name: ChildConsensusRuntimePolicyName = DEFAULT_CHILD_CONSENSUS_RUNTIME_POLICY,
    parent_selected_move: str = "parent_terminal",
    child_selected_move: str = "experimental_child_terminal",
    evidence: dict[str, Any],
) -> ChildConsensusRuntimeDecision:
    """Choose a runtime terminal under an explicit child-consensus policy.

    Evidence fields are generic gate facts, not learner-visible stage/basin names.
    The function does not rank legal moves, call a provider, or mutate parent state.
    """

    if policy_name not in {
        "parent_only",
        "child_shadow_only",
        "child_consensus_canary_balanced",
        "child_consensus_canary_failclosed",
        "no_child_canary_harness_control",
    }:
        raise ValueError(f"unknown child consensus runtime policy: {policy_name}")

    gate = _gate_from_evidence(evidence)
    child_shadow = policy_name == "child_shadow_only"
    experimental = policy_name in {
        "child_consensus_canary_balanced",
        "child_consensus_canary_failclosed",
        "no_child_canary_harness_control",
    }
    can_influence = False
    if policy_name == "child_consensus_canary_balanced":
        can_influence = gate["balanced_open"]
    elif policy_name == "child_consensus_canary_failclosed":
        can_influence = gate["failclosed_open"]

    final = child_selected_move if can_influence else parent_selected_move
    reason = "child_gate_opened" if can_influence else _gate_closed_reason(policy_name, gate)
    return ChildConsensusRuntimeDecision(
        policy_name=policy_name,
        final_selected_move=final,
        parent_selected_move=parent_selected_move,
        child_selected_move=child_selected_move if gate["consensus_active"] or child_shadow or experimental else None,
        child_changed_selected_move=final != parent_selected_move,
        child_can_influence=can_influence,
        child_shadow_active=child_shadow,
        gate_opened=can_influence,
        consensus_active=gate["consensus_active"],
        gate_reason=reason,
        child_used_in_main_runtime=False,
        child_used_in_experimental_runtime=experimental and policy_name != "no_child_canary_harness_control",
        child_used_in_shadow_only=child_shadow,
        fail_closed=policy_name == "child_consensus_canary_failclosed",
    )


def _gate_from_evidence(evidence: dict[str, Any]) -> dict[str, bool]:
    parent_robust = bool(evidence.get("parent_robust_all_reply_response", False))
    parent_partial = bool(evidence.get("parent_partial_support", False))
    child_boundary = bool(evidence.get("child_boundary_recognition", False))
    child_consensus = bool(evidence.get("child_consensus_evidence", False))
    child_foundation = bool(evidence.get("child_foundation_response", False))
    child_continuation = bool(evidence.get("child_same_graph_continuation", False))
    child_shared = bool(evidence.get("child_shared_atom_support", False))
    child_quorum = bool(evidence.get("child_boundary_quorum_activation", False))
    child_actuator = bool(evidence.get("child_actuator_confirmation", False))
    decoy_veto = bool(evidence.get("decoy_veto_active", False))
    hard_decoy_veto = bool(evidence.get("hard_decoy_veto_active", False))
    cache_uncertain = bool(evidence.get("cache_live_uncertain", False))
    actuator_uncertain = bool(evidence.get("actuator_uncertain", False))
    reply_robust = bool(evidence.get("reply_envelope_robust", True))
    failclosed_confirmation = bool(evidence.get("failclosed_confirmation", False))
    consensus_active = (
        not parent_robust
        and parent_partial
        and child_boundary
        and child_consensus
        and child_foundation
        and (child_continuation or child_shared or child_quorum)
    )
    uncertainty_clear = not cache_uncertain and not actuator_uncertain
    veto_clear = not decoy_veto and not hard_decoy_veto
    balanced_open = consensus_active and child_actuator and reply_robust and uncertainty_clear and veto_clear
    failclosed_open = balanced_open and failclosed_confirmation
    return {
        "parent_robust": parent_robust,
        "child_boundary": child_boundary,
        "consensus_active": consensus_active,
        "child_actuator": child_actuator,
        "decoy_veto": decoy_veto,
        "hard_decoy_veto": hard_decoy_veto,
        "cache_uncertain": cache_uncertain,
        "actuator_uncertain": actuator_uncertain,
        "reply_robust": reply_robust,
        "balanced_open": balanced_open,
        "failclosed_open": failclosed_open,
    }


def _gate_closed_reason(policy_name: str, gate: dict[str, bool]) -> str:
    if policy_name in {"parent_only", "child_shadow_only", "no_child_canary_harness_control"}:
        return "gate_closed_policy_disabled"
    if gate["parent_robust"]:
        return "gate_closed_parent_robust"
    if gate["decoy_veto"]:
        return "gate_closed_decoy_veto"
    if gate["hard_decoy_veto"]:
        return "gate_closed_hard_decoy_veto"
    if gate["cache_uncertain"]:
        return "gate_closed_cache_uncertain"
    if gate["actuator_uncertain"] or not gate["child_actuator"]:
        return "gate_closed_actuator_uncertain"
    if not gate["child_boundary"]:
        return "gate_closed_no_child_boundary"
    if not gate["consensus_active"]:
        return "gate_closed_no_consensus"
    if not gate["reply_robust"]:
        return "gate_closed_reply_not_robust"
    return "gate_closed_reply_not_robust"
