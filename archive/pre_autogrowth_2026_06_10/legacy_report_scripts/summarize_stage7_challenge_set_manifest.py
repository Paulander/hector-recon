#!/usr/bin/env python3
"""Create the Stage 7 challenge set manifest for KRK strategy arbitration.

The manifest marks Stage 7 residuals as held-out challenge cases for future
strategy-arbitration / plan-selection work. It is non-causal documentation and
does not implement repairs or run new labels.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any


CHALLENGE_FAMILIES = [
    {
        "family_key": "0926_candidate_move",
        "display_name": "0926-like candidate-move family",
        "source_artifacts": [
            "stage7_0926_move_shape_role_candidate_audit.json",
            "stage7_0926_candidate_move_layer_smoke.json",
        ],
        "tests_hypotheses": ["missing_feature_ontology", "strategy_arbitration_phase_boundary"],
        "known_partial_success": "CandidateMoveFrame role identified exactly one visible matching move in the 0926 case.",
        "rejected_repair": "Do not hardcode e4d3 or create state-hash move exceptions.",
    },
    {
        "family_key": "069_drive_fence",
        "display_name": "069-like drive/fence arbitration families",
        "source_artifacts": [
            "stage7_069_drive_support_post_box_diagnosis.json",
            "stage7_069_score_normalization_probe.json",
            "stage7_drive_fence_family_balanced_summary.json",
        ],
        "tests_hypotheses": ["strategy_arbitration_phase_boundary", "bad_curriculum_boundary"],
        "known_partial_success": "Drive/fence family-specific ownership repairs showed existing providers can solve some cases.",
        "rejected_repair": "Do not revive broad drive support or broad score bonuses.",
    },
    {
        "family_key": "2cc_post_box_continuation",
        "display_name": "2cc-like post-box continuation families",
        "source_artifacts": [
            "stage7_2cc_candidate_move_dtm_alignment.json",
            "stage7_capsule_trajectory_fidelity_audit.json",
            "stage7_expanded_ranked_capsule_trajectory_fidelity_audit.json",
        ],
        "tests_hypotheses": ["training_objective_model_expression", "continuation_capacity"],
        "known_partial_success": "DTM/top-k labels show theoretical signal, but learned capsule ownership still failed closed loop.",
        "rejected_repair": "Do not use DTM/tablebase at runtime and do not tune Plan Capsule micro-parameters again.",
    },
    {
        "family_key": "plan_capsule_owned_residuals",
        "display_name": "Plan Capsule owned-arbitration residuals",
        "source_artifacts": [
            "stage7_plan_capsule_owned_failure_analysis_50_h40.json",
            "stage7_expanded_ranked_capsule_phase1_replay_h40.json",
        ],
        "tests_hypotheses": ["continuation_capacity", "training_objective_model_expression"],
        "known_partial_success": "Plan Capsule entry/owned-window instrumentation made multi-ply failures inspectable.",
        "rejected_repair": "Do not add another runtime Plan Capsule tweak from this checkpoint.",
    },
    {
        "family_key": "reward_contract_mismatch",
        "display_name": "box_shrink reward/contract mismatch cases",
        "source_artifacts": [
            "stage7_box_shrink_semantic_audit.json",
            "stage7_box_shrink_candidates.json",
        ],
        "tests_hypotheses": ["missing_feature_ontology", "bad_curriculum_boundary"],
        "known_partial_success": "Growth Monitor / StructuralCandidate path captured mismatch evidence non-causally.",
        "rejected_repair": "Do not promote Stage 7 from local reward confirmation alone.",
    },
    {
        "family_key": "stage0_fallback_failures",
        "display_name": "known stage0_basin fallback failures",
        "source_artifacts": [
            "stage7_evidence_merge_table.json",
            "stage7_unified_strategy_arbitration_dataset.json",
        ],
        "tests_hypotheses": ["strategy_arbitration_phase_boundary", "bad_curriculum_boundary"],
        "known_partial_success": "Evidence shows high-scoring fallback ownership can be wrong near post-box boundaries.",
        "rejected_repair": "Do not add broad stage0 suppression.",
    },
]


def _load_optional_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _artifact_presence(root: Path, names: list[str]) -> dict[str, bool]:
    return {name: (root / name).exists() for name in names}


def build_manifest(artifact_root: Path) -> dict[str, Any]:
    evidence_merge = _load_optional_json(artifact_root / "stage7_evidence_merge_table.json")
    dataset = _load_optional_json(Path("reports/strategy_arbitration/krk_strategy_arbitration_dataset_v0.json"))
    rows = evidence_merge.get("rows") or []
    records = dataset.get("records") or []
    hypothesis_counts = Counter(label for row in rows for label in row.get("hypothesis_labels") or [])

    families = []
    for family in CHALLENGE_FAMILIES:
        family = dict(family)
        family["artifact_presence"] = _artifact_presence(artifact_root, family["source_artifacts"])
        family["causal_status"] = "non_causal_challenge_case"
        family["optimization_target"] = False
        family["held_out_challenge_case"] = True
        families.append(family)

    manifest = {
        "schema_version": "stage7_challenge_set_manifest.v1",
        "causal_status": "non_causal_manifest",
        "runtime_behavior_changed": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_status": "local_valid_composition_quarantined",
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "purpose": "Treat Stage 7 residuals as held-out KRK strategy-arbitration challenge cases, not as the current optimization target.",
        "summary": {
            "challenge_family_count": len(families),
            "evidence_merge_row_count": len(rows),
            "strategy_dataset_record_count": len(records),
            "evidence_hypothesis_label_counts": dict(hypothesis_counts),
        },
        "families": families,
        "global_rejected_paths": [
            "stage7_runtime_repair",
            "support_adapter",
            "score_bonus_or_provider_penalty",
            "stage0_suppression",
            "plan_capsule_micro_tuning",
            "runtime_dtm_or_tablebase",
            "stage7_promotion",
            "stage8_training",
        ],
        "recommended_use": "Use these families to evaluate whether a broader KRK strategy arbiter explains ownership, feature, continuation, and curriculum-boundary failures.",
    }
    validate_manifest(manifest)
    return manifest


def validate_manifest(manifest: dict[str, Any]) -> None:
    if manifest.get("schema_version") != "stage7_challenge_set_manifest.v1":
        raise ValueError("unexpected manifest schema")
    if manifest.get("causal_status") != "non_causal_manifest":
        raise ValueError("manifest must be non-causal")
    if manifest.get("runtime_behavior_changed") is not False:
        raise ValueError("manifest must not change runtime behavior")
    if manifest.get("runtime_dtm_or_tablebase_lookup") is not False:
        raise ValueError("manifest must not use runtime DTM/tablebase")
    if manifest.get("stage7_promotion_allowed") is not False or manifest.get("stage8_training_allowed") is not False:
        raise ValueError("Stage 7 promotion and Stage 8 training must remain blocked")
    if not manifest.get("families"):
        raise ValueError("manifest must include challenge families")


def render_markdown(manifest: dict[str, Any]) -> str:
    lines = [
        "# Stage 7 Challenge Set Manifest",
        "",
        "This manifest is non-causal. Stage 7 residuals are held-out challenge cases for KRK strategy arbitration, not local repair targets.",
        "",
        "## Status",
        "",
        f"- Stage 7 status: `{manifest['stage7_status']}`",
        f"- Stage 7 promotion allowed: `{manifest['stage7_promotion_allowed']}`",
        f"- Stage 8 training allowed: `{manifest['stage8_training_allowed']}`",
        f"- Runtime behavior changed: `{manifest['runtime_behavior_changed']}`",
        "",
        "## Summary",
        "",
        f"- Challenge families: `{manifest['summary']['challenge_family_count']}`",
        f"- Evidence merge rows: `{manifest['summary']['evidence_merge_row_count']}`",
        f"- Strategy dataset records: `{manifest['summary']['strategy_dataset_record_count']}`",
        f"- Evidence hypothesis labels: `{manifest['summary']['evidence_hypothesis_label_counts']}`",
        "",
        "## Families",
        "",
    ]
    for family in manifest["families"]:
        lines.extend(
            [
                f"### {family['display_name']}",
                "",
                f"- Family key: `{family['family_key']}`",
                f"- Tests hypotheses: `{family['tests_hypotheses']}`",
                f"- Known partial success: {family['known_partial_success']}",
                f"- Rejected repair: {family['rejected_repair']}",
                f"- Artifact presence: `{family['artifact_presence']}`",
                "",
            ]
        )
    lines.extend(["## Global Rejected Paths", ""])
    lines.extend(f"- {item}" for item in manifest["global_rejected_paths"])
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact-root", type=Path, default=Path("reports/structural_candidates"))
    parser.add_argument("--json-output", type=Path, required=True)
    parser.add_argument("--markdown-output", type=Path, required=True)
    parser.add_argument("--no-json-stdout", action="store_true")
    args = parser.parse_args()

    manifest = build_manifest(args.artifact_root)
    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.markdown_output.write_text(render_markdown(manifest), encoding="utf-8")
    if not args.no_json_stdout:
        print(json.dumps(manifest, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
