from pathlib import Path

from recon_lite_chess.autogrowth import (
    PersistedStagedPredecessorPoolConfig,
    run_persisted_staged_predecessor_pool,
)


def test_tg28j_smoke_reports_pool_and_purity_fields(tmp_path: Path) -> None:
    result = run_persisted_staged_predecessor_pool(
        config=PersistedStagedPredecessorPoolConfig(
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
            max_staged_source_positions=1,
            max_staged_first_move_candidates=1,
            max_cache_candidate_moves=2,
            max_ablation_positions=0,
            max_foundation_sanity_positions=1,
            max_foundation_ablation_positions=1,
            max_samples=4,
            schedule_names=("tg28h_mixed_balanced_baseline",),
            staged_pool_path=str(tmp_path / "pool.jsonl"),
            staged_pool_index_path=str(tmp_path / "pool_index.json"),
            progress_output=str(tmp_path / "progress.json"),
        )
    )

    payload = result.to_dict()
    decision = payload["decision"]
    assert payload["checkpoint"] == "TG28j_persisted_staged_predecessor_pool"
    assert Path(tmp_path / "pool_index.json").exists()
    assert Path(tmp_path / "progress.json").exists()
    assert decision["foundation_frozen"] is True
    assert decision["action_ranker_used_for_runtime"] is False
    assert decision["runtime_tablebase_or_dtm_move_source"] is False
    assert decision["direct_provider_override"] is False
    assert decision["stage_labels_learner_visible"] is False
    assert decision["staged_labels_learner_visible"] is False
    assert decision["staged_pool_path"] == str(tmp_path / "pool.jsonl")
    assert decision["staged_pool_index_path"] == str(tmp_path / "pool_index.json")
    assert "staged_pool_entry_count" in decision
    assert "tg28h_mixed_balanced_baseline" in payload["schedule_comparison"]
