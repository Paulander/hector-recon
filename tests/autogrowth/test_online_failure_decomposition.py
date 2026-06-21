from pathlib import Path

from recon_lite_chess.autogrowth import (
    OnlineFailureDecompositionConfig,
    TinyOnlineKRKEpisodeRunnerConfig,
    run_online_failure_decomposition,
)


def test_tg29b_smoke_reports_decomposition_no_cheat_fields(tmp_path: Path) -> None:
    result = run_online_failure_decomposition(
        config=OnlineFailureDecompositionConfig(
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
            reply_policies=("deterministic_worst_foundation_reply",),
        )
    )

    payload = result.to_dict()
    decision = payload["decision"]
    assert payload["checkpoint"] == "TG29b_online_failure_decomposition"
    assert decision["repair_applied"] is False
    assert decision["foundation_frozen"] is True
    assert decision["action_ranker_used_for_runtime"] is False
    assert decision["runtime_tablebase_or_dtm_move_source"] is False
    assert decision["direct_provider_override"] is False
    assert decision["stage_labels_learner_visible"] is False
    assert decision["episode_count"] == 1
    assert "failure_bucket_counts" in decision
    assert "transition_semantics" in decision
    assert "foundation_cache_equivalence" in payload
