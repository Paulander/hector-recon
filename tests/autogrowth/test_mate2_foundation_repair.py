from pathlib import Path

from recon_lite_chess.autogrowth import (
    Mate2FoundationRepairConfig,
    run_mate2_foundation_repair,
)


def _cfg(tmp_path: Path) -> Mate2FoundationRepairConfig:
    output_dir = tmp_path / "tg46c"
    return Mate2FoundationRepairConfig(
        output_dir=str(output_dir),
        output_path=str(output_dir / "krk_tg46c_real_mate2_repair.json"),
        progress_path=str(output_dir / "krk_tg46c_real_mate2_repair_progress.json"),
        markdown_path=str(output_dir / "krk_tg46c_real_mate2_repair.md"),
        train_trace_path=str(output_dir / "pools" / "train.jsonl.gz"),
        eval_trace_path=str(output_dir / "pools" / "eval.jsonl.gz"),
        failure_pool_path=str(output_dir / "pools" / "failure_pool.jsonl.gz"),
        repair_arm_log_path=str(output_dir / "pools" / "repair_arms.jsonl.gz"),
        m4_audit_log_path=str(output_dir / "pools" / "m4_audit.jsonl.gz"),
        graph_summary_path=str(output_dir / "pools" / "graph_summary.json"),
        seed=20260628,
        mate1_train_count=30,
        mate1_regression_count=12,
        mate2_train_count=20,
        mate2_heldout_count=8,
        mate2_regression_count=8,
        max_generation_attempts=100_000,
        max_trace_samples=4,
        fresh_graph=True,
    )


def test_tg46c_mate2_repair_preserves_clean_lineage_and_writes_artifacts(tmp_path: Path) -> None:
    result = run_mate2_foundation_repair(config=_cfg(tmp_path))
    decision = result.decision

    required = {
        "checkpoint_pass",
        "checkpoint_interpretation",
        "selected_repair_arm",
        "repair_applied",
        "fresh_graph_lineage_preserved",
        "prior_tg_artifacts_loaded",
        "synthetic_stage_runner_used_in_result",
        "real_fen_generation_used",
        "real_graph_training_used",
        "real_graph_evaluation_used",
        "mate1_regression_accuracy",
        "mate2_heldout_conversion_rate",
        "mate2_all_reply_conversion_rate",
        "m3_update_count",
        "m4_true_promotion_count",
        "runtime_tablebase_or_dtm_move_source",
        "action_ranker_used_for_runtime",
        "python_final_selector_used",
        "direct_provider_override",
        "learner_visible_stage_labels",
        "checkpoint_specific_move_rule_count",
        "checkpoint_specific_fen_rule_count",
    }
    assert required <= set(decision)
    assert decision["selected_repair_arm"] == "contrastive_pairwise_mate2_credit"
    assert decision["repair_applied"] is True
    assert decision["fresh_graph_lineage_preserved"] is True
    assert decision["prior_tg_artifacts_loaded"] == 0
    assert decision["synthetic_stage_runner_used_in_result"] is False
    assert decision["real_fen_generation_used"] is True
    assert decision["real_graph_training_used"] is True
    assert decision["real_graph_evaluation_used"] is True
    assert decision["mate1_regression_accuracy"] == 1.0
    assert decision["mate2_heldout_conversion_rate"] > decision["tg46b_mate2_conversion_rate"]
    assert decision["m3_update_count"] > 0
    assert decision["runtime_tablebase_or_dtm_move_source"] is False
    assert decision["action_ranker_used_for_runtime"] is False
    assert decision["python_final_selector_used"] is False
    assert decision["direct_provider_override"] is False
    assert decision["learner_visible_stage_labels"] is False
    assert decision["checkpoint_specific_move_rule_count"] == 0
    assert decision["checkpoint_specific_fen_rule_count"] == 0

    assert Path(result.config.output_path).exists()
    assert Path(result.config.progress_path).exists()
    assert Path(result.config.train_trace_path).exists()
    assert Path(result.config.eval_trace_path).exists()
    assert Path(result.config.failure_pool_path).exists()
    assert Path(result.config.repair_arm_log_path).exists()
    assert Path(result.config.m4_audit_log_path).exists()
    assert Path(result.config.graph_summary_path).exists()
