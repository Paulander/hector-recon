#!/usr/bin/env python3
"""Audit whether existing Stage 7 artifacts can backfill clean success controls.

This script is replay-free and non-causal. It explains why the current
sequence-policy benchmark still requires new held-out Stage 7 clean labels:
many existing success rows are duplicate state/move controls, while richer
success rows are sandbox-sourced and cannot close the clean-control gate.
"""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "reports/structural_candidates/stage7_clean_artifact_manifest_v0.json"
CLEAN_RECOVERY = ROOT / "reports/structural_candidates/stage7_clean_sequence_control_recovery_v0.json"
POST_BOX_RECOVERY = (
    ROOT / "reports/structural_candidates/stage7_post_box_sequence_control_recovery_v0.json"
)
OUTPUT_JSON = ROOT / "reports/structural_candidates/stage7_clean_success_backfill_audit_v0.json"
OUTPUT_MD = ROOT / "reports/structural_candidates/stage7_clean_success_backfill_audit_v0.md"

SCHEMA_VERSION = "stage7_clean_success_backfill_audit.v0"

COMMON_FALSE_FLAGS = {
    "runtime_behavior_changed": False,
    "runtime_defaults_changed": False,
    "runtime_selector_implemented": False,
    "runtime_score_changes": False,
    "runtime_direct_routing": False,
    "runtime_dtm_or_tablebase_lookup": False,
    "gameplay_topology_mutation": False,
    "stage7_promotion_allowed": False,
    "stage8_training_allowed": False,
}


def _load(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise TypeError(f"{path} must contain a JSON object")
    return data


def _control_key(row: dict[str, Any]) -> tuple[str, str, str] | None:
    fen = row.get("fen")
    move = row.get("move_uci") or row.get("move")
    result = row.get("result") or row.get("source_observed_outcome")
    if not fen or not move or not result:
        return None
    return str(fen), str(move), str(result)


def _packet_key(terms: dict[str, Any]) -> tuple[str, str, str] | None:
    fen = terms.get("fen")
    move = terms.get("move")
    result = terms.get("playout_result")
    if not fen or not move or not result:
        return None
    return str(fen), str(move), str(result)


def _is_h40_compatible_result(terms: dict[str, Any]) -> bool:
    result = terms.get("playout_result")
    max_plies = terms.get("max_plies")
    plies = terms.get("plies")
    if result not in {"mate", "max_plies", "draw"}:
        return False
    if isinstance(max_plies, int) and max_plies > 40:
        return False
    if result == "mate" and isinstance(plies, int) and plies > 40:
        return False
    if result != "mate" and max_plies != 40:
        return False
    return True


def _recover_manifest_candidate_rows(
    manifest: dict[str, Any],
) -> tuple[list[dict[str, Any]], Counter[str]]:
    rows: list[dict[str, Any]] = []
    skipped: Counter[str] = Counter()
    for manifest_row in manifest.get("rows") or []:
        if not isinstance(manifest_row, dict):
            continue
        if manifest_row.get("candidate_for_clean_control_recovery") is not True:
            continue
        artifact = manifest_row.get("artifact")
        if not artifact:
            skipped["missing_artifact"] += 1
            continue
        artifact_path = ROOT / str(artifact)
        if not artifact_path.exists():
            skipped["missing_artifact_file"] += 1
            continue
        payload = _load(artifact_path)
        for packet in payload.get("handoff_packets") or []:
            if not isinstance(packet, dict) or packet.get("phase") != "playout_summary":
                continue
            terms = packet.get("evidence_terms") or {}
            if not isinstance(terms, dict) or terms.get("label") != "box_shrink":
                continue
            if not _is_h40_compatible_result(terms):
                skipped["not_h40_compatible"] += 1
                continue
            key = _packet_key(terms)
            if key is None:
                skipped["missing_key_terms"] += 1
                continue
            rows.append(
                {
                    "artifact": artifact,
                    "classification": manifest_row.get("classification"),
                    "source_default_off_or_baseline": manifest_row.get(
                        "default_off_or_baseline_marker"
                    ),
                    "key": key,
                    "fen": key[0],
                    "move_uci": key[1],
                    "result": key[2],
                    "plies": terms.get("plies"),
                    "max_plies": terms.get("max_plies"),
                    "semantic_alignment_status": terms.get("semantic_alignment_status"),
                    "eligible_clean_source": True,
                }
            )
    return rows, skipped


def _unique_key_summary(rows: list[dict[str, Any]], *, result: str) -> dict[str, Any]:
    matching = [row for row in rows if row.get("result") == result]
    sources_by_key: dict[tuple[str, str, str], list[str]] = defaultdict(list)
    for row in matching:
        key = row.get("key")
        if isinstance(key, list):
            key = tuple(key)
        if not isinstance(key, tuple):
            key = _control_key(row)
        if key is None:
            continue
        sources_by_key[key].append(str(row.get("artifact") or row.get("source_artifact")))
    return {
        "raw_row_count": len(matching),
        "unique_key_count": len(sources_by_key),
        "duplicate_row_count": sum(max(0, len(sources) - 1) for sources in sources_by_key.values()),
        "unique_keys": [
            {
                "fen": key[0],
                "move_uci": key[1],
                "result": key[2],
                "source_count": len(sources),
                "example_sources": sorted(set(sources))[:8],
            }
            for key, sources in sorted(sources_by_key.items())
        ],
    }


def build_payload(
    *,
    manifest: dict[str, Any] | None = None,
    clean_recovery: dict[str, Any] | None = None,
    post_box_recovery: dict[str, Any] | None = None,
) -> dict[str, Any]:
    manifest = manifest or _load(MANIFEST)
    clean_recovery = clean_recovery or _load(CLEAN_RECOVERY)
    post_box_recovery = post_box_recovery or _load(POST_BOX_RECOVERY)

    manifest_rows, skipped = _recover_manifest_candidate_rows(manifest)
    clean_success_keys = {
        _control_key(row)
        for row in clean_recovery.get("controls") or []
        if row.get("control_role") == "clean_sequence_success_control"
    }
    clean_success_keys.discard(None)
    clean_failure_keys = {
        _control_key(row)
        for row in clean_recovery.get("controls") or []
        if row.get("control_role") == "clean_sequence_hard_negative"
    }
    clean_failure_keys.discard(None)
    manifest_success_keys = {
        tuple(row["key"]) for row in manifest_rows if row.get("result") == "mate"
    }
    manifest_failure_keys = {
        tuple(row["key"]) for row in manifest_rows if row.get("result") != "mate"
    }
    backfillable_success_keys = sorted(manifest_success_keys - clean_success_keys)
    post_box_success_controls = [
        row
        for row in post_box_recovery.get("controls") or []
        if row.get("source_observed_outcome") == "mate"
    ]
    post_box_unique_keys = {
        _control_key(row)
        for row in post_box_success_controls
        if _control_key(row) is not None
    }

    success_summary = _unique_key_summary(manifest_rows, result="mate")
    failure_summary = {
        "raw_row_count": sum(1 for row in manifest_rows if row.get("result") != "mate"),
        "unique_key_count": len(manifest_failure_keys),
        "current_recovered_unique_key_count": len(clean_failure_keys),
    }
    success_required = int(
        clean_recovery.get("acceptance", {}).get("clean_sequence_success_controls_required", 5)
    )
    current_success_count = len(clean_success_keys)
    eligible_new_success_count = len(backfillable_success_keys)
    projected_success_count = current_success_count + eligible_new_success_count
    can_close_gate_replay_free = projected_success_count >= success_required
    decision_status = (
        "stage7_clean_success_backfill_available"
        if can_close_gate_replay_free
        else "stage7_clean_success_backfill_exhausted_pending_label_execution"
    )

    return {
        "schema_version": SCHEMA_VERSION,
        "causal_status": "non_causal_replay_free_backfill_audit",
        **COMMON_FALSE_FLAGS,
        "source_artifacts": [
            "reports/structural_candidates/stage7_clean_artifact_manifest_v0.json",
            "reports/structural_candidates/stage7_clean_sequence_control_recovery_v0.json",
            "reports/structural_candidates/stage7_post_box_sequence_control_recovery_v0.json",
        ],
        "summary": {
            "manifest_clean_candidate_count": sum(
                1
                for row in manifest.get("rows") or []
                if isinstance(row, dict)
                and row.get("candidate_for_clean_control_recovery") is True
            ),
            "manifest_h40_compatible_row_count": len(manifest_rows),
            "manifest_h40_compatible_result_counts": dict(
                Counter(row.get("result") for row in manifest_rows)
            ),
            "current_clean_success_controls": current_success_count,
            "clean_success_controls_required": success_required,
            "manifest_unique_success_controls": len(manifest_success_keys),
            "eligible_new_success_controls": eligible_new_success_count,
            "projected_success_controls_after_backfill": projected_success_count,
            "can_close_success_gate_replay_free": can_close_gate_replay_free,
            "current_clean_hard_negative_controls": len(clean_failure_keys),
            "manifest_unique_hard_negative_controls": len(manifest_failure_keys),
            "sandbox_sourced_post_box_success_controls": len(post_box_success_controls),
            "sandbox_sourced_post_box_unique_success_controls": len(post_box_unique_keys),
            "sandbox_sourced_controls_usable_for_clean_gate": False,
            "skipped_counts": dict(skipped),
            "runtime_authorization_row_count": 0,
            "selector_training_row_count": 0,
            "stage7_training_row_count": 0,
        },
        "clean_success_key_audit": success_summary,
        "clean_hard_negative_key_audit": failure_summary,
        "backfillable_success_keys": [
            {"fen": key[0], "move_uci": key[1], "result": key[2]}
            for key in backfillable_success_keys
        ],
        "non_backfillable_success_evidence": {
            "reason": "sandbox_or_repair_sourced_success_controls_are_not_clean_heldout_controls",
            "control_count": len(post_box_success_controls),
            "unique_key_count": len(post_box_unique_keys),
            "example_controls": [
                {
                    "state_id": row.get("state_id"),
                    "fen": row.get("fen"),
                    "move_uci": row.get("move_uci"),
                    "source_artifact": row.get("source_artifact"),
                    "control_quality": row.get("control_quality"),
                }
                for row in post_box_success_controls[:10]
            ],
        },
        "decision": {
            "status": decision_status,
            "recommended_next_step": (
                "refresh_sequence_policy_inputs_with_replay_free_backfill"
                if can_close_gate_replay_free
                else "explicitly_approve_stage7_diverse_clean_label_execution_or_defer_sequence_benchmark"
            ),
            "runtime_changes_allowed": False,
            "label_run_allowed": False,
            "selector_allowed": False,
            "selector_training_allowed": False,
            "stage7_promotion_allowed": False,
            "stage8_training_allowed": False,
        },
    }


def write_markdown(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    decision = payload["decision"]
    lines = [
        "# Stage 7 Clean Success Backfill Audit v0",
        "",
        f"Status: `{decision['status']}`",
        "",
        "This replay-free audit checks whether existing clean/default-off Stage 7 artifacts can close the clean success-control gate without running new labels. It does not train, route, score, promote Stage 7, or train Stage 8.",
        "",
        "## Summary",
        "",
    ]
    for key, value in summary.items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(
        [
            "",
            "## Clean Success Keys",
            "",
            f"- raw_success_rows: `{payload['clean_success_key_audit']['raw_row_count']}`",
            f"- unique_success_keys: `{payload['clean_success_key_audit']['unique_key_count']}`",
            f"- duplicate_success_rows: `{payload['clean_success_key_audit']['duplicate_row_count']}`",
        ]
    )
    for row in payload["clean_success_key_audit"]["unique_keys"]:
        lines.append(
            f"- `{row['fen']}` move=`{row['move_uci']}` sources=`{row['source_count']}`"
        )
    lines.extend(
        [
            "",
            "## Non-Backfillable Evidence",
            "",
            f"- reason: `{payload['non_backfillable_success_evidence']['reason']}`",
            f"- sandbox_sourced_success_controls: `{payload['non_backfillable_success_evidence']['control_count']}`",
            f"- sandbox_sourced_unique_success_controls: `{payload['non_backfillable_success_evidence']['unique_key_count']}`",
            "",
            "## Decision",
            "",
            f"- recommended_next_step: `{decision['recommended_next_step']}`",
            "- runtime_changes_allowed: `false`",
            "- label_run_allowed: `false`",
            "- selector_training_allowed: `false`",
            "- Stage 7 promotion and Stage 8 training remain blocked.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    payload = build_payload()
    OUTPUT_JSON.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    OUTPUT_MD.write_text(write_markdown(payload), encoding="utf-8")
    print(
        json.dumps(
            {
                "decision": payload["decision"]["status"],
                "current_clean_success_controls": payload["summary"][
                    "current_clean_success_controls"
                ],
                "eligible_new_success_controls": payload["summary"][
                    "eligible_new_success_controls"
                ],
                "can_close_success_gate_replay_free": payload["summary"][
                    "can_close_success_gate_replay_free"
                ],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
