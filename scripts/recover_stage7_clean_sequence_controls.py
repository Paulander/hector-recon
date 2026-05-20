#!/usr/bin/env python3
"""Recover clean replay-free Stage 7 sequence controls from approved artifacts."""

from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = Path("reports/structural_candidates/stage7_clean_artifact_manifest_v0.json")
OUT_JSON = Path("reports/structural_candidates/stage7_clean_sequence_control_recovery_v0.json")
OUT_MD = Path("reports/structural_candidates/stage7_clean_sequence_control_recovery_v0.md")


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _term_key(terms: dict[str, Any]) -> tuple[str, str] | None:
    fen = terms.get("fen")
    move = terms.get("move")
    if not fen or not move:
        return None
    return str(fen), str(move)


def _state_id(prefix: str, *parts: Any) -> str:
    digest = hashlib.sha1("|".join(str(part) for part in parts).encode("utf-8")).hexdigest()[:12]
    return f"{prefix}.{digest}"


def _best_move_for_provider(terms: dict[str, Any], provider: str | None) -> str | None:
    if not provider:
        return None
    skills = terms.get("successor_skills")
    if not isinstance(skills, dict):
        return None
    provider_payload = skills.get(provider)
    if not isinstance(provider_payload, dict):
        return None
    move = provider_payload.get("best_move")
    return str(move) if move else None


def _clean_manifest_rows(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for row in manifest.get("rows") or []:
        if not isinstance(row, dict):
            continue
        if row.get("candidate_for_clean_control_recovery") is True:
            rows.append(row)
    return rows


def _recover_from_artifact(row: dict[str, Any]) -> tuple[list[dict[str, Any]], Counter[str]]:
    artifact = row["artifact"]
    payload = _load(Path(artifact))
    skipped = Counter()
    companion_by_key: dict[tuple[str, str], dict[str, Any]] = {}
    for packet in payload.get("handoff_packets") or []:
        if not isinstance(packet, dict):
            continue
        if packet.get("phase") != "post_opponent_reply":
            continue
        terms = packet.get("evidence_terms") or {}
        if not isinstance(terms, dict) or terms.get("label") != "box_shrink":
            continue
        key = _term_key(terms)
        if key is not None:
            companion_by_key[key] = terms

    controls = []
    for packet in payload.get("handoff_packets") or []:
        if not isinstance(packet, dict):
            continue
        if packet.get("phase") != "playout_summary":
            continue
        terms = packet.get("evidence_terms") or {}
        if not isinstance(terms, dict) or terms.get("label") != "box_shrink":
            continue
        result = terms.get("playout_result")
        if result not in {"mate", "max_plies", "draw"}:
            skipped["unsupported_result"] += 1
            continue
        key = _term_key(terms)
        if key is None:
            skipped["missing_fen_or_move"] += 1
            continue
        max_plies = terms.get("max_plies")
        plies = terms.get("plies")
        if isinstance(max_plies, int) and max_plies > 40:
            skipped["horizon_above_h40"] += 1
            continue
        if result == "mate" and isinstance(plies, int) and plies > 40:
            skipped["mate_after_h40"] += 1
            continue
        if result != "mate" and max_plies != 40:
            skipped["non_mate_not_h40"] += 1
            continue
        companion = companion_by_key.get(key, {})
        selected_provider = companion.get("successor_selected_skill")
        selected_move = _best_move_for_provider(companion, str(selected_provider) if selected_provider else None)
        control_role = "clean_sequence_success_control" if result == "mate" else "clean_sequence_hard_negative"
        controls.append(
            {
                "schema_version": "stage7_clean_sequence_control.v0",
                "state_id": _state_id("clean", key[0], key[1], result, selected_provider, plies),
                "fen": key[0],
                "move_uci": key[1],
                "selected_provider": selected_provider,
                "selected_provider_move": selected_move,
                "selected_provider_score": companion.get("successor_best_score"),
                "selected_provider_second_score": companion.get("successor_second_score"),
                "selected_skill_source": companion.get("selected_skill_source"),
                "result": result,
                "control_role": control_role,
                "plies": plies,
                "max_plies": max_plies,
                "semantic_alignment_status": terms.get("semantic_alignment_status"),
                "failure_classes": terms.get("failure_classes") or companion.get("failure_classes") or [],
                "source_artifact": artifact,
                "source_classification": row.get("classification"),
                "source_default_off_or_baseline": row.get("default_off_or_baseline_marker"),
                "source_runtime_activity_fields": row.get("runtime_test_activity_fields") or [],
                "source_enabled_flags": row.get("enabled_flags") or [],
                "causal_status": "non_causal_replay_free_label",
            }
        )
    return controls, skipped


def build_recovery() -> dict[str, Any]:
    manifest = _load(MANIFEST)
    controls = []
    duplicate_sources: dict[tuple[str, str, str], list[str]] = defaultdict(list)
    skipped = Counter()
    seen: set[tuple[str, str, str]] = set()
    source_rows = _clean_manifest_rows(manifest)
    for row in source_rows:
        rows, row_skipped = _recover_from_artifact(row)
        skipped.update(row_skipped)
        for control in rows:
            key = (control["fen"], control["move_uci"], control["result"])
            duplicate_sources[key].append(control["source_artifact"])
            if key in seen:
                skipped["duplicate_control"] += 1
                continue
            seen.add(key)
            controls.append(control)

    role_counts = Counter(row["control_role"] for row in controls)
    result_counts = Counter(row["result"] for row in controls)
    provider_counts = Counter(str(row.get("selected_provider")) for row in controls)
    source_class_counts = Counter(row["source_classification"] for row in controls)
    source_counts = Counter(row["source_artifact"] for row in controls)
    success_count = role_counts.get("clean_sequence_success_control", 0)
    hard_negative_count = role_counts.get("clean_sequence_hard_negative", 0)
    acceptance = {
        "clean_sequence_success_controls_required": 5,
        "clean_sequence_hard_negatives_required": 5,
        "clean_sequence_success_controls_met": success_count >= 5,
        "clean_sequence_hard_negatives_met": hard_negative_count >= 5,
        "runtime_authorization_allowed": False,
    }
    if acceptance["clean_sequence_success_controls_met"] and acceptance["clean_sequence_hard_negatives_met"]:
        status = "clean_sequence_controls_recovered_for_offline_source_bias_audit"
        next_step = "build_clean_selected_path_dataset_and_source_bias_audit"
    else:
        status = "clean_sequence_controls_insufficient"
        next_step = "bounded_clean_h40_label_job_or_review"

    return {
        "schema_version": "stage7_clean_sequence_control_recovery.v0",
        "causal_status": "non_causal_replay_free_recovery",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_selector_implemented": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "source_artifacts": [str(MANIFEST)],
        "source_candidate_count": len(source_rows),
        "controls": controls,
        "summary": {
            "control_count": len(controls),
            "role_counts": dict(role_counts),
            "result_counts": dict(result_counts),
            "selected_provider_counts": dict(provider_counts),
            "source_classification_counts": dict(source_class_counts),
            "source_artifact_counts": dict(source_counts),
            "skipped_counts": dict(skipped),
            "duplicate_source_key_count": sum(1 for sources in duplicate_sources.values() if len(sources) > 1),
            "usable_for_offline_benchmark": len(controls) > 0,
            "usable_for_runtime_authorization": False,
        },
        "acceptance": acceptance,
        "decision": {
            "status": status,
            "recommended_next_step": next_step,
            "runtime_work_allowed": False,
        },
    }


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Stage 7 Clean Sequence Control Recovery v0",
        "",
        f"Status: `{payload['decision']['status']}`",
        "",
        "Replay-free recovery of clean Stage 7 sequence controls from manifest-approved current-profile/default-off artifacts.",
        "",
        "## Summary",
        "",
    ]
    for key, value in payload["summary"].items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Acceptance", ""])
    for key, value in payload["acceptance"].items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Controls", ""])
    for row in payload["controls"][:30]:
        lines.append(
            "- "
            f"`{row['state_id']}` {row['control_role']} result=`{row['result']}` "
            f"provider=`{row.get('selected_provider')}` source=`{row['source_artifact']}`"
        )
    if len(payload["controls"]) > 30:
        lines.append(f"- ... `{len(payload['controls']) - 30}` additional controls omitted")
    lines.extend(["", f"Next step: `{payload['decision']['recommended_next_step']}`", ""])
    return "\n".join(lines)


def main() -> None:
    payload = build_recovery()
    (ROOT / OUT_JSON).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (ROOT / OUT_MD).write_text(render_markdown(payload), encoding="utf-8")


if __name__ == "__main__":
    main()
