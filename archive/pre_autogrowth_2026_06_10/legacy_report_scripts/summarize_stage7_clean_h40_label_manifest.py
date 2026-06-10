#!/usr/bin/env python3
"""Define a bounded clean Stage 7 h40 label job to fill control gaps."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
RECOVERY = Path("reports/structural_candidates/stage7_clean_sequence_control_recovery_v0.json")
TOPOLOGY = Path(
    "snapshots/krk_triplet_pipeline/adaptive_krk_stage6_drive_overlay_composed/topology/krk_entry_topology.json"
)
OUT_JSON = Path("reports/structural_candidates/stage7_clean_h40_label_manifest_v0.json")
OUT_MD = Path("reports/structural_candidates/stage7_clean_h40_label_manifest_v0.md")
PLANNED_OUTPUT = Path("reports/structural_candidates/stage7_clean_h40_label_run_seed17_10_h40.json")


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def build_manifest() -> dict[str, Any]:
    recovery = _load(RECOVERY)
    success_have = int(
        (recovery.get("summary", {}).get("role_counts") or {}).get("clean_sequence_success_control", 0) or 0
    )
    negative_have = int(
        (recovery.get("summary", {}).get("role_counts") or {}).get("clean_sequence_hard_negative", 0) or 0
    )
    success_required = int(
        recovery.get("acceptance", {}).get("clean_sequence_success_controls_required", 5) or 5
    )
    success_gap = max(0, success_required - success_have)
    job = {
        "job_id": "stage7.clean_h40.seed17.samples10.v0",
        "purpose": "fill_clean_stage7_sequence_success_control_gap",
        "topology": str(TOPOLOGY),
        "label": "box_shrink",
        "samples": 10,
        "seed": 17,
        "playout_max_plies": 40,
        "composition_profile": "handoff_composition_v1",
        "position_mode": "curriculum",
        "black_policy": "adversarial",
        "enable_diagnostic_caches": True,
        "parallel_workers": 1,
        "trace_mode": "thin_handoff_packets_no_full_playout_traces",
        "json_output": str(PLANNED_OUTPUT),
        "forbidden_flags": [
            "--enable-stage7-king-tempo",
            "--enable-stage7-drive-repair",
            "--enable-stage7-post-king-tempo",
            "--enable-stage7-post-box-continuation",
            "--enable-stage7-learned-post-box-continuation",
            "--enable-stage7-post-box-frozen-model-candidate",
            "--enable-stage7-plan-capsule",
            "--enable-candidate-move-layer",
            "--enable-stage7-king-support-fence-stabilizer",
            "--enable-krk-strategy-arbiter-sandbox",
            "--enable-krk-two-stage-abstention-selector",
        ],
        "command": [
            "uv",
            "run",
            "python",
            "scripts/test_krk_landmark_progress.py",
            "--topology",
            str(TOPOLOGY),
            "--label",
            "box_shrink",
            "--samples",
            "10",
            "--seed",
            "17",
            "--playout-max-plies",
            "40",
            "--composition-profile",
            "handoff_composition_v1",
            "--enable-diagnostic-caches",
            "--early-stop-stable-suggestions",
            "2",
            "--json-output",
            str(PLANNED_OUTPUT),
            "--no-json-stdout",
        ],
    }
    label_run_allowed = success_gap > 0 and TOPOLOGY.exists()
    return {
        "schema_version": "stage7_clean_h40_label_manifest.v0",
        "causal_status": "non_causal_label_manifest",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_selector_implemented": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "source_artifacts": [str(RECOVERY)],
        "current_control_gap": {
            "clean_sequence_success_controls_have": success_have,
            "clean_sequence_success_controls_required": success_required,
            "clean_sequence_success_controls_gap": success_gap,
            "clean_sequence_hard_negatives_have": negative_have,
        },
        "jobs": [job],
        "summary": {
            "job_count": 1,
            "max_total_samples": 10,
            "max_horizon": 40,
            "topology_exists": TOPOLOGY.exists(),
            "planned_output": str(PLANNED_OUTPUT),
            "label_run_allowed_by_manifest": label_run_allowed,
            "runtime_work_allowed": False,
        },
        "decision": {
            "status": "bounded_clean_h40_label_manifest_ready" if label_run_allowed else "no_label_run_needed_or_topology_missing",
            "recommended_next_step": "run_single_bounded_clean_h40_label_job" if label_run_allowed else "review_clean_control_gap",
            "runtime_work_allowed": False,
        },
    }


def render_markdown(payload: dict[str, Any]) -> str:
    job = payload["jobs"][0]
    lines = [
        "# Stage 7 Clean h40 Label Manifest v0",
        "",
        f"Status: `{payload['decision']['status']}`",
        "",
        "Bounded non-causal label manifest to fill clean Stage 7 sequence-control gaps. This is a data-labeling job only; it does not enable any runtime repair.",
        "",
        "## Current Gap",
        "",
    ]
    for key, value in payload["current_control_gap"].items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(
        [
            "",
            "## Job",
            "",
            f"- job_id: `{job['job_id']}`",
            f"- samples: `{job['samples']}`",
            f"- horizon: `{job['playout_max_plies']}`",
            f"- seed: `{job['seed']}`",
            f"- output: `{job['json_output']}`",
            "",
            "Command:",
            "",
            "```bash",
            " ".join(job["command"]),
            "```",
            "",
            "Forbidden flags:",
            "",
        ]
    )
    for flag in job["forbidden_flags"]:
        lines.append(f"- `{flag}`")
    lines.extend(["", f"Next step: `{payload['decision']['recommended_next_step']}`", ""])
    return "\n".join(lines)


def main() -> None:
    payload = build_manifest()
    (ROOT / OUT_JSON).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (ROOT / OUT_MD).write_text(render_markdown(payload), encoding="utf-8")


if __name__ == "__main__":
    main()
