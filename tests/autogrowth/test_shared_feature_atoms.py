from recon_lite_chess.autogrowth import (
    SharedFeatureAtomConfig,
    run_shared_feature_atom_experiment,
)


def test_tg26s_smoke_reports_shared_atoms_and_required_fields() -> None:
    result = run_shared_feature_atom_experiment(
        config=SharedFeatureAtomConfig(
            train_count=3,
            heldout_count=2,
            train_repetitions=1,
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
    assert payload["checkpoint"] == "TG26s_shared_feature_atom_substrate"
    assert payload["runtime_purity_boundary"]["action_ranker_used_for_runtime"] is False
    assert payload["runtime_purity_boundary"]["runtime_tablebase_or_dtm_move_source"] is False
    assert payload["runtime_purity_boundary"]["stage_labels_learner_visible"] is False
    assert payload["shared_atom"]["shared_feature_atoms"] is True
    assert payload["shared_atom"]["grouped_cache_terminals_enabled"] is False
    assert payload["shared_atom"]["graph"]["shared_atom_count"] > 0
    assert payload["shared_atom"]["graph"]["reused_atom_count"] > 0
    for key in (
        "checkpoint_pass",
        "train_count",
        "heldout_count",
        "baseline_prototype_accuracy",
        "shared_atom_accuracy",
        "shared_projection_accuracy",
        "post_prune_accuracy",
        "null_selection_count_by_arm",
        "shared_atom_count",
        "triplet_local_feature_terminal_count",
        "grouped_cache_terminal_count",
        "reused_atom_count",
        "atom_activation_distribution",
        "atom_confirmation_distribution",
        "atom_false_positive_distribution",
        "top_positive_atoms",
        "top_negative_atoms",
        "top_reused_atoms",
        "pruned_exact_terminal_count",
        "pruned_triplet_count",
        "ablation_results",
        "scheduler_equivalence_mismatch_count",
        "runtime_purity_boundary",
    ):
        assert key in decision
