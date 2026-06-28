from pathlib import Path

from recon_lite_chess.autogrowth import (
    M4FoundationConsolidationConfig,
    run_m4_foundation_consolidation,
)


def _cfg(tmp_path: Path) -> M4FoundationConsolidationConfig:
    output_dir = tmp_path / "tg46d"
    return M4FoundationConsolidationConfig(
        output_dir=str(output_dir),
        output_path=str(output_dir / "krk_tg46d_m4_foundation_consolidation.json"),
        progress_path=str(output_dir / "krk_tg46d_m4_foundation_consolidation_progress.json"),
        markdown_path=str(output_dir / "krk_tg46d_m4_foundation_consolidation.md"),
        train_trace_path=str(output_dir / "pools" / "train.jsonl.gz"),
        eval_trace_path=str(output_dir / "pools" / "eval.jsonl.gz"),
        m4_audit_log_path=str(output_dir / "pools" / "m4_audit.jsonl.gz"),
        promotion_candidate_log_path=str(output_dir / "pools" / "promotion_candidates.jsonl.gz"),
        m4_only_eval_log_path=str(output_dir / "pools" / "m4_only_eval.jsonl.gz"),
        graph_summary_path=str(output_dir / "pools" / "graph_summary.json"),
        promoted_foundation_artifact_path=str(output_dir / "promoted_foundation.json"),
        seed=20260628,
        mate1_train_count=30,
        mate1_regression_count=12,
        mate2_train_count=20,
        mate2_heldout_count=8,
        mate2_regression_count=8,
        max_generation_attempts=100_000,
        fresh_graph=True,
    )


def test_tg46d_m4_consolidation_promotes_graph_mediated_bundle(tmp_path: Path) -> None:
    result = run_m4_foundation_consolidation(config=_cfg(tmp_path))
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
        "m4_true_promotion_count",
        "m4_promoted_terminal_count",
        "m4_promoted_bundle_count",
        "m4_promoted_quorum_count",
        "best_promotion_unit_type",
        "mate1_regression_accuracy_M4_only",
        "mate2_heldout_conversion_M4_only",
        "mature_materialized_count",
        "ablation_results",
        "runtime_tablebase_or_dtm_move_source",
        "action_ranker_used_for_runtime",
        "python_final_selector_used",
        "direct_provider_override",
        "learner_visible_stage_labels",
        "checkpoint_specific_move_rule_count",
        "checkpoint_specific_fen_rule_count",
    }
    assert required <= set(decision)
    assert decision["selected_repair_arm"] == "evidence_bundle_promotion"
    assert decision["repair_applied"] is True
    assert decision["fresh_graph_lineage_preserved"] is True
    assert decision["prior_tg_artifacts_loaded"] == 0
    assert decision["synthetic_stage_runner_used_in_result"] is False
    assert decision["m4_true_promotion_count"] > 0
    assert decision["m4_promoted_terminal_count"] > 0
    assert decision["m4_promoted_bundle_count"] == 1
    assert decision["m4_promoted_quorum_count"] == 1
    assert decision["best_promotion_unit_type"] == "evidence_bundle_quorum"
    assert decision["mate1_regression_accuracy_M4_only"] == 1.0
    assert decision["mate2_heldout_conversion_M4_only"] > 0.0
    assert decision["ablation_results"]["m4_ablation_causal"] is True
    assert decision["runtime_tablebase_or_dtm_move_source"] is False
    assert decision["action_ranker_used_for_runtime"] is False
    assert decision["python_final_selector_used"] is False
    assert decision["direct_provider_override"] is False
    assert decision["learner_visible_stage_labels"] is False
    assert decision["checkpoint_specific_move_rule_count"] == 0
    assert decision["checkpoint_specific_fen_rule_count"] == 0

    assert Path(result.config.output_path).exists()
    assert Path(result.config.progress_path).exists()
    assert Path(result.config.m4_audit_log_path).exists()
    assert Path(result.config.promotion_candidate_log_path).exists()
    assert Path(result.config.m4_only_eval_log_path).exists()
    assert Path(result.config.graph_summary_path).exists()
    assert Path(result.config.promoted_foundation_artifact_path).exists()
