from pathlib import Path

from recon_lite_chess.autogrowth import (
    CachedTrajectorySelectionRepairConfig,
    TinyOnlineKRKEpisodeRunnerConfig,
    run_cached_trajectory_selection_repair,
)


def test_tg29h_smoke_writes_cache_and_no_cheat_fields(tmp_path: Path) -> None:
    result = run_cached_trajectory_selection_repair(
        config=CachedTrajectorySelectionRepairConfig(
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
            trajectory_cache_path=str(tmp_path / "cache.jsonl"),
            trajectory_cache_index_path=str(tmp_path / "cache_index.json"),
            max_failure_starts=1,
            max_safe_candidates_per_start=1,
            max_repair_cache_candidate_moves=3,
            max_reply_envelope_replies_per_candidate=1,
            seed_cache_from_tg29g=True,
            run_repair_episodes=False,
        )
    )

    output = result.write_json(tmp_path / "tg29h.json")
    payload = result.to_dict()
    decision = payload["decision"]
    assert output.exists()
    assert Path(decision["trajectory_cache_path"]).exists()
    assert Path(decision["trajectory_cache_index_path"]).exists()
    assert payload["checkpoint"] == "TG29h_cached_trajectory_selection_repair"
    assert decision["foundation_frozen"] is True
    assert decision["action_ranker_used_for_runtime"] is False
    assert decision["runtime_tablebase_or_dtm_move_source"] is False
    assert decision["direct_provider_override"] is False
    assert decision["trajectory_labels_learner_visible"] is False
    assert decision["audited_failure_start_count"] >= 1
    assert decision["audited_candidate_count"] >= 1
    assert decision["trajectory_cache_entry_count"] >= 1
