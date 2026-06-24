from pathlib import Path

from recon_lite_chess.autogrowth import (
    S1FullReplyCacheOnlineRecheckConfig,
    TinyOnlineKRKEpisodeRunnerConfig,
    run_s1_full_reply_cache_online_recheck,
)


def test_tg29o_smoke_persists_s1_cache_and_reuses_without_shortcuts(tmp_path: Path) -> None:
    result = run_s1_full_reply_cache_online_recheck(
        config=S1FullReplyCacheOnlineRecheckConfig(
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
            s1_cache_path=str(tmp_path / "s1_cache.jsonl"),
            s1_cache_index_path=str(tmp_path / "s1_cache_index.json"),
            run_max3_diagnostic=False,
            run_slightly_larger_online_set=False,
        )
    )

    output = result.write_json(tmp_path / "tg29o.json")
    decision = result.decision
    assert output.exists()
    assert Path(result.config.s1_cache_path).exists()
    assert Path(result.config.s1_cache_index_path).exists()
    assert decision["checkpoint_pass"] is True
    assert decision["s1_cache_entry_count"] >= 1
    assert decision["s1_cache_hit_rate_first_pass"] == 0.0
    assert decision["s1_cache_hit_rate_second_pass"] == 1.0
    assert decision["s1_live_rollout_count_second_pass"] == 0
    assert decision["s1_cache_live_mismatch_count"] == 0
    assert decision["s1_selected_all_reply_foundation_count"] >= 1
    assert decision["s1_selected_one_reply_later_failed_count"] == 0
    assert decision["max2_episode_success_count"] == decision["max2_episode_count"]
    assert decision["s1_full_reply_repair_ablation_causal"] is True
    assert decision["action_ranker_used_for_runtime"] is False
    assert decision["runtime_tablebase_or_dtm_move_source"] is False
    assert decision["direct_provider_override"] is False
    assert decision["s1_labels_learner_visible"] is False
