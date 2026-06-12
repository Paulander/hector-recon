import json

from recon_lite_chess.autogrowth import FenceBoundaryRehearsalConfig, run_fence_boundary_rehearsal


def test_tg26f_fence_boundary_rehearsal_contract(tmp_path) -> None:
    tg26c = tmp_path / "tg26c.json"
    tg26c.write_text(
        json.dumps({
            "schema_version": "krk_autogrowth_tg26c_edge_fence_handoff_curriculum.v0",
            "checkpoint": "TG26c_edge_fence_handoff_curriculum",
            "stages": [{}, {}],
        }),
        encoding="utf-8",
    )
    tg26e = tmp_path / "tg26e.json"
    tg26e.write_text(
        json.dumps({
            "schema_version": "krk_autogrowth_tg26e_persisted_pool_validation.v0",
            "stages": [
                {
                    "label": "fence_hold",
                    "eval_slices": {
                        "boundary_near_miss": {
                            "conversion_count": 0,
                            "position_count": 3,
                            "rook_loss_count": 0,
                            "confinement_regression_count": 0,
                        }
                    },
                }
            ],
        }),
        encoding="utf-8",
    )
    result = run_fence_boundary_rehearsal(
        config=FenceBoundaryRehearsalConfig(
            seed=45,
            foundation_mate1_train_count=24,
            foundation_mate1_heldout_count=8,
            foundation_mate1_mirror_count=4,
            foundation_mate2_train_count=4,
            foundation_mate2_heldout_count=2,
            train_pool_size=6,
            fence_rehearsal_pool_size=3,
            eval_window_size=3,
            train_chunk_size=12,
            max_chunks_per_stage=1,
            top_k_deep_score=3,
            max_generation_attempts=80_000,
            max_samples=2,
            mate1_regression_threshold=0.0,
            mate2_regression_threshold=0.0,
            tg26c_main_artifact_path=str(tg26c),
            tg26e_reference_artifact_path=str(tg26e),
        )
    )
    output = result.write_json(tmp_path / "tg26f.json")
    payload = json.loads(output.read_text(encoding="utf-8"))

    assert payload["schema_version"] == "krk_autogrowth_tg26f_fence_boundary_rehearsal.v0"
    assert payload["training_runway"]["fence_boundary_rehearsal"] is True
    assert payload["training_runway"]["curriculum_labels_learner_visible"] is False
    assert payload["training_runway"]["direct_provider_override"] is False
    assert payload["training_runway"]["runtime_tablebase_or_dtm_move_source"] is False
    assert "fence_unfiltered_rehearsal" in payload["pools"]
    assert "fence_boundary_rehearsal" in payload["pools"]
    fence = next(stage for stage in payload["stages"] if stage["label"] == "fence_hold")
    assert fence["rehearsal_pool_ids"] == {
        "unfiltered_curriculum": "fence_unfiltered_rehearsal",
        "boundary_near_miss": "fence_boundary_rehearsal",
    }
    assert set(fence["eval_slices"]) == {
        "filtered_train_like",
        "unfiltered_curriculum",
        "boundary_near_miss",
    }
    assert payload["decision"]["stage_competence_claim"] is False
    assert payload["decision"]["m4_consolidation_event_count"] == 0
