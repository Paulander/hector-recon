from pathlib import Path

from recon_lite_chess.autogrowth import (
    MatureCandidatePostSelectionSufficiencyAuditConfig,
    run_mature_candidate_post_selection_sufficiency_audit,
)


def test_tg29v_audits_selected_mature_candidates_without_shortcut_repair(tmp_path: Path) -> None:
    result = run_mature_candidate_post_selection_sufficiency_audit(
        config=MatureCandidatePostSelectionSufficiencyAuditConfig(
            base=MatureCandidatePostSelectionSufficiencyAuditConfig().base.__class__(
                progress_output=str(tmp_path / "progress.json"),
            ),
            followup_cache_path=str(tmp_path / "followup.jsonl"),
            followup_cache_index_path=str(tmp_path / "followup_index.json"),
        )
    )

    output = result.write_json(tmp_path / "tg29v.json")
    decision = result.decision
    assert output.exists()
    assert Path(result.config.base.progress_output).exists()
    assert Path(result.config.followup_cache_path).exists()
    assert Path(result.config.followup_cache_index_path).exists()
    assert decision["checkpoint_pass"] is True
    assert decision["repair_applied"] is False
    assert decision["selected_mature_candidate_count"] == 2
    assert decision["reply_policy_fragile_maturity_count"] > 0
    assert decision["followup_candidate_exists_count"] > 0
    assert decision["targeted_episode_success_count"] == 0
    assert decision["decoy_false_handoff_count"] == 0
    assert decision["depth_labels_learner_visible"] is False
    assert decision["quality_tier_labels_learner_visible"] is False
    assert decision["continuation_labels_learner_visible"] is False
    assert decision["action_ranker_used_for_runtime"] is False
    assert decision["runtime_tablebase_or_dtm_move_source"] is False
    assert decision["python_final_selector_used"] is False
    assert decision["direct_provider_override"] is False
