from pathlib import Path

from recon_lite_chess.autogrowth import (
    ReplyRobustProgressPoolConfig,
    TinyOnlineKRKEpisodeRunnerConfig,
    run_reply_robust_progress_pool,
)


def test_tg29e_smoke_writes_pool_and_no_cheat_fields(tmp_path: Path) -> None:
    result = run_reply_robust_progress_pool(
        config=ReplyRobustProgressPoolConfig(
            base=TinyOnlineKRKEpisodeRunnerConfig(
                episode_count=1,
                max_white_moves_per_episode=1,
                foundation_mate1_train_count=4,
                foundation_mate1_heldout_count=2,
                foundation_mate2_train_count=1,
                foundation_mate2_heldout_count=1,
                bridge_frontier_train_count=1,
                bridge_frontier_heldout_count=1,
                generic_edge_train_count=1,
                generic_edge_heldout_count=1,
                staged_train_count=0,
                staged_heldout_count=0,
                staged_regression_count=0,
                staged_near_miss_count=0,
                near_miss_heldout_count=0,
                max_ablation_positions=0,
                max_foundation_sanity_positions=1,
                max_foundation_ablation_positions=1,
                max_samples=4,
                max_episode_ablation_count=0,
                schedule_names=("tg28h_mixed_balanced_baseline",),
                progress_output=str(tmp_path / "progress.json"),
            ),
            pool_path=str(tmp_path / "pool.jsonl"),
            pool_index_path=str(tmp_path / "pool_index.json"),
            reply_policies=("deterministic_worst_foundation_reply",),
            comparison_reply_policies=(),
            max_repair_cache_candidate_moves=3,
            progress_positive_train_target=1,
            progress_positive_heldout_target=1,
            low_progress_negative_target=1,
            near_miss_target=1,
            regression_target=1,
            min_progress_positive_train_count=1,
            min_progress_positive_heldout_count=0,
            min_low_progress_negative_count=0,
            min_near_miss_count=0,
            min_regression_count=0,
            max_forward_filter_starts=2,
            max_audit_low_progress_episodes=1,
            max_audit_turns_per_episode=1,
            training_arms=(
                "combined_reply_robust_baseline",
                "combined_reply_robust_plus_progress_positive_replay",
            ),
        )
    )

    payload = result.to_dict()
    decision = payload["decision"]
    assert payload["checkpoint"] == "TG29e_reply_robust_progress_positive_pool"
    assert Path(payload["pool_index"]["progress_pool_path"]).exists()
    assert Path(payload["pool_index"]["progress_pool_index_path"]).exists()
    assert decision["foundation_frozen"] is True
    assert decision["action_ranker_used_for_runtime"] is False
    assert decision["runtime_tablebase_or_dtm_move_source"] is False
    assert decision["direct_provider_override"] is False
    assert decision["stage_labels_learner_visible"] is False
    assert decision["episode_count"] == 1
    assert decision["audited_candidate_count"] >= 0
