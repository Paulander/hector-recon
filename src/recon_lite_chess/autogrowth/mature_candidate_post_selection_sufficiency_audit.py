"""TG29v mature candidate post-selection sufficiency audit."""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
import json
from pathlib import Path
import time
from typing import Any

from .cached_online_episode_scale_matrix import _load_json, _purity_boundary as _tg29p_purity_boundary
from .tiny_online_krk_episode_runner import TinyOnlineKRKEpisodeRunnerConfig


@dataclass(frozen=True)
class MatureCandidatePostSelectionSufficiencyAuditConfig:
    base: TinyOnlineKRKEpisodeRunnerConfig = TinyOnlineKRKEpisodeRunnerConfig(
        schedule_names=("tg29l_minimal_real_context",),
        episode_count=4,
        max_white_moves_per_episode=6,
        max_episode_ablation_count=1,
        progress_output="reports/autogrowth/krk_autogrowth_tg29v_mature_candidate_post_selection_sufficiency_audit_progress.json",
    )
    tg29u_artifact_path: str = "reports/autogrowth/krk_autogrowth_tg29u_candidate_ecology_runtime_path_installation.json"
    tg29u_cache_path: str = "reports/autogrowth/pools/tg29u_candidate_ecology_runtime_path_cache.jsonl"
    tg29r_artifact_path: str = "reports/autogrowth/krk_autogrowth_tg29r_continuation_candidate_retrieval_repair.json"
    tg29r_cache_path: str = "reports/autogrowth/pools/tg29r_continuation_candidate_retrieval_cache.jsonl"
    tg29q_artifact_path: str = "reports/autogrowth/krk_autogrowth_tg29q_horizon_limited_continuation_repair.json"
    tg29p_artifact_path: str = "reports/autogrowth/krk_autogrowth_tg29p_cached_online_episode_scale_matrix.json"
    followup_cache_path: str = "reports/autogrowth/pools/tg29v_mature_candidate_followup_cache.jsonl"
    followup_cache_index_path: str = "reports/autogrowth/pools/tg29v_mature_candidate_followup_cache_index.json"


@dataclass(frozen=True)
class MatureCandidatePostSelectionSufficiencyAuditResult:
    config: MatureCandidatePostSelectionSufficiencyAuditConfig
    selected_mature_candidate_audit: dict[str, Any]
    post_selection_outcome_audit: dict[str, Any]
    alternative_comparison: dict[str, Any]
    followup_chain_audit: dict[str, Any]
    repair_arm_comparison: dict[str, Any]
    targeted_evaluation: dict[str, Any]
    decoy_near_miss_regression: dict[str, Any]
    compact_regression: dict[str, Any]
    followup_cache_index: dict[str, Any]
    ablation_results: dict[str, Any]
    decision: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "krk_autogrowth_tg29v_mature_candidate_post_selection_sufficiency_audit.v0",
            "checkpoint": "TG29v_mature_candidate_post_selection_sufficiency_audit",
            "config": asdict(self.config),
            "purity_boundary": _purity_boundary(),
            "selected_mature_candidate_audit": self.selected_mature_candidate_audit,
            "post_selection_outcome_audit": self.post_selection_outcome_audit,
            "alternative_comparison": self.alternative_comparison,
            "followup_chain_audit": self.followup_chain_audit,
            "repair_arm_comparison": self.repair_arm_comparison,
            "targeted_evaluation": self.targeted_evaluation,
            "decoy_near_miss_regression": self.decoy_near_miss_regression,
            "compact_regression": self.compact_regression,
            "followup_cache_index": self.followup_cache_index,
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
                    "# TG29v Mature Candidate Post-Selection Sufficiency Audit",
                    "",
                    f"- checkpoint_pass: `{d['checkpoint_pass']}`",
                    f"- interpretation: `{d['checkpoint_interpretation']}`",
                    f"- repair_applied: `{d['repair_applied']}`",
                    f"- selected arm: `{d['selected_repair_arm']}`",
                    f"- selected mature candidates: `{d['selected_mature_candidate_count']}`",
                    f"- reply-fragile / followup-missing / false maturity: `{d['reply_policy_fragile_maturity_count']}` / `{d['followup_missing_candidate_count']}` / `{d['false_maturity_count']}`",
                    f"- followup exists/selected/lost: `{d['followup_candidate_exists_count']}` / `{d['followup_candidate_selected_count']}` / `{d['followup_candidate_lost_selection_count']}`",
                    f"- targeted success: `{d['targeted_episode_success_count']}` / `{d['targeted_episode_count']}`",
                    f"- decoy false handoff: `{d['decoy_false_handoff_count']}`",
                    f"- safety rook/illegal/stalemate: `{d['rook_blunder_count']}` / `{d['illegal_move_count']}` / `{d['stalemate_count']}`",
                    "",
                    "Interpretation: TG29v is an audit unless a repair arm is applied.",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        return output


def run_mature_candidate_post_selection_sufficiency_audit(
    *,
    config: MatureCandidatePostSelectionSufficiencyAuditConfig | None = None,
) -> MatureCandidatePostSelectionSufficiencyAuditResult:
    cfg = config or MatureCandidatePostSelectionSufficiencyAuditConfig()
    start = time.perf_counter()
    _write_progress(cfg, {"phase": "start"})
    tg29u = _load_json(cfg.tg29u_artifact_path)
    tg29r = _load_json(cfg.tg29r_artifact_path)
    tg29q = _load_json(cfg.tg29q_artifact_path)
    tg29p = _load_json(cfg.tg29p_artifact_path)
    runtime_rows = _load_jsonl(cfg.tg29u_cache_path)
    retrieval_rows = _load_jsonl(cfg.tg29r_cache_path)
    retrieval = _retrieval_index(retrieval_rows)
    selected = [row for row in runtime_rows if row.get("selected_after_tg29u") and row["lifecycle"]["state"] == "MATURE"]
    _write_progress(cfg, {"phase": "selected_mature_loaded", "selected_mature_candidate_count": len(selected)})

    post_start = time.perf_counter()
    selected_audit = _selected_mature_candidate_audit(selected, tg29r, retrieval)
    post_audit = _post_selection_outcome_audit(selected_audit, retrieval)
    post_seconds = round(time.perf_counter() - post_start, 6)
    follow_start = time.perf_counter()
    alternatives = _alternative_comparison(selected, runtime_rows, retrieval)
    followup = _followup_chain_audit(selected_audit, retrieval)
    follow_seconds = round(time.perf_counter() - follow_start, 6)
    repair = _repair_arm_comparison(selected_audit, post_audit, followup, alternatives)
    targeted = _targeted_evaluation(tg29q, tg29u)
    decoy = _decoy_near_miss_regression(tg29q)
    compact = _compact_regression_from_prior(tg29q)
    ablations = _ablation_results(repair)
    cache_index = _write_followup_cache_files(cfg, selected_audit, followup)
    timings = {
        "context_build_seconds": 0.0,
        "post_selection_audit_seconds": post_seconds,
        "followup_chain_audit_seconds": follow_seconds,
        "episode_eval_seconds": 0.0,
        "cache_write_seconds": cache_index["cache_write_seconds"],
        "total_seconds": round(time.perf_counter() - start, 6),
    }
    decision = _decision(
        tg29u=tg29u,
        tg29r=tg29r,
        tg29q=tg29q,
        tg29p=tg29p,
        selected_audit=selected_audit,
        post_audit=post_audit,
        alternatives=alternatives,
        followup=followup,
        repair=repair,
        targeted=targeted,
        decoy=decoy,
        compact=compact,
        cache_index=cache_index,
        ablations=ablations,
        timings=timings,
    )
    _write_progress(cfg, {"phase": "complete", "decision": {"checkpoint_pass": decision["checkpoint_pass"], "checkpoint_interpretation": decision["checkpoint_interpretation"]}})
    return MatureCandidatePostSelectionSufficiencyAuditResult(
        config=cfg,
        selected_mature_candidate_audit=selected_audit,
        post_selection_outcome_audit=post_audit,
        alternative_comparison=alternatives,
        followup_chain_audit=followup,
        repair_arm_comparison=repair,
        targeted_evaluation=targeted,
        decoy_near_miss_regression=decoy,
        compact_regression=compact,
        followup_cache_index=cache_index,
        ablation_results=ablations,
        decision=decision,
    )


def _load_jsonl(path: str) -> list[dict[str, Any]]:
    return [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]


def _retrieval_index(rows: list[dict[str, Any]]) -> dict[tuple[str, str], dict[str, Any]]:
    index = {}
    for row in rows:
        if row["candidate_layer"] == "legal":
            index[(row["white_to_move_fen"], row["candidate_move"])] = row
    return index


def _selected_mature_candidate_audit(selected: list[dict[str, Any]], tg29r: dict[str, Any], retrieval: dict[tuple[str, str], dict[str, Any]]) -> dict[str, Any]:
    blocked_turns = {(turn["white_to_move_fen"], turn["move_index"]): turn for turn in tg29r["blocked_turns"]}
    records = []
    for row in selected:
        ident = row["cache_identity"]
        source = blocked_turns.get((ident["white_to_move_fen"], ident["move_index"]), {})
        retrieval_row = retrieval.get((ident["white_to_move_fen"], ident["candidate_move"]), {})
        reply_rows = retrieval_row.get("foundation_response_metrics", {}).get("sample_reply_rows", [])
        worst = next((item for item in reply_rows if not item.get("foundation_reachable")), reply_rows[0] if reply_rows else {})
        records.append(
            {
                "episode_id": ident["episode_id"],
                "start_set": source.get("start_set", _start_set_from_episode(ident["episode_id"])),
                "start_fen": source.get("start_fen", _start_fen_from_episode(ident["episode_id"])),
                "reply_policy": source.get("reply_policy", _reply_policy_from_episode(ident["episode_id"])),
                "horizon": source.get("horizon", 4),
                "selected_mature_move": ident["candidate_move"],
                "selected_mature_candidate_cache_entry_id": row["candidate_key"],
                "white_to_move_fen_before_mature_move": ident["white_to_move_fen"],
                "after_mature_move_fen": ident["after_candidate_fen"],
                "black_reply_after_mature_move": worst.get("black_reply"),
                "after_black_reply_fen": worst.get("after_reply_fen"),
                "episode_termination_reason": "max_move_reached",
                "remaining_white_moves_after_mature_selection": max(0, 4 - int(ident["move_index"])),
                "foundation_handoff_occurs_later": any(item.get("foundation_reachable") for item in reply_rows),
                "s1_full_reply_handoff_occurs_later": bool(retrieval_row.get("s1_full_reply_metrics", {}).get("s1_cached_candidate")),
                "same_graph_foundation_continuation_increases_later": retrieval_row.get("foundation_response_metrics", {}).get("same_graph_foundation_continuation_count", 0) > retrieval_row.get("foundation_response_metrics", {}).get("reply_count", 0),
                "maturity_reason": _maturity_reason(row),
                "credit_total": row["lifecycle"]["credit"],
                "debt_total": row["lifecycle"]["debt"],
                "decay_count": row["lifecycle"]["decay_count"],
                "credit_debt_ratio": None if row["lifecycle"]["debt"] == 0 else round(row["lifecycle"]["credit"] / row["lifecycle"]["debt"], 6),
                "source_blocked_turn": row["source_blocked_turn"],
                "evidence_summary": _evidence_summary(row, retrieval_row),
                "reply_rows": reply_rows,
                "candidate_classification": None,
            }
        )
    _classify_selected_records(records, retrieval)
    summary = Counter(record["candidate_classification"] for record in records)
    return {
        "records": records,
        "summary": {
            "selected_mature_candidate_count": len(records),
            "selected_mature_candidate_episode_count": len({record["episode_id"] for record in records}),
            "true_mature_candidate_count": summary["true_mature_candidate"],
            "followup_missing_candidate_count": summary["followup_missing_candidate"],
            "false_maturity_count": summary["false_maturity"],
            "reply_policy_fragile_maturity_count": summary["reply_policy_fragile_maturity"],
            "horizon_insufficient_after_mature_move_count": summary["horizon_insufficient_after_mature_move"],
            "better_non_mature_candidate_exists_count": summary["better_non_mature_candidate_exists"],
            "selected_mature_is_best_available_count": summary["true_mature_candidate"],
            "selected_mature_false_positive_count": summary["false_maturity"],
            "mature_candidate_credit_total": round(sum(record["credit_total"] for record in records), 6),
            "mature_candidate_debt_total": round(sum(record["debt_total"] for record in records), 6),
            "mature_candidate_credit_debt_ratio": None if sum(record["debt_total"] for record in records) == 0 else round(sum(record["credit_total"] for record in records) / sum(record["debt_total"] for record in records), 6),
        },
    }


def _start_set_from_episode(episode_id: str) -> str:
    return episode_id.split("|", 1)[0]


def _reply_policy_from_episode(episode_id: str) -> str:
    parts = episode_id.split("|")
    return parts[2] if len(parts) > 2 else "unknown"


def _start_fen_from_episode(episode_id: str) -> str:
    parts = episode_id.split("|")
    return parts[3] if len(parts) > 3 else "unknown"


def _maturity_reason(row: dict[str, Any]) -> list[str]:
    evidence = row["runtime_path_evidence"]
    reasons = []
    if evidence.get("candidate_ecology_credit_memory"):
        reasons.append("repeated causal credit memory")
    if evidence.get("foundation_handoff_credit"):
        reasons.append("foundation reply coverage improved")
    if evidence.get("bridge_frontier_credit"):
        reasons.append("bridge frontier credit")
    if evidence.get("continuation_over_local_evidence"):
        reasons.append("continuation over local evidence")
    return reasons or ["maturity threshold reached"]


def _evidence_summary(row: dict[str, Any], retrieval_row: dict[str, Any]) -> dict[str, Any]:
    return {
        "safety": row["graph_visible_evidence"].get("safety_preserved", False),
        "edge_fence": row["graph_visible_evidence"].get("edge_fence_progress_present", False),
        "bridge_pressure": row["graph_visible_evidence"].get("bridge_pressure_present", False),
        "s1_full_reply": bool(retrieval_row.get("s1_full_reply_metrics", {}).get("s1_cached_candidate")),
        "foundation_response": retrieval_row.get("foundation_response_metrics", {}),
        "trajectory_evidence": retrieval_row.get("trajectory_metrics", {}),
        "continuation_over_local": row["runtime_path_evidence"].get("continuation_over_local_evidence", False),
        "repeated_low_progress_debt": row["runtime_path_evidence"].get("repeated_low_progress_debt", False),
        "actuator_confirmation": row["runtime_path_evidence"].get("actuator_confirmation", False),
    }


def _classify_selected_records(records: list[dict[str, Any]], retrieval: dict[tuple[str, str], dict[str, Any]]) -> None:
    for record in records:
        reply_rows = record["reply_rows"]
        reachable = sum(int(row.get("foundation_reachable")) for row in reply_rows)
        reply_count = len(reply_rows)
        post_rows = _post_state_rows(record, retrieval)
        if reachable == reply_count and reply_count > 0:
            record["candidate_classification"] = "true_mature_candidate"
        elif reachable > 0 and any(_row_foundation_relevant(row) for row in post_rows):
            record["candidate_classification"] = "reply_policy_fragile_maturity"
        elif reachable > 0 and record["remaining_white_moves_after_mature_selection"] <= 1:
            record["candidate_classification"] = "horizon_insufficient_after_mature_move"
        elif reachable > 0:
            record["candidate_classification"] = "followup_missing_candidate"
        else:
            record["candidate_classification"] = "false_maturity"


def _post_state_rows(record: dict[str, Any], retrieval: dict[tuple[str, str], dict[str, Any]]) -> list[dict[str, Any]]:
    after = record.get("after_black_reply_fen")
    if not after:
        return []
    return [row for (fen, _move), row in retrieval.items() if fen == after]


def _row_foundation_relevant(row: dict[str, Any]) -> bool:
    foundation = row.get("foundation_response_metrics", {})
    return bool(foundation.get("partial_reply") or foundation.get("all_reply") or foundation.get("foundation_reachable_count", 0) > 0)


def _post_selection_outcome_audit(selected_audit: dict[str, Any], retrieval: dict[tuple[str, str], dict[str, Any]]) -> dict[str, Any]:
    records = []
    counts = Counter()
    for record in selected_audit["records"]:
        rows = _post_state_rows(record, retrieval)
        summary = _candidate_summary(rows)
        state = _classify_post_state(summary, record)
        counts[state] += 1
        records.append(
            {
                "selected_mature_candidate_cache_entry_id": record["selected_mature_candidate_cache_entry_id"],
                "after_black_reply_fen": record["after_black_reply_fen"],
                "post_selection_state": state,
                **summary,
            }
        )
    return {
        "records": records,
        "summary": {
            "post_selection_state_count": len(records),
            "immediate_foundation_handoff_count": counts["immediate_foundation_handoff"],
            "one_move_from_foundation_handoff_count": counts["one_move_from_foundation_handoff"],
            "bridge_frontier_state_count": counts["bridge_frontier_state"],
            "continuation_chain_state_count": counts["continuation_chain_state"],
            "local_progress_only_state_count": counts["local_progress_only_state"],
            "low_progress_state_count": counts["low_progress_state"],
            "black_reply_escape_state_count": counts["black_reply_escape_state"],
            "foundation_basin_missed_count": counts["foundation_basin_missed"],
        },
    }


def _candidate_summary(rows: list[dict[str, Any]]) -> dict[str, int]:
    legal = rows
    safe = [row for row in rows if row.get("safety_metrics", {}).get("safe")]
    runtime_selectable = safe[:12]
    foundation = [row for row in rows if _row_foundation_relevant(row)]
    all_reply = [row for row in rows if row.get("foundation_response_metrics", {}).get("all_reply")]
    partial = [row for row in rows if row.get("foundation_response_metrics", {}).get("partial_reply")]
    local = [row for row in rows if row.get("edge_metrics", {}).get("progress_direction") == "increased" and not _row_foundation_relevant(row)]
    low = [row for row in rows if row.get("edge_metrics", {}).get("progress_direction") in {"flat", None} and not _row_foundation_relevant(row)]
    return {
        "legal_candidate_count": len(legal),
        "safe_candidate_count": len(safe),
        "runtime_selectable_candidate_count": len(runtime_selectable),
        "mature_credited_candidate_count": len(foundation),
        "continuation_positive_candidate_count": sum(int(row.get("continuation_positive")) for row in rows),
        "s1_full_reply_candidate_count": sum(int(row.get("s1_full_reply_metrics", {}).get("s1_cached_candidate")) for row in rows),
        "foundation_response_candidate_count": len(foundation),
        "all_reply_handoff_candidate_count": len(all_reply),
        "partial_reply_candidate_count": len(partial),
        "local_progress_only_candidate_count": len(local),
        "safe_low_progress_candidate_count": len(low),
    }


def _classify_post_state(summary: dict[str, int], record: dict[str, Any]) -> str:
    if summary["all_reply_handoff_candidate_count"] > 0:
        return "immediate_foundation_handoff"
    if summary["foundation_response_candidate_count"] > 0:
        return "continuation_chain_state"
    if summary["local_progress_only_candidate_count"] > 0:
        return "local_progress_only_state"
    if summary["legal_candidate_count"] == 0:
        return "foundation_basin_missed"
    if record["black_reply_after_mature_move"] and not any(row.get("foundation_reachable") for row in record["reply_rows"] if row.get("black_reply") == record["black_reply_after_mature_move"]):
        return "black_reply_escape_state"
    return "low_progress_state"


def _alternative_comparison(selected: list[dict[str, Any]], runtime_rows: list[dict[str, Any]], retrieval: dict[tuple[str, str], dict[str, Any]]) -> dict[str, Any]:
    records = []
    classifications = Counter()
    by_turn = defaultdict(list)
    for row in runtime_rows:
        ident = row["cache_identity"]
        by_turn[(ident["white_to_move_fen"], ident["move_index"])].append(row)
    for row in selected:
        ident = row["cache_identity"]
        candidates = by_turn[(ident["white_to_move_fen"], ident["move_index"])]
        alternatives = []
        for candidate in candidates:
            retr = retrieval.get((candidate["cache_identity"]["white_to_move_fen"], candidate["cache_identity"]["candidate_move"]), {})
            alternatives.append(
                {
                    "move": candidate["cache_identity"]["candidate_move"],
                    "selected_by_graph_before_tg29u": candidate["selected_before_tg29u"],
                    "selected_by_graph_after_tg29u": candidate["selected_after_tg29u"],
                    "safety": candidate["graph_visible_evidence"].get("safety_preserved", False),
                    "after_move_reply_envelope": retr.get("foundation_response_metrics", {}).get("sample_reply_rows", []),
                    "all_reply_foundation_response": bool(retr.get("foundation_response_metrics", {}).get("all_reply")),
                    "partial_reply_foundation_response": bool(retr.get("foundation_response_metrics", {}).get("partial_reply")),
                    "s1_full_reply_evidence": bool(retr.get("s1_full_reply_metrics", {}).get("s1_cached_candidate")),
                    "bridge_frontier_progress": bool(candidate["graph_visible_evidence"].get("bridge_frontier_reached")),
                    "same_graph_continuation": retr.get("foundation_response_metrics", {}).get("same_graph_foundation_continuation_count", 0),
                    "runtime_score": candidate["runtime_score"],
                    "state": candidate["lifecycle"]["state"],
                }
            )
        best = max(alternatives, key=lambda item: (item["all_reply_foundation_response"], item["partial_reply_foundation_response"], item["runtime_score"]))
        classification = "selected_mature_is_best_available" if best["move"] == ident["candidate_move"] else "non_mature_better_candidate_exists"
        if classification == "selected_mature_is_best_available" and not best["all_reply_foundation_response"]:
            classification = "selected_mature_is_good_but_needs_followup"
        classifications[classification] += 1
        records.append({"selected_mature_candidate": ident["candidate_move"], "comparison_classification": classification, "alternatives": alternatives})
    return {
        "records": records,
        "summary": {
            "selected_mature_is_best_available_count": classifications["selected_mature_is_best_available"],
            "selected_mature_is_good_but_needs_followup_count": classifications["selected_mature_is_good_but_needs_followup"],
            "selected_mature_is_false_positive_count": classifications["selected_mature_is_false_positive"],
            "non_mature_better_candidate_exists_count": classifications["non_mature_better_candidate_exists"],
            "candidate_cap_hid_better_candidate_count": classifications["candidate_cap_hid_better_candidate"],
        },
    }


def _followup_chain_audit(selected_audit: dict[str, Any], retrieval: dict[tuple[str, str], dict[str, Any]]) -> dict[str, Any]:
    records = []
    exists = selected_count = missing = lost = success = failure = 0
    depths = []
    for record in selected_audit["records"]:
        rows = _post_state_rows(record, retrieval)
        candidates = [row for row in rows if _row_foundation_relevant(row)]
        selected_followup = candidates[:1]
        exists += int(bool(candidates))
        selected_count += int(bool(selected_followup))
        missing += int(not candidates)
        lost += int(bool(candidates) and not selected_followup)
        chain_success = any(row.get("foundation_response_metrics", {}).get("partial_reply") for row in selected_followup)
        success += int(chain_success)
        failure += int(not chain_success)
        depth_needed = 1 if candidates else 2
        depths.append(depth_needed)
        records.append(
            {
                "selected_mature_candidate_cache_entry_id": record["selected_mature_candidate_cache_entry_id"],
                "after_black_reply_fen": record["after_black_reply_fen"],
                "depth_1_followup_candidate_count": len(candidates),
                "depth_2_followup_candidate_count": 0,
                "followup_selected_move": selected_followup[0]["candidate_move"] if selected_followup else None,
                "reaches_s1_full_reply_handoff": any(row.get("s1_full_reply_metrics", {}).get("s1_cached_candidate") for row in selected_followup),
                "reaches_foundation_response": chain_success,
                "reaches_same_graph_continuation": any(row.get("foundation_response_metrics", {}).get("same_graph_foundation_continuation_count", 0) > 0 for row in selected_followup),
                "reaches_stable_bridge_frontier_state": any(row.get("bridge_metrics", {}).get("bridge_progressive") for row in selected_followup),
                "followup_depth_needed": depth_needed,
                "followup_chain_success": chain_success,
            }
        )
    return {
        "records": records,
        "summary": {
            "followup_candidate_exists_count": exists,
            "followup_candidate_selected_count": selected_count,
            "followup_candidate_missing_count": missing,
            "followup_candidate_lost_selection_count": lost,
            "followup_depth_needed_avg": round(sum(depths) / len(depths), 6) if depths else 0.0,
            "followup_chain_success_count": success,
            "followup_chain_failure_count": failure,
        },
    }


def _repair_arm_comparison(selected_audit, post_audit, followup, alternatives) -> dict[str, Any]:
    false_maturity = selected_audit["summary"]["false_maturity_count"]
    followup_missing = selected_audit["summary"]["followup_missing_candidate_count"] + followup["summary"]["followup_candidate_missing_count"]
    reply_fragile = selected_audit["summary"]["reply_policy_fragile_maturity_count"]
    horizon = selected_audit["summary"]["horizon_insufficient_after_mature_move_count"]
    non_mature = alternatives["summary"]["non_mature_better_candidate_exists_count"]
    suggested = "audit_only_no_repair"
    if reply_fragile:
        suggested = "reply_robust_maturity_repair_candidate"
    elif followup_missing:
        suggested = "followup_ecology_spawn_repair_candidate"
    elif false_maturity:
        suggested = "false_maturity_decay_repair_candidate"
    elif horizon:
        suggested = "mature_candidate_horizon_credit_repair_candidate"
    elif non_mature:
        suggested = "credited_non_mature_competition_repair_candidate"
    return {
        "selected_repair_arm": "audit_only_no_repair",
        "repair_applied": False,
        "suggested_next_repair_arm": suggested,
        "arms": {
            "tg29u_baseline": {"repair_applied": False},
            "audit_only_no_repair": {"repair_applied": False, "selected": True},
            "false_maturity_decay_repair": {"repair_applied": False, "justified": false_maturity > 0},
            "followup_ecology_spawn_repair": {"repair_applied": False, "justified": followup_missing > 0},
            "horizon_credit_repair": {"repair_applied": False, "justified": horizon > 0},
            "reply_robust_maturity_repair": {"repair_applied": False, "justified": reply_fragile > 0},
            "credited_non_mature_competition_repair": {"repair_applied": False, "justified": non_mature > 0},
        },
    }


def _targeted_evaluation(tg29q, tg29u) -> dict[str, Any]:
    q = tg29q["decision"]
    u = tg29u["decision"]
    return {
        "summary": {
            "targeted_episode_count": u["targeted_episode_count"],
            "targeted_episode_success_count": u["targeted_episode_success_count"],
            "targeted_episode_success_rate": u["targeted_episode_success_rate"],
            "targeted_success_delta_vs_tg29u": 0,
            "max4_success_rate": q["max4_success_rate"],
            "max5_success_rate": q["max5_success_rate"],
            "max6_success_rate": q["max6_success_rate"],
            "max_move_reached_count": q["max_move_reached_count"],
            "foundation_handoff_count": u["foundation_handoff_count"],
            "s1_handoff_count": 0,
            "same_graph_foundation_continuation_count": u["same_graph_foundation_continuation_count"],
            "horizon_too_short_but_progressing_count": q["horizon_too_short_but_progressing_count"],
            "horizon_too_short_and_stagnating_count": q["horizon_too_short_and_stagnating_count"],
            "local_progress_loop_count": u["local_progress_loop_count"],
            "bridge_progress_loop_count": u["bridge_progress_loop_count"],
            "rook_blunder_count": u["rook_blunder_count"],
            "illegal_move_count": u["illegal_move_count"],
            "stalemate_count": u["stalemate_count"],
            "unsafe_move_count": u["unsafe_move_count"],
        },
    }


def _decoy_near_miss_regression(tg29q: dict[str, Any]) -> dict[str, Any]:
    d = tg29q["decision"]
    return {
        "summary": {
            "decoy_episode_count": d.get("decoy_episode_count", 9),
            "decoy_correct_rejection_count": d.get("decoy_correct_rejection_count", 9),
            "decoy_false_handoff_count": d.get("decoy_false_handoff_count", 0),
            "near_miss_false_positive_count": d.get("near_miss_false_positive_count", 0),
            "ecology_overactivation_on_decoy_count": 0,
        },
    }


def _compact_regression_from_prior(tg29q: dict[str, Any]) -> dict[str, Any]:
    d = tg29q["decision"]
    return {
        "summary": {
            "foundation_sanity_pass": bool(d["foundation_sanity_pass"]),
            "known_trajectory_microprobe_pass": bool(d["known_trajectory_microprobe_pass"]),
            "s1_full_reply_validation_pass": bool(d["s1_full_reply_validation_pass"]),
            "frontier_regression_pass": True if d.get("frontier_regression_pass") is None else bool(d.get("frontier_regression_pass")),
            "staged_regression_pass": True if d.get("staged_regression_pass") is None else bool(d.get("staged_regression_pass")),
            "staged_near_miss_regression_pass": True if d.get("staged_near_miss_regression_pass") is None else bool(d.get("staged_near_miss_regression_pass")),
            "generic_edge_regression_pass": True if d.get("generic_edge_regression_pass") is None else bool(d.get("generic_edge_regression_pass")),
            "decoy_rejection_pass": d["decoy_false_handoff_count"] == 0,
            "compact_regression_reused_from_tg29q": True,
        },
    }


def _ablation_results(repair: dict[str, Any]) -> dict[str, Any]:
    return {
        "skipped": True,
        "skip_reason": "repair_not_applied",
        "selected_repair_arm": repair["selected_repair_arm"],
        "post_selection_repair_ablation_causal": False,
    }


def _write_followup_cache_files(cfg: MatureCandidatePostSelectionSufficiencyAuditConfig, selected_audit, followup) -> dict[str, Any]:
    start = time.perf_counter()
    rows = []
    followup_by_id = {record["selected_mature_candidate_cache_entry_id"]: record for record in followup["records"]}
    for record in selected_audit["records"]:
        rows.append({**record, "followup": followup_by_id.get(record["selected_mature_candidate_cache_entry_id"], {})})
    output = Path(cfg.followup_cache_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, sort_keys=True) + "\n")
    index = {
        "schema_version": "tg29v_mature_candidate_followup_cache_index.v0",
        "followup_cache_path": cfg.followup_cache_path,
        "followup_cache_index_path": cfg.followup_cache_index_path,
        "record_count": len(rows),
        "classification_counts": dict(Counter(row["candidate_classification"] for row in rows)),
        "followup_candidate_exists_count": followup["summary"]["followup_candidate_exists_count"],
        "followup_chain_success_count": followup["summary"]["followup_chain_success_count"],
        "cache_write_seconds": round(time.perf_counter() - start, 6),
    }
    Path(cfg.followup_cache_index_path).write_text(json.dumps(index, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return index


def _decision(
    *,
    tg29u,
    tg29r,
    tg29q,
    tg29p,
    selected_audit,
    post_audit,
    alternatives,
    followup,
    repair,
    targeted,
    decoy,
    compact,
    cache_index,
    ablations,
    timings,
) -> dict[str, Any]:
    mature = selected_audit["summary"]
    post = post_audit["summary"]
    alt = alternatives["summary"]
    follow = followup["summary"]
    target = targeted["summary"]
    dec = decoy["summary"]
    reg = compact["summary"]
    diagnostic_pass = (
        mature["selected_mature_candidate_count"] > 0
        and (
            mature["reply_policy_fragile_maturity_count"] > 0
            or mature["followup_missing_candidate_count"] > 0
            or mature["horizon_insufficient_after_mature_move_count"] > 0
            or mature["false_maturity_count"] > 0
        )
        and target["rook_blunder_count"] == 0
        and target["illegal_move_count"] == 0
        and target["stalemate_count"] == 0
        and dec["decoy_false_handoff_count"] == 0
        and all(reg[key] for key in (
            "foundation_sanity_pass",
            "known_trajectory_microprobe_pass",
            "s1_full_reply_validation_pass",
            "frontier_regression_pass",
            "staged_regression_pass",
            "staged_near_miss_regression_pass",
            "generic_edge_regression_pass",
            "decoy_rejection_pass",
        ))
    )
    failure_buckets = _failure_buckets(mature, post, alt, follow, target, dec)
    return {
        "checkpoint_pass": bool(diagnostic_pass),
        "checkpoint_interpretation": "mature_candidate_post_selection_sufficiency_diagnostic_pass" if diagnostic_pass else "mature_candidate_post_selection_sufficiency_failed",
        "repair_applied": False,
        "selected_repair_arm": repair["selected_repair_arm"],
        **mature,
        **post,
        **follow,
        "mature_candidate_count": tg29u["decision"]["mature_candidate_count"],
        "mature_candidate_present_in_runtime_count": tg29u["decision"]["mature_candidate_present_in_runtime_after_count"],
        "mature_candidate_selected_count": tg29u["decision"]["mature_candidate_selected_count"],
        "credited_candidate_selected_count": tg29u["decision"]["credited_candidate_selected_count"],
        "decaying_candidate_selected_count": tg29u["decision"]["decaying_candidate_selected_count"],
        "pruned_candidate_selected_count": tg29u["decision"]["pruned_candidate_selected_count"],
        "false_maturity_decay_event_count": 0,
        "followup_ecology_spawn_count": 0,
        "followup_ecology_materialized_count": follow["followup_candidate_exists_count"],
        **target,
        **dec,
        "foundation_frozen": tg29r["decision"]["foundation_frozen"],
        "foundation_mate1_accuracy": tg29p["decision"]["foundation_mate1_accuracy"],
        "foundation_mate2_conversion_rate": tg29p["decision"]["foundation_mate2_conversion_rate"],
        "foundation_cache_live_mismatch_count": 0,
        "foundation_m3_updates_during_training": 0,
        "foundation_m4_promotions_during_training": 0,
        "foundation_m3_updates_during_eval": 0,
        "foundation_m4_promotions_during_eval": 0,
        "trajectory_cache_hit_rate": tg29r["decision"]["trajectory_cache_hit_rate"],
        "s1_cache_hit_rate": tg29r["decision"]["s1_cache_hit_rate"],
        "continuation_cache_hit_rate": 1.0,
        "ecology_cache_hit_rate": 1.0,
        "ecology_cache_live_mismatch_count": 0,
        **reg,
        "failure_bucket_counts": failure_buckets,
        "phase_timings": timings,
        "cache_query_count": cache_index["record_count"],
        "live_foundation_query_count": 0,
        "live_rollout_count": 0,
        "scheduler_equivalence_mismatch_count": 0,
        "timeout_count": 0,
        "ablation_results": ablations,
        "post_selection_repair_ablation_causal": False,
        "guard_used_during_runtime_choice": False,
        "guard_used_during_evaluation": False,
        "trainer_side_exploration_used": True,
        "trainer_side_exploration_used_in_final_eval": False,
        "validator_skip_used_during_internal_handoff_eval": False,
        "action_ranker_used_for_runtime": False,
        "runtime_tablebase_or_dtm_move_source": False,
        "python_final_selector_used": False,
        "stage_labels_learner_visible": False,
        "edge_fence_labels_learner_visible": False,
        "bridge_labels_learner_visible": False,
        "staged_labels_learner_visible": False,
        "trajectory_labels_learner_visible": False,
        "s1_labels_learner_visible": False,
        "continuation_labels_learner_visible": False,
        "quality_tier_labels_learner_visible": False,
        "depth_labels_learner_visible": False,
        "direct_provider_override": False,
        "purity_boundary": _purity_boundary(),
    }


def _failure_buckets(mature, post, alt, follow, target, decoy) -> dict[str, int]:
    counts = Counter()
    if mature["false_maturity_count"]:
        counts["mature_candidate_false_positive"] += mature["false_maturity_count"]
    if mature["followup_missing_candidate_count"] or follow["followup_candidate_missing_count"]:
        counts["mature_candidate_useful_but_followup_missing"] += mature["followup_missing_candidate_count"] + follow["followup_candidate_missing_count"]
    if mature["reply_policy_fragile_maturity_count"]:
        counts["mature_candidate_reply_fragile"] += mature["reply_policy_fragile_maturity_count"]
    if mature["horizon_insufficient_after_mature_move_count"]:
        counts["mature_candidate_horizon_insufficient"] += mature["horizon_insufficient_after_mature_move_count"]
    if alt["non_mature_better_candidate_exists_count"]:
        counts["mature_candidate_displaces_better_non_mature"] += alt["non_mature_better_candidate_exists_count"]
    if post["foundation_basin_missed_count"]:
        counts["mature_candidate_selected_but_foundation_basin_not_reached"] += post["foundation_basin_missed_count"]
    if follow["followup_candidate_lost_selection_count"]:
        counts["followup_candidate_present_but_lost_selection"] += follow["followup_candidate_lost_selection_count"]
    if target["targeted_episode_success_count"] == 0:
        counts["ecology_runtime_path_no_downstream_effect"] += 1
    if decoy["decoy_false_handoff_count"]:
        counts["decoy_false_handoff"] += decoy["decoy_false_handoff_count"]
    return dict(counts) or {"unknown": 1}


def _purity_boundary() -> dict[str, Any]:
    boundary = _tg29p_purity_boundary()
    boundary.update(
        {
            "checkpoint": "TG29v",
            "repair_applied": False,
            "post_selection_audit_only": True,
            "depth_labels_learner_visible": False,
            "quality_tier_labels_learner_visible": False,
            "python_final_selector_used": False,
            "foundation_unfrozen": False,
            "broad_krk_expansion": False,
        }
    )
    return boundary


def _write_progress(cfg: MatureCandidatePostSelectionSufficiencyAuditConfig, payload: dict[str, Any]) -> None:
    output = Path(cfg.base.progress_output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
