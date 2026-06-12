import json

from recon_lite_chess.autogrowth import HandoffFilterValidationConfig, run_handoff_filter_validation


def test_tg26d_handoff_filter_validation_reports_separate_slices(tmp_path) -> None:
    main_artifact = tmp_path / "tg26c_main.json"
    main_artifact.write_text(
        json.dumps({
            "schema_version": "krk_autogrowth_tg26c_edge_fence_handoff_curriculum.v0",
            "checkpoint": "TG26c_edge_fence_handoff_curriculum",
            "stages": [{}, {}],
        }),
        encoding="utf-8",
    )
    result = run_handoff_filter_validation(
        config=HandoffFilterValidationConfig(
            seed=43,
            foundation_mate1_train_count=24,
            foundation_mate1_heldout_count=8,
            foundation_mate1_mirror_count=4,
            foundation_mate2_train_count=4,
            foundation_mate2_heldout_count=2,
            train_pool_size=8,
            train_chunk_size=12,
            eval_window_size=4,
            max_chunks_per_stage=1,
            top_k_deep_score=3,
            max_generation_attempts=80_000,
            max_samples=2,
            mate1_regression_threshold=0.0,
            mate2_regression_threshold=0.0,
            tg26c_main_artifact_path=str(main_artifact),
        )
    )
    output = result.write_json(tmp_path / "tg26d.json")
    payload = json.loads(output.read_text(encoding="utf-8"))

    assert payload["schema_version"] == "krk_autogrowth_tg26d_handoff_filter_validation.v0"
    assert payload["artifact_integrity"]["parseable_full_json"] is True
    assert payload["training_runway"]["curriculum_filter_is_schedule_only"] is True
    assert payload["training_runway"]["curriculum_labels_learner_visible"] is False
    assert payload["training_runway"]["direct_provider_override"] is False
    assert payload["training_runway"]["runtime_tablebase_or_dtm_move_source"] is False
    assert len(payload["stages"]) == 2
    for stage in payload["stages"]:
        assert stage["m3_update_count"] > 0
        assert stage["m4_consolidation_event_count"] == 0
        assert set(stage["eval_slices"]) == {
            "filtered_train_like",
            "unfiltered_curriculum",
            "boundary_near_miss",
        }
        assert stage["train_pool"]["accepted_positions"] == 8
        assert stage["train_pool"]["generator_attempts"] >= 8
        assert "no_handoff_candidate" in stage["train_pool"]["rejection_reasons"]
        assert "cache_hit_rate" not in stage["train_pool"]
        assert "cheap_cache_hit_rate" in stage["train_pool"]["scoring_cost"]
        for metrics in stage["eval_slices"].values():
            assert "direct_mate_count" in metrics
            assert "mate1_handoff_count" in metrics
            assert "mate2_handoff_count" in metrics
            assert "illegal_count" in metrics
    assert payload["decision"]["m4_consolidation_event_count"] == 0
    assert payload["decision"]["stage_competence_claim"] is False
    assert set(payload["decision"]["stage_signals"]) == {"edge_trap", "fence_hold"}
