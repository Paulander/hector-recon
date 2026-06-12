import json

from recon_lite_chess.autogrowth import PersistedPoolValidationConfig, run_persisted_pool_validation


def test_tg26e_persisted_pool_validation_contract(tmp_path) -> None:
    main_artifact = tmp_path / "tg26c_main.json"
    main_artifact.write_text(
        json.dumps({
            "schema_version": "krk_autogrowth_tg26c_edge_fence_handoff_curriculum.v0",
            "checkpoint": "TG26c_edge_fence_handoff_curriculum",
            "stages": [{}, {}],
        }),
        encoding="utf-8",
    )
    result = run_persisted_pool_validation(
        config=PersistedPoolValidationConfig(
            seed=44,
            foundation_mate1_train_count=24,
            foundation_mate1_heldout_count=8,
            foundation_mate1_mirror_count=4,
            foundation_mate2_train_count=4,
            foundation_mate2_heldout_count=2,
            train_pool_size=6,
            eval_window_size=3,
            train_chunk_size=10,
            max_chunks_per_stage=1,
            top_k_deep_score=3,
            max_generation_attempts=80_000,
            max_samples=2,
            mate1_regression_threshold=0.0,
            mate2_regression_threshold=0.0,
            tg26c_main_artifact_path=str(main_artifact),
        )
    )
    output = result.write_json(tmp_path / "tg26e.json")
    payload = json.loads(output.read_text(encoding="utf-8"))

    assert payload["schema_version"] == "krk_autogrowth_tg26e_persisted_pool_validation.v0"
    assert payload["training_runway"]["persisted_pools"] is True
    assert payload["training_runway"]["curriculum_labels_learner_visible"] is False
    assert payload["training_runway"]["direct_provider_override"] is False
    assert set(payload["pools"]) == {
        "edge_filtered",
        "edge_unfiltered",
        "edge_boundary_near_miss",
        "fence_filtered",
        "fence_unfiltered",
        "fence_boundary_near_miss",
    }
    for pool in payload["pools"].values():
        assert pool["stats"]["accepted_count"] == pool["position_count"]
        assert pool["stats"]["generation_attempts"] >= pool["position_count"]
        assert "no_handoff_candidate" in pool["stats"]["rejection_counts"]
        assert "cheap_cache_hit_rate" in pool["stats"]["scoring_cost"]
        assert pool["stats"]["top_k_deep_score"] == 3
        first = pool["entries"][0]
        assert "fen" in first
        assert first["handoff_type"] in {"none", "Mate_In_1", "Mate_In_2"}
        assert "cheap_candidate_scores" in first
        assert "deep_candidate_scores" in first
        assert "best_candidate_action" in first
        assert "cached_action_keys" in first
    for stage in payload["stages"]:
        assert set(stage["eval_slices"]) == {
            "filtered_train_like",
            "unfiltered_curriculum",
            "boundary_near_miss",
        }
        assert stage["m4_consolidation_event_count"] == 0
    assert payload["decision"]["stage_competence_claim"] is False
    assert payload["decision"]["m4_consolidation_event_count"] == 0
