from recon_lite_chess.autogrowth import (
    NativeFoundationGeneralizationConfig,
    run_native_foundation_generalization,
)


def test_tg26r_smoke_reports_generalization_arms_and_required_decision_fields() -> None:
    result = run_native_foundation_generalization(
        config=NativeFoundationGeneralizationConfig(
            mate1_train_count=6,
            mate1_heldout_count=3,
            mate2_train_count=3,
            mate2_heldout_count=1,
            train_repetitions=1,
            continuation_repetitions=1,
            equivalence_mate1_count=1,
            equivalence_mate2_count=0,
            max_samples=4,
        )
    )

    payload = result.to_dict()
    assert payload["checkpoint"] == "TG26r_native_foundation_generalization_repair"
    assert payload["purity_boundary"]["action_ranker_used_for_runtime"] is False
    assert payload["purity_boundary"]["runtime_tablebase_or_dtm_move_source"] is False
    assert payload["purity_boundary"]["stage_labels_learner_visible"] is False
    assert payload["exact_arm"]["key_mode"] == "exact"
    assert payload["prototype_arm"]["key_mode"] == "prototype"
    assert payload["canonical_arm"]["key_mode"] == "canonical"
    for key in (
        "generated_mate1_train_count",
        "generated_mate1_heldout_accuracy",
        "generated_mate2_train_count",
        "generated_mate2_heldout_conversion",
        "null_selection_count",
        "nearest_triplet_diagnostics",
        "exact_vs_prototype_comparison",
        "raw_vs_canonical_comparison",
        "scheduler_equivalence_mismatch_count",
        "m4_true_promotion_count",
        "mature_materialized_count",
        "checkpoint_pass",
    ):
        assert key in payload["decision"]
    assert payload["exact_vs_prototype_comparison"]["baseline_key_mode"] == "exact"
    assert payload["exact_vs_prototype_comparison"]["variant_key_mode"] == "prototype"
    assert payload["raw_vs_canonical_comparison"]["variant_key_mode"] == "canonical"
