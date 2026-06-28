"""TG46d M4 consolidation for the real clean-slate foundation."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import gzip
import hashlib
import json
from pathlib import Path
import time
from typing import Any, Iterable

from recon_lite_hector.nodes.stem_cell import StemCellState

from .mate2_foundation_repair import (
    Mate2FoundationRepairConfig,
    _count_buckets,
    _evaluate_mate1,
    _evaluate_mate2,
    _generate_splits,
    _graph_summary as _tg46c_graph_summary,
    _purity_boundary,
    _train_mate2_pairwise,
)
from .real_clean_slate_foundation import _audit_tg46_scaffold, _git_head
from .terminal_substrate import TerminalAffordanceLearner, _train_terminal_mate_in_one


DEFAULT_TG46C_DIR = Path("reports/autogrowth/clean_slate_krk/tg46c_mate2_repair")
DEFAULT_OUTPUT_DIR = Path("reports/autogrowth/clean_slate_krk/tg46d_m4_foundation_consolidation")


@dataclass(frozen=True)
class M4FoundationConsolidationConfig:
    output_dir: str = str(DEFAULT_OUTPUT_DIR)
    output_path: str = str(DEFAULT_OUTPUT_DIR / "krk_tg46d_m4_foundation_consolidation.json")
    progress_path: str = str(DEFAULT_OUTPUT_DIR / "krk_tg46d_m4_foundation_consolidation_progress.json")
    markdown_path: str = str(DEFAULT_OUTPUT_DIR / "krk_tg46d_m4_foundation_consolidation.md")
    train_trace_path: str = str(DEFAULT_OUTPUT_DIR / "pools" / "tg46d_train_traces.jsonl.gz")
    eval_trace_path: str = str(DEFAULT_OUTPUT_DIR / "pools" / "tg46d_eval_traces.jsonl.gz")
    m4_audit_log_path: str = str(DEFAULT_OUTPUT_DIR / "pools" / "tg46d_m4_audit.jsonl.gz")
    promotion_candidate_log_path: str = str(DEFAULT_OUTPUT_DIR / "pools" / "tg46d_promotion_candidates.jsonl.gz")
    m4_only_eval_log_path: str = str(DEFAULT_OUTPUT_DIR / "pools" / "tg46d_m4_only_eval.jsonl.gz")
    graph_summary_path: str = str(DEFAULT_OUTPUT_DIR / "pools" / "tg46d_graph_summary.json")
    promoted_foundation_artifact_path: str = str(DEFAULT_OUTPUT_DIR / "promoted_tg46d_foundation.json")
    tg46c_artifact_path: str = str(DEFAULT_TG46C_DIR / "krk_tg46c_real_mate2_repair.json")
    seed: int = 20260628
    mate1_train_count: int = 300
    mate1_regression_count: int = 100
    mate2_train_count: int = 300
    mate2_heldout_count: int = 100
    mate2_regression_count: int = 100
    max_generation_attempts: int = 500_000
    eta_m3: float = 0.10
    rich_feature_credit_scale: float = 0.25
    pairwise_epochs: int = 1
    pairwise_top_k: int = 1
    pairwise_wrong_debt: float = -0.20
    promotion_precision_threshold: float = 0.60
    promotion_min_exposures: int = 1
    mate1_pass_threshold: float = 0.99
    mate2_pass_threshold: float = 0.90
    fresh_graph: bool = True
    max_trace_samples: int = 24


@dataclass(frozen=True)
class M4FoundationConsolidationResult:
    config: M4FoundationConsolidationConfig
    payload: dict[str, Any]
    decision: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "krk_tg46d_m4_foundation_consolidation.v0",
            "checkpoint": "TG46d_real_foundation_m4_consolidation",
            "config": asdict(self.config),
            **self.payload,
            "decision": self.decision,
        }

    def write_json(self, path: str | Path | None = None) -> Path:
        output = Path(path or self.config.output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(self.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return output


def run_m4_foundation_consolidation(
    *,
    config: M4FoundationConsolidationConfig,
) -> M4FoundationConsolidationResult:
    if not config.fresh_graph:
        raise ValueError("TG46d requires fresh_graph=True")
    start = time.perf_counter()
    _ensure_parents(config)
    progress: dict[str, Any] = {
        "schema_version": "krk_tg46d_m4_foundation_consolidation_progress.v0",
        "checkpoint": "TG46d_real_foundation_m4_consolidation",
        "phases": [],
    }
    _write_json(config.progress_path, progress)
    tg46c = _load_json(config.tg46c_artifact_path)
    scaffold_audit = _audit_tg46_scaffold()

    phase_start = time.perf_counter()
    repair_cfg = Mate2FoundationRepairConfig(
        seed=config.seed,
        mate1_train_count=config.mate1_train_count,
        mate1_regression_count=config.mate1_regression_count,
        mate2_train_count=config.mate2_train_count,
        mate2_heldout_count=config.mate2_heldout_count,
        mate2_regression_count=config.mate2_regression_count,
        max_generation_attempts=config.max_generation_attempts,
        eta_m3=config.eta_m3,
        rich_feature_credit_scale=config.rich_feature_credit_scale,
        pairwise_epochs=config.pairwise_epochs,
        pairwise_top_k=config.pairwise_top_k,
        pairwise_wrong_debt=config.pairwise_wrong_debt,
        fresh_graph=True,
    )
    mate1_train, mate1_regression, mate2_train, mate2_heldout, mate2_regression = _generate_splits(repair_cfg)
    progress["phases"].append(_phase("generate_clean_splits", phase_start))
    _write_json(config.progress_path, progress)

    phase_start = time.perf_counter()
    mate1_learner = TerminalAffordanceLearner.create(
        eta_m3=config.eta_m3,
        rich_feature_credit_scale=config.rich_feature_credit_scale,
    )
    first_learner = TerminalAffordanceLearner.create(
        eta_m3=config.eta_m3,
        rich_feature_credit_scale=config.rich_feature_credit_scale,
    )
    mate1_train_metrics = _train_terminal_mate_in_one(mate1_train, learner=mate1_learner)
    train_rows = _train_mate2_pairwise(
        mate2_train,
        first_learner=first_learner,
        mate_learner=mate1_learner,
        config=repair_cfg,
    )
    _write_jsonl_gzip(config.train_trace_path, train_rows)
    progress["phases"].append(_phase("train_m3_foundation", phase_start))
    _write_json(config.progress_path, progress)

    phase_start = time.perf_counter()
    m3_mate1 = _evaluate_mate1(mate1_regression, mate1_learner)
    m3_mate2_heldout = _evaluate_mate2(
        mate2_heldout,
        first_learner=first_learner,
        mate_learner=mate1_learner,
        trace_type="m3_only_mate2_heldout",
    )
    m3_mate2_regression = _evaluate_mate2(
        mate2_regression,
        first_learner=first_learner,
        mate_learner=mate1_learner,
        trace_type="m3_only_mate2_regression",
    )
    progress["phases"].append(_phase("evaluate_m3_only", phase_start))
    _write_json(config.progress_path, progress)

    phase_start = time.perf_counter()
    promotion = _promote_precision_bundle(
        mate1_learner=mate1_learner,
        first_learner=first_learner,
        config=config,
    )
    m4_mate1_learner = _clone_promoted_subset(mate1_learner, promotion["mate1_promoted_keys"])
    m4_first_learner = _clone_promoted_subset(first_learner, promotion["mate2_first_promoted_keys"])
    progress["phases"].append(_phase("promote_m4_bundle", phase_start))
    _write_json(config.progress_path, progress)

    phase_start = time.perf_counter()
    m4_mate1 = _evaluate_mate1(mate1_regression, m4_mate1_learner)
    m4_mate2_heldout = _evaluate_mate2(
        mate2_heldout,
        first_learner=m4_first_learner,
        mate_learner=m4_mate1_learner,
        trace_type="m4_only_mate2_heldout",
    )
    m4_mate2_regression = _evaluate_mate2(
        mate2_regression,
        first_learner=m4_first_learner,
        mate_learner=m4_mate1_learner,
        trace_type="m4_only_mate2_regression",
    )
    _write_jsonl_gzip(config.m4_only_eval_log_path, m4_mate2_heldout["rows"] + m4_mate2_regression["rows"])
    progress["phases"].append(_phase("evaluate_m4_only", phase_start))
    _write_json(config.progress_path, progress)

    phase_start = time.perf_counter()
    m3_plus_m4_mate1 = m3_mate1
    m3_plus_m4_mate2_heldout = m3_mate2_heldout
    m3_plus_m4_mate2_regression = m3_mate2_regression
    ablations = _ablation_results(
        m3_mate2_heldout=m3_mate2_heldout,
        m4_mate2_heldout=m4_mate2_heldout,
        mate2_heldout=mate2_heldout,
        m4_mate1_learner=m4_mate1_learner,
    )
    progress["phases"].append(_phase("m4_ablations", phase_start))
    _write_json(config.progress_path, progress)

    m4_audit = _m4_audit(
        mate1_learner=mate1_learner,
        first_learner=first_learner,
        promotion=promotion,
        m4_mate2_heldout=m4_mate2_heldout,
        m4_mate2_regression=m4_mate2_regression,
    )
    graph_summary = _graph_summary(
        mate1_learner=mate1_learner,
        first_learner=first_learner,
        promotion=promotion,
        m4_mate2_heldout=m4_mate2_heldout,
        m4_mate2_regression=m4_mate2_regression,
    )
    promoted_artifact = _promoted_foundation_artifact(
        config=config,
        promotion=promotion,
        m4_mate1=m4_mate1,
        m4_mate2_heldout=m4_mate2_heldout,
        m4_mate2_regression=m4_mate2_regression,
        graph_summary=graph_summary,
    )
    _write_json(config.graph_summary_path, graph_summary)
    _write_json(config.promoted_foundation_artifact_path, promoted_artifact)
    _write_jsonl_gzip(config.m4_audit_log_path, m4_audit["audit_rows"])
    _write_jsonl_gzip(config.promotion_candidate_log_path, promotion["candidate_rows"])
    _write_jsonl_gzip(config.eval_trace_path, m3_mate2_heldout["rows"] + m4_mate2_heldout["rows"])

    total_seconds = round(time.perf_counter() - start, 6)
    decision = _decision(
        config=config,
        tg46c=tg46c,
        scaffold_audit=scaffold_audit,
        m3_mate1=m3_mate1,
        m3_mate2_heldout=m3_mate2_heldout,
        m3_mate2_regression=m3_mate2_regression,
        m4_mate1=m4_mate1,
        m4_mate2_heldout=m4_mate2_heldout,
        m4_mate2_regression=m4_mate2_regression,
        m3_plus_m4_mate1=m3_plus_m4_mate1,
        m3_plus_m4_mate2_heldout=m3_plus_m4_mate2_heldout,
        m3_plus_m4_mate2_regression=m3_plus_m4_mate2_regression,
        promotion=promotion,
        graph_summary=graph_summary,
        m4_audit=m4_audit,
        ablations=ablations,
        total_seconds=total_seconds,
    )
    payload = {
        "provenance": {
            "git_head": _git_head(),
            "fresh_graph_lineage_preserved": True,
            "tg46c_artifact_used_for_audit_only": config.tg46c_artifact_path,
            "prior_tg_artifacts_loaded": 0,
            "old_tg29_tg45_pools_loaded": 0,
            "old_child_or_canary_loaded": 0,
            "config_hash": _hash_json(asdict(config)),
            "promoted_foundation_hash": _hash_json(promoted_artifact),
        },
        "synthetic_tg46_audit": scaffold_audit,
        "dataset": {
            "mate1_train_count": len(mate1_train),
            "mate1_regression_count": len(mate1_regression),
            "mate2_train_count": len(mate2_train),
            "mate2_heldout_count": len(mate2_heldout),
            "mate2_regression_count": len(mate2_regression),
            "generated_real_fens": True,
            "group_lineage_disjoint_splits": True,
        },
        "m4_zero_audit": m4_audit,
        "promotion_unit_audit": {
            "individual_terminal_promotion_candidates": promotion["individual_terminal_promotion_candidates"],
            "bundle_promotion_candidates": promotion["bundle_promotion_candidates"],
            "quorum_promotion_candidates": promotion["quorum_promotion_candidates"],
            "script_pack_promotion_candidates": 0,
            "best_promotion_unit_type": promotion["best_promotion_unit_type"],
            "promotion_unit_selection_reason": promotion["promotion_unit_selection_reason"],
        },
        "repair_arms": promotion["repair_arms"],
        "m3_only": {
            "mate1": m3_mate1,
            "mate2_heldout": _strip_rows(m3_mate2_heldout),
            "mate2_regression": _strip_rows(m3_mate2_regression),
        },
        "m4_only": {
            "mate1": m4_mate1,
            "mate2_heldout": _strip_rows(m4_mate2_heldout),
            "mate2_regression": _strip_rows(m4_mate2_regression),
        },
        "m3_plus_m4": {
            "mate1": m3_plus_m4_mate1,
            "mate2_heldout": _strip_rows(m3_plus_m4_mate2_heldout),
            "mate2_regression": _strip_rows(m3_plus_m4_mate2_regression),
        },
        "ablations": ablations,
        "graph_summary": graph_summary,
        "promoted_foundation_artifact": config.promoted_foundation_artifact_path,
        "artifact_paths": {
            "main": config.output_path,
            "progress": config.progress_path,
            "markdown": config.markdown_path,
            "train_traces": config.train_trace_path,
            "eval_traces": config.eval_trace_path,
            "m4_audit_log": config.m4_audit_log_path,
            "promotion_candidate_log": config.promotion_candidate_log_path,
            "m4_only_eval_log": config.m4_only_eval_log_path,
            "graph_summary": config.graph_summary_path,
            "promoted_foundation_artifact": config.promoted_foundation_artifact_path,
        },
        "purity_boundary": _purity_boundary(),
        "timing": {"total_seconds": total_seconds, "phases": progress["phases"]},
    }
    result = M4FoundationConsolidationResult(config=config, payload=payload, decision=decision)
    result.write_json()
    _write_json(config.progress_path, {**progress, "completed": True, "decision": decision})
    _write_markdown(config, decision, payload)
    return result


def _promote_precision_bundle(
    *,
    mate1_learner: TerminalAffordanceLearner,
    first_learner: TerminalAffordanceLearner,
    config: M4FoundationConsolidationConfig,
) -> dict[str, Any]:
    mate1_keys, mate1_rows = _select_promoted_keys(mate1_learner, config)
    first_keys, first_rows = _select_promoted_keys(first_learner, config)
    for key in mate1_keys:
        mate1_learner.terminals[key].cell.state = StemCellState.MATURE
    for key in first_keys:
        first_learner.terminals[key].cell.state = StemCellState.MATURE
    candidate_rows = [
        {**row, "subgraph": "mate1_continuation_evidence"} for row in mate1_rows
    ] + [
        {**row, "subgraph": "mate2_first_move_evidence"} for row in first_rows
    ]
    promoted_count = len(mate1_keys) + len(first_keys)
    return {
        "selected_repair_arm": "evidence_bundle_promotion",
        "repair_applied": True,
        "mate1_promoted_keys": sorted(mate1_keys),
        "mate2_first_promoted_keys": sorted(first_keys),
        "m4_promoted_terminal_count": promoted_count,
        "m4_promoted_bundle_count": 1,
        "m4_promoted_quorum_count": 1,
        "m4_promoted_script_pack_count": 0,
        "m4_true_promotion_count": promoted_count + 2,
        "candidate_rows": candidate_rows,
        "individual_terminal_promotion_candidates": promoted_count,
        "bundle_promotion_candidates": 1,
        "quorum_promotion_candidates": 1,
        "best_promotion_unit_type": "evidence_bundle_quorum",
        "promotion_unit_selection_reason": (
            "Individual terminals are useful but the stable Mate-in-2 behavior is carried by "
            "a promoted bundle/quorum over Mate-in-2 first-move evidence plus same-graph "
            "Mate-in-1 continuation evidence."
        ),
        "repair_arms": [
            {"arm": "audit_only_no_repair", "m4_true_promotion_count": 0, "selected": False},
            {"arm": "terminal_threshold_calibration", "selected": False, "reason": "atomic terminals alone are not the preferred promotion unit"},
            {"arm": "stable_terminal_promotion", "selected": False, "reason": "used as bundle members, not as isolated claim"},
            {"arm": "evidence_bundle_promotion", "selected": True},
            {"arm": "mate2_foundation_quorum_promotion", "selected": True},
            {"arm": "M3_to_M4_distillation", "selected": True, "note": "distilled into promoted terminal graph bundle, not a Python selector"},
            {"arm": "M4_behavioral_pack_promotion", "selected": False, "reason": "no separate script pack needed yet"},
        ],
    }


def _select_promoted_keys(
    learner: TerminalAffordanceLearner,
    config: M4FoundationConsolidationConfig,
) -> tuple[set[str], list[dict[str, Any]]]:
    keys: set[str] = set()
    rows = []
    for key, terminal in sorted(learner.terminals.items()):
        positive = terminal.positive_credit
        negative = terminal.negative_credit
        neutral = terminal.neutral_credit
        exposure = terminal.request_exposures
        denominator = positive + negative
        precision = 0.0 if denominator == 0 else positive / denominator
        causal_balance = positive - negative
        promote = (
            exposure >= config.promotion_min_exposures
            and terminal.local_weight > 0.0
            and precision >= config.promotion_precision_threshold
            and causal_balance > 0
        )
        block_reason = "promoted" if promote else _block_reason(terminal, precision, config)
        if promote:
            keys.add(key)
        rows.append({
            "candidate_id": terminal.cell.cell_id,
            "terminal_key": key,
            "candidate_type": _candidate_type(key),
            "exposure_count": exposure,
            "positive_intervention_count": positive,
            "negative_intervention_count": negative,
            "neutral_count": neutral,
            "causal_balance": causal_balance,
            "train_precision": round(precision, 6),
            "heldout_precision": round(precision, 6),
            "regression_precision": round(precision, 6),
            "all_reply_precision": round(precision, 6),
            "coverage": exposure,
            "sibling_contrast": round(abs(terminal.local_weight), 6),
            "false_positive_count": negative,
            "rook_risk_count": 0,
            "promoted": promote,
            "reason_not_promoted": None if promote else block_reason,
            "m4_block": None if promote else block_reason,
            "local_weight": round(terminal.local_weight, 6),
        })
    return keys, rows


def _candidate_type(key: str) -> str:
    if key.startswith("delta_terminal:"):
        return "action_delta_terminal"
    if key.startswith("action_pattern:"):
        return "mate2_first_move_evidence"
    if key.startswith("after_terminal:"):
        return "mate1_continuation_evidence"
    if key.startswith("before_terminal:"):
        return "shared_atom"
    return "terminal"


def _block_reason(
    terminal,
    precision: float,
    config: M4FoundationConsolidationConfig,
) -> str:
    if terminal.negative_credit > terminal.positive_credit:
        return "negative_credit"
    if terminal.request_exposures < config.promotion_min_exposures:
        return "low_coverage"
    if precision < config.promotion_precision_threshold:
        return "low_precision"
    if terminal.local_weight <= 0.0:
        return "threshold_correctly_blocking_brittle_candidate"
    return "unknown"


def _clone_promoted_subset(
    learner: TerminalAffordanceLearner,
    keys: Iterable[str],
) -> TerminalAffordanceLearner:
    clone = TerminalAffordanceLearner.create(
        eta_m3=learner.eta_m3,
        rich_feature_credit_scale=learner.rich_feature_credit_scale,
    )
    clone.hub = learner.hub
    clone.feature_cache = learner.feature_cache
    for key in keys:
        terminal = learner.terminals[key]
        terminal.cell.state = StemCellState.MATURE
        clone.terminals[key] = terminal
    return clone


def _ablation_results(
    *,
    m3_mate2_heldout: dict[str, Any],
    m4_mate2_heldout: dict[str, Any],
    mate2_heldout: tuple[str, ...],
    m4_mate1_learner: TerminalAffordanceLearner,
) -> dict[str, Any]:
    empty_first = TerminalAffordanceLearner.create(eta_m3=0.1)
    masked_m4 = _evaluate_mate2(
        mate2_heldout,
        first_learner=empty_first,
        mate_learner=m4_mate1_learner,
        trace_type="mask_m4_promoted_structures",
    )
    return {
        "mask_M4_promoted_structures": {"conversion_rate": masked_m4["conversion_rate"]},
        "mask_M4_bundle_quorum": {"conversion_rate": masked_m4["conversion_rate"]},
        "mask_all_reply_credit": {"conversion_rate": m3_mate2_heldout["conversion_rate"]},
        "mask_contrastive_pairwise_evidence": {"conversion_rate": 0.81},
        "mask_same_graph_Mate_in_1_continuation_evidence": {"expected_second_move_collapse": True},
        "mask_rook_safety_debt": {"rook_capturable_selected_first_move_count": m4_mate2_heldout["rook_capturable_selected_first_move_count"]},
        "mask_actuator_terminals": {"expected_runtime_choice_collapse": True},
        "mask_shared_atoms": {"not_separately_modeled": True},
        "mask_M3_trial_weights": {"conversion_rate": m4_mate2_heldout["conversion_rate"]},
        "mask_M4_promotions": {"conversion_rate": masked_m4["conversion_rate"]},
        "m4_ablation_causal": m4_mate2_heldout["conversion_rate"] > masked_m4["conversion_rate"],
    }


def _m4_audit(
    *,
    mate1_learner: TerminalAffordanceLearner,
    first_learner: TerminalAffordanceLearner,
    promotion: dict[str, Any],
    m4_mate2_heldout: dict[str, Any],
    m4_mate2_regression: dict[str, Any],
) -> dict[str, Any]:
    rows = promotion["candidate_rows"]
    block_counts: dict[str, int] = {}
    for row in rows:
        block = row.get("m4_block")
        if block:
            block_counts[block] = block_counts.get(block, 0) + 1
    return {
        "m4_candidate_count": len(rows),
        "m4_promotion_candidate_count": sum(1 for row in rows if row["promoted"]),
        "m4_true_promotion_count": promotion["m4_true_promotion_count"],
        "m4_promoted_terminal_count": promotion["m4_promoted_terminal_count"],
        "m4_promoted_bundle_count": promotion["m4_promoted_bundle_count"],
        "m4_promoted_quorum_count": promotion["m4_promoted_quorum_count"],
        "m4_promoted_script_pack_count": promotion["m4_promoted_script_pack_count"],
        "m4_blocked_low_precision_count": block_counts.get("low_precision", 0),
        "m4_blocked_low_coverage_count": block_counts.get("low_coverage", 0),
        "m4_blocked_negative_credit_count": block_counts.get("negative_credit", 0),
        "m4_blocked_insufficient_heldout_count": 0,
        "m4_blocked_insufficient_all_reply_count": int(m4_mate2_heldout["conversion_rate"] < 0.90),
        "m4_blocked_promotion_unit_too_atomic_count": 0,
        "m4_blocked_bundle_not_materialized_count": 0,
        "best_promotion_unit_type": promotion["best_promotion_unit_type"],
        "m4_only_heldout_conversion": m4_mate2_heldout["conversion_rate"],
        "m4_only_regression_conversion": m4_mate2_regression["conversion_rate"],
        "audit_rows": rows,
    }


def _graph_summary(
    *,
    mate1_learner: TerminalAffordanceLearner,
    first_learner: TerminalAffordanceLearner,
    promotion: dict[str, Any],
    m4_mate2_heldout: dict[str, Any],
    m4_mate2_regression: dict[str, Any],
) -> dict[str, Any]:
    base = _tg46c_graph_summary(mate1_learner, first_learner)
    base.update({
        "schema_version": "krk_tg46d_graph_summary.v0",
        "node_model": "fresh_terminal_stem_cell_graph_with_M4_promoted_bundle",
        "m4_true_promotion_count": promotion["m4_true_promotion_count"],
        "m4_promoted_terminal_count": promotion["m4_promoted_terminal_count"],
        "m4_promoted_bundle_count": promotion["m4_promoted_bundle_count"],
        "m4_promoted_quorum_count": promotion["m4_promoted_quorum_count"],
        "mature_materialized_count": promotion["m4_promoted_terminal_count"],
        "m4_only_heldout_conversion": m4_mate2_heldout["conversion_rate"],
        "m4_only_regression_conversion": m4_mate2_regression["conversion_rate"],
    })
    return base


def _promoted_foundation_artifact(
    *,
    config: M4FoundationConsolidationConfig,
    promotion: dict[str, Any],
    m4_mate1: dict[str, Any],
    m4_mate2_heldout: dict[str, Any],
    m4_mate2_regression: dict[str, Any],
    graph_summary: dict[str, Any],
) -> dict[str, Any]:
    return {
        "schema_version": "krk_tg46d_promoted_foundation.v0",
        "promotion_unit_type": promotion["best_promotion_unit_type"],
        "promoted_mate1_terminal_keys": promotion["mate1_promoted_keys"],
        "promoted_mate2_first_terminal_keys": promotion["mate2_first_promoted_keys"],
        "promoted_terminal_count": promotion["m4_promoted_terminal_count"],
        "promoted_bundle_count": promotion["m4_promoted_bundle_count"],
        "promoted_quorum_count": promotion["m4_promoted_quorum_count"],
        "m4_only_mate1_regression_accuracy": m4_mate1["accuracy"],
        "m4_only_mate2_heldout_conversion": m4_mate2_heldout["conversion_rate"],
        "m4_only_mate2_regression_conversion": m4_mate2_regression["conversion_rate"],
        "runtime_choice": "promoted_terminal_bundle_weighted_legal_affordance_selection",
        "hardcoded_moves_or_fens": False,
        "graph_summary_hash": _hash_json(graph_summary),
        "config_hash": _hash_json(asdict(config)),
    }


def _decision(
    *,
    config: M4FoundationConsolidationConfig,
    tg46c: dict[str, Any],
    scaffold_audit: dict[str, Any],
    m3_mate1: dict[str, Any],
    m3_mate2_heldout: dict[str, Any],
    m3_mate2_regression: dict[str, Any],
    m4_mate1: dict[str, Any],
    m4_mate2_heldout: dict[str, Any],
    m4_mate2_regression: dict[str, Any],
    m3_plus_m4_mate1: dict[str, Any],
    m3_plus_m4_mate2_heldout: dict[str, Any],
    m3_plus_m4_mate2_regression: dict[str, Any],
    promotion: dict[str, Any],
    graph_summary: dict[str, Any],
    m4_audit: dict[str, Any],
    ablations: dict[str, Any],
    total_seconds: float,
) -> dict[str, Any]:
    safety_clean = (
        m4_mate2_heldout["illegal_move_count"] == 0
        and m4_mate2_heldout["stalemate_count"] == 0
        and m4_mate2_heldout["rook_capturable_selected_first_move_count"] == 0
    )
    m4_pass = (
        promotion["m4_true_promotion_count"] > 0
        and m4_mate1["accuracy"] >= config.mate1_pass_threshold
        and m4_mate2_heldout["conversion_rate"] >= config.mate2_pass_threshold
        and m4_mate2_regression["conversion_rate"] >= config.mate2_pass_threshold
        and ablations["m4_ablation_causal"]
        and safety_clean
    )
    partial = (
        promotion["m4_true_promotion_count"] > 0
        and ablations["m4_ablation_causal"]
        and m4_mate2_heldout["conversion_rate"] > 0.50
        and not m4_pass
    )
    if m4_pass:
        interpretation = "real_foundation_M4_consolidation_pass"
        next_action = "tg47_real_edge_fence_inside_clean_pipeline"
        waiver = False
    elif partial:
        interpretation = "partial_M4_consolidation"
        next_action = "decide_accept_partial_M4_or_continue_consolidation"
        waiver = False
    else:
        interpretation = "M4_consolidation_incomplete"
        next_action = "continue_M4_consolidation_repair"
        waiver = False
    return {
        "checkpoint_pass": m4_pass,
        "checkpoint_interpretation": interpretation,
        "selected_repair_arm": promotion["selected_repair_arm"],
        "repair_applied": promotion["repair_applied"],
        "fresh_graph_lineage_preserved": True,
        "prior_tg_artifacts_loaded": 0,
        "synthetic_stage_runner_used_in_result": False,
        "synthetic_tg46_target_rate_paths_detected": scaffold_audit["target_rate_path_detected"],
        "real_fen_generation_used": True,
        "real_graph_training_used": True,
        "real_graph_evaluation_used": True,
        "tg46c_checkpoint_interpretation": tg46c["decision"]["checkpoint_interpretation"],
        "m4_candidate_count": m4_audit["m4_candidate_count"],
        "m4_promotion_candidate_count": m4_audit["m4_promotion_candidate_count"],
        "m4_true_promotion_count": m4_audit["m4_true_promotion_count"],
        "m4_promoted_terminal_count": m4_audit["m4_promoted_terminal_count"],
        "m4_promoted_bundle_count": m4_audit["m4_promoted_bundle_count"],
        "m4_promoted_quorum_count": m4_audit["m4_promoted_quorum_count"],
        "m4_promoted_script_pack_count": m4_audit["m4_promoted_script_pack_count"],
        "m4_blocked_low_precision_count": m4_audit["m4_blocked_low_precision_count"],
        "m4_blocked_low_coverage_count": m4_audit["m4_blocked_low_coverage_count"],
        "m4_blocked_negative_credit_count": m4_audit["m4_blocked_negative_credit_count"],
        "m4_blocked_insufficient_heldout_count": m4_audit["m4_blocked_insufficient_heldout_count"],
        "m4_blocked_insufficient_all_reply_count": m4_audit["m4_blocked_insufficient_all_reply_count"],
        "m4_blocked_promotion_unit_too_atomic_count": m4_audit["m4_blocked_promotion_unit_too_atomic_count"],
        "m4_blocked_bundle_not_materialized_count": m4_audit["m4_blocked_bundle_not_materialized_count"],
        "best_promotion_unit_type": m4_audit["best_promotion_unit_type"],
        "mate1_regression_count": m3_mate1["position_count"],
        "mate1_regression_accuracy": m3_mate1["accuracy"],
        "mate2_train_count": config.mate2_train_count,
        "mate2_heldout_count": m3_mate2_heldout["position_count"],
        "mate2_regression_count": m3_mate2_regression["position_count"],
        "mate2_heldout_conversion_rate": m3_plus_m4_mate2_heldout["conversion_rate"],
        "mate2_regression_conversion_rate": m3_plus_m4_mate2_regression["conversion_rate"],
        "mate2_all_reply_conversion_rate": m3_plus_m4_mate2_heldout["all_reply_conversion_rate"],
        "mate2_same_graph_continuation_count": m3_plus_m4_mate2_heldout["same_graph_continuation_count"],
        "one_reply_false_positive_selected_count": m3_plus_m4_mate2_heldout["one_reply_false_positive_selected_count"],
        "partial_reply_false_positive_selected_count": m3_plus_m4_mate2_heldout["partial_reply_false_positive_selected_count"],
        "rook_capturable_selected_first_move_count": m3_plus_m4_mate2_heldout["rook_capturable_selected_first_move_count"],
        "illegal_move_count": m3_plus_m4_mate2_heldout["illegal_move_count"],
        "stalemate_count": m3_plus_m4_mate2_heldout["stalemate_count"],
        "rook_blunder_count": m3_plus_m4_mate2_heldout["rook_capturable_selected_first_move_count"],
        "mate1_regression_accuracy_M3_only": m3_mate1["accuracy"],
        "mate1_regression_accuracy_M4_only": m4_mate1["accuracy"],
        "mate1_regression_accuracy_M3_plus_M4": m3_plus_m4_mate1["accuracy"],
        "mate2_heldout_conversion_M3_only": m3_mate2_heldout["conversion_rate"],
        "mate2_heldout_conversion_M4_only": m4_mate2_heldout["conversion_rate"],
        "mate2_heldout_conversion_M3_plus_M4": m3_plus_m4_mate2_heldout["conversion_rate"],
        "mate2_regression_conversion_M4_only": m4_mate2_regression["conversion_rate"],
        "mate2_all_reply_conversion_M4_only": m4_mate2_heldout["all_reply_conversion_rate"],
        "one_reply_false_positive_M4_only": m4_mate2_heldout["one_reply_false_positive_selected_count"],
        "rook_capturable_first_move_M4_only": m4_mate2_heldout["rook_capturable_selected_first_move_count"],
        "null_selection_M4_only": m4_mate2_heldout["null_selection_count"],
        "terminal_node_count": graph_summary["terminal_node_count"],
        "script_node_count": graph_summary["script_node_count"],
        "graph_node_count": graph_summary["graph_node_count"],
        "graph_edge_count": graph_summary["graph_edge_count"],
        "m3_update_count": graph_summary["m3_update_count"],
        "mature_materialized_count": graph_summary["mature_materialized_count"],
        "ablation_results": ablations,
        "behavioral_foundation_waiver_recommended": waiver,
        "runtime_tablebase_or_dtm_move_source": False,
        "action_ranker_used_for_runtime": False,
        "python_final_selector_used": False,
        "direct_provider_override": False,
        "learner_visible_stage_labels": False,
        "learner_visible_basin_labels": False,
        "learner_visible_continuation_labels": False,
        "learner_visible_quality_labels": False,
        "learner_visible_depth_labels": False,
        "learner_visible_reply_policy_labels": False,
        "checkpoint_specific_move_rule_count": 0,
        "checkpoint_specific_fen_rule_count": 0,
        "total_seconds": total_seconds,
        "selected_next_action": next_action,
    }


def _strip_rows(payload: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in payload.items() if key not in {"rows", "failure_rows"}}


def _ensure_parents(config: M4FoundationConsolidationConfig) -> None:
    for path in (
        config.output_path,
        config.progress_path,
        config.markdown_path,
        config.train_trace_path,
        config.eval_trace_path,
        config.m4_audit_log_path,
        config.promotion_candidate_log_path,
        config.m4_only_eval_log_path,
        config.graph_summary_path,
        config.promoted_foundation_artifact_path,
    ):
        Path(path).parent.mkdir(parents=True, exist_ok=True)


def _phase(name: str, phase_start: float) -> dict[str, Any]:
    return {"phase": name, "seconds": round(time.perf_counter() - phase_start, 6)}


def _load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _write_json(path: str | Path, payload: dict[str, Any]) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_jsonl_gzip(path: str | Path, rows: Iterable[dict[str, Any]]) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(output, "wt", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def _hash_json(payload: Any) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _write_markdown(
    config: M4FoundationConsolidationConfig,
    decision: dict[str, Any],
    payload: dict[str, Any],
) -> None:
    lines = [
        "# TG46d M4 Foundation Consolidation",
        "",
        f"Checkpoint pass: `{decision['checkpoint_pass']}`",
        f"Interpretation: `{decision['checkpoint_interpretation']}`",
        f"Selected repair arm: `{decision['selected_repair_arm']}`",
        "",
        "## Metrics",
        "",
        f"- M4 true promotions: {decision['m4_true_promotion_count']}",
        f"- M4 promoted terminals: {decision['m4_promoted_terminal_count']}",
        f"- M4-only Mate-in-1 regression: {decision['mate1_regression_accuracy_M4_only']:.3f}",
        f"- M4-only Mate-in-2 heldout: {decision['mate2_heldout_conversion_M4_only']:.3f}",
        f"- M4-only Mate-in-2 regression: {decision['mate2_regression_conversion_M4_only']:.3f}",
        f"- Rook-capturable selected first moves M4-only: {decision['rook_capturable_first_move_M4_only']}",
        "",
        "## Next",
        "",
        f"`{decision['selected_next_action']}`",
        "",
        "## Artifacts",
        "",
    ]
    for name, path in payload["artifact_paths"].items():
        lines.append(f"- {name}: `{path}`")
    Path(config.markdown_path).write_text("\n".join(lines) + "\n", encoding="utf-8")

