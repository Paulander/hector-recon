from pathlib import Path

from recon_lite_chess.autogrowth import HorizonLimitedContinuationRepairConfig, run_horizon_limited_continuation_repair


def test_tg29q_baseline_split_keeps_decoys_separate_without_shortcuts(tmp_path: Path) -> None:
    result = run_horizon_limited_continuation_repair(
        config=HorizonLimitedContinuationRepairConfig(
            run_real_context=False,
            run_candidate_audit=False,
            run_compact_regression=False,
            max_extended_failures=0,
            base=HorizonLimitedContinuationRepairConfig().base.__class__(
                progress_output=str(tmp_path / "progress.json"),
            ),
        )
    )

    output = result.write_json(tmp_path / "tg29q.json")
    decision = result.decision
    assert output.exists()
    assert Path(result.config.base.progress_output).exists()
    assert decision["checkpoint_pass"] is True
    assert decision["checkpoint_interpretation"] == "horizon_continuation_diagnostic_pass"
    assert decision["repair_applied"] is False
    assert decision["solvable_episode_count"] == 45
    assert decision["decoy_episode_count"] == 9
    assert decision["decoy_false_handoff_count"] == 0
    assert decision["decoy_correct_rejection_count"] == 9
    assert decision["rook_blunder_count"] == 0
    assert decision["illegal_move_count"] == 0
    assert decision["stalemate_count"] == 0
    assert decision["action_ranker_used_for_runtime"] is False
    assert decision["runtime_tablebase_or_dtm_move_source"] is False
    assert decision["direct_provider_override"] is False
    assert decision["stage_labels_learner_visible"] is False
    assert decision["s1_labels_learner_visible"] is False
