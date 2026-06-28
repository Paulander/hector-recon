from pathlib import Path

from recon_lite_chess.autogrowth import (
    RealCleanSlateFoundationConfig,
    run_real_clean_slate_krk_foundation,
)


def _cfg(tmp_path: Path) -> RealCleanSlateFoundationConfig:
    output_dir = tmp_path / "tg46b"
    return RealCleanSlateFoundationConfig(
        output_dir=str(output_dir),
        output_path=str(output_dir / "krk_tg46b_real_clean_slate_foundation.json"),
        progress_path=str(output_dir / "krk_tg46b_real_clean_slate_foundation_progress.json"),
        markdown_path=str(output_dir / "krk_tg46b_real_clean_slate_foundation.md"),
        mate1_train_trace_path=str(output_dir / "pools" / "mate1_train.jsonl.gz"),
        mate1_eval_trace_path=str(output_dir / "pools" / "mate1_eval.jsonl.gz"),
        mate2_train_trace_path=str(output_dir / "pools" / "mate2_train.jsonl.gz"),
        mate2_eval_trace_path=str(output_dir / "pools" / "mate2_eval.jsonl.gz"),
        failure_pool_path=str(output_dir / "pools" / "failure_pool.jsonl.gz"),
        graph_summary_path=str(output_dir / "pools" / "graph_summary.json"),
        seed=20260628,
        mate1_train_count=30,
        mate1_heldout_count=12,
        mate2_train_count=20,
        mate2_heldout_count=8,
        max_generation_attempts=100_000,
        max_trace_samples=3,
        fresh_graph=True,
    )


def test_tg46b_real_clean_slate_foundation_uses_real_graph_and_artifacts(tmp_path: Path) -> None:
    result = run_real_clean_slate_krk_foundation(config=_cfg(tmp_path))
    decision = result.decision

    required = {
        "checkpoint_pass",
        "checkpoint_interpretation",
        "synthetic_tg46_target_rate_paths_detected",
        "synthetic_stage_runner_used_in_result",
        "fresh_graph",
        "generated_krk_fens_used",
        "placeholder_fens_used",
        "real_legal_move_evaluation_used",
        "real_graph_training_used",
        "real_graph_evaluation_used",
        "real_graph_artifact_written",
        "real_failure_pool_used",
        "loaded_prior_tg_artifact_count",
        "mate1_heldout_accuracy",
        "mate2_heldout_conversion_rate",
        "m3_update_count",
        "runtime_tablebase_or_dtm_move_source",
        "action_ranker_used_for_runtime",
        "python_final_selector_used",
        "direct_provider_override",
        "learner_visible_stage_labels",
        "selected_next_action",
        "purity_boundary",
    }
    assert required <= set(decision)
    assert decision["synthetic_tg46_target_rate_paths_detected"] is True
    assert decision["synthetic_stage_runner_used_in_result"] is False
    assert decision["fresh_graph"] is True
    assert decision["generated_krk_fens_used"] is True
    assert decision["placeholder_fens_used"] is False
    assert decision["real_legal_move_evaluation_used"] is True
    assert decision["real_graph_training_used"] is True
    assert decision["real_graph_evaluation_used"] is True
    assert decision["loaded_prior_tg_artifact_count"] == 0
    assert decision["mate1_heldout_accuracy"] == 1.0
    assert decision["m3_update_count"] > 0
    assert decision["runtime_tablebase_or_dtm_move_source"] is False
    assert decision["action_ranker_used_for_runtime"] is False
    assert decision["python_final_selector_used"] is False
    assert decision["direct_provider_override"] is False
    assert decision["learner_visible_stage_labels"] is False

    assert Path(result.config.output_path).exists()
    assert Path(result.config.progress_path).exists()
    assert Path(result.config.failure_pool_path).exists()
    assert Path(result.config.graph_summary_path).exists()
