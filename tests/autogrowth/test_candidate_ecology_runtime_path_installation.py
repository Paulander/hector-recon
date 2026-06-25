from pathlib import Path

from recon_lite_chess.autogrowth import (
    CandidateEcologyRuntimePathInstallationConfig,
    run_candidate_ecology_runtime_path_installation,
)


def test_tg29u_installs_ecology_runtime_path_without_shortcuts(tmp_path: Path) -> None:
    result = run_candidate_ecology_runtime_path_installation(
        config=CandidateEcologyRuntimePathInstallationConfig(
            base=CandidateEcologyRuntimePathInstallationConfig().base.__class__(
                progress_output=str(tmp_path / "progress.json"),
            ),
            runtime_cache_path=str(tmp_path / "runtime.jsonl"),
            runtime_cache_index_path=str(tmp_path / "runtime_index.json"),
        )
    )

    output = result.write_json(tmp_path / "tg29u.json")
    decision = result.decision
    assert output.exists()
    assert Path(result.config.base.progress_output).exists()
    assert Path(result.config.runtime_cache_path).exists()
    assert Path(result.config.runtime_cache_index_path).exists()
    assert decision["checkpoint_pass"] is True
    assert decision["ecology_runtime_path_installed"] is True
    assert decision["repair_applied"] is False
    assert decision["mature_candidate_count"] == 3
    assert decision["mature_candidate_selected_after_count"] > decision["mature_candidate_selected_before_count"]
    assert decision["mature_candidate_selected_count"] == decision["mature_candidate_selected_after_count"]
    assert decision["decaying_candidate_selected_count"] == 0
    assert decision["pruned_candidate_selected_count"] == 0
    assert decision["decoy_false_handoff_count"] == 0
    assert decision["quality_tier_labels_learner_visible"] is False
    assert decision["continuation_labels_learner_visible"] is False
    assert decision["action_ranker_used_for_runtime"] is False
    assert decision["runtime_tablebase_or_dtm_move_source"] is False
    assert decision["python_final_selector_used"] is False
    assert decision["direct_provider_override"] is False
