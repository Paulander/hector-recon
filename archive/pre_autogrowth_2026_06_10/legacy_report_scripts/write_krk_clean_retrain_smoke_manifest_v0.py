#!/usr/bin/env python3
"""Write a tiny clean KRK retrain smoke manifest.

This is a bounded execution plan for command plumbing only. It is intentionally
not a substitute for the full clean curriculum run.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PREFLIGHT = Path("reports/krk_clean_retrain_preflight_v0.json")
OUT_JSON = Path("reports/krk_clean_retrain_smoke_manifest_v0.json")
OUT_MD = Path("reports/krk_clean_retrain_smoke_manifest_v0.md")
SMOKE_ROOT = Path("snapshots/krk_triplet_pipeline/clean_retrain_checkpoint_v0_smoke")
PYTHON = ".venv/bin/python3"


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def build_payload() -> dict[str, Any]:
    preflight = _load(PREFLIGHT)
    output_dir = SMOKE_ROOT / "stage2a_edge_trap_close_smoke" / "baseline"
    topology_path = SMOKE_ROOT / "stage2a_edge_trap_close_smoke" / "topology" / "krk_entry_topology.json"
    learner_path = output_dir / "final_learner.pkl"
    expected_outputs = [str(learner_path), str(topology_path)]
    output_collisions = [path for path in expected_outputs if (ROOT / path).exists()]
    train_cmd = [
        "UV_CACHE_DIR=/tmp/uv-cache",
        "uv",
        "run",
        "python",
        "scripts/train_baseline_krk_chain.py",
        "--stage0-cycles",
        "1",
        "--stage1-cycles",
        "1",
        "--samples-per-cycle",
        "8",
        "--output-dir",
        str(output_dir),
        "--save-learner",
        str(learner_path),
        "--device",
        "cpu",
        "--seed",
        "7",
        "--snapshot-every",
        "0",
        "--min-mature-for-goals",
        "6",
        "--feature-set",
        "krk_rich_v1",
        "--max-curriculum-stage",
        "1",
        "--stage1-position-mode",
        "mate_in_2",
        "--stage0-balance-corners",
    ]
    compile_cmd = [
        "UV_CACHE_DIR=/tmp/uv-cache",
        "uv",
        "run",
        "python",
        "scripts/baseline_to_recon.py",
        "--learner",
        str(learner_path),
        "--output",
        str(topology_path),
    ]
    parse_cmd = [
        "UV_CACHE_DIR=/tmp/uv-cache",
        "uv",
        "run",
        "python",
        "-c",
        (
            "import json, pathlib; "
            f"p=pathlib.Path('{topology_path}'); "
            "d=json.loads(p.read_text()); "
            "assert 'nodes' in d and 'edges' in d"
        ),
    ]
    blockers = []
    if output_collisions:
        blockers.append("smoke_output_collision")
    if not (preflight.get("decision") or {}).get("safe_to_request_run_review"):
        blockers.append("clean_retrain_preflight_not_ready")
    return {
        "schema_version": "krk_clean_retrain_smoke_manifest.v0",
        "causal_status": "bounded_smoke_manifest_only_not_run",
        "source_artifacts": [str(PREFLIGHT)],
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_selector_implemented": False,
        "runtime_score_changes": False,
        "runtime_direct_routing": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "selector_training_allowed": False,
        "smoke_scope": {
            "purpose": "command_plumbing_only",
            "stage_scope": ["stage0_mate_in_1", "stage1_backchain"],
            "samples_per_cycle": 8,
            "stage0_cycles": 1,
            "stage1_cycles": 1,
            "max_curriculum_stage": 1,
            "stage7_rows": 0,
            "stage8_training": False,
        },
        "output_root": str(SMOKE_ROOT),
        "expected_outputs": expected_outputs,
        "output_collisions": output_collisions,
        "commands": {
            "train_smoke": train_cmd,
            "compile_topology": compile_cmd,
            "parse_topology": parse_cmd,
        },
        "blockers": blockers,
        "decision": {
            "status": (
                "clean_retrain_smoke_manifest_ready_not_run"
                if not blockers
                else "clean_retrain_smoke_manifest_blocked"
            ),
            "smoke_run_authorized_by_this_manifest": False,
            "full_run_authorized_by_this_manifest": False,
            "safe_to_request_smoke_run_approval": not blockers,
            "runtime_selector_allowed": False,
            "recommended_next_step": (
                "request_explicit_smoke_run_approval"
                if not blockers
                else "fix_smoke_manifest_blockers"
            ),
        },
    }


def write_markdown(payload: dict[str, Any]) -> None:
    lines = [
        "# KRK Clean Retrain Smoke Manifest v0",
        "",
        "This is a tiny command-plumbing smoke manifest. It does not run training and is not a full curriculum validation.",
        "",
        "## Decision",
        "",
    ]
    for key, value in payload["decision"].items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Smoke Scope", ""])
    for key, value in payload["smoke_scope"].items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Commands", ""])
    for key, command in payload["commands"].items():
        lines.append(f"- {key}: `" + " ".join(str(part) for part in command) + "`")
    lines.extend(["", "## Blockers", ""])
    if payload["blockers"]:
        for blocker in payload["blockers"]:
            lines.append(f"- `{blocker}`")
    else:
        lines.append("- `none`")
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "The smoke scope excludes Stage 7 and Stage 8, does not enable candidate-generation observation as causal behavior, and does not authorize the full clean retrain.",
        ]
    )
    (ROOT / OUT_MD).write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    payload = build_payload()
    (ROOT / OUT_JSON).write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    write_markdown(payload)
    print(json.dumps(payload["decision"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
