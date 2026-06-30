from recon_lite_chess.autogrowth.handoff_reachability_audit import (
    HandoffReachabilityAuditConfig,
    _decision,
    classify_blocker,
)
from recon_lite_chess.autogrowth.terminal_substrate import TerminalAffordanceLearner


def _first_audit(
    *,
    all_reply: bool = False,
    any_reply: bool = False,
    partial: bool = False,
    unsafe_second: bool = False,
    graded: bool = False,
) -> dict:
    return {
        "all_reply_second_handoff": all_reply,
        "any_reply_second_handoff": any_reply or all_reply,
        "has_partial_second_support": partial,
        "reply_envelope_success_rate": 1.0 if all_reply else 0.0,
        "unsafe_second_required": unsafe_second,
        "first_graded_success": graded,
    }


def _oracle_audit(
    *,
    all_reply: bool = False,
    any_reply: bool = False,
    partial: bool = False,
    unsafe_second: bool = False,
    graded: bool = False,
) -> dict:
    first = _first_audit(
        all_reply=all_reply,
        any_reply=any_reply,
        partial=partial,
        unsafe_second=unsafe_second,
        graded=graded,
    )
    return {
        "all_reply_second_handoff": all_reply,
        "any_reply_second_handoff": any_reply or all_reply,
        "has_partial_second_support": partial,
        "reply_envelope_success_rate": 1.0 if all_reply else 0.0,
        "best_first_audit": first,
    }


def test_tg47g_partial_only_handoff_is_not_success() -> None:
    blocker = classify_blocker(
        family="fence_hold_progress",
        selected=_first_audit(partial=True),
        oracle=_oracle_audit(partial=True),
    )

    assert blocker == "only_partial_reply_support"


def test_tg47g_decoy_partial_and_all_reply_handoffs_are_leaks() -> None:
    partial = classify_blocker(
        family="decoy_edge",
        selected=_first_audit(partial=True),
        oracle=_oracle_audit(),
    )
    all_reply = classify_blocker(
        family="hard_decoy_edge",
        selected=_first_audit(),
        oracle=_oracle_audit(all_reply=True),
    )

    assert partial == "decoy_partial_handoff_leak"
    assert all_reply == "decoy_all_reply_handoff_leak"


def test_tg47g_selected_and_oracle_first_move_audits_are_not_conflated() -> None:
    selected_bad = classify_blocker(
        family="edge_trap_progress",
        selected=_first_audit(),
        oracle=_oracle_audit(all_reply=True),
    )
    selected_good = classify_blocker(
        family="edge_trap_progress",
        selected=_first_audit(all_reply=True),
        oracle=_oracle_audit(),
    )

    assert selected_bad == "selected_first_move_bad"
    assert selected_good == "reachable_with_selected_first"


def test_tg47g_unsafe_second_move_cannot_satisfy_handoff() -> None:
    blocker = classify_blocker(
        family="fence_hold_progress",
        selected=_first_audit(unsafe_second=True),
        oracle=_oracle_audit(unsafe_second=True),
    )

    assert blocker == "unsafe_second_move_required"


def test_tg47g_decision_reports_freeze_purity_and_explicit_blockers() -> None:
    row = {
        "family": "fence_hold_progress",
        "selected_first_audit": _first_audit(partial=True),
        "oracle_first_audit": _oracle_audit(partial=True),
        "blocker_classification": "only_partial_reply_support",
        "decoy_partial_handoff_leak": False,
        "decoy_all_reply_handoff_leak": False,
    }
    decision = _decision(
        config=HandoffReachabilityAuditConfig(),
        parent_hash="parent-hash",
        parent_before={"pass": True},
        parent_after={"pass": True},
        audit_rows=[row],
        edge_learner=TerminalAffordanceLearner.create(eta_m3=0.08),
        total_seconds=0.1,
    )

    assert decision["checkpoint_pass"] is True
    assert decision["repair_applied"] is False
    assert decision["diagnostic_only"] is True
    assert decision["parent_foundation_frozen"] is True
    assert decision["parent_foundation_hash"] == "parent-hash"
    assert decision["parent_foundation_m3_delta_during_audit"] == 0
    assert decision["parent_foundation_m4_delta_during_audit"] == 0
    assert decision["edge_learner_weight_delta_during_audit"] == 0
    assert decision["old_tg_pools_loaded"] == 0
    assert decision["old_canary_loaded"] is False
    assert decision["child_branch_loaded"] is False
    assert decision["boundary_pool_loaded"] is False
    assert decision["runtime_tablebase_or_dtm_move_source"] is False
    assert decision["action_ranker_used_for_runtime"] is False
    assert decision["python_final_selector_used"] is False
    assert decision["direct_provider_override"] is False
    assert "only_partial_reply_support" in decision["blocker_classification_counts"]
    assert "no_blocker_classification" not in decision["blocker_classification_counts"]
