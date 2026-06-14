import json

from recon_lite_chess.autogrowth import (
    ContextGatedEdgeFenceValidationConfig,
    TerminalEdgeFenceValidationConfig,
    run_context_gated_edge_fence_validation,
    run_terminal_edge_fence_validation,
    validate_learner_record,
)


def test_tg26i_terminal_edge_fence_validation_contract(tmp_path) -> None:
    tg26c = tmp_path / "tg26c.json"
    tg26c.write_text(
        json.dumps({
            "schema_version": "krk_autogrowth_tg26c_edge_fence_handoff_curriculum.v0",
            "checkpoint": "TG26c_edge_fence_handoff_curriculum",
            "stages": [],
        }),
        encoding="utf-8",
    )
    tg26g = tmp_path / "tg26g.json"
    tg26g.write_text(
        json.dumps({
            "schema_version": "krk_autogrowth_tg26g_fence_boundary_signal.v0",
            "stages": [
                {
                    "label": "edge_trap",
                    "eval_slices": {
                        "unfiltered_curriculum": {
                            "conversion_count": 12,
                            "position_count": 32,
                            "rook_loss_count": 0,
                            "confinement_regression_count": 0,
                        },
                        "boundary_near_miss": {
                            "conversion_count": 4,
                            "position_count": 32,
                            "rook_loss_count": 0,
                            "confinement_regression_count": 0,
                        },
                    },
                },
                {
                    "label": "fence_hold",
                    "eval_slices": {
                        "unfiltered_curriculum": {
                            "conversion_count": 3,
                            "position_count": 32,
                            "rook_loss_count": 0,
                            "confinement_regression_count": 0,
                        },
                        "boundary_near_miss": {
                            "conversion_count": 0,
                            "position_count": 32,
                            "rook_loss_count": 0,
                            "confinement_regression_count": 0,
                        },
                    },
                },
            ],
        }),
        encoding="utf-8",
    )
    result = run_terminal_edge_fence_validation(
        config=TerminalEdgeFenceValidationConfig(
            seed=2701,
            foundation_seed=2702,
            foundation_mate1_train_count=36,
            foundation_mate1_heldout_count=12,
            foundation_mate1_mirror_count=6,
            foundation_mate2_train_count=4,
            foundation_mate2_heldout_count=2,
            train_pool_size=4,
            fence_rehearsal_pool_size=2,
            eval_window_size=2,
            train_chunk_size=4,
            max_chunks_per_stage=1,
            mate1_regression_threshold=0.50,
            mate2_regression_threshold=0.0,
            max_generation_attempts=120_000,
            top_k_deep_score=2,
            max_samples=1,
            tg26c_main_artifact_path=str(tg26c),
            tg26g_reference_artifact_path=str(tg26g),
        )
    )
    output = result.write_json(tmp_path / "tg26i.json")
    payload = json.loads(output.read_text(encoding="utf-8"))

    assert payload["schema_version"] == "krk_autogrowth_tg26i_terminal_edge_fence_validation.v0"
    assert payload["training_runway"]["uses_terminal_native_foundation"] is True
    assert payload["training_runway"]["uses_terminal_native_stage_rankers"] is True
    assert payload["training_runway"]["action_ranker_status"] == "reference_scaffolding_only"
    assert payload["training_runway"]["direct_provider_override"] is False
    assert payload["training_runway"]["runtime_tablebase_or_dtm_move_source"] is False
    assert payload["local_recon_structure"]["behavior_choice_mediated_by_terminal_activations"] is True
    assert payload["foundation"]["source_checkpoint"] == "TG26h_terminal_substrate_revival"
    assert len(payload["stages"]) == 2
    assert {stage["label"] for stage in payload["stages"]} == {"edge_trap", "fence_hold"}
    for stage in payload["stages"]:
        assert "stage_terminal_substrate" in stage
        assert stage["stage_terminal_substrate"]["terminal_count"] > 0
        assert stage["m4_consolidation_event_count"] == 0
    assert payload["decision"]["stage_competence_claim"] is False
    assert payload["decision"]["broad_random_krk_enabled"] is False
    validate_learner_record(payload["stages"][0]["stage_terminal_substrate"]["top_positive_terminals"])


def test_tg26m_context_gated_edge_fence_validation_contract(tmp_path) -> None:
    tg26c = tmp_path / "tg26c.json"
    tg26c.write_text(
        json.dumps({
            "schema_version": "krk_autogrowth_tg26c_edge_fence_handoff_curriculum.v0",
            "checkpoint": "TG26c_edge_fence_handoff_curriculum",
            "stages": [],
        }),
        encoding="utf-8",
    )
    tg26i = tmp_path / "tg26i.json"
    tg26i.write_text(
        json.dumps({
            "schema_version": "krk_autogrowth_tg26i_terminal_edge_fence_validation.v0",
            "stages": [
                {
                    "label": "edge_trap",
                    "eval_slices": {
                        "unfiltered_curriculum": {
                            "conversion_count": 8,
                            "position_count": 16,
                            "rook_loss_count": 0,
                            "confinement_regression_count": 0,
                        },
                        "boundary_near_miss": {
                            "conversion_count": 4,
                            "position_count": 16,
                            "rook_loss_count": 0,
                            "confinement_regression_count": 0,
                        },
                    },
                },
                {
                    "label": "fence_hold",
                    "eval_slices": {
                        "unfiltered_curriculum": {
                            "conversion_count": 1,
                            "position_count": 16,
                            "rook_loss_count": 0,
                            "confinement_regression_count": 0,
                        },
                        "boundary_near_miss": {
                            "conversion_count": 0,
                            "position_count": 16,
                            "rook_loss_count": 0,
                            "confinement_regression_count": 0,
                        },
                    },
                },
            ],
        }),
        encoding="utf-8",
    )
    result = run_context_gated_edge_fence_validation(
        config=ContextGatedEdgeFenceValidationConfig(
            seed=2711,
            include_symmetries=False,
            foundation_train_repetitions=1,
            train_pool_size=4,
            fence_rehearsal_pool_size=2,
            eval_window_size=2,
            train_chunk_size=4,
            max_chunks_per_stage=1,
            mate1_regression_threshold=0.0,
            mate2_regression_threshold=0.0,
            max_generation_attempts=120_000,
            top_k_deep_score=2,
            max_samples=1,
            tg26c_main_artifact_path=str(tg26c),
            tg26i_reference_artifact_path=str(tg26i),
        )
    )
    output = result.write_json(tmp_path / "tg26m.json")
    payload = json.loads(output.read_text(encoding="utf-8"))

    assert payload["schema_version"] == "krk_autogrowth_tg26m_context_gated_edge_fence_validation.v0"
    assert payload["training_runway"]["uses_tg26l_context_gated_foundation"] is True
    assert payload["training_runway"]["direct_provider_override"] is False
    assert payload["training_runway"]["runtime_tablebase_or_dtm_move_source"] is False
    assert payload["local_recon_structure"]["mate2_handoff_mediated_by_context_gate_and_terminal_weights"] is True
    assert payload["foundation"]["source_checkpoint"] == "TG26l_context_gated_curriculum"
    assert payload["foundation"]["mate2_no_confirmed_gate_count"] == 0
    assert {stage["label"] for stage in payload["stages"]} == {"edge_trap", "fence_hold"}
    for stage in payload["stages"]:
        assert "stage_terminal_substrate" in stage
        assert stage["m4_consolidation_event_count"] == 0
    assert payload["decision"]["stage_competence_claim"] is False
    assert payload["decision"]["broad_random_krk_enabled"] is False
