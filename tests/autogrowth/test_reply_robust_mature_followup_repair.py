from pathlib import Path

from recon_lite_chess.autogrowth import ReplyRobustMatureFollowupRepairConfig, run_reply_robust_mature_followup_repair


def test_tg29w_materializes_followup_evidence_without_shortcut_repair(tmp_path: Path) -> None:
    result = run_reply_robust_mature_followup_repair(
        config=ReplyRobustMatureFollowupRepairConfig(
            base=ReplyRobustMatureFollowupRepairConfig().base.__class__(
                progress_output=str(tmp_path / "progress.json"),
            ),
            runtime_cache_path=str(tmp_path / "runtime.jsonl"),
            runtime_cache_index_path=str(tmp_path / "runtime_index.json"),
        )
    )

    output = result.write_json(tmp_path / "tg29w.json")
    decision = result.decision
    assert output.exists()
    assert Path(result.config.base.progress_output).exists()
    assert Path(result.config.runtime_cache_path).exists()
    assert Path(result.config.runtime_cache_index_path).exists()
    assert decision["checkpoint_pass"] is True
    assert decision["repair_applied"] is False
    assert decision["selected_mature_candidate_count"] == 2
    assert decision["useful_with_followup_count"] == 1
    assert decision["foundation_basin_missed_count"] == 1
    assert decision["followup_ecology_materialized_count"] == 2
    assert decision["followup_candidate_success_count"] == 1
    assert decision["targeted_episode_success_count"] == 0
    assert decision["decoy_false_handoff_count"] == 0
    assert decision["reply_policy_labels_learner_visible"] is False
    assert decision["depth_labels_learner_visible"] is False
    assert decision["quality_tier_labels_learner_visible"] is False
    assert decision["action_ranker_used_for_runtime"] is False
    assert decision["runtime_tablebase_or_dtm_move_source"] is False
    assert decision["python_final_selector_used"] is False
    assert decision["direct_provider_override"] is False
