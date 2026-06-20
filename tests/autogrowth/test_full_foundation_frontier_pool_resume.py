from pathlib import Path

from recon_lite_chess.autogrowth import (
    FullFoundationFrontierPoolResumeConfig,
    run_full_foundation_frontier_pool_resume,
)


def _smoke_config(tmp_path: Path) -> FullFoundationFrontierPoolResumeConfig:
    return FullFoundationFrontierPoolResumeConfig(
        foundation_mate1_train_count=4,
        foundation_mate1_heldout_count=2,
        foundation_mate2_train_count=1,
        foundation_mate2_heldout_count=1,
        bridge_frontier_train_count=1,
        bridge_frontier_heldout_count=0,
        generic_edge_safety_regression_count=0,
        minimum_train_count=0,
        minimum_heldout_count=0,
        minimum_regression_count=0,
        basin_random_count=2,
        max_generation_attempts=250_000,
        max_pool_generation_seconds=0.01,
        max_cache_candidate_moves=3,
        max_ablation_positions=0,
        max_foundation_sanity_positions=1,
        max_foundation_ablation_positions=1,
        max_samples=4,
        replay_count=1,
        compact_pool_path=str(tmp_path / "missing_compact_pool.jsonl"),
        full_pool_path=str(tmp_path / "full_pool.jsonl"),
        full_pool_index_path=str(tmp_path / "full_pool_index.json"),
        progress_output=str(tmp_path / "progress.json"),
    )


def test_tg28f_smoke_writes_full_pool_resume_artifacts(tmp_path: Path) -> None:
    cfg = _smoke_config(tmp_path)

    result = run_full_foundation_frontier_pool_resume(config=cfg)
    payload = result.to_dict()
    decision = payload["decision"]

    assert payload["checkpoint"] == "TG28f_full_foundation_frontier_pool_resume"
    assert Path(cfg.full_pool_path).exists()
    assert Path(cfg.full_pool_index_path).exists()
    assert Path(cfg.progress_output).exists()
    assert payload["pool"]["pool_stats"]["full_pool_entry_count"] >= 0
    assert payload["pool"]["foundation_config_hash"]
    assert payload["pool"]["cache_config_hash"]
    assert payload["anchor_index"]["anchor_count"] >= 1
    assert decision["foundation_frozen"] is True
    assert decision["foundation_cache_used_as_memoized_graph_response"] is True
    assert decision["foundation_cache_used_as_provider"] is False
    assert decision["action_ranker_used_for_runtime"] is False
    assert decision["runtime_tablebase_or_dtm_move_source"] is False
    assert decision["direct_provider_override"] is False
    assert decision["bridge_labels_learner_visible"] is False
    assert "phase_timings" in decision
    assert "full_pool_generation_seconds" in decision["phase_timings"]

    first_lines = Path(cfg.full_pool_path).read_text(encoding="utf-8").splitlines()
    assert len(first_lines) == payload["pool"]["pool_stats"]["full_pool_entry_count"]

    resumed = run_full_foundation_frontier_pool_resume(config=cfg)
    resumed_payload = resumed.to_dict()
    assert resumed_payload["pool"]["pool_stats"]["loaded_existing_entries"] >= len(first_lines)
    assert len(Path(cfg.full_pool_path).read_text(encoding="utf-8").splitlines()) == len(first_lines)
