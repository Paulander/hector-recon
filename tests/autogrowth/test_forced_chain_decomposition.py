from pathlib import Path

from recon_lite_chess.autogrowth import (
    ForcedChainDecompositionConfig,
    run_forced_chain_decomposition,
)


def test_tg26z_smoke_reports_forced_chain_decomposition_fields(tmp_path: Path) -> None:
    progress = tmp_path / "tg26z_progress.json"
    result = run_forced_chain_decomposition(
        config=ForcedChainDecompositionConfig(
            mate1_train_count=4,
            mate1_heldout_count=2,
            mate2_train_count=1,
            mate2_heldout_count=1,
            max_shared_atom_candidates_per_choice=2,
            non_forced_sample_limit=1,
            max_samples=2,
            equivalence_count=1,
            progress_output=str(progress),
        )
    )

    payload = result.to_dict()
    decision = payload["decision"]
    assert payload["checkpoint"] == "TG26z_forced_chain_decomposition"
    assert progress.exists()
    for key in (
        "checkpoint_pass",
        "mate1_heldout_accuracy",
        "mate1_null_count",
        "continuation_mate1_accuracy",
        "continuation_mate1_null_count",
        "forced_first_chain_success_rate",
        "forced_first_same_graph_second_move_count",
        "mate2_conversion_rate",
        "mate2_first_move_success_rate",
        "mate2_same_graph_second_move_count",
        "attention_false_positive_count",
        "attention_false_negative_count",
        "deep_reply_checks_run",
        "average_deep_reply_checks_per_position",
        "failure_bucket_counts",
        "chain_terminal_failure_count",
        "mate1_continuation_failure_count",
        "selection_failure_count",
        "candidate_cap_failure_count",
        "graph_confirmed_chain_count",
        "scheduler_equivalence_mismatch_count",
        "m3_update_count",
        "m4_promotion_count_by_terminal_kind",
        "ablation_results",
        "guard_used_during_runtime_choice",
        "guard_used_during_evaluation",
        "validator_skip_used_during_internal_handoff_eval",
        "action_ranker_used_for_runtime",
        "runtime_tablebase_or_dtm_move_source",
        "stage_labels_learner_visible",
        "purity_boundary",
    ):
        assert key in decision
    for bucket in (
        "attention_gate_rejected_candidate",
        "attention_gate_admitted_candidate",
        "mate1_continuation_failed_after_reply",
        "mate1_continuation_succeeded_but_chain_terminal_failed",
        "chain_terminal_succeeded_but_first_move_quorum_failed",
        "first_move_quorum_succeeded_but_selection_lost",
        "compute_budget_or_candidate_cap_blocked",
        "no_failure",
    ):
        assert bucket in decision["failure_bucket_counts"]
    assert decision["guard_used_during_runtime_choice"] is False
    assert decision["guard_used_during_evaluation"] is False
    assert decision["validator_skip_used_during_internal_handoff_eval"] is False
    assert decision["action_ranker_used_for_runtime"] is False
    assert decision["runtime_tablebase_or_dtm_move_source"] is False
    assert decision["stage_labels_learner_visible"] is False
