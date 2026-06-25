from pathlib import Path

from recon_lite_chess.autogrowth import (
    CachedOnlineEpisodeScaleMatrixConfig,
    TinyOnlineKRKEpisodeRunnerConfig,
    run_cached_online_episode_scale_matrix,
)


def test_tg29p_smoke_cached_online_episode_matrix_without_shortcuts(tmp_path: Path) -> None:
    result = run_cached_online_episode_scale_matrix(
        config=CachedOnlineEpisodeScaleMatrixConfig(
            base=TinyOnlineKRKEpisodeRunnerConfig(
                episode_count=2,
                max_white_moves_per_episode=2,
                foundation_mate1_train_count=4,
                foundation_mate1_heldout_count=2,
                foundation_mate2_train_count=1,
                foundation_mate2_heldout_count=1,
                bridge_frontier_train_count=0,
                bridge_frontier_heldout_count=0,
                generic_edge_train_count=0,
                generic_edge_heldout_count=0,
                staged_train_count=0,
                staged_heldout_count=0,
                staged_regression_count=0,
                staged_near_miss_count=0,
                near_miss_heldout_count=0,
                max_ablation_positions=0,
                max_foundation_sanity_positions=1,
                max_foundation_ablation_positions=1,
                max_samples=4,
                max_episode_ablation_count=1,
                schedule_names=("tg29l_minimal_real_context",),
                progress_output=str(tmp_path / "progress.json"),
            ),
            start_counts={
                "known_repaired_starts": 2,
                "staged_pool_starts": 0,
                "frontier_near_starts": 0,
                "generic_edge_starts": 0,
                "near_miss_or_decoy_starts": 0,
            },
            horizons=(2,),
            black_reply_policies=("deterministic_worst_foundation_reply",),
            diagnostic_arm_start_limit=2,
            run_diagnostic_arms=False,
            run_representative_ablations=False,
            run_compact_regression=False,
        )
    )

    output = result.write_json(tmp_path / "tg29p.json")
    decision = result.decision
    assert output.exists()
    assert Path(result.config.base.progress_output).exists()
    assert result.start_sets["counts"]["known_repaired_starts"] == 2
    assert decision["checkpoint_pass"] is True
    assert decision["total_episode_count"] >= 2
    assert decision["foundation_frozen"] is True
    assert decision["foundation_m3_updates_during_eval"] == 0
    assert decision["foundation_m4_promotions_during_eval"] == 0
    assert decision["s1_cache_live_mismatch_count"] == 0
    assert decision["trajectory_cache_live_mismatch_count"] == 0
    assert decision["rook_blunder_count"] == 0
    assert decision["illegal_move_count"] == 0
    assert decision["stalemate_count"] == 0
    assert decision["s1_selected_one_reply_later_failed_count"] == 0
    assert decision["action_ranker_used_for_runtime"] is False
    assert decision["runtime_tablebase_or_dtm_move_source"] is False
    assert decision["direct_provider_override"] is False
    assert decision["stage_labels_learner_visible"] is False
    assert decision["s1_labels_learner_visible"] is False
