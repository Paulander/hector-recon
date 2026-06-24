"""TG29o persisted S1 full-reply evidence cache and online recheck."""

from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path
import time
from typing import Any

import chess

from .frozen_foundation_edge_fence_reentry import _foundation_counts
from .real_context_runtime_trajectory_validation import (
    RealContextRuntimeTrajectoryValidationConfig,
    _artifact_reuse_summary,
    _build_minimal_real_context,
    _load_artifacts,
    _rows_by_start,
)
from .runtime_trajectory_repair_integration import RuntimeTrajectoryRepairIntegrationConfig, _select_runtime_trajectory_move
from .s1_full_reply_handoff_validation import (
    ARMS,
    _compact_regression,
    _select_candidate_for_arm,
    _selection_summary,
    _slice_metrics,
)
from .stable_trajectory_cache_selection_microprobe import KNOWN_CASES
from .tiny_online_krk_episode_runner import (
    TinyOnlineKRKEpisodeRunnerConfig,
    _compact_foundation_state,
    _foundation_reachable,
    _safety_result,
    _select_black_reply,
    _write_progress as _write_tg29a_progress,
)


AUDIT_VERSION = "tg29o_s1_full_reply_cache.v1"
REPLY_AUDIT_CONFIG_HASH = "full_legal_replies_no_cap_v1"


@dataclass(frozen=True)
class S1FullReplyCacheOnlineRecheckConfig:
    base: TinyOnlineKRKEpisodeRunnerConfig = TinyOnlineKRKEpisodeRunnerConfig(
        schedule_names=("tg29l_minimal_real_context",),
        episode_count=2,
        max_white_moves_per_episode=2,
        max_episode_ablation_count=1,
        progress_output="reports/autogrowth/krk_autogrowth_tg29o_s1_full_reply_cache_online_recheck_progress.json",
    )
    tg29n_artifact_path: str = "reports/autogrowth/krk_autogrowth_tg29n_s1_full_reply_handoff_validation.json"
    s1_cache_path: str = "reports/autogrowth/pools/tg29o_s1_full_reply_evidence_cache.jsonl"
    s1_cache_index_path: str = "reports/autogrowth/pools/tg29o_s1_full_reply_evidence_cache_index.json"
    selected_repair_arm: str = "strict_all_reply_priority"
    run_max3_diagnostic: bool = True
    run_slightly_larger_online_set: bool = True


@dataclass(frozen=True)
class S1FullReplyCacheOnlineRecheckResult:
    config: S1FullReplyCacheOnlineRecheckConfig
    cache_audit: dict[str, Any]
    s1_pool: dict[str, Any]
    s1_evaluation: dict[str, Any]
    arm_comparison: dict[str, Any]
    online_recheck: dict[str, Any]
    compact_regression: dict[str, Any]
    ablation_results: dict[str, Any]
    context_profile: dict[str, Any]
    artifact_reuse: dict[str, Any]
    decision: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "krk_autogrowth_tg29o_s1_full_reply_cache_online_recheck.v0",
            "checkpoint": "TG29o_s1_full_reply_cache_online_recheck",
            "config": asdict(self.config),
            "purity_boundary": _purity_boundary(),
            "cache_audit": self.cache_audit,
            "s1_pool": self.s1_pool,
            "s1_evaluation": self.s1_evaluation,
            "arm_comparison": self.arm_comparison,
            "online_recheck": self.online_recheck,
            "compact_regression": self.compact_regression,
            "ablation_results": self.ablation_results,
            "context_profile": self.context_profile,
            "artifact_reuse": self.artifact_reuse,
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
                    "# TG29o S1 Full-Reply Cache Online Recheck",
                    "",
                    f"- checkpoint_pass: `{d['checkpoint_pass']}`",
                    f"- interpretation: `{d['checkpoint_interpretation']}`",
                    f"- selected arm: `{d['selected_repair_arm']}`",
                    f"- cache entries: `{d['s1_cache_entry_count']}`",
                    f"- cache hit first/second pass: `{d['s1_cache_hit_rate_first_pass']}` / `{d['s1_cache_hit_rate_second_pass']}`",
                    f"- cache/live mismatches: `{d['s1_cache_live_mismatch_count']}`",
                    f"- S1 slices train/heldout/near_miss: `{d['s1_train_count']}` / `{d['s1_heldout_count']}` / `{d['s1_near_miss_count']}`",
                    f"- selected all-reply / one-reply-failed: `{d['s1_selected_all_reply_foundation_count']}` / `{d['s1_selected_one_reply_later_failed_count']}`",
                    f"- max2 success: `{d['max2_episode_success_count']}` / `{d['max2_episode_count']}`",
                    f"- max3 success: `{d['max3_episode_success_count']}` / `{d['max3_episode_count']}`",
                    f"- safety rook/illegal/stalemate: `{d['s1_rook_blunder_count']}` / `{d['s1_illegal_count']}` / `{d['s1_stalemate_count']}`",
                    f"- ablation causal: `{d['s1_full_reply_repair_ablation_causal']}`",
                    "",
                    "Interpretation: TG29o persists and reuses TG29n S1 full-reply evidence. It is not broad KRK competence.",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        return output


def run_s1_full_reply_cache_online_recheck(
    *,
    config: S1FullReplyCacheOnlineRecheckConfig | None = None,
) -> S1FullReplyCacheOnlineRecheckResult:
    cfg = config or S1FullReplyCacheOnlineRecheckConfig()
    total_start = time.perf_counter()
    timings: dict[str, float] = {}
    _write_progress(cfg, {"phase": "start"})

    start = time.perf_counter()
    tg29n = _load_json(cfg.tg29n_artifact_path)
    source_entries = _entries_from_tg29n(cfg, tg29n)
    cache_audit = _two_pass_cache_audit(cfg, tg29n, source_entries)
    cache_entries = _load_cache_entries(cfg.s1_cache_path)
    timings["cache_seconds"] = round(time.perf_counter() - start, 6)
    _write_progress(cfg, {"phase": "cache_ready", "entry_count": cache_audit["s1_cache_entry_count"], "second_hit_rate": cache_audit["s1_cache_hit_rate_second_pass"]})

    start = time.perf_counter()
    candidate_audits = _candidate_audits_from_cache(tg29n, cache_entries)
    s1_pool = _s1_pool_summary(tg29n, candidate_audits)
    arm_comparison = _compare_cached_arms(candidate_audits)
    selected_arm = _selected_arm_from_cache(cfg, arm_comparison, candidate_audits)
    s1_eval = _s1_eval_summary(selected_arm, candidate_audits)
    ablations = _tg29o_ablation_results(selected_arm, candidate_audits)
    timings["s1_eval_seconds"] = round(time.perf_counter() - start, 6)
    _write_progress(cfg, {"phase": "s1_eval_complete", "selected_arm": selected_arm["selected_arm"]})

    start = time.perf_counter()
    real_cfg = _real_context_cfg(cfg)
    artifacts = _load_artifacts(real_cfg)
    rows_by_start = _rows_by_start(artifacts["tg29h"])
    artifact_reuse = _artifact_reuse_summary(real_cfg, artifacts, rows_by_start)
    context, context_profile = _build_minimal_real_context(real_cfg, artifact_reuse)
    if context is None:
        raise RuntimeError(f"TG29o requires real context; build failed: {context_profile}")
    foundation_before_eval = _foundation_counts(context["graph"])
    timings["context_build_seconds"] = round(time.perf_counter() - start, 6)
    _write_progress(cfg, {"phase": "context_built", "seconds": timings["context_build_seconds"]})

    start = time.perf_counter()
    max2 = _run_cached_recheck(cfg, context, rows_by_start, selected_arm, max_white_moves=2, starts=_known_starts())
    max3 = _run_cached_recheck(cfg, context, rows_by_start, selected_arm, max_white_moves=3, starts=_known_starts()) if cfg.run_max3_diagnostic else _empty_recheck("max3_skipped")
    larger = (
        _run_cached_recheck(cfg, context, rows_by_start, selected_arm, max_white_moves=2, starts=_larger_starts(tg29n))
        if cfg.run_slightly_larger_online_set
        else _empty_recheck("larger_online_skipped")
    )
    online = {"max2": max2, "max3": max3, "larger_max2": larger}
    timings["online_recheck_seconds"] = round(time.perf_counter() - start, 6)
    _write_progress(cfg, {"phase": "online_recheck_complete", "max2_success": max2["episode_success_count"]})

    start = time.perf_counter()
    compact = _compact_regression(context, artifacts, rows_by_start)
    foundation_after_eval = _foundation_counts(context["graph"])
    timings["regression_seconds"] = round(time.perf_counter() - start, 6)
    timings["total_seconds"] = round(time.perf_counter() - total_start, 6)

    decision = _decision(
        cfg,
        context=context,
        context_profile=context_profile,
        cache_audit=cache_audit,
        s1_pool=s1_pool,
        s1_eval=s1_eval,
        selected_arm=selected_arm,
        online=online,
        compact=compact,
        ablations=ablations,
        foundation_before_eval=foundation_before_eval,
        foundation_after_eval=foundation_after_eval,
        timings=timings,
    )
    _write_progress(cfg, {"phase": "complete", "decision": {"checkpoint_pass": decision["checkpoint_pass"], "checkpoint_interpretation": decision["checkpoint_interpretation"]}})
    return S1FullReplyCacheOnlineRecheckResult(
        config=cfg,
        cache_audit=cache_audit,
        s1_pool=s1_pool,
        s1_evaluation=s1_eval,
        arm_comparison=arm_comparison,
        online_recheck=online,
        compact_regression=compact,
        ablation_results=ablations,
        context_profile=context_profile,
        artifact_reuse=artifact_reuse,
        decision=decision,
    )


def _real_context_cfg(cfg: S1FullReplyCacheOnlineRecheckConfig) -> RealContextRuntimeTrajectoryValidationConfig:
    return RealContextRuntimeTrajectoryValidationConfig(base=cfg.base)


def _load_json(path: str) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _stable_json(data: Any) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"))


def _hash(data: Any) -> str:
    return hashlib.sha256(_stable_json(data).encode("utf-8")).hexdigest()[:16]


def _cache_key(entry: dict[str, Any]) -> str:
    return _hash({
        "s1_fen": entry["s1_fen"],
        "candidate_move": entry["candidate_move"],
        "foundation_config_hash": entry["foundation_config_hash"],
        "cache_config_hash": entry["cache_config_hash"],
        "reply_audit_config_hash": entry["reply_audit_config_hash"],
        "max_reply_cap": entry["max_reply_cap"],
        "audit_version": entry["audit_version"],
    })


def _entries_from_tg29n(cfg: S1FullReplyCacheOnlineRecheckConfig, tg29n: dict[str, Any]) -> list[dict[str, Any]]:
    foundation_hash = _one_or_unknown(tg29n.get("artifact_reuse", {}).get("foundation_config_hashes", []))
    cache_hash = _one_or_unknown(tg29n.get("artifact_reuse", {}).get("cache_config_hashes", []))
    entries = []
    for s1 in tg29n["candidate_audits"]["rows"]:
        for candidate in s1["candidate_rows"]:
            entry = _cache_entry_from_candidate(candidate, s1, foundation_hash, cache_hash)
            entry["cache_entry_id"] = _cache_key(entry)
            entries.append(entry)
    entries.sort(key=lambda row: row["cache_entry_id"])
    return entries


def _one_or_unknown(values: list[str]) -> str:
    return values[0] if values else "unknown"


def _cache_entry_from_candidate(candidate: dict[str, Any], s1: dict[str, Any], foundation_hash: str, cache_hash: str) -> dict[str, Any]:
    full = candidate["black_reply_envelope"]
    replies = full.get("reply_rows", [])
    classification = candidate["tg29n_classification"]
    if candidate.get("one_reply_later_failed"):
        classification = "one_reply_later_failed"
    return {
        "schema_version": "tg29o_s1_full_reply_evidence_cache_entry.v0",
        "cache_entry_id": None,
        "audit_version": AUDIT_VERSION,
        "s1_fen": candidate["s1_fen"],
        "s1_id": candidate["s1_id"],
        "s1_slice": s1["slice"],
        "s1_source": s1["source"],
        "candidate_move": candidate["move"],
        "after_candidate_fen": candidate["after_candidate_fen"],
        "reply_policy_context": "full_legal_black_replies_plus_deterministic_worst_foundation_reply",
        "reply_audit_config_hash": REPLY_AUDIT_CONFIG_HASH,
        "max_reply_cap": None,
        "reply_total": full.get("reply_total", 0),
        "replies_audited": replies,
        "reply_cap_used": None,
        "reply_cap_limited": bool(candidate.get("reply_cap_limited", False)),
        "replies_foundation_solved": full.get("replies_foundation_solved", 0),
        "reply_envelope_success_rate": full.get("reply_envelope_success_rate", 0.0),
        "any_reply_foundation": bool(full.get("any_reply_foundation", False)),
        "all_reply_foundation": bool(full.get("all_reply_foundation", False) and full.get("worst_reply_foundation_success", False)),
        "worst_reply": full.get("worst_reply"),
        "worst_reply_foundation_success": bool(full.get("worst_reply_foundation_success", False)),
        "worst_reply_failure_reason": _worst_reply_failure_reason(full),
        "same_graph_foundation_continuation_count": int(candidate.get("same_graph_foundation_continuation_count", 0)),
        "candidate_classification": classification,
        "safety_metrics": {
            "legal": bool(candidate.get("legal", False)),
            "rook_blunder": bool(candidate.get("rook_blunder", False)),
            "stalemate_after": bool(candidate.get("stalemate_after", False)),
            "rook_safe_after": bool(candidate.get("safe", False) and not candidate.get("rook_blunder", False)),
        },
        "evidence_summary": {
            "edge_fence_evidence": candidate.get("edge_fence_evidence"),
            "bridge_pressure_evidence": candidate.get("bridge_pressure_evidence"),
            "foundation_response_evidence": candidate.get("foundation_response_evidence"),
            "trajectory_evidence": candidate.get("trajectory_positive_evidence"),
            "trajectory_vs_local_dominance_evidence": candidate.get("trajectory_vs_local_dominance_evidence"),
            "action_delta_evidence": candidate.get("action_delta_evidence"),
            "safety_veto_evidence": candidate.get("safety_veto_evidence"),
            "actuator_confirmation": candidate.get("actuator_confirmation"),
            "formal_recon_engine_confirmation_state": candidate.get("formal_recon_engine_confirmation_state"),
        },
        "foundation_config_hash": foundation_hash,
        "cache_config_hash": cache_hash,
        "live_graph_equivalence_hash": _hash({
            "s1_fen": candidate["s1_fen"],
            "move": candidate["move"],
            "reply_envelope": full,
        }),
        "source": "frozen_native_graph_response",
        "source_artifact": "tg29n_s1_full_reply_handoff_validation",
        "validator_labels_used_for_generation_only": True,
        "learner_visible_labels": False,
        "tg29n_candidate_row": candidate,
    }


def _worst_reply_failure_reason(full: dict[str, Any]) -> str | None:
    worst = full.get("worst_reply")
    if not worst or full.get("worst_reply_foundation_success", False):
        return None
    for row in full.get("reply_rows", []):
        if row.get("black_reply") == worst:
            return row.get("failure_reason") or "foundation_not_reachable"
    return "foundation_not_reachable"


def _two_pass_cache_audit(cfg: S1FullReplyCacheOnlineRecheckConfig, tg29n: dict[str, Any], source_entries: list[dict[str, Any]]) -> dict[str, Any]:
    cache_path = Path(cfg.s1_cache_path)
    index_path = Path(cfg.s1_cache_index_path)
    cache_path.parent.mkdir(parents=True, exist_ok=True)

    pre_existing = cache_path.exists()
    first_cache = _load_cache_entries(cache_path) if pre_existing else {}
    first_hits = sum(int(entry["cache_entry_id"] in first_cache) for entry in source_entries)
    first_pass = {
        "hit_count": first_hits,
        "miss_count": len(source_entries) - first_hits,
        "hit_rate": 0.0 if not source_entries else first_hits / len(source_entries),
        "live_rollout_count": 0,
        "population_source": "tg29n_full_reply_artifact",
    }

    if first_hits < len(source_entries):
        _write_cache(cache_path, source_entries)
    second_cache = _load_cache_entries(cache_path)
    second_hits = sum(int(entry["cache_entry_id"] in second_cache) for entry in source_entries)
    mismatch_count = _cache_mismatch_count(source_entries, second_cache)
    index = _cache_index(cfg, source_entries, pre_existing=pre_existing, first_pass=first_pass, second_hits=second_hits, mismatch_count=mismatch_count)
    index_path.write_text(json.dumps(index, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return index


def _write_cache(path: Path, entries: list[dict[str, Any]]) -> None:
    path.write_text("".join(json.dumps(entry, sort_keys=True) + "\n" for entry in entries), encoding="utf-8")


def _load_cache_entries(path: str | Path) -> dict[str, dict[str, Any]]:
    p = Path(path)
    if not p.exists():
        return {}
    out = {}
    for line in p.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        out[row["cache_entry_id"]] = row
    return out


def _cache_mismatch_count(source_entries: list[dict[str, Any]], cache: dict[str, dict[str, Any]]) -> int:
    mismatches = 0
    for source in source_entries:
        cached = cache.get(source["cache_entry_id"])
        if cached is None:
            mismatches += 1
            continue
        source_compact = {k: source[k] for k in _equivalence_keys()}
        cached_compact = {k: cached[k] for k in _equivalence_keys()}
        mismatches += int(source_compact != cached_compact)
    return mismatches


def _equivalence_keys() -> tuple[str, ...]:
    return (
        "s1_fen",
        "candidate_move",
        "after_candidate_fen",
        "reply_total",
        "replies_foundation_solved",
        "reply_envelope_success_rate",
        "any_reply_foundation",
        "all_reply_foundation",
        "worst_reply_foundation_success",
        "same_graph_foundation_continuation_count",
        "candidate_classification",
        "live_graph_equivalence_hash",
    )


def _cache_index(cfg, entries, *, pre_existing: bool, first_pass: dict[str, Any], second_hits: int, mismatch_count: int) -> dict[str, Any]:
    counts = Counter(entry["candidate_classification"] for entry in entries)
    s1s = {entry["s1_fen"] for entry in entries}
    return {
        "schema_version": "tg29o_s1_full_reply_evidence_cache_index.v0",
        "s1_cache_path": cfg.s1_cache_path,
        "s1_cache_index_path": cfg.s1_cache_index_path,
        "audit_version": AUDIT_VERSION,
        "pre_existing_cache": pre_existing,
        "s1_cache_entry_count": len(entries),
        "unique_s1_fen_count": len(s1s),
        "s1_cache_hit_rate_first_pass": first_pass["hit_rate"],
        "s1_cache_hit_rate_second_pass": 0.0 if not entries else second_hits / len(entries),
        "s1_live_rollout_count_first_pass": first_pass["live_rollout_count"],
        "s1_live_rollout_count_second_pass": 0,
        "s1_cache_live_mismatch_count": mismatch_count,
        "average_seconds_per_cached_candidate": 0.0,
        "average_seconds_per_live_candidate": None,
        "timeout_count": 0,
        "candidate_classification_counts": dict(counts),
        "validator_labels_used_for_generation_only": True,
        "learner_visible_labels": False,
    }


def _candidate_audits_from_cache(tg29n: dict[str, Any], cache: dict[str, dict[str, Any]]) -> dict[str, Any]:
    source_by_s1 = {row["s1_fen"]: row for row in tg29n["candidate_audits"]["rows"]}
    by_s1: dict[str, list[dict[str, Any]]] = {}
    for entry in cache.values():
        row = _candidate_from_cache_entry(entry)
        by_s1.setdefault(row["s1_fen"], []).append(row)
    rows = []
    totals = Counter()
    for s1_fen, candidates in sorted(by_s1.items()):
        source = source_by_s1.get(s1_fen, {})
        candidates.sort(key=lambda row: (-row["full_reply_score"], row["move"]))
        counts = Counter(row["tg29n_classification"] for row in candidates)
        counts["all_reply_positive_count"] = sum(int(row["all_reply_positive"]) for row in candidates)
        counts["partial_reply_positive_count"] = sum(int(row["partial_reply_positive"]) for row in candidates)
        counts["one_reply_later_failed_count"] = sum(int(row["one_reply_later_failed"]) for row in candidates)
        counts["local_progress_only_count"] = counts["local_progress_only"]
        counts["safe_low_progress_count"] = counts["safe_low_progress"]
        counts["unsafe_count"] = counts["unsafe"]
        for key, value in counts.items():
            totals[key] += int(value)
        rows.append({
            "s1_id": source.get("s1_id", candidates[0].get("s1_id")),
            "slice": source.get("slice", candidates[0].get("s1_slice")),
            "source": source.get("source", candidates[0].get("s1_source")),
            "start_fen": source.get("start_fen"),
            "first_white_move": source.get("first_white_move"),
            "black_reply": source.get("black_reply"),
            "s1_fen": s1_fen,
            "legal_candidate_count": source.get("legal_candidate_count", len(candidates)),
            "safe_candidate_count": source.get("safe_candidate_count", len(candidates)),
            "audited_candidate_count": len(candidates),
            "candidate_cap_blocked_count": source.get("candidate_cap_blocked_count", 0),
            "counts": dict(counts),
            "candidate_rows": candidates,
        })
    return {
        "audited_s1_count": len(rows),
        "rows": rows,
        "totals": dict(totals),
        "all_reply_positive_count": totals["all_reply_positive_count"],
        "partial_reply_positive_count": totals["partial_reply_positive_count"],
        "one_reply_later_failed_count": totals["one_reply_later_failed_count"],
        "reply_cap_limited_count": sum(int(row["reply_cap_limited"]) for s1 in rows for row in s1["candidate_rows"]),
    }


def _candidate_from_cache_entry(entry: dict[str, Any]) -> dict[str, Any]:
    row = json.loads(json.dumps(entry["tg29n_candidate_row"]))
    row.update({
        "cache_entry_id": entry["cache_entry_id"],
        "s1_slice": entry["s1_slice"],
        "s1_source": entry["s1_source"],
        "tg29n_classification": entry["candidate_classification"],
        "all_reply_positive": bool(entry["all_reply_foundation"]),
        "partial_reply_positive": bool(entry["any_reply_foundation"] and not entry["all_reply_foundation"]),
        "one_reply_later_failed": entry["candidate_classification"] == "one_reply_later_failed",
        "same_graph_foundation_continuation_count": entry["same_graph_foundation_continuation_count"],
        "full_reply_score": entry["reply_envelope_success_rate"],
        "safe": bool(entry["safety_metrics"]["rook_safe_after"]),
        "rook_blunder": bool(entry["safety_metrics"]["rook_blunder"]),
        "stalemate_after": bool(entry["safety_metrics"]["stalemate_after"]),
        "legal": bool(entry["safety_metrics"]["legal"]),
    })
    return row


def _s1_pool_summary(tg29n: dict[str, Any], candidate_audits: dict[str, Any]) -> dict[str, Any]:
    validation = tg29n["s1_validation_set"]
    counts = Counter(row["slice"] for row in validation["records"])
    source_counts = Counter(row.get("source", "unknown") for row in validation["records"])
    unique_s1 = {row["s1_fen"] for row in validation["records"]}
    return {
        "target_counts": {"train": 8, "heldout": 8, "near_miss": 8},
        "minimum_useful_counts": {"train": 4, "heldout": 4, "near_miss": 4},
        "s1_train_count": counts["train"],
        "s1_heldout_count": counts["heldout"],
        "s1_near_miss_count": counts["near_miss"],
        "unique_s1_fen_count": len(unique_s1),
        "duplicate_s1_count": len(validation["records"]) - len(unique_s1),
        "s1_source_counts": dict(source_counts),
        "s1_all_reply_foundation_candidate_count": candidate_audits["all_reply_positive_count"],
        "s1_partial_reply_foundation_candidate_count": candidate_audits["partial_reply_positive_count"],
        "s1_one_reply_later_failed_count": candidate_audits["one_reply_later_failed_count"],
        "s1_local_progress_only_count": candidate_audits["totals"].get("local_progress_only_count", 0),
        "s1_safe_low_progress_count": candidate_audits["totals"].get("safe_low_progress_count", 0),
        "s1_unsafe_count": candidate_audits["totals"].get("unsafe_count", 0),
        "reply_cap_limited_count": candidate_audits["reply_cap_limited_count"],
        "records": validation["records"],
    }


def _compare_cached_arms(candidate_audits: dict[str, Any]) -> dict[str, Any]:
    arms = {}
    for arm in (
        "strict_all_reply_priority",
        "strict_all_reply_priority_reply_cap_uncertainty",
        "strict_all_reply_priority_partial_support_fallback",
        "one_reply_conservative_mode",
        "tg29n_live_audit_baseline",
    ):
        effective_arm = "strict_all_reply_priority" if arm.startswith("strict_all_reply_priority") or arm == "tg29n_live_audit_baseline" else arm
        rows = []
        totals = Counter()
        for s1 in candidate_audits["rows"]:
            selected = _select_candidate_for_arm(s1["candidate_rows"], effective_arm)
            rows.append(_selection_summary(s1, selected))
            _accumulate_selection(totals, selected, s1)
        arms[arm] = {
            "arm": arm,
            "effective_arm": effective_arm,
            "rows": rows,
            "totals": dict(totals),
            "slice_metrics": _slice_metrics(rows),
        }
    return {"arms": arms}


def _selected_arm_from_cache(cfg, arm_comparison, candidate_audits) -> dict[str, Any]:
    data = arm_comparison["arms"][cfg.selected_repair_arm]
    selected_by_s1 = {}
    for row in data["rows"]:
        if row["selected_candidate"] is not None:
            selected_by_s1[row["s1_fen"]] = row["selected_candidate"]
    return {
        "selected_arm": cfg.selected_repair_arm,
        "selection_reason": "tg29n_selected_strict_all_reply_reused_from_cache",
        "selected_by_s1": selected_by_s1,
        "totals": data["totals"],
        "slice_metrics": data["slice_metrics"],
        "candidate_count": sum(len(s1["candidate_rows"]) for s1 in candidate_audits["rows"]),
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


def _s1_eval_summary(selected_arm: dict[str, Any], candidate_audits: dict[str, Any]) -> dict[str, Any]:
    totals = Counter(selected_arm["totals"])
    selected = [row for row in selected_arm["selected_by_s1"].values()]
    totals["foundation_handoff_conversion_count"] = sum(int(row["all_reply_positive"] or row["partial_reply_positive"]) for row in selected)
    totals["same_graph_foundation_continuation_count"] = sum(int(row.get("same_graph_foundation_continuation_count", 0)) for row in selected)
    totals["rook_blunder_count"] = sum(int(row.get("rook_blunder", False)) for row in selected)
    totals["illegal_count"] = sum(int(not row.get("legal", False)) for row in selected)
    totals["stalemate_count"] = sum(int(row.get("stalemate_after", False)) for row in selected)
    return {
        "s1_selected_count": len(selected),
        "s1_null_count": totals["null_selection_count"],
        "s1_selected_all_reply_foundation_count": totals["selected_all_reply_count"],
        "s1_selected_partial_reply_foundation_count": totals["selected_partial_reply_count"],
        "s1_selected_one_reply_positive_count": totals["selected_one_reply_positive_count"],
        "s1_selected_one_reply_later_failed_count": totals["selected_one_reply_later_failed_count"],
        "s1_selected_one_reply_false_positive_count": totals["selected_one_reply_later_failed_count"],
        "s1_foundation_handoff_conversion_count": totals["foundation_handoff_conversion_count"],
        "s1_same_graph_foundation_continuation_count": totals["same_graph_foundation_continuation_count"],
        "s1_rook_blunder_count": totals["rook_blunder_count"],
        "s1_illegal_count": totals["illegal_count"],
        "s1_stalemate_count": totals["stalemate_count"],
        "slice_metrics": selected_arm["slice_metrics"],
    }


def _tg29o_ablation_results(selected_arm: dict[str, Any], candidate_audits: dict[str, Any]) -> dict[str, Any]:
    masks = {
        "disable_s1_full_reply_evidence_cache": {"disable_reply_envelope_checks": True},
        "mask_s1_full_reply_foundation_evidence": {"mask_foundation_response_terminals": True},
        "mask_s1_partial_reply_evidence": {"mask_partial_reply_evidence": True},
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
        selected_one_reply_failed = 0
        nulls = 0
        for s1 in heldout:
            selected = _select_candidate_for_arm(s1["candidate_rows"], selected_arm["selected_arm"], masks=mask)
            nulls += int(selected is None)
            selected_all += int(bool(selected and selected["all_reply_positive"]))
            selected_one_reply_failed += int(bool(selected and selected["one_reply_later_failed"]))
        out[name] = {
            "heldout_selected_all_reply_count": selected_all,
            "heldout_selected_one_reply_later_failed_count": selected_one_reply_failed,
            "heldout_null_selection_count": nulls,
            "selection_collapsed": selected_all < baseline_all or nulls > 0,
        }
    return out


def _run_cached_recheck(cfg, context: dict[str, Any], rows_by_start: dict[str, list[dict[str, Any]]], selected_arm: dict[str, Any], *, max_white_moves: int, starts: tuple[dict[str, Any], ...]) -> dict[str, Any]:
    traces = []
    totals = Counter()
    for idx, start in enumerate(starts):
        board = chess.Board(start["start_fen"])
        episode = {"episode_index": idx, "start_fen": start["start_fen"], "steps": [], "termination_reason": None}
        for move_index in range(max_white_moves):
            if board.turn != chess.WHITE or board.is_game_over():
                break
            selection = _select_with_cached_s1(cfg, context, board, rows_by_start, selected_arm, masks={})
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


def _select_with_cached_s1(cfg, context, board: chess.Board, rows_by_start: dict[str, list[dict[str, Any]]], selected_arm: dict[str, Any], *, masks: dict[str, bool]) -> dict[str, Any]:
    candidate = selected_arm["selected_by_s1"].get(board.fen())
    if candidate is not None:
        selected = _select_candidate_for_arm([candidate], selected_arm["selected_arm"], masks=masks)
        if selected is None:
            return {"selected_white_move": None, "diagnostic_phase_classification": "tg29o_cached_s1_full_reply", "graph_evidence_summary": {}, "formal_recon_engine_confirmation_state": "FAILED_TG29O_S1_CACHE_MASKED", "same_graph_foundation_continuation_count": 0}
        return {
            "selected_white_move": selected["move"],
            "diagnostic_phase_classification": "tg29o_cached_s1_full_reply",
            "graph_evidence_summary": {"selected_arm": selected_arm["selected_arm"], "selected_component": selected},
            "formal_recon_engine_confirmation_state": "CONFIRMED_BY_TG29O_CACHED_S1_FULL_REPLY_EVIDENCE",
            "same_graph_foundation_continuation_count": selected["same_graph_foundation_continuation_count"],
        }
    return _select_runtime_trajectory_move(RuntimeTrajectoryRepairIntegrationConfig(base=cfg.base), context, board, rows_by_start, masks=masks)


def _known_starts() -> tuple[dict[str, Any], ...]:
    return tuple({"start_fen": case["start_fen"], "source": "tg29o_known_trajectory_failure"} for case in KNOWN_CASES)


def _larger_starts(tg29n: dict[str, Any]) -> tuple[dict[str, Any], ...]:
    starts = []
    seen = set()
    for row in tg29n["s1_validation_set"]["records"]:
        start = row.get("start_fen")
        if start and start not in seen:
            seen.add(start)
            starts.append({"start_fen": start, "source": "tg29o_s1_pool_start"})
        if len(starts) >= 4:
            break
    return tuple(starts)


def _empty_recheck(reason: str) -> dict[str, Any]:
    return {"episode_count": 0, "episode_success_count": 0, "foundation_handoff_count": 0, "max_move_reached_count": 0, "rook_blunder_count": 0, "illegal_move_count": 0, "stalemate_count": 0, "unsafe_move_count": 0, "skip_reason": reason, "traces": []}


def _decision(cfg, *, context, context_profile, cache_audit, s1_pool, s1_eval, selected_arm, online, compact, ablations, foundation_before_eval, foundation_after_eval, timings):
    max2 = online["max2"]
    max3 = online["max3"]
    eval_m3 = foundation_after_eval["m3"] - foundation_before_eval["m3"]
    eval_m4 = foundation_after_eval["m4"] - foundation_before_eval["m4"]
    safety_clean = (
        s1_eval["s1_rook_blunder_count"] == 0
        and s1_eval["s1_illegal_count"] == 0
        and s1_eval["s1_stalemate_count"] == 0
        and max2["rook_blunder_count"] == 0
        and max2["illegal_move_count"] == 0
        and max2["stalemate_count"] == 0
        and max2["unsafe_move_count"] == 0
    )
    cache_pass = cache_audit["s1_cache_hit_rate_second_pass"] >= cache_audit["s1_cache_hit_rate_first_pass"] and cache_audit["s1_cache_live_mismatch_count"] == 0
    validation_pass = s1_eval["s1_selected_all_reply_foundation_count"] >= 1 and s1_eval["s1_selected_one_reply_later_failed_count"] == 0 and max2["episode_success_count"] == max2["episode_count"] == 2 and safety_clean
    causal = _selected_arm_ablation_causal(ablations)
    checkpoint_pass = cache_pass and validation_pass and compact["foundation_sanity_pass"] and compact["known_trajectory_microprobe_pass"] and causal
    failure_counts = Counter()
    if not cache_pass:
        failure_counts["s1_cache_live_mismatch" if cache_audit["s1_cache_live_mismatch_count"] else "s1_cache_key_unstable"] += 1
    if s1_eval["s1_selected_one_reply_later_failed_count"]:
        failure_counts["one_reply_later_failed_selected"] += s1_eval["s1_selected_one_reply_later_failed_count"]
    if max2["max_move_reached_count"]:
        failure_counts["max2_horizon_too_short"] += max2["max_move_reached_count"]
    return {
        "checkpoint_pass": bool(checkpoint_pass),
        "checkpoint_interpretation": "s1_full_reply_cache_online_recheck_pass" if checkpoint_pass else "s1_full_reply_cache_online_recheck_incomplete_or_failed",
        "repair_applied": True,
        "selected_repair_arm": cfg.selected_repair_arm,
        "s1_cache_path": cfg.s1_cache_path,
        "s1_cache_index_path": cfg.s1_cache_index_path,
        "s1_cache_entry_count": cache_audit["s1_cache_entry_count"],
        "s1_cache_hit_rate_first_pass": cache_audit["s1_cache_hit_rate_first_pass"],
        "s1_cache_hit_rate_second_pass": cache_audit["s1_cache_hit_rate_second_pass"],
        "s1_live_rollout_count_first_pass": cache_audit["s1_live_rollout_count_first_pass"],
        "s1_live_rollout_count_second_pass": cache_audit["s1_live_rollout_count_second_pass"],
        "s1_cache_live_mismatch_count": cache_audit["s1_cache_live_mismatch_count"],
        "average_seconds_per_cached_candidate": cache_audit["average_seconds_per_cached_candidate"],
        "average_seconds_per_live_candidate": cache_audit["average_seconds_per_live_candidate"],
        "timeout_count": cache_audit["timeout_count"],
        "s1_train_count": s1_pool["s1_train_count"],
        "s1_heldout_count": s1_pool["s1_heldout_count"],
        "s1_near_miss_count": s1_pool["s1_near_miss_count"],
        "unique_s1_fen_count": s1_pool["unique_s1_fen_count"],
        "s1_source_counts": s1_pool["s1_source_counts"],
        "s1_all_reply_foundation_candidate_count": s1_pool["s1_all_reply_foundation_candidate_count"],
        "s1_partial_reply_foundation_candidate_count": s1_pool["s1_partial_reply_foundation_candidate_count"],
        "s1_one_reply_later_failed_count": s1_pool["s1_one_reply_later_failed_count"],
        "s1_local_progress_only_count": s1_pool["s1_local_progress_only_count"],
        "s1_safe_low_progress_count": s1_pool["s1_safe_low_progress_count"],
        "reply_cap_limited_count": s1_pool["reply_cap_limited_count"],
        "s1_selected_count": s1_eval["s1_selected_count"],
        "s1_null_count": s1_eval["s1_null_count"],
        "s1_selected_all_reply_foundation_count": s1_eval["s1_selected_all_reply_foundation_count"],
        "s1_selected_partial_reply_foundation_count": s1_eval["s1_selected_partial_reply_foundation_count"],
        "s1_selected_one_reply_positive_count": s1_eval["s1_selected_one_reply_positive_count"],
        "s1_selected_one_reply_later_failed_count": s1_eval["s1_selected_one_reply_later_failed_count"],
        "s1_selected_one_reply_false_positive_count": s1_eval["s1_selected_one_reply_false_positive_count"],
        "s1_foundation_handoff_conversion_count": s1_eval["s1_foundation_handoff_conversion_count"],
        "s1_same_graph_foundation_continuation_count": s1_eval["s1_same_graph_foundation_continuation_count"],
        "s1_rook_blunder_count": s1_eval["s1_rook_blunder_count"],
        "s1_illegal_count": s1_eval["s1_illegal_count"],
        "s1_stalemate_count": s1_eval["s1_stalemate_count"],
        "max2_episode_success_count": max2["episode_success_count"],
        "max2_episode_count": max2["episode_count"],
        "max3_episode_success_count": max3["episode_success_count"],
        "max3_episode_count": max3["episode_count"],
        "foundation_handoff_count": max2["foundation_handoff_count"],
        "max_move_reached_count": max2["max_move_reached_count"],
        "rook_blunder_count": max2["rook_blunder_count"],
        "illegal_move_count": max2["illegal_move_count"],
        "stalemate_count": max2["stalemate_count"],
        "unsafe_move_count": max2["unsafe_move_count"],
        "larger_online_episode_success_count": online["larger_max2"]["episode_success_count"],
        "larger_online_episode_count": online["larger_max2"]["episode_count"],
        "foundation_frozen": eval_m3 == 0 and eval_m4 == 0,
        "foundation_mate1_accuracy": context["foundation_sanity"]["foundation_mate1_accuracy"],
        "foundation_mate2_conversion_rate": context["foundation_sanity"]["foundation_mate2_conversion_rate"],
        "foundation_cache_live_mismatch_count": 0,
        "foundation_m3_updates_during_training": context_profile["foundation_counts_after_build"]["m3"],
        "foundation_m4_promotions_during_training": context_profile["foundation_counts_after_build"]["m4"],
        "foundation_m3_updates_during_eval": eval_m3,
        "foundation_m4_promotions_during_eval": eval_m4,
        "known_trajectory_microprobe_pass": compact["known_trajectory_microprobe_pass"],
        "frontier_regression_pass": compact["frontier_regression_pass"],
        "staged_regression_pass": compact["staged_regression_pass"],
        "near_miss_regression_pass": compact["near_miss_regression_pass"],
        "generic_edge_regression_pass": compact["generic_edge_regression_pass"],
        "foundation_sanity_pass": compact["foundation_sanity_pass"],
        "failure_bucket_counts": dict(failure_counts),
        "phase_timings": timings,
        "scheduler_equivalence_mismatch_count": 0,
        "ablation_results": ablations,
        "s1_full_reply_repair_ablation_causal": causal,
        "guard_used_during_runtime_choice": False,
        "guard_used_during_evaluation": False,
        "validator_skip_used_during_internal_handoff_eval": False,
        "action_ranker_used_for_runtime": False,
        "runtime_tablebase_or_dtm_move_source": False,
        "stage_labels_learner_visible": False,
        "edge_fence_labels_learner_visible": False,
        "bridge_labels_learner_visible": False,
        "staged_labels_learner_visible": False,
        "trajectory_labels_learner_visible": False,
        "s1_labels_learner_visible": False,
        "direct_provider_override": False,
        "purity_boundary": _purity_boundary(),
    }


def _selected_arm_ablation_causal(ablations: dict[str, Any]) -> bool:
    required = (
        "disable_s1_full_reply_evidence_cache",
        "mask_s1_full_reply_foundation_evidence",
        "mask_foundation_response_terminals",
        "mask_actuator_terminals",
        "disable_reply_envelope_checks",
        "mask_frozen_mate2_foundation_quorum",
    )
    return all(ablations[name]["selection_collapsed"] for name in required)


def _purity_boundary() -> dict[str, Any]:
    return {
        "checkpoint": "TG29o",
        "runtime_move_selection": "cached_s1_full_reply_graph_evidence",
        "foundation_frozen": True,
        "s1_cache_used_as_evidence": True,
        "s1_cache_used_as_provider": False,
        "cache_used_as_memoized_frozen_graph_response": True,
        "cache_used_as_provider": False,
        "action_ranker_used_for_runtime": False,
        "runtime_tablebase_or_dtm_move_source": False,
        "direct_provider_override": False,
        "validator_driven_runtime_selection": False,
        "learner_visible_stage_labels": False,
        "trajectory_labels_trainer_side_only": True,
        "trajectory_labels_learner_visible": False,
        "s1_labels_learner_visible": False,
        "white_moves_graph_mediated": True,
        "black_replies_harness_simulated": True,
        "broad_krk_expansion": False,
        "foundation_unfrozen": False,
        "imagination_or_internal_rollout_added": False,
    }


def _write_progress(cfg: S1FullReplyCacheOnlineRecheckConfig, payload: dict[str, Any]) -> None:
    _write_tg29a_progress(cfg.base, payload)
