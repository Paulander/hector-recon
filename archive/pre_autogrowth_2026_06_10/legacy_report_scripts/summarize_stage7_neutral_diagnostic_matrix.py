#!/usr/bin/env python3
"""Summarize Stage 7 evidence into a neutral diagnostic matrix.

This script is report-only. It reads existing non-causal artifacts and writes a
matrix that distinguishes the active Stage 7 hypotheses without changing
runtime behavior, mutating topology, or adding a repair path.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


HYPOTHESIS_IDS = [
    "strategy_arbitration_phase_boundary",
    "continuation_capacity",
    "missing_feature_ontology",
    "training_objective_model_expression",
    "bad_standalone_curriculum_boundary",
]


def _load_optional_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _artifact(path: Path) -> dict[str, Any]:
    return {
        "path": str(path),
        "exists": path.exists(),
    }


def _rate_text(value: Any) -> str:
    if isinstance(value, (int, float)):
        return f"{value:.3f}"
    return "unknown"


def _count_text(value: Any) -> str:
    if isinstance(value, int):
        return str(value)
    return "unknown"


def _evidence_artifacts(root: Path) -> dict[str, dict[str, Any]]:
    names = {
        "family_diagnosis": "stage7_post_box_family_diagnosis.json",
        "remaining_dtm": "stage7_remaining_dtm_candidate_summary.json",
        "candidate_move_0926": "stage7_0926_move_shape_role_candidate_audit.json",
        "candidate_move_2cc": "stage7_2cc_candidate_move_dtm_alignment.json",
        "m3_trainability": "stage7_post_box_m3_trainability_assessment.json",
        "capsule_fidelity": "stage7_capsule_trajectory_fidelity_audit.json",
        "expanded_capsule_fidelity": "stage7_expanded_ranked_capsule_trajectory_fidelity_audit.json",
        "expanded_capsule_replay": "stage7_expanded_ranked_capsule_phase1_replay_h40.json",
        "strategy_arbitration": "stage7_unified_strategy_arbitration_probe.json",
        "strategy_arbitration_dataset": "stage7_unified_strategy_arbitration_dataset.json",
    }
    return {key: _artifact(root / name) for key, name in names.items()}


def _load_artifacts(root: Path) -> dict[str, dict[str, Any]]:
    return {key: _load_optional_json(Path(item["path"])) for key, item in _evidence_artifacts(root).items()}


def _hypothesis(
    *,
    hypothesis_id: str,
    title: str,
    evidence_for: list[str],
    evidence_against: list[str],
    missing_evidence: list[str],
    confidence: str,
    recommended_next_test: str,
    forbidden_next_steps: list[str],
    next_test_causal_status: str = "non_causal",
) -> dict[str, Any]:
    if confidence not in {"low", "medium", "high"}:
        raise ValueError(f"invalid confidence: {confidence}")
    if next_test_causal_status not in {"non_causal", "sandbox_only", "causal_promoted"}:
        raise ValueError(f"invalid next_test_causal_status: {next_test_causal_status}")
    return {
        "hypothesis_id": hypothesis_id,
        "title": title,
        "evidence_for": evidence_for,
        "evidence_against": evidence_against,
        "missing_evidence": missing_evidence,
        "confidence": confidence,
        "recommended_next_test": recommended_next_test,
        "forbidden_next_steps": forbidden_next_steps,
        "next_test_causal_status": next_test_causal_status,
    }


def build_matrix(artifact_root: Path) -> dict[str, Any]:
    artifacts = _load_artifacts(artifact_root)
    artifact_index = _evidence_artifacts(artifact_root)

    family = artifacts["family_diagnosis"]
    remaining = artifacts["remaining_dtm"]
    candidate_0926 = artifacts["candidate_move_0926"]
    candidate_2cc = artifacts["candidate_move_2cc"]
    m3 = artifacts["m3_trainability"]
    capsule = artifacts["capsule_fidelity"]
    expanded = artifacts["expanded_capsule_fidelity"]
    expanded_replay = artifacts["expanded_capsule_replay"]
    arbitration = artifacts["strategy_arbitration"]

    family_counts = family.get("family_diagnosis_counts") or {}
    unresolved_count = family_counts.get("unresolved_by_existing_forced_providers_at_h80")
    forced_success_count = family_counts.get("existing_provider_can_convert_if_family_role_selects_it")

    remaining_counts = remaining.get("diagnosis_counts") or {}
    dtm_won_failed = remaining_counts.get("dtm_won_within_validation_horizon_but_current_continuation_failed")

    candidate_0926_summary = candidate_0926.get("summary") or {}
    match_0926 = candidate_0926_summary.get("total_matching_moves")

    candidate_2cc_dtm = candidate_2cc.get("dtm") or {}
    candidate_2cc_graph = candidate_2cc.get("legal_first_current_graph") or {}

    m3_counts = m3.get("counts") or {}
    m3_labels = m3.get("diagnostic_labels") or []

    capsule_acc = capsule.get("teacher_forced_accuracy") or {}
    expanded_acc = expanded.get("teacher_forced_accuracy") or {}
    expanded_result_counts = expanded_replay.get("result_counts") or {}
    expanded_selected_counts = expanded_replay.get("selected_skill_counts") or {}

    arbitration_answers = arbitration.get("answers") or {}
    arbitration_states = arbitration.get("dataset_state_count")
    arbitration_labeled = arbitration.get("labeled_state_count")
    arbitration_relevance = arbitration.get("box_area_relevance_outcome_counts") or {}

    common_forbidden = [
        "train_stage8",
        "promote_stage7",
        "add_broad_provider_bonus_or_penalty",
        "add_runtime_dtm_or_tablebase_policy",
        "mutate_topology_during_gameplay",
        "make_trace_or_candidate_records_causal",
        "change_runtime_defaults",
    ]

    hypotheses = [
        _hypothesis(
            hypothesis_id="strategy_arbitration_phase_boundary",
            title="Strategy arbitration / phase-boundary issue",
            evidence_for=[
                "Earlier family diagnosis found "
                f"{_count_text(forced_success_count)} families where an existing provider could convert if selected.",
                "The unified arbitration dataset now records provider suggestions, raw score, provider-local rank, normalized score, visible board terms, and move-shape terms in a shared evidence format.",
                "Prior broad support adapters and role-owned arbitration work showed that provider ownership can matter, which keeps arbitration as a live hypothesis.",
            ],
            evidence_against=[
                "The first bounded unified arbitration probe did not identify a better owner: "
                f"raw_global_top_conversion_rate={_rate_text(arbitration.get('raw_global_top_conversion_rate'))}, "
                f"provider_local_rank1_oracle_coverage={_rate_text(arbitration.get('provider_local_rank1_oracle_coverage'))}.",
                "The small arbitration sample had "
                f"box_area_relevance_outcome_counts={arbitration_relevance or 'unknown'}, so low box relevance / near-edge ownership is not yet supported by the sampled residuals.",
                f"Probe answers were {arbitration_answers or 'missing'}, so no causal arbitration change is justified.",
            ],
            missing_evidence=[
                "A stratified provider-suggestion dataset covering successful and failed Stage 7 states, not just three residual states.",
                "Bounded h40 labels for at most the best provider-local candidate per provider across high/medium/low box-area relevance buckets.",
                "A direct comparison of raw global score, provider-local rank, and role-owned arbitration on the same state set.",
            ],
            confidence="medium",
            recommended_next_test=(
                "Extend the unified arbitration probe only as a small, stratified, non-causal dataset: "
                "success/failure states, capped provider-best labels, h40, caches/thin traces, no runtime arbitration."
            ),
            forbidden_next_steps=common_forbidden
            + [
                "make_role_owned_arbitration_causal",
                "increase_support_bonus_to_overcome_raw_score_scale",
            ],
        ),
        _hypothesis(
            hypothesis_id="continuation_capacity",
            title="Continuation-capacity issue",
            evidence_for=[
                "Family diagnosis found "
                f"{_count_text(unresolved_count)} families unresolved by existing forced providers at h80.",
                "Remaining DTM summary reports "
                f"{_count_text(dtm_won_failed)} DTM-won-within-validation-horizon states where current continuation still failed.",
                "The learnable post-box provider can be selected, but the expanded ranked replay still reports "
                f"result_counts={expanded_result_counts or 'unknown'} with selected_skill_counts={expanded_selected_counts or 'unknown'}.",
                "M3 trainability assessment reports "
                f"probe_result={m3.get('probe_result', 'unknown')} and diagnostic labels={m3_labels or 'unknown'}.",
            ],
            evidence_against=[
                "Continuation capacity is not absent everywhere: family diagnosis found "
                f"{_count_text(forced_success_count)} families where existing providers could convert if selected.",
                "Candidate-move / DTM alignment for 2cc reports all legal moves winning in tablebase terms, so the issue may be closed-loop policy quality rather than theoretical capacity.",
            ],
            missing_evidence=[
                "A compact residual-state table separating forced-provider failure, current-graph legal-first failure, and DTM-won-but-policy-failed cases under h40.",
                "A closed-loop comparison showing whether provider ownership fails immediately, after the second/third move, or only after handoff.",
                "Evidence that a narrow provider has trainable internal move-policy edges before any new training is justified.",
            ],
            confidence="medium",
            recommended_next_test=(
                "Build a replay-free residual continuation-capacity table from existing forced-provider, legal-first, DTM, and capsule replay artifacts; "
                "only add tiny h40 labels for missing cells."
            ),
            forbidden_next_steps=common_forbidden
            + [
                "train_broad_full_krk_continuation",
                "declare_missing_capacity_from_h80_forced_failure_alone",
            ],
        ),
        _hypothesis(
            hypothesis_id="missing_feature_ontology",
            title="Missing-feature / ontology issue",
            evidence_for=[
                "The 0926 candidate-move role audit found a visible move-shape role with "
                f"total_matching_moves={_count_text(match_0926)}, showing that better visible action terms can separate at least one family.",
                "The 2cc DTM alignment artifact exposes DTM-positive trajectory terms that include box area, mobility, rook safety, and king-support deltas, which are richer than a plain box-shrink label.",
                "Earlier reward-contract and role-boundary failures show that local reward confirmation can diverge from visible semantic continuation requirements.",
            ],
            evidence_against=[
                "Expanded Plan Capsule training used richer trajectory evidence but still failed closed-loop, so missing terms alone are not proven sufficient.",
                "The latest arbitration sample did not support low box-area relevance as the missing phase-boundary term; sampled residuals were high relevance.",
                "Visible plan/candidate layers can already fire in some cases; failure persists after ownership and visibility improvements.",
            ],
            missing_evidence=[
                "A term-contrast table between successful and failed post-box continuations across phase-boundary, edge-net pressure, king-support pressure, and box relevance terms.",
                "Evidence that new terms separate residual families without overmatching successful-exit states.",
                "Worst-reply safety/progress terms for the same candidate moves where feasible.",
            ],
            confidence="medium",
            recommended_next_test=(
                "Run a replay-free visible-term contrast over existing success/failure artifacts, then add only small targeted labels for terms that are absent from current traces."
            ),
            forbidden_next_steps=common_forbidden
            + [
                "add_new_causal_visible_terms_without_separability_evidence",
                "hardcode_state_hash_or_exact_move",
            ],
        ),
        _hypothesis(
            hypothesis_id="training_objective_model_expression",
            title="Training-objective / model-expression issue",
            evidence_for=[
                "The initial capsule trajectory audit reports "
                f"DTM-positive top1={_rate_text(capsule_acc.get('dtm_positive_top1_rate'))} and "
                f"top3={_rate_text(capsule_acc.get('dtm_positive_top3_rate'))}.",
                "After expanded DTM-margin supervision, fidelity improved only modestly to "
                f"DTM-positive top1={_rate_text(expanded_acc.get('dtm_positive_top1_rate'))} and "
                f"top3={_rate_text(expanded_acc.get('dtm_positive_top3_rate'))}, while closed-loop replay remained max_plies.",
                "Strict-negative and expanded-ranked probes changed neither the diagnosis nor closed-loop conversion enough; the first positive miss remains the same 2cc family in the fidelity audit.",
                "M3 assessment indicates the previous scripted terminal path lacked useful trainable internal move-policy edges.",
            ],
            evidence_against=[
                "DTM-positive top3 around 0.800 means the representation contains partial ranking signal; the problem may be compounding/handoff rather than pure expressivity.",
                "The offline seed is still narrow and biased toward residual families, so general model-expression conclusions remain provisional.",
                "Some families were solvable by existing providers when forced, so not all Stage 7 failures require a learned post-box policy.",
            ],
            missing_evidence=[
                "A small offline benchmark comparing current scoring, pairwise/ranked preference loss, and visible-term heuristics on identical train/test trajectory states.",
                "A DAgger-style closed-loop drift table that labels states visited by the learned capsule, without using DTM at runtime.",
                "Train/test split fidelity metrics to avoid overreading a two-family residual seed.",
            ],
            confidence="high",
            recommended_next_test=(
                "Run an offline-only model-expression benchmark on existing DTM trajectory states: current learner versus ranked/pairwise scorer, with top-k fidelity and closed-loop drift diagnostics."
            ),
            forbidden_next_steps=common_forbidden
            + [
                "increase_runtime_owner_bonus",
                "tune_plan_capsule_commitment_as_a_proxy_for_policy_quality",
            ],
        ),
        _hypothesis(
            hypothesis_id="bad_standalone_curriculum_boundary",
            title="Bad standalone curriculum boundary",
            evidence_for=[
                "Stage 7 remains local_valid_composition_quarantined after local semantic improvements, support adapters, family-specific ownership, candidate-move roles, Plan Capsule ownership, and learnable overlay probes.",
                "The 2cc artifact classifies the residual as a multi-step continuation policy gap rather than a single-move gap, which suggests box_shrink may be an unstable owner near phase transitions.",
                "Plan Capsule and handoff evidence repeatedly point toward short continuation windows or edge-net/king-support concepts beyond a standalone box-shrink objective.",
            ],
            evidence_against=[
                "Box-shrink local behavior is not useless; local/one-ply semantics improved and some families can be routed to existing continuation providers.",
                "The unified arbitration sample is too small to prove a global curriculum-boundary failure.",
                "A better training objective or missing ontology terms might still make Stage 7 composable without redefining the curriculum boundary.",
            ],
            missing_evidence=[
                "A boundary audit comparing Stage 7 as standalone owner versus as a handoff trigger into edge-net, king-support, drive, fence, or mate-basin roles.",
                "Evidence from broader KRK stages showing whether box_shrink failures disappear when embedded in a larger strategy objective.",
                "A non-causal comparison of local reward labels against conversion-relevant ownership labels.",
            ],
            confidence="medium",
            recommended_next_test=(
                "Create a non-causal curriculum-boundary audit that treats box_shrink as local evidence plus handoff trigger, not as a promoted independent owner."
            ),
            forbidden_next_steps=common_forbidden
            + [
                "train_stage8_to_paper_over_stage7",
                "promote_box_shrink_as_independent_stage_from_local_success",
            ],
        ),
    ]

    current_best_interpretation = {
        "summary": (
            "Stage 7 is best treated as local_valid_composition_quarantined. The strongest current evidence is "
            "a training-objective/model-expression and closed-loop continuation gap in the learnable post-box capsule. "
            "Continuation capacity, missing ontology, and curriculum-boundary hypotheses remain plausible. The first "
            "unified strategy-arbitration probe is useful infrastructure but too small to justify causal arbitration."
        ),
        "do_not_choose_repair_yet": True,
        "next_proposed_step": (
            "Run one neutral, replay-free evidence merge that combines the diagnostic matrix with a small stratified "
            "arbitration/term/capacity table. Add only bounded h40 labels for missing cells; keep all outputs non-causal."
        ),
        "why_this_step": (
            "It distinguishes the active hypotheses without optimizing a single favored repair path or changing runtime defaults."
        ),
    }

    matrix = {
        "schema_version": "stage7_neutral_diagnostic_matrix.v1",
        "causal_status": "non_causal",
        "runtime_behavior_changed": False,
        "stage7_status": "local_valid_composition_quarantined",
        "stage8_training_allowed": False,
        "stage7_promotion_allowed": False,
        "artifact_root": str(artifact_root),
        "evidence_artifacts": artifact_index,
        "current_best_interpretation": current_best_interpretation,
        "hypotheses": hypotheses,
        "performance_rules": [
            "prefer_replay_free_analysis",
            "use_h40_as_practical_horizon",
            "use_h80_plus_only_for_classification_not_promotion",
            "avoid_exhaustive_legal_first_sweeps_by_default",
            "use_caches_parallel_workers_and_thin_traces_for_new_labels",
            "stop_if_projected_runtime_is_hours",
        ],
        "hard_constraints": common_forbidden,
    }
    validate_matrix(matrix)
    return matrix


def validate_matrix(matrix: dict[str, Any]) -> None:
    if matrix.get("schema_version") != "stage7_neutral_diagnostic_matrix.v1":
        raise ValueError("unexpected schema_version")
    if matrix.get("causal_status") != "non_causal":
        raise ValueError("matrix must be non-causal")
    if matrix.get("runtime_behavior_changed") is not False:
        raise ValueError("matrix must not change runtime behavior")
    hypotheses = matrix.get("hypotheses")
    if not isinstance(hypotheses, list) or len(hypotheses) != len(HYPOTHESIS_IDS):
        raise ValueError("matrix must include all expected hypotheses")
    ids = [item.get("hypothesis_id") for item in hypotheses if isinstance(item, dict)]
    if ids != HYPOTHESIS_IDS:
        raise ValueError(f"unexpected hypothesis order/ids: {ids}")
    required = {
        "evidence_for",
        "evidence_against",
        "missing_evidence",
        "confidence",
        "recommended_next_test",
        "forbidden_next_steps",
        "next_test_causal_status",
    }
    for item in hypotheses:
        missing = required - set(item)
        if missing:
            raise ValueError(f"hypothesis {item.get('hypothesis_id')} missing {sorted(missing)}")
        if item["next_test_causal_status"] == "causal_promoted":
            raise ValueError("next tests must not be causal/promoted for this matrix")


def render_markdown(matrix: dict[str, Any]) -> str:
    lines: list[str] = [
        "# Stage 7 Neutral Diagnostic Matrix",
        "",
        "This report is non-causal. It does not change runtime behavior, promote Stage 7, train Stage 8, or add a repair path.",
        "",
        "## Current Best Interpretation",
        "",
        str(matrix["current_best_interpretation"]["summary"]),
        "",
        f"Next proposed step: {matrix['current_best_interpretation']['next_proposed_step']}",
        "",
        f"Justification: {matrix['current_best_interpretation']['why_this_step']}",
        "",
        "## Matrix",
        "",
    ]
    for hypothesis in matrix["hypotheses"]:
        lines.extend(
            [
                f"### {hypothesis['title']}",
                "",
                f"- Confidence: {hypothesis['confidence']}",
                f"- Next test causal status: {hypothesis['next_test_causal_status']}",
                "",
                "Evidence for:",
            ]
        )
        lines.extend(f"- {item}" for item in hypothesis["evidence_for"])
        lines.append("")
        lines.append("Evidence against:")
        lines.extend(f"- {item}" for item in hypothesis["evidence_against"])
        lines.append("")
        lines.append("Missing evidence:")
        lines.extend(f"- {item}" for item in hypothesis["missing_evidence"])
        lines.append("")
        lines.append(f"Recommended next test: {hypothesis['recommended_next_test']}")
        lines.append("")
        lines.append("Forbidden next steps:")
        lines.extend(f"- {item}" for item in hypothesis["forbidden_next_steps"])
        lines.append("")
    lines.extend(
        [
            "## Evidence Artifacts",
            "",
        ]
    )
    for key, item in matrix["evidence_artifacts"].items():
        status = "present" if item["exists"] else "missing"
        lines.append(f"- {key}: {status} - `{item['path']}`")
    lines.extend(
        [
            "",
            "## Performance Rules",
            "",
        ]
    )
    lines.extend(f"- {item}" for item in matrix["performance_rules"])
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact-root", type=Path, default=Path("reports/structural_candidates"))
    parser.add_argument("--json-output", type=Path, required=True)
    parser.add_argument("--markdown-output", type=Path, required=True)
    parser.add_argument("--no-json-stdout", action="store_true")
    args = parser.parse_args()

    matrix = build_matrix(args.artifact_root)
    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(json.dumps(matrix, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.markdown_output.write_text(render_markdown(matrix), encoding="utf-8")
    if not args.no_json_stdout:
        print(json.dumps(matrix, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
