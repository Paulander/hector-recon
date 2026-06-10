#!/usr/bin/env python3
"""Validate additional Stage 7 clean label outputs without executing labels."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DIVERSE_VALIDATOR = ROOT / "scripts/validate_stage7_diverse_clean_sampling_outputs_v0.py"
MANIFEST = ROOT / "reports/structural_candidates/stage7_additional_clean_sampling_manifest_v0.json"
OUTPUT_JSON = ROOT / "reports/structural_candidates/stage7_additional_clean_sampling_output_validation_v0.json"
OUTPUT_MD = ROOT / "reports/structural_candidates/stage7_additional_clean_sampling_output_validation_v0.md"


def _load_validator():
    spec = importlib.util.spec_from_file_location(DIVERSE_VALIDATOR.stem, DIVERSE_VALIDATOR)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load validator script: {DIVERSE_VALIDATOR}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


validator = _load_validator()


def _additional_status(status: str | None) -> str | None:
    if status is None:
        return None
    return status.replace("stage7_diverse_clean_sampling", "stage7_additional_clean_sampling")


def build_payload(*, manifest: dict[str, Any] | None = None) -> dict[str, Any]:
    manifest = manifest or json.loads(MANIFEST.read_text(encoding="utf-8"))
    if (
        (manifest.get("decision") or {}).get("status")
        == "stage7_additional_clean_sampling_manifest_not_applicable_success_gate_closed"
    ):
        return {
            "schema_version": "stage7_additional_clean_sampling_output_validation.v0",
            "causal_status": "non_causal_output_validation",
            **validator.COMMON_FALSE_FLAGS,
            "source_artifacts": [
                "reports/structural_candidates/stage7_additional_clean_sampling_manifest_v0.json"
            ],
            "summary": {
                "job_count": 0,
                "output_exists_count": 0,
                "output_valid_count": 0,
                "all_outputs_present": False,
                "all_present_outputs_valid": True,
                "all_outputs_valid": False,
                "parse_error_count": 0,
                "parsed_playout_count": 0,
                "result_counts": {},
                "issue_counts": {},
                "stage7_training_row_count": 0,
                "selector_training_row_count": 0,
                "runtime_authorization_row_count": 0,
            },
            "output_checks": [],
            "decision": {
                "status": (
                    "stage7_additional_clean_sampling_outputs_not_applicable_success_gate_closed"
                ),
                "recommended_next_step": "rerun_passive_sequence_policy_gate_stack",
                "runtime_changes_allowed": False,
                "label_run_allowed": False,
                "selector_allowed": False,
                "selector_training_allowed": False,
                "stage7_promotion_allowed": False,
                "stage8_training_allowed": False,
            },
        }

    original_manifest = validator.MANIFEST
    try:
        validator.MANIFEST = MANIFEST
        payload = validator.build_payload(manifest=manifest)
    finally:
        validator.MANIFEST = original_manifest

    payload["schema_version"] = "stage7_additional_clean_sampling_output_validation.v0"
    payload["source_artifacts"] = [
        "reports/structural_candidates/stage7_additional_clean_sampling_manifest_v0.json"
    ]
    payload["decision"]["status"] = _additional_status(payload["decision"].get("status"))
    payload["decision"]["recommended_next_step"] = _additional_status(
        payload["decision"].get("recommended_next_step")
    )
    return payload


def write_markdown(payload: dict[str, Any]) -> str:
    rendered = validator.write_markdown(payload)
    return (
        rendered.replace("Stage 7 Diverse Clean Sampling", "Stage 7 Additional Clean Sampling")
        .replace("stage7_diverse_clean_sampling", "stage7_additional_clean_sampling")
        .replace("diverse-clean", "additional-clean")
    )


def main() -> None:
    payload = build_payload()
    OUTPUT_JSON.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    OUTPUT_MD.write_text(write_markdown(payload), encoding="utf-8")
    print(f"wrote {OUTPUT_JSON.relative_to(ROOT)}")
    print(f"wrote {OUTPUT_MD.relative_to(ROOT)}")
    print(payload["decision"]["status"])


if __name__ == "__main__":
    main()
