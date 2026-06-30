import chess

from recon_lite_chess.autogrowth.validated_reachability_expansion import (
    ValidatedReachabilityExpansionConfig,
    _blocking_family,
    _decision,
    _first_candidates,
)


def _first(*, graph_all: bool = False, graph_partial: bool = False, valid_all: bool = False, valid_partial: bool = False) -> dict:
    return {
        "graph_positive_all_reply_handoff": graph_all,
        "graph_positive_any_reply_handoff": graph_all or graph_partial,
        "graph_positive_partial_handoff": graph_partial,
        "validated_all_reply_handoff": valid_all,
        "validated_any_reply_handoff": valid_all or valid_partial,
        "validated_partial_handoff": valid_partial,
    }


def _row(
    family: str,
    *,
    selected: dict | None = None,
    oracle: dict | None = None,
    blocking_family: str = "no_validated_second_move",
) -> dict:
    selected = selected or _first()
    oracle = oracle or _first()
    partial = bool(
        not selected["validated_all_reply_handoff"]
        and not oracle["validated_all_reply_handoff"]
        and (selected["validated_partial_handoff"] or oracle["validated_partial_handoff"])
    )
    no_response = bool(
        not selected["validated_all_reply_handoff"]
        and not oracle["validated_all_reply_handoff"]
        and not selected["validated_partial_handoff"]
        and not oracle["validated_partial_handoff"]
    )
    decoy = family in {"decoy_edge", "hard_decoy_edge"}
    return {
        "family": family,
        "selected_first_audit": selected,
        "oracle_first_audit": oracle,
        "validated_partial_only": partial,
        "no_validated_response": no_response,
        "decoy_validated_all_reply_false_handoff": bool(
            decoy and (selected["validated_all_reply_handoff"] or oracle["validated_all_reply_handoff"])
        ),
        "decoy_validated_partial_false_handoff": bool(
            decoy and (selected["validated_partial_handoff"] or oracle["validated_partial_handoff"])
        ),
        "blocking_family": blocking_family,
        "false_basin_quarantine_count": 0,
    }


def test_tg47i_graph_positive_response_is_not_validated_reachability() -> None:
    selected = _first(graph_all=True)
    oracle = _first(graph_all=True)

    assert _blocking_family(family="edge_trap_close", selected=selected, oracle=oracle) == "parent_foundation_basin_too_narrow"

    decision = _decision(
        config=ValidatedReachabilityExpansionConfig(),
        parent_hash="parent-hash",
        parent_before={"pass": True},
        parent_after={"pass": True},
        trace_rows=[_row("edge_trap_close", selected=selected, oracle=oracle, blocking_family="parent_foundation_basin_too_narrow")],
        false_basin_terminal_counts={"terminal:a": 1},
        parent_weight_delta=0,
        edge_weight_delta=0,
        total_seconds=0.1,
    )

    assert decision["non_decoy_selected_first_validated_all_reply_rate"] == 0.0
    assert decision["non_decoy_oracle_first_validated_all_reply_rate"] == 0.0
    assert decision["checkpoint_interpretation"] == "foundation_basin_or_objective_blocker"


def test_tg47i_partial_only_support_is_not_success() -> None:
    selected = _first(valid_partial=True)
    oracle = _first()

    assert _blocking_family(family="fence_hold_progress", selected=selected, oracle=oracle) == "only_partial_validated_support"

    decision = _decision(
        config=ValidatedReachabilityExpansionConfig(),
        parent_hash="parent-hash",
        parent_before={"pass": True},
        parent_after={"pass": True},
        trace_rows=[_row("fence_hold_progress", selected=selected, oracle=oracle, blocking_family="only_partial_validated_support")],
        false_basin_terminal_counts={},
        parent_weight_delta=0,
        edge_weight_delta=0,
        total_seconds=0.1,
    )

    assert decision["fence_hold_selected_first_validated_all_reply_rate"] == 0.0
    assert decision["fence_hold_validated_partial_only_count"] == 1


def test_tg47i_selected_and_oracle_rates_are_not_conflated() -> None:
    rows = [
        _row(
            "edge_trap_close",
            selected=_first(),
            oracle=_first(valid_all=True),
            blocking_family="selected_first_wrong_but_oracle_exists",
        ),
        _row("fence_hold_progress", selected=_first(), oracle=_first(), blocking_family="no_validated_second_move"),
    ]

    decision = _decision(
        config=ValidatedReachabilityExpansionConfig(),
        parent_hash="parent-hash",
        parent_before={"pass": True},
        parent_after={"pass": True},
        trace_rows=rows,
        false_basin_terminal_counts={},
        parent_weight_delta=0,
        edge_weight_delta=0,
        total_seconds=0.1,
    )

    assert decision["non_decoy_selected_first_validated_all_reply_rate"] == 0.0
    assert decision["non_decoy_oracle_first_validated_all_reply_rate"] == 0.5
    assert decision["checkpoint_interpretation"] == "first_move_selection_blocker"


def test_tg47i_decoy_partial_support_is_not_positive_target() -> None:
    row = _row(
        "decoy_edge",
        selected=_first(valid_partial=True),
        oracle=_first(),
        blocking_family="decoy_partial_near_basin",
    )

    decision = _decision(
        config=ValidatedReachabilityExpansionConfig(),
        parent_hash="parent-hash",
        parent_before={"pass": True},
        parent_after={"pass": True},
        trace_rows=[row],
        false_basin_terminal_counts={},
        parent_weight_delta=0,
        edge_weight_delta=0,
        total_seconds=0.1,
    )

    assert decision["non_decoy_selected_first_validated_all_reply_rate"] == 0.0
    assert decision["decoy_validated_partial_false_handoff_count"] == 1
    assert decision["checkpoint_interpretation"] == "foundation_basin_or_objective_blocker"


def test_tg47i_exhaustive_first_mode_does_not_apply_top_k_cap() -> None:
    board = chess.Board("8/8/8/8/8/8/4R3/4K1k1 w - - 0 1")
    config = ValidatedReachabilityExpansionConfig(first_move_mode="exhaustive", top_k_first=1)

    candidates = _first_candidates(board, config=config)

    assert len(candidates) > 1


def test_tg47i_decision_reports_mutation_invariants_density_and_next_action() -> None:
    rows = [_row("edge_trap_close", selected=_first(valid_all=True), oracle=_first(valid_all=True), blocking_family="validated_target_selected")]

    decision = _decision(
        config=ValidatedReachabilityExpansionConfig(),
        parent_hash="parent-hash",
        parent_before={"pass": True},
        parent_after={"pass": True},
        trace_rows=rows,
        false_basin_terminal_counts={"terminal:a": 2},
        parent_weight_delta=0,
        edge_weight_delta=0,
        total_seconds=0.1,
    )

    assert decision["parent_foundation_weight_delta_during_audit"] == 0
    assert decision["edge_learner_weight_delta_during_audit"] == 0
    assert "validated_target_density_by_family" in decision
    assert "edge_trap_close" in decision["validated_target_density_by_family"]
    assert "validated_target_density_by_horizon" in decision
    assert decision["selected_next_action"] == "train_handoff_specific_continuation_materialization"
    assert decision["false_basin_terminal_counts"] == {"terminal:a": 2}
    assert decision["runtime_tablebase_or_dtm_move_source"] is False
    assert decision["python_final_selector_used"] is False
    assert decision["direct_provider_override"] is False
