from pathlib import Path

from recon_lite_chess.autogrowth import (
    PersistedFoundationBackedFrontierPoolConfig,
    run_persisted_foundation_backed_frontier_pool,
)


def test_tg28e_smoke_writes_resumable_pool_and_decision_fields(tmp_path: Path) -> None:
    pool_path = tmp_path / "pool.jsonl"
    index_path = tmp_path / "pool_index.json"
    progress_path = tmp_path / "progress.json"

    result = run_persisted_foundation_backed_frontier_pool(
        config=PersistedFoundationBackedFrontierPoolConfig(
            foundation_mate1_train_count=4,
            foundation_mate1_heldout_count=2,
            foundation_mate2_train_count=1,
            foundation_mate2_heldout_count=1,
            bridge_frontier_train_count=2,
            bridge_frontier_heldout_count=2,
            generic_edge_safety_regression_count=1,
            basin_random_count=2,
            max_generation_attempts=20_000,
            max_cache_candidate_moves=3,
            max_ablation_positions=0,
            max_foundation_sanity_positions=1,
            max_foundation_ablation_positions=1,
            max_samples=4,
            replay_count=1,
            pool_path=str(pool_path),
            pool_index_path=str(index_path),
            progress_output=str(progress_path),
        )
    )

    payload = result.to_dict()
    decision = payload["decision"]
    assert payload["checkpoint"] == "TG28e_persisted_foundation_backed_frontier_pool"
    assert pool_path.exists()
    assert index_path.exists()
    assert progress_path.exists()
    assert decision["pool_entry_count"] >= 1
    assert decision["foundation_frozen"] is True
    assert decision["foundation_cache_used_as_memoized_graph_response"] is True
    assert decision["foundation_cache_used_as_provider"] is False
    assert decision["action_ranker_used_for_runtime"] is False
    assert decision["runtime_tablebase_or_dtm_move_source"] is False
    assert decision["direct_provider_override"] is False
    assert decision["bridge_labels_learner_visible"] is False
    assert "phase_timings" in decision
    assert "pool_generation_seconds" in decision["phase_timings"]
    assert payload["pool"]["deterministic_and_resumable"] is True

    first_lines = pool_path.read_text(encoding="utf-8").splitlines()
    assert len(first_lines) == decision["pool_entry_count"]

    resumed = run_persisted_foundation_backed_frontier_pool(
        config=PersistedFoundationBackedFrontierPoolConfig(
            foundation_mate1_train_count=4,
            foundation_mate1_heldout_count=2,
            foundation_mate2_train_count=1,
            foundation_mate2_heldout_count=1,
            bridge_frontier_train_count=2,
            bridge_frontier_heldout_count=2,
            generic_edge_safety_regression_count=1,
            basin_random_count=2,
            max_generation_attempts=20_000,
            max_cache_candidate_moves=3,
            max_ablation_positions=0,
            max_foundation_sanity_positions=1,
            max_foundation_ablation_positions=1,
            max_samples=4,
            replay_count=1,
            pool_path=str(pool_path),
            pool_index_path=str(index_path),
            progress_output=str(progress_path),
        )
    )
    resumed_payload = resumed.to_dict()
    assert resumed_payload["pool"]["pool_stats"]["loaded_existing_entries"] >= decision["pool_entry_count"]
    assert len(pool_path.read_text(encoding="utf-8").splitlines()) == len(first_lines)
