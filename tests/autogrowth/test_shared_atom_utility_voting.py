from recon_lite_chess.autogrowth import (
    SharedAtomUtilityVotingConfig,
    run_shared_atom_utility_voting,
)


def test_tg26t_smoke_reports_utility_voting_arms_and_required_fields() -> None:
    result = run_shared_atom_utility_voting(
        config=SharedAtomUtilityVotingConfig(
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
    assert payload["checkpoint"] == "TG26t_shared_atom_utility_voting"
    assert payload["purity_boundary"]["action_ranker_used_for_runtime"] is False
    assert payload["purity_boundary"]["runtime_tablebase_or_dtm_move_source"] is False
    assert payload["purity_boundary"]["stage_labels_learner_visible"] is False
    for arm in (
        "shared_weighted_vote",
        "shared_action_atom_score",
        "shared_contrastive_credit",
        "soft_quorum",
    ):
        assert payload[arm]["heldout"]["position_count"] == 2
    for key in (
        "checkpoint_pass",
        "baseline_prototype_accuracy",
        "shared_hard_overlap_accuracy",
        "shared_weighted_vote_accuracy",
        "shared_action_atom_score_accuracy",
        "shared_contrastive_credit_accuracy",
        "soft_quorum_accuracy",
        "null_count_per_arm",
        "target_move_candidate_diagnostics",
        "action_atom_inclusion_exclusion_diagnostics",
        "active_atom_overlap_distribution",
        "atom_utility_contribution_samples",
        "top_positive_atoms",
        "top_negative_atoms",
        "high_precision_but_unused_atoms",
        "scheduler_equivalence_mismatches",
        "strict_native_quorum_materialized",
        "soft_quorum_selected_without_full_triplet_confirmation_count",
        "purity_boundary",
    ):
        assert key in decision
