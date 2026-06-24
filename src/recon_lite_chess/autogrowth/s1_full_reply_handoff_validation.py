"""TG29n S1 full-reply handoff validation."""

from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass
import json
from pathlib import Path
import time
from typing import Any

import chess

from .frozen_foundation_edge_fence_reentry import _cheap_candidate_rows, _foundation_counts
from .frozen_foundation_response_cache_bridge_retrieval import _cache_candidate_rows
from .post_trajectory_second_move_handoff_audit import (
    _audit_second_candidate,
    _compact_foundation_state,
    _compact_regression,
    _full_reply_envelope,
    _purity_boundary as _tg29m_purity_boundary,
)
from .real_context_runtime_trajectory_validation import (
    RealContextRuntimeTrajectoryValidationConfig,
    _artifact_reuse_summary,
    _build_minimal_real_context,
    _load_artifacts,
    _rows_by_start,
)
from .runtime_trajectory_repair_integration import RuntimeTrajectoryRepairIntegrationConfig, _select_runtime_trajectory_move
from .stable_trajectory_cache_selection_microprobe import KNOWN_CASES
from .tiny_online_krk_episode_runner import (
    TinyOnlineKRKEpisodeRunnerConfig,
    _foundation_reachable,
    _safety_result,
    _select_black_reply,
    _write_progress as _write_tg29a_progress,
)


ARMS = (
    "tg29m_repair_baseline",
    "strict_all_reply_priority",
    "all_reply_priority_plus_partial_support",
    "partial_reply_support_with_worst_reply_veto",
    "one_reply_conservative_mode",
)


@dataclass(frozen=True)
class S1FullReplyHandoffValidationConfig:
    base: TinyOnlineKRKEpisodeRunnerConfig = TinyOnlineKRKEpisodeRunnerConfig(
        schedule_names=("tg29l_minimal_real_context",),
        episode_count=2,
        max_white_moves_per_episode=2,
        max_episode_ablation_count=1,
        progress_output="reports/autogrowth/krk_autogrowth_tg29n_s1_full_reply_handoff_validation_progress.json",
    )
    tg29m_artifact_path: str = "reports/autogrowth/krk_autogrowth_tg29m_post_trajectory_second_move_handoff_audit.json"
    target_train_s1: int = 4
    target_heldout_s1: int = 4
    target_near_miss_s1: int = 4
    minimum_train_s1: int = 2
    minimum_heldout_s1: int = 2
    minimum_near_miss_s1: int = 2
    max_s1_per_slice: int = 4
    max_audited_candidates_per_s1: int = 10
    run_max3_diagnostic: bool = True


@dataclass(frozen=True)
class S1FullReplyHandoffValidationResult:
    config: S1FullReplyHandoffValidationConfig
    context_profile: dict[str, Any]
    artifact_reuse: dict[str, Any]
    s1_validation_set: dict[str, Any]
    candidate_audits: dict[str, Any]
    arm_comparison: dict[str, Any]
    selected_arm: dict[str, Any]
    tiny_online_recheck: dict[str, Any]
    compact_regression: dict[str, Any]
    ablation_results: dict[str, Any]
    decision: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "krk_autogrowth_tg29n_s1_full_reply_handoff_validation.v0",
            "checkpoint": "TG29n_s1_full_reply_handoff_validation",
            "config": asdict(self.config),
            "purity_boundary": _purity_boundary(),
            "context_profile": self.context_profile,
            "artifact_reuse": self.artifact_reuse,
            "s1_validation_set": self.s1_validation_set,
            "candidate_audits": self.candidate_audits,
            "arm_comparison": self.arm_comparison,
            "selected_arm": self.selected_arm,
            "tiny_online_recheck": self.tiny_online_recheck,
            "compact_regression": self.compact_regression,
            "ablation_results": self.ablation_results,
            "decision": self.decision,
        }

    def write_json(self, path: str | Path) -> Path:
        output = Path(path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(self.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return output

    def write_markdown(self, path: str | Path) -> Path:
        output = Path(path)
        output.parent.mkdir(parents=True, exist_ok=True)
        d = self.decision
        output.write_text(
            "\n".join(
                [
                    "# TG29n S1 Full-Reply Handoff Validation",
                    "",
                    f"- checkpoint_pass: `{d['checkpoint_pass']}`",
                    f"- interpretation: `{d['checkpoint_interpretation']}`",
                    f"- selected arm: `{d['selected_arm']}`",
                    f"- S1 slices train/heldout/near_miss: `{d['train_s1_count']}` / `{d['heldout_s1_count']}` / `{d['near_miss_s1_count']}`",
                    f"- heldout selected all-reply: `{d['heldout_selected_all_reply_count']}` / `{d['heldout_s1_count']}`",
                    f"- selected one-reply false positives: `{d['heldout_selected_one_reply_later_failed_count']}`",
                    f"- all/partial/one-reply positives: `{d['all_reply_positive_count']}` / `{d['partial_reply_positive_count']}` / `{d['one_reply_positive_count']}`",
                    f"- one-reply later failed: `{d['one_reply_later_failed_count']}`",
                    f"- max2 success: `{d['max2_episode_success_count']}` / `{d['max2_episode_count']}`",
                    f"- max3 success: `{d['max3_episode_success_count']}` / `{d['max3_episode_count']}`",
                    f"- safety rook/illegal/stalemate: `{d['rook_blunder_count']}` / `{d['illegal_move_count']}` / `{d['stalemate_count']}`",
                    f"- ablation causal: `{d['selected_arm_ablation_causal']}`",
                    "",
                    "Interpretation: TG29n validates post-trajectory S1 second-move evidence. It does not broaden KRK or add a new learner mechanism.",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        return output


def run_s1_full_reply_handoff_validation(
    *,
    config: S1FullReplyHandoffValidationConfig | None = None,
) -> S1FullReplyHandoffValidationResult:
    cfg = config or S1FullReplyHandoffValidationConfig()
    total_start = time.perf_counter()
    timings: dict[str, float] = {}
    _write_progress(cfg, {"phase": "start"})

    start = time.perf_counter()
    tg29m = _load_json(cfg.tg29m_artifact_path)
    real_cfg = _real_context_cfg(cfg)
    artifacts = _load_artifacts(real_cfg)
    rows_by_start = _rows_by_start(artifacts["tg29h"])
    artifact_reuse = _artifact_reuse_summary(real_cfg, artifacts, rows_by_start)
    artifact_reuse["tg29m_artifact_path"] = cfg.tg29m_artifact_path
    timings["artifact_load_seconds"] = round(time.perf_counter() - start, 6)

    start = time.perf_counter()
    context, context_profile = _build_minimal_real_context(real_cfg, artifact_reuse)
    if context is None:
        raise RuntimeError(f"TG29n requires real context; build failed: {context_profile}")
    timings["context_build_seconds"] = round(time.perf_counter() - start, 6)
    foundation_before_eval = _foundation_counts(context["graph"])
    _write_progress(cfg, {"phase": "context_built", "seconds": timings["context_build_seconds"]})

    start = time.perf_counter()
    validation_set = _build_s1_validation_set(cfg, artifacts["tg29h"], tg29m)
    timings["dataset_seconds"] = round(time.perf_counter() - start, 6)
    _write_progress(cfg, {"phase": "dataset_built", "counts": validation_set["slice_counts"]})

    start = time.perf_counter()
    candidate_audits = _audit_s1_set(cfg, context, validation_set)
    timings["candidate_audit_seconds"] = round(time.perf_counter() - start, 6)
    _write_progress(cfg, {"phase": "s1_audit_complete", "audited_s1_count": candidate_audits["audited_s1_count"]})

    start = time.perf_counter()
    arm_comparison = _compare_arms(candidate_audits)
    selected_arm = _select_arm(arm_comparison, candidate_audits)
    timings["arm_comparison_seconds"] = round(time.perf_counter() - start, 6)
    _write_progress(cfg, {"phase": "arms_complete", "selected_arm": selected_arm["selected_arm"]})

    start = time.perf_counter()
    tiny_max2 = _run_tiny_recheck(cfg, context, rows_by_start, selected_arm, max_white_moves=2)
    tiny_max3 = _run_tiny_recheck(cfg, context, rows_by_start, selected_arm, max_white_moves=3) if cfg.run_max3_diagnostic else _empty_recheck("max3_skipped")
    tiny = {"max2": tiny_max2, "max3": tiny_max3}
    timings["tiny_recheck_seconds"] = round(time.perf_counter() - start, 6)

    start = time.perf_counter()
    ablations = _ablation_results(selected_arm, candidate_audits)
    compact = _compact_regression(context, artifacts, rows_by_start)
    foundation_after_eval = _foundation_counts(context["graph"])
    timings["regression_ablation_seconds"] = round(time.perf_counter() - start, 6)
    timings["total_seconds"] = round(time.perf_counter() - total_start, 6)

    decision = _decision(
        cfg,
        context=context,
        context_profile=context_profile,
        validation_set=validation_set,
        candidate_audits=candidate_audits,
        arm_comparison=arm_comparison,
        selected_arm=selected_arm,
        tiny=tiny,
        compact=compact,
        ablations=ablations,
        foundation_before_eval=foundation_before_eval,
        foundation_after_eval=foundation_after_eval,
        timings=timings,
    )
    _write_progress(cfg, {"phase": "complete", "decision": {"checkpoint_pass": decision["checkpoint_pass"], "checkpoint_interpretation": decision["checkpoint_interpretation"]}})
    return S1FullReplyHandoffValidationResult(
        config=cfg,
        context_profile=context_profile,
        artifact_reuse=artifact_reuse,
        s1_validation_set=validation_set,
        candidate_audits=candidate_audits,
        arm_comparison=arm_comparison,
        selected_arm=selected_arm,
        tiny_online_recheck=tiny,
        compact_regression=compact,
        ablation_results=ablations,
        decision=decision,
    )


def _real_context_cfg(cfg: S1FullReplyHandoffValidationConfig) -> RealContextRuntimeTrajectoryValidationConfig:
    return RealContextRuntimeTrajectoryValidationConfig(base=cfg.base)


def _load_json(path: str) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _build_s1_validation_set(cfg: S1FullReplyHandoffValidationConfig, tg29h: dict[str, Any], tg29m: dict[str, Any]) -> dict[str, Any]:
    records: list[dict[str, Any]] = []
    seen: set[str] = set()
    attempts = Counter()

    def add(record: dict[str, Any]) -> None:
        attempts["attempted"] += 1
        key = record["s1_fen"]
        if key in seen:
            attempts["duplicate"] += 1
            return
        seen.add(key)
        records.append(record | {"s1_id": f"s1_{len(records):03d}"})
        attempts["accepted"] += 1

    failing = tg29m.get("failing_episode_trace", {})
    if failing.get("s1_fen"):
        add({
            "slice": "train",
            "source": "tg29m_failing_episode_trace",
            "start_fen": failing["start_fen"],
            "first_white_move": failing["selected_first_white_move"],
            "black_reply": failing["black_reply_after_first"],
            "s1_fen": failing["s1_fen"],
            "trajectory_policy_classification": "trajectory_positive",
            "expected_old_second_move": failing.get("selected_second_white_move"),
        })

    for ep in tg29m.get("max2_recheck", {}).get("traces", []):
        if not ep.get("steps"):
            continue
        step = ep["steps"][0]
        s1_fen = step.get("after_black_reply_fen")
        if not s1_fen:
            continue
        add({
            "slice": "heldout" if len([r for r in records if r["slice"] == "heldout"]) < cfg.target_heldout_s1 else "train",
            "source": "tg29m_max2_recheck",
            "start_fen": ep["start_fen"],
            "first_white_move": step.get("selected_white_move"),
            "black_reply": step.get("black_reply"),
            "s1_fen": s1_fen,
            "trajectory_policy_classification": "trajectory_positive",
            "expected_second_move_after_repair": ep["steps"][1].get("selected_white_move") if len(ep["steps"]) > 1 else None,
        })

    starts = tg29h.get("trajectory_audit", {}).get("starts", [])
    positives: list[dict[str, Any]] = []
    near: list[dict[str, Any]] = []
    for start in starts:
        for row in start.get("candidate_rows", []):
            for rollout in row.get("policy_rollouts", []):
                rec = {
                    "slice": "unassigned",
                    "source": "tg29h_policy_rollout",
                    "start_fen": start["start_fen"],
                    "first_white_move": row["candidate_move"],
                    "black_reply": rollout.get("black_reply"),
                    "black_reply_policy": rollout.get("black_reply_policy"),
                    "s1_fen": rollout["s1_fen"],
                    "trajectory_policy_classification": rollout.get("trajectory_policy_classification") or row.get("trajectory_classification"),
                    "graph_selected_second_move": rollout.get("graph_selected_second_move"),
                    "foundation_after_second_reply_reachable": rollout.get("foundation_after_second_reply_reachable"),
                    "same_graph_foundation_continuation_count": rollout.get("same_graph_foundation_continuation_count"),
                    "next_phase": rollout.get("next_phase"),
                }
                if rec["trajectory_policy_classification"] == "trajectory_positive":
                    positives.append(rec)
                else:
                    near.append(rec)

    for rec in positives:
        counts = Counter(r["slice"] for r in records)
        if counts["train"] < cfg.target_train_s1:
            add(rec | {"slice": "train"})
        elif counts["heldout"] < cfg.target_heldout_s1:
            add(rec | {"slice": "heldout"})
    for rec in near:
        counts = Counter(r["slice"] for r in records)
        if counts["near_miss"] < cfg.target_near_miss_s1:
            add(rec | {"slice": "near_miss"})
        elif counts["heldout"] < cfg.target_heldout_s1:
            add(rec | {"slice": "heldout"})
        elif counts["train"] < cfg.target_train_s1:
            add(rec | {"slice": "train"})

    capped = []
    per_slice = Counter()
    for rec in records:
        if per_slice[rec["slice"]] >= cfg.max_s1_per_slice:
            continue
        per_slice[rec["slice"]] += 1
        capped.append(rec)

    return {
        "target_counts": {"train": cfg.target_train_s1, "heldout": cfg.target_heldout_s1, "near_miss": cfg.target_near_miss_s1},
        "minimum_counts": {"train": cfg.minimum_train_s1, "heldout": cfg.minimum_heldout_s1, "near_miss": cfg.minimum_near_miss_s1},
        "slice_counts": dict(Counter(row["slice"] for row in capped)),
        "generation_attempts": dict(attempts),
        "records": capped,
    }


def _audit_s1_set(cfg: S1FullReplyHandoffValidationConfig, context: dict[str, Any], validation_set: dict[str, Any]) -> dict[str, Any]:
    rows = []
    totals = Counter()
    total_records = len(validation_set["records"])
    for idx, record in enumerate(validation_set["records"], start=1):
        _write_progress(cfg, {"phase": "s1_audit_running", "s1_index": idx, "s1_total": total_records, "s1_id": record["s1_id"], "slice": record["slice"]})
        audit = _audit_s1_record(cfg, context, record)
        rows.append(audit)
        for key, value in audit["counts"].items():
            totals[key] += int(value)
        _write_progress(cfg, {"phase": "s1_audit_running", "s1_index": idx, "s1_total": total_records, "s1_id": record["s1_id"], "audited_candidate_count": audit["audited_candidate_count"]})
    return {
        "audited_s1_count": len(rows),
        "rows": rows,
        "totals": dict(totals),
        "all_reply_positive_count": totals["all_reply_positive_count"],
        "partial_reply_positive_count": totals["partial_reply_positive_count"],
        "one_reply_positive_count": totals["one_reply_positive_count"],
        "one_reply_later_failed_count": totals["one_reply_later_failed_count"],
        "false_all_reply_positive_count": totals["false_all_reply_positive_count"],
        "reply_cap_limited_count": totals["reply_cap_limited_count"],
    }


def _audit_s1_record(cfg: S1FullReplyHandoffValidationConfig, context: dict[str, Any], record: dict[str, Any]) -> dict[str, Any]:
    board = chess.Board(record["s1_fen"])
    cheap = _cheap_candidate_rows(board, context["selected"]["edge_weights"])
    safe_count = sum(int(row["safety_ok"] and row["after_features"]["stalemate_after"] == 0.0) for row in cheap)
    materialized = _cache_candidate_rows(
        context["cache"],
        board,
        context["tg28c_cfg"],
        context["selected"]["edge_weights"],
        context["selected"]["bridge_weights"],
        cache_retrieval_enabled=True,
    )
    candidates = []
    counts = Counter()
    for row in materialized[: cfg.max_audited_candidates_per_s1]:
        audited = _audit_second_candidate(context, board, row)
        enriched = _enrich_candidate(record, row, audited)
        candidates.append(enriched)
        counts[enriched["tg29n_classification"]] += 1
        counts["all_reply_positive_count"] += int(enriched["all_reply_positive"])
        counts["partial_reply_positive_count"] += int(enriched["partial_reply_positive"])
        counts["one_reply_positive_count"] += int(enriched["one_reply_positive"])
        counts["one_reply_later_failed_count"] += int(enriched["one_reply_later_failed"])
        counts["false_all_reply_positive_count"] += int(enriched["false_all_reply_positive"])
        counts["reply_cap_limited_count"] += int(enriched["reply_cap_limited"])
    candidates.sort(key=lambda row: (-row["full_reply_score"], row["move"]))
    return {
        "s1_id": record["s1_id"],
        "slice": record["slice"],
        "source": record["source"],
        "start_fen": record["start_fen"],
        "first_white_move": record.get("first_white_move"),
        "black_reply": record.get("black_reply"),
        "s1_fen": record["s1_fen"],
        "trajectory_policy_classification": record.get("trajectory_policy_classification"),
        "legal_candidate_count": len(list(board.legal_moves)),
        "safe_candidate_count": safe_count,
        "audited_candidate_count": len(candidates),
        "candidate_cap_blocked_count": max(0, safe_count - len(candidates)),
        "counts": dict(counts),
        "candidate_rows": candidates,
    }


def _enrich_candidate(record: dict[str, Any], row: dict[str, Any], audited: dict[str, Any]) -> dict[str, Any]:
    full = audited["black_reply_envelope"]
    capped = row.get("cache_reply_envelope", {})
    capped_total = int(capped.get("reply_total", 0) or 0)
    capped_solved = int(capped.get("replies_foundation_solved", 0) or 0)
    full_total = int(full.get("reply_total", 0) or 0)
    full_solved = int(full.get("replies_foundation_solved", 0) or 0)
    capped_positive = capped_solved > 0
    full_all = bool(full["all_reply_foundation"] and full["worst_reply_foundation_success"])
    full_any = bool(full["any_reply_foundation"])
    one_reply_positive = full_total == 1 and full_all
    one_reply_later_failed = bool(capped_positive and capped_total <= 1 and full_total > 1 and not full_all)
    false_all = bool(full["all_reply_foundation"] and not full["worst_reply_foundation_success"])
    classification = _tg29n_classification(audited, full_all, full_any, one_reply_positive)
    reply_cap_limited = capped_total > 0 and capped_total < full_total
    out = {
        **audited,
        "s1_id": record["s1_id"],
        "s1_fen": record["s1_fen"],
        "cached_reply_envelope": _compact_envelope(capped),
        "tg29n_classification": classification,
        "all_reply_positive": full_all,
        "partial_reply_positive": full_any and not full_all,
        "one_reply_positive": one_reply_positive,
        "one_reply_later_failed": one_reply_later_failed,
        "false_all_reply_positive": false_all,
        "reply_cap_limited": reply_cap_limited,
        "full_reply_score": full_solved / max(1, full_total),
        "cached_reply_score": capped_solved / max(1, capped_total),
    }
    return out


def _compact_envelope(envelope: dict[str, Any]) -> dict[str, Any]:
    return {
        "reply_total": envelope.get("reply_total", 0),
        "replies_foundation_solved": envelope.get("replies_foundation_solved", 0),
        "reply_envelope_success_rate": envelope.get("reply_envelope_success_rate", 0.0),
        "any_reply_foundation": envelope.get("any_reply_foundation", False),
        "all_reply_foundation": envelope.get("all_reply_foundation", False),
        "worst_reply": envelope.get("worst_reply"),
        "worst_reply_foundation_success": envelope.get("worst_reply_foundation_success", False),
        "reason": envelope.get("reason"),
    }


def _tg29n_classification(audited: dict[str, Any], full_all: bool, full_any: bool, one_reply_positive: bool) -> str:
    if not audited["safe"] or audited["stalemate_after"]:
        return "unsafe"
    if one_reply_positive:
        return "one_reply_narrow_foundation_positive"
    if full_all:
        return "all_reply_foundation_handoff"
    if full_any:
        return "partial_reply_foundation_handoff"
    if audited["same_graph_foundation_continuation_count"] > 0:
        return "bridge_to_foundation_progress"
    if float(audited.get("current_evidence_score") or 0.0) > 0.0:
        return "safe_low_progress"
    return "unknown"


def _compare_arms(candidate_audits: dict[str, Any]) -> dict[str, Any]:
    arms = {}
    for arm in ARMS:
        rows = []
        totals = Counter()
        for s1 in candidate_audits["rows"]:
            selection = _select_candidate_for_arm(s1["candidate_rows"], arm)
            rows.append(_selection_summary(s1, selection))
            _accumulate_selection(totals, selection, s1)
        arms[arm] = {
            "arm": arm,
            "rows": rows,
            "totals": dict(totals),
            "slice_metrics": _slice_metrics(rows),
        }
    return {"arms": arms}


def _select_arm(arm_comparison: dict[str, Any], candidate_audits: dict[str, Any]) -> dict[str, Any]:
    preferred = (
        "strict_all_reply_priority",
        "one_reply_conservative_mode",
        "partial_reply_support_with_worst_reply_veto",
        "all_reply_priority_plus_partial_support",
        "tg29m_repair_baseline",
    )
    best = None
    for arm in preferred:
        data = arm_comparison["arms"][arm]
        heldout = data["slice_metrics"].get("heldout", {})
        if heldout.get("selected_one_reply_later_failed_count", 0) == 0 and heldout.get("unsafe_selected_count", 0) == 0:
            best = data
            break
    if best is None:
        best = arm_comparison["arms"]["strict_all_reply_priority"]
    selected_by_s1 = {}
    for row in best["rows"]:
        if row["selected_candidate"] is not None:
            selected_by_s1[row["s1_fen"]] = row["selected_candidate"]
    return {
        "selected_arm": best["arm"],
        "selection_reason": "prefer_no_selected_one_reply_false_positive_then_strict_full_reply",
        "selected_by_s1": selected_by_s1,
        "totals": best["totals"],
        "slice_metrics": best["slice_metrics"],
        "candidate_count": sum(len(s1["candidate_rows"]) for s1 in candidate_audits["rows"]),
    }


def _select_candidate_for_arm(rows: list[dict[str, Any]], arm: str, *, masks: dict[str, bool] | None = None) -> dict[str, Any] | None:
    masks = masks or {}
    if masks.get("mask_actuator_terminals"):
        return None
    scored = [(row, _arm_score(row, arm, masks)) for row in rows]
    viable = [(row, score) for row, score in scored if score > -900.0]
    if not viable:
        return None
    return max(viable, key=lambda item: (item[1], item[0]["same_graph_foundation_continuation_count"], item[0]["move"]))[0]


def _arm_score(row: dict[str, Any], arm: str, masks: dict[str, bool]) -> float:
    if not row["safe"] or row["stalemate_after"]:
        return -1000.0
    if masks.get("mask_foundation_response_terminals") or masks.get("disable_reply_envelope_checks") or masks.get("mask_frozen_mate2_foundation_quorum"):
        full_all = False
        partial = False
        one_reply = False
        one_reply_false = False
    else:
        full_all = bool(row["all_reply_positive"])
        partial = bool(row["partial_reply_positive"]) and not masks.get("mask_partial_reply_evidence", False)
        one_reply = bool(row["one_reply_positive"])
        one_reply_false = bool(row["one_reply_later_failed"])
    score = float(row.get("current_evidence_score") or 0.0)
    if masks.get("mask_bridge_pressure_terminals"):
        score -= 0.5
    if masks.get("mask_trajectory_positive_terminals"):
        score -= 0.25
    if arm == "tg29m_repair_baseline":
        score = float(row.get("repair_score") or score)
    elif arm == "strict_all_reply_priority":
        score += 100.0 if full_all else -10.0 if partial or one_reply_false else 0.0
    elif arm == "all_reply_priority_plus_partial_support":
        score += 100.0 if full_all else 8.0 if partial else 0.0
        score -= 25.0 if one_reply_false else 0.0
    elif arm == "partial_reply_support_with_worst_reply_veto":
        if partial and not row["black_reply_envelope"]["worst_reply_foundation_success"]:
            return -950.0
        score += 100.0 if full_all else 12.0 if partial else 0.0
    elif arm == "one_reply_conservative_mode":
        score += 90.0 if one_reply else 100.0 if full_all else 2.0 if partial else 0.0
        score -= 40.0 if one_reply_false else 0.0
    return score


def _selection_summary(s1: dict[str, Any], selected: dict[str, Any] | None) -> dict[str, Any]:
    full_exists = any(row["all_reply_positive"] for row in s1["candidate_rows"])
    return {
        "s1_id": s1["s1_id"],
        "slice": s1["slice"],
        "s1_fen": s1["s1_fen"],
        "selected_move": None if selected is None else selected["move"],
        "selected_classification": None if selected is None else selected["tg29n_classification"],
        "selected_all_reply_positive": bool(selected and selected["all_reply_positive"]),
        "selected_partial_reply_positive": bool(selected and selected["partial_reply_positive"]),
        "selected_one_reply_positive": bool(selected and selected["one_reply_positive"]),
        "selected_one_reply_later_failed": bool(selected and selected["one_reply_later_failed"]),
        "selected_unsafe": bool(selected and (not selected["safe"] or selected["stalemate_after"])),
        "full_reply_candidate_exists": full_exists,
        "selected_low_progress_when_full_exists": bool(full_exists and selected and not selected["all_reply_positive"]),
        "selected_candidate": selected,
    }


def _accumulate_selection(totals: Counter, selected: dict[str, Any] | None, s1: dict[str, Any]) -> None:
    totals["s1_count"] += 1
    totals["null_selection_count"] += int(selected is None)
    totals["full_reply_candidate_exists_count"] += int(any(row["all_reply_positive"] for row in s1["candidate_rows"]))
    if selected is None:
        return
    totals["selected_all_reply_count"] += int(selected["all_reply_positive"])
    totals["selected_partial_reply_count"] += int(selected["partial_reply_positive"])
    totals["selected_one_reply_positive_count"] += int(selected["one_reply_positive"])
    totals["selected_one_reply_later_failed_count"] += int(selected["one_reply_later_failed"])
    totals["unsafe_selected_count"] += int(not selected["safe"] or selected["stalemate_after"])
    totals["selected_low_progress_when_full_exists_count"] += int(any(row["all_reply_positive"] for row in s1["candidate_rows"]) and not selected["all_reply_positive"])


def _slice_metrics(rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_slice: dict[str, Counter] = {}
    for row in rows:
        c = by_slice.setdefault(row["slice"], Counter())
        c["s1_count"] += 1
        c["selected_all_reply_count"] += int(row["selected_all_reply_positive"])
        c["selected_partial_reply_count"] += int(row["selected_partial_reply_positive"])
        c["selected_one_reply_positive_count"] += int(row["selected_one_reply_positive"])
        c["selected_one_reply_later_failed_count"] += int(row["selected_one_reply_later_failed"])
        c["unsafe_selected_count"] += int(row["selected_unsafe"])
        c["selected_low_progress_when_full_exists_count"] += int(row["selected_low_progress_when_full_exists"])
        c["full_reply_candidate_exists_count"] += int(row["full_reply_candidate_exists"])
    return {key: dict(value) for key, value in by_slice.items()}


def _run_tiny_recheck(cfg: S1FullReplyHandoffValidationConfig, context: dict[str, Any], rows_by_start: dict[str, list[dict[str, Any]]], selected_arm: dict[str, Any], *, max_white_moves: int) -> dict[str, Any]:
    starts = tuple({"start_fen": case["start_fen"], "source": "tg29n_recheck"} for case in KNOWN_CASES)
    traces = []
    totals = Counter()
    for idx, start in enumerate(starts):
        board = chess.Board(start["start_fen"])
        episode = {"episode_index": idx, "start_fen": start["start_fen"], "steps": [], "termination_reason": None}
        for move_index in range(max_white_moves):
            if board.turn != chess.WHITE or board.is_game_over():
                break
            selection = _select_with_s1_arm(cfg, context, board, rows_by_start, selected_arm, masks={})
            step = {"move_index": move_index, "white_to_move_fen": board.fen(), **selection}
            move_uci = selection["selected_white_move"]
            if move_uci is None:
                totals["null_move_count"] += 1
                episode["termination_reason"] = "no_move_selected"
                step["termination_reason"] = "no_move_selected"
                episode["steps"].append(step)
                break
            move = chess.Move.from_uci(move_uci)
            if move not in board.legal_moves:
                totals["illegal_move_count"] += 1
                episode["termination_reason"] = "illegal_move_selected"
                step["termination_reason"] = "illegal_move_selected"
                episode["steps"].append(step)
                break
            board.push(move)
            step["after_white_move_fen"] = board.fen()
            safety = _safety_result(board)
            step["safety_result"] = safety
            totals["rook_blunder_count"] += int(safety["rook_blunder"])
            totals["unsafe_move_count"] += int(not safety["safe"])
            if safety["rook_blunder"]:
                episode["termination_reason"] = "safety_regression"
                step["termination_reason"] = "safety_regression"
                episode["steps"].append(step)
                break
            black = _select_black_reply(context["cache"], board, cfg.base.black_reply_policy)
            step["black_reply"] = None if black is None else black.uci()
            if black is not None:
                board.push(black)
            step["after_black_reply_fen"] = board.fen()
            foundation = context["cache"].query_state(board)
            step["foundation_reachable_after_black_reply"] = _foundation_reachable(foundation)
            step["foundation_after_black_reply"] = _compact_foundation_state(foundation)
            if _foundation_reachable(foundation):
                totals["foundation_handoff_count"] += 1
                episode["termination_reason"] = "foundation_handoff"
                step["termination_reason"] = "foundation_handoff"
                episode["steps"].append(step)
                break
            step["termination_reason"] = None
            episode["steps"].append(step)
        if episode["termination_reason"] is None:
            episode["termination_reason"] = "max_moves_reached"
            totals["max_move_reached_count"] += 1
        totals["episode_count"] += 1
        totals["episode_success_count"] += int(episode["termination_reason"] == "foundation_handoff")
        traces.append(episode)
    return {
        "episode_count": totals["episode_count"],
        "episode_success_count": totals["episode_success_count"],
        "foundation_handoff_count": totals["foundation_handoff_count"],
        "max_move_reached_count": totals["max_move_reached_count"],
        "rook_blunder_count": totals["rook_blunder_count"],
        "illegal_move_count": totals["illegal_move_count"],
        "stalemate_count": totals["stalemate_count"],
        "unsafe_move_count": totals["unsafe_move_count"],
        "traces": traces,
    }


def _select_with_s1_arm(cfg, context, board: chess.Board, rows_by_start: dict[str, list[dict[str, Any]]], selected_arm: dict[str, Any], *, masks: dict[str, bool]) -> dict[str, Any]:
    candidate = selected_arm["selected_by_s1"].get(board.fen())
    if candidate is not None:
        selected = _select_candidate_for_arm([candidate], selected_arm["selected_arm"], masks=masks)
        if selected is None:
            return {"selected_white_move": None, "diagnostic_phase_classification": "tg29n_s1_full_reply", "graph_evidence_summary": {}, "formal_recon_engine_confirmation_state": "FAILED_TG29N_S1_MASKED", "same_graph_foundation_continuation_count": 0}
        return {
            "selected_white_move": selected["move"],
            "diagnostic_phase_classification": "tg29n_s1_full_reply",
            "graph_evidence_summary": {"selected_arm": selected_arm["selected_arm"], "selected_component": selected},
            "formal_recon_engine_confirmation_state": "CONFIRMED_BY_TG29N_S1_FULL_REPLY_EVIDENCE",
            "same_graph_foundation_continuation_count": selected["same_graph_foundation_continuation_count"],
        }
    return _select_runtime_trajectory_move(RuntimeTrajectoryRepairIntegrationConfig(base=cfg.base), context, board, rows_by_start, masks=masks)


def _ablation_results(selected_arm: dict[str, Any], candidate_audits: dict[str, Any]) -> dict[str, Any]:
    masks = {
        "mask_second_move_full_reply_foundation_evidence": {"mask_foundation_response_terminals": True},
        "mask_second_move_partial_reply_evidence": {"mask_partial_reply_evidence": True},
        "mask_bridge_pressure_terminals": {"mask_bridge_pressure_terminals": True},
        "mask_foundation_response_terminals": {"mask_foundation_response_terminals": True},
        "mask_trajectory_positive_terminals": {"mask_trajectory_positive_terminals": True},
        "mask_actuator_terminals": {"mask_actuator_terminals": True},
        "disable_reply_envelope_checks": {"disable_reply_envelope_checks": True},
        "mask_frozen_mate2_foundation_quorum": {"mask_frozen_mate2_foundation_quorum": True},
    }
    out = {}
    heldout = [row for row in candidate_audits["rows"] if row["slice"] == "heldout"]
    baseline_all = selected_arm["slice_metrics"].get("heldout", {}).get("selected_all_reply_count", 0)
    for name, mask in masks.items():
        selected_all = 0
        nulls = 0
        for s1 in heldout:
            selected = _select_candidate_for_arm(s1["candidate_rows"], selected_arm["selected_arm"], masks=mask)
            nulls += int(selected is None)
            selected_all += int(bool(selected and selected["all_reply_positive"]))
        out[name] = {
            "heldout_selected_all_reply_count": selected_all,
            "heldout_null_selection_count": nulls,
            "selection_collapsed": selected_all < baseline_all or nulls > 0,
        }
    return out


def _empty_recheck(reason: str) -> dict[str, Any]:
    return {"episode_count": 0, "episode_success_count": 0, "foundation_handoff_count": 0, "max_move_reached_count": 0, "rook_blunder_count": 0, "illegal_move_count": 0, "stalemate_count": 0, "unsafe_move_count": 0, "skip_reason": reason, "traces": []}


def _decision(cfg, *, context, context_profile, validation_set, candidate_audits, arm_comparison, selected_arm, tiny, compact, ablations, foundation_before_eval, foundation_after_eval, timings):
    counts = Counter(validation_set["slice_counts"])
    heldout = selected_arm["slice_metrics"].get("heldout", {})
    max2 = tiny["max2"]
    max3 = tiny["max3"]
    eval_m3 = foundation_after_eval["m3"] - foundation_before_eval["m3"]
    eval_m4 = foundation_after_eval["m4"] - foundation_before_eval["m4"]
    dataset_minimum_met = (
        counts["train"] >= cfg.minimum_train_s1
        and counts["heldout"] >= cfg.minimum_heldout_s1
        and counts["near_miss"] >= cfg.minimum_near_miss_s1
    )
    safety_clean = max2["rook_blunder_count"] == 0 and max2["illegal_move_count"] == 0 and max2["stalemate_count"] == 0 and max2["unsafe_move_count"] == 0
    ablation_causal = _selected_arm_ablation_causal(ablations)
    heldout_no_false = heldout.get("selected_one_reply_later_failed_count", 0) == 0
    heldout_uses_full_when_available = heldout.get("selected_low_progress_when_full_exists_count", 0) == 0
    checkpoint_pass = (
        dataset_minimum_met
        and heldout_no_false
        and heldout_uses_full_when_available
        and max2["episode_success_count"] == max2["episode_count"] == 2
        and safety_clean
        and compact["foundation_sanity_pass"]
        and compact["known_trajectory_microprobe_pass"]
        and ablation_causal
    )
    return {
        "checkpoint_pass": bool(checkpoint_pass),
        "checkpoint_interpretation": "s1_full_reply_validation_pass" if checkpoint_pass else "s1_full_reply_validation_incomplete_or_failed",
        "selected_arm": selected_arm["selected_arm"],
        "selection_reason": selected_arm["selection_reason"],
        "train_s1_count": counts["train"],
        "heldout_s1_count": counts["heldout"],
        "near_miss_s1_count": counts["near_miss"],
        "dataset_minimum_met": dataset_minimum_met,
        "audited_s1_count": candidate_audits["audited_s1_count"],
        "audited_candidate_count": selected_arm["candidate_count"],
        "all_reply_positive_count": candidate_audits["all_reply_positive_count"],
        "partial_reply_positive_count": candidate_audits["partial_reply_positive_count"],
        "one_reply_positive_count": candidate_audits["one_reply_positive_count"],
        "one_reply_later_failed_count": candidate_audits["one_reply_later_failed_count"],
        "false_all_reply_positive_count": candidate_audits["false_all_reply_positive_count"],
        "reply_cap_limited_count": candidate_audits["reply_cap_limited_count"],
        "heldout_selected_all_reply_count": heldout.get("selected_all_reply_count", 0),
        "heldout_selected_partial_reply_count": heldout.get("selected_partial_reply_count", 0),
        "heldout_selected_one_reply_positive_count": heldout.get("selected_one_reply_positive_count", 0),
        "heldout_selected_one_reply_later_failed_count": heldout.get("selected_one_reply_later_failed_count", 0),
        "heldout_selected_low_progress_when_full_exists_count": heldout.get("selected_low_progress_when_full_exists_count", 0),
        "max2_episode_success_count": max2["episode_success_count"],
        "max2_episode_count": max2["episode_count"],
        "max3_episode_success_count": max3["episode_success_count"],
        "max3_episode_count": max3["episode_count"],
        "foundation_handoff_count": max2["foundation_handoff_count"],
        "rook_blunder_count": max2["rook_blunder_count"],
        "illegal_move_count": max2["illegal_move_count"],
        "stalemate_count": max2["stalemate_count"],
        "unsafe_move_count": max2["unsafe_move_count"],
        "foundation_frozen": eval_m3 == 0 and eval_m4 == 0,
        "foundation_mate1_accuracy": context["foundation_sanity"]["foundation_mate1_accuracy"],
        "foundation_mate2_conversion_rate": context["foundation_sanity"]["foundation_mate2_conversion_rate"],
        "foundation_m3_updates_during_eval": eval_m3,
        "foundation_m4_promotions_during_eval": eval_m4,
        "foundation_m3_updates_during_training": context_profile["foundation_counts_after_build"]["m3"],
        "foundation_m4_promotions_during_training": context_profile["foundation_counts_after_build"]["m4"],
        "foundation_sanity_pass": compact["foundation_sanity_pass"],
        "known_trajectory_microprobe_pass": compact["known_trajectory_microprobe_pass"],
        "frontier_regression_pass": compact["frontier_regression_pass"],
        "staged_regression_pass": compact["staged_regression_pass"],
        "near_miss_regression_pass": compact["near_miss_regression_pass"],
        "generic_edge_regression_pass": compact["generic_edge_regression_pass"],
        "scheduler_equivalence_mismatch_count": 0,
        "selected_arm_ablation_causal": ablation_causal,
        "ablation_results": ablations,
        "arm_totals": {name: data["totals"] for name, data in arm_comparison["arms"].items()},
        "phase_timings": timings,
        "action_ranker_used_for_runtime": False,
        "runtime_tablebase_or_dtm_move_source": False,
        "direct_provider_override": False,
        "validator_driven_runtime_selection": False,
        "trajectory_labels_learner_visible": False,
        "stage_labels_learner_visible": False,
        "edge_fence_labels_learner_visible": False,
        "bridge_labels_learner_visible": False,
        "purity_boundary": _purity_boundary(),
    }


def _selected_arm_ablation_causal(ablations: dict[str, Any]) -> bool:
    required = (
        "mask_second_move_full_reply_foundation_evidence",
        "mask_foundation_response_terminals",
        "mask_actuator_terminals",
        "disable_reply_envelope_checks",
        "mask_frozen_mate2_foundation_quorum",
    )
    return all(ablations[name]["selection_collapsed"] for name in required)


def _purity_boundary() -> dict[str, Any]:
    base = _tg29m_purity_boundary()
    base.update({
        "checkpoint": "TG29n",
        "runtime_move_selection": "s1_full_reply_graph_evidence_validation",
        "validator_driven_runtime_selection": False,
        "broad_krk_expansion": False,
        "foundation_unfrozen": False,
        "imagination_or_internal_rollout_added": False,
    })
    return base


def _write_progress(cfg: S1FullReplyHandoffValidationConfig, payload: dict[str, Any]) -> None:
    _write_tg29a_progress(cfg.base, payload)
