from pathlib import Path

from recon_lite_chess.autogrowth import (
    StableTrajectoryCacheSelectionMicroprobeConfig,
    TinyOnlineKRKEpisodeRunnerConfig,
    run_stable_trajectory_cache_selection_microprobe,
)


def test_tg29i_smoke_stable_cache_and_no_cheat_fields(tmp_path: Path) -> None:
    result = run_stable_trajectory_cache_selection_microprobe(
        config=StableTrajectoryCacheSelectionMicroprobeConfig(
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
            trajectory_cache_path=str(tmp_path / "stable_cache.jsonl"),
            trajectory_cache_index_path=str(tmp_path / "stable_cache_index.json"),
        )
    )

    output = result.write_json(tmp_path / "tg29i.json")
    payload = result.to_dict()
    decision = payload["decision"]
    assert output.exists()
    assert Path(decision["trajectory_cache_path"]).exists()
    assert Path(decision["trajectory_cache_index_path"]).exists()
    assert payload["checkpoint"] == "TG29i_stable_trajectory_cache_selection_microprobe"
    assert decision["foundation_frozen"] is True
    assert decision["action_ranker_used_for_runtime"] is False
    assert decision["runtime_tablebase_or_dtm_move_source"] is False
    assert decision["direct_provider_override"] is False
    assert decision["trajectory_labels_learner_visible"] is False
    assert decision["stable_cache_key_mismatch_count"] == 0
    assert decision["live_rollout_count_second_pass"] == 0
    assert decision["known_trajectory_candidate_count"] == 2
