from pathlib import Path

from recon_lite_chess.autogrowth import (
    ContinuationCandidateEcologyMaterializationConfig,
    run_continuation_candidate_ecology_materialization,
)


def test_tg29t_over_spawns_candidate_ecology_without_runtime_shortcuts(tmp_path: Path) -> None:
    result = run_continuation_candidate_ecology_materialization(
        config=ContinuationCandidateEcologyMaterializationConfig(
            base=ContinuationCandidateEcologyMaterializationConfig().base.__class__(
                progress_output=str(tmp_path / "progress.json"),
            ),
            ecology_cache_path=str(tmp_path / "ecology.jsonl"),
            ecology_cache_index_path=str(tmp_path / "ecology_index.json"),
            ecology_cycle_count=8,
        )
    )

    output = result.write_json(tmp_path / "tg29t.json")
    decision = result.decision
    assert output.exists()
    assert Path(result.config.base.progress_output).exists()
    assert Path(result.config.ecology_cache_path).exists()
    assert Path(result.config.ecology_cache_index_path).exists()
    assert decision["checkpoint_pass"] is True
    assert decision["repair_applied"] is False
    assert decision["spawned_candidate_count"] == 81
    assert decision["safe_candidate_count"] == 75
    assert decision["materialized_continuation_candidate_count"] == 81
    assert decision["candidate_credit_event_count"] > 0
    assert decision["candidate_debt_event_count"] > 0
    assert decision["candidate_decay_event_count"] > 0
    assert decision["trainer_side_exploration_used"] is True
    assert decision["trainer_side_exploration_used_in_final_eval"] is False
    assert decision["continuation_labels_learner_visible"] is False
    assert decision["trainer_quality_tiers_learner_visible"] is False
    assert decision["action_ranker_used_for_runtime"] is False
    assert decision["runtime_tablebase_or_dtm_move_source"] is False
    assert decision["python_final_selector_used"] is False
    assert decision["direct_provider_override"] is False
