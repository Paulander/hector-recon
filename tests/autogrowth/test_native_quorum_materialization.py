from recon_lite_chess.autogrowth import (
    NativeQuorumMaterializationConfig,
    run_native_quorum_materialization,
)


def test_tg26u_smoke_materializes_native_quorum_and_reports_ablations() -> None:
    result = run_native_quorum_materialization(
        config=NativeQuorumMaterializationConfig(
            train_count=3,
            heldout_count=2,
            max_ticks=20,
            max_samples=4,
            max_candidates_per_move=1,
            max_shared_atom_candidates_per_choice=2,
            shared_atom_min_overlap=6,
            equivalence_count=1,
        )
    )

    payload = result.to_dict()
    decision = payload["decision"]
    assert payload["checkpoint"] == "TG26u_native_quorum_materialization"
    assert payload["purity_boundary"]["strict_native_quorum_materialized"] is True
    assert payload["purity_boundary"]["soft_quorum_diagnostic_only"] is True
    assert payload["purity_boundary"]["action_ranker_used_for_runtime"] is False
    assert payload["purity_boundary"]["runtime_tablebase_or_dtm_move_source"] is False
    assert payload["purity_boundary"]["stage_labels_learner_visible"] is False

    for key in (
        "checkpoint_pass",
        "baseline_prototype_accuracy",
        "soft_quorum_accuracy",
        "materialized_quorum_accuracy",
        "materialized_quorum_nulls",
        "strict_native_quorum_materialized",
        "soft_quorum_selected_without_full_triplet_confirmation_count",
        "materialized_quorum_confirmed_inside_formal_engine_count",
        "featurehub_backed_atoms_used",
        "scheduler_equivalence_mismatch_count",
        "top_atom_ablation_accuracy",
        "action_atom_ablation_accuracy",
        "actuator_ablation_accuracy",
        "purity_boundary",
    ):
        assert key in decision

    assert decision["strict_native_quorum_materialized"] is True
    assert decision["actuator_ablation_accuracy"] == 0.0
    assert payload["materialized_quorum_veto_atoms"]["heldout"]["strict_native_quorum_materialized"] is True
    assert payload["ablations"]["remove_materialized_quorum_keep_shared_atoms"]["accuracy"] == 0.0

