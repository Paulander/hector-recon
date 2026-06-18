from recon_lite_chess.autogrowth import (
    NativeQuorumMate2ChainingConfig,
    run_native_quorum_mate2_chaining,
)


def test_tg26v_smoke_reports_native_mate2_chain_fields() -> None:
    result = run_native_quorum_mate2_chaining(
        config=NativeQuorumMate2ChainingConfig(
            mate1_train_count=3,
            mate1_heldout_count=1,
            mate2_train_count=1,
            mate2_heldout_count=1,
            max_ticks=20,
            max_samples=3,
            max_candidates_per_move=1,
            max_shared_atom_candidates_per_choice=2,
            shared_atom_min_overlap=6,
            equivalence_count=1,
        )
    )

    payload = result.to_dict()
    decision = payload["decision"]
    assert payload["checkpoint"] == "TG26v_native_quorum_mate2_chaining"
    assert payload["purity_boundary"]["same_native_graph_for_mate1_and_mate2"] is True
    assert payload["purity_boundary"]["hardcoded_mate1_handoff"] is False
    assert payload["purity_boundary"]["action_ranker_used_for_runtime"] is False
    assert payload["purity_boundary"]["runtime_tablebase_or_dtm_move_source"] is False
    assert payload["purity_boundary"]["stage_labels_learner_visible"] is False

    for key in (
        "checkpoint_pass",
        "mate1_materialized_quorum_accuracy",
        "mate1_materialized_quorum_nulls",
        "mate2_train_count",
        "mate2_heldout_count",
        "mate2_first_move_success_rate",
        "mate2_conversion_rate",
        "same_graph_second_move_count",
        "hardcoded_mate1_handoff",
        "runtime_tablebase_or_dtm_move_source",
        "action_ranker_used_for_runtime",
        "materialized_mate2_quorum_confirmed_count",
        "soft_chain_diagnostic_accuracy",
        "strict_native_chain_materialized",
        "scheduler_equivalence_mismatch_count",
        "mate2_first_move_ablation_conversion",
        "mate1_quorum_ablation_conversion",
        "actuator_ablation_conversion",
        "purity_boundary",
    ):
        assert key in decision

    assert decision["hardcoded_mate1_handoff"] is False
    assert decision["runtime_tablebase_or_dtm_move_source"] is False
    assert decision["action_ranker_used_for_runtime"] is False
    assert payload["materialized_native_chain"]["strict_native_chain_materialized"] is True

