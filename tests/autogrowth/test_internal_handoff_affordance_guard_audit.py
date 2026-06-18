from recon_lite_chess.autogrowth import (
    InternalHandoffAffordanceConfig,
    run_internal_handoff_affordance_guard_audit,
)


def test_tg26w_smoke_reports_internal_handoff_fields() -> None:
    result = run_internal_handoff_affordance_guard_audit(
        config=InternalHandoffAffordanceConfig(
            mate1_train_count=3,
            mate1_heldout_count=1,
            mate2_train_count=1,
            mate2_heldout_count=1,
            guardless_probe_position_count=0,
            max_ticks=20,
            max_samples=3,
            max_shared_atom_candidates_per_choice=2,
            shared_atom_min_overlap=6,
            equivalence_count=1,
        )
    )

    payload = result.to_dict()
    decision = payload["decision"]
    assert payload["checkpoint"] == "TG26w_internal_handoff_affordance_guard_audit"
    assert payload["purity_boundary"]["internal_handoff_affordance_materialized"] is True
    assert payload["purity_boundary"]["guard_used_during_runtime_choice"] is False
    assert payload["purity_boundary"]["guard_used_during_evaluation"] is False
    assert payload["purity_boundary"]["runtime_tablebase_or_dtm_move_source"] is False
    assert payload["purity_boundary"]["stage_labels_learner_visible"] is False

    for key in (
        "checkpoint_pass",
        "guarded_conversion_rate",
        "guardless_probe_conversion_rate",
        "internal_handoff_conversion_rate",
        "internal_handoff_first_move_success_rate",
        "internal_handoff_same_graph_second_move_count",
        "guard_used_during_training",
        "guard_used_during_runtime_choice",
        "guard_used_during_evaluation",
        "validator_skip_used_during_internal_handoff_eval",
        "fully_evaluated_candidate_count",
        "skipped_candidate_count",
        "internal_gate_approved_candidate_count",
        "internal_gate_rejected_candidate_count",
        "false_positive_internal_gate_count",
        "false_negative_internal_gate_count",
        "materialized_handoff_terminal_count",
        "materialized_handoff_quorum_count",
        "materialized_mate2_quorum_confirmed_count",
        "hardcoded_mate1_handoff",
        "runtime_tablebase_or_dtm_move_source",
        "action_ranker_used_for_runtime",
        "stage_labels_learner_visible",
        "scheduler_equivalence_mismatch_count",
        "ablation_results",
        "purity_boundary",
    ):
        assert key in decision

    assert decision["guard_used_during_runtime_choice"] is False
    assert decision["guard_used_during_evaluation"] is False
    assert decision["validator_skip_used_during_internal_handoff_eval"] is False
    assert decision["hardcoded_mate1_handoff"] is False

