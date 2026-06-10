#!/usr/bin/env python3
"""Design and probe visible runtime proxy candidates for paired KRK ownership.

This is an evidence/design package only. It translates the successful offline
paired-ownership semantic gate into candidate visible proxy terms, then checks
how much signal is recoverable without using forbidden outcome labels.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
INVENTORY = Path("reports/krk_state_local_paired_ownership_inventory_v1.json")
PROBE_V1 = Path("reports/krk_state_local_paired_ownership_probe_v1.json")
ERROR_AUDIT = Path("reports/krk_state_local_paired_ownership_error_audit_v0.json")
RUNTIME_PACKET = Path("reports/krk_state_local_paired_selector_runtime_review_packet_v0.json")

OUT_DESIGN_JSON = Path("reports/krk_state_local_paired_runtime_proxy_design_v0.json")
OUT_DESIGN_MD = Path("reports/krk_state_local_paired_runtime_proxy_design_v0.md")
OUT_DATASET_JSON = Path("reports/krk_state_local_paired_runtime_proxy_dataset_v0.json")
OUT_DATASET_MD = Path("reports/krk_state_local_paired_runtime_proxy_dataset_v0.md")
OUT_PROBE_JSON = Path("reports/krk_state_local_paired_runtime_proxy_probe_v0.json")
OUT_PROBE_MD = Path("reports/krk_state_local_paired_runtime_proxy_probe_v0.md")
OUT_REVIEW_JSON = Path("reports/krk_state_local_paired_runtime_proxy_review_v0.json")
OUT_REVIEW_MD = Path("reports/krk_state_local_paired_runtime_proxy_review_v0.md")


RUNTIME_FALSE_KEYS = (
    "runtime_behavior_changed",
    "runtime_defaults_changed",
    "runtime_selector_implemented",
    "runtime_candidate_generator_implemented",
    "runtime_terminals_added",
    "runtime_dtm_or_tablebase_lookup",
    "gameplay_topology_mutation",
    "stage7_promotion_allowed",
    "stage8_training_allowed",
    "selector_training_allowed",
)


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _runtime_false_block() -> dict[str, bool]:
    return {key: False for key in RUNTIME_FALSE_KEYS}


def _nested(row: dict[str, Any], path: str) -> Any:
    value: Any = row
    for part in path.split("."):
        if not isinstance(value, dict):
            return None
        value = value.get(part)
    return value


def _context_term(row: dict[str, Any], prefix: str) -> str:
    for term in row.get("context_terms") or []:
        if str(term).startswith(prefix):
            return str(term).split(":", 1)[1]
    return "missing"


def _target_failure_risk(row: dict[str, Any]) -> bool:
    return row.get("comparison_label") == "prefer_capacity_alternative"


def _target_safe_preservation(row: dict[str, Any]) -> bool:
    return row.get("comparison_label") != "prefer_capacity_alternative"


def _source_stage_group(stage: str | None) -> str:
    if stage in {"stage4", "stage5", "stage6"}:
        return str(stage)
    return "other"


def _proxy_terms(row: dict[str, Any]) -> dict[str, Any]:
    terminal = row.get("terminal_space_context") or {}
    forced_capacity_only = (
        row.get("owner_b_evidence_channel") == "forced_capacity"
        and row.get("owner_b_role") == "forced_capacity_alternative"
    )
    normal_selected_owner = row.get("owner_a_evidence_channel") == "normal_selected_playout"
    selected_owner_family = str(row.get("owner_a_family") or "unknown")
    alternative_family = str(row.get("owner_b_family") or "unknown")
    selected_provider_validated_family = selected_owner_family in {
        "stage0_basin",
        "edge_trap",
        "fence_established",
        "drive_to_edge",
    }
    protected_stage = row.get("source_stage") in {"stage4", "stage5", "stage6"}
    return {
        "selected_owner_family": selected_owner_family,
        "alternative_owner_family": alternative_family,
        "family_pair": f"{selected_owner_family}->{alternative_family}",
        "source_stage": _source_stage_group(row.get("source_stage")),
        "active_landmark_label": row.get("active_landmark_label") or "missing",
        "black_king_edge_bucket": terminal.get("black_king_edge_bucket") or "missing",
        "box_area_relevance": terminal.get("box_area_relevance") or "missing",
        "white_king_support_bucket": terminal.get("white_king_support_bucket") or "missing",
        "rook_safe_proxy": str(terminal.get("rook_safe_proxy")),
        "selected_piece": _context_term(row, "selected_piece:"),
        "king_distance_delta": _context_term(row, "king_distance_delta:"),
        "rook_distance_delta": _context_term(row, "rook_distance_delta:"),
        "box_area_delta": _context_term(row, "box_area_delta:"),
        "rook_safe_after_proxy": _context_term(row, "rook_safe_after_proxy:"),
        "normal_selected_owner_visible": normal_selected_owner,
        "forced_capacity_alternative_lab_visible": forced_capacity_only,
        "selected_provider_validated_family": selected_provider_validated_family,
        "protected_stage": protected_stage,
    }


def _build_design() -> dict[str, Any]:
    runtime_packet = _load(RUNTIME_PACKET)
    if runtime_packet.get("causal_status") != "non_causal_runtime_review_packet":
        raise ValueError("runtime review packet must remain non-causal")
    design = {
        "schema_version": "krk_state_local_paired_runtime_proxy_design.v0",
        "causal_status": "non_causal_proxy_design",
        **_runtime_false_block(),
        "implementation_allowed_by_this_design": False,
        "source_artifacts": [str(RUNTIME_PACKET), str(PROBE_V1), str(ERROR_AUDIT)],
        "purpose": (
            "Translate the offline safe-preservation semantic gate into candidate "
            "visible runtime proxies without changing routing, scoring, topology, or training."
        ),
        "proxy_specs": [
            {
                "proxy_id": "terminal.krk.selected_owner_failure_risk_proxy",
                "proxy_type": "visible_runtime_proxy_candidate",
                "meaning": (
                    "The currently selected owner may be unsafe in this state-local context; "
                    "a competing owner may need review."
                ),
                "candidate_visible_terms": [
                    "current_selected_owner_provider_family",
                    "active_landmark_label",
                    "source_stage/profile scope",
                    "terminal_space_context buckets",
                    "selected_move_shape/post_move proxy terms",
                    "same-state competing provider proposal evidence if a future candidate set exposes it",
                ],
                "forbidden_terms": [
                    "owner_a_positive",
                    "selected_playout_result",
                    "future h40 conversion result",
                    "DTM/tablebase label",
                    "forced-provider h40 result as direct runtime input",
                ],
                "forbidden_causal_uses": [
                    "directly suppress selected owner",
                    "directly boost alternative provider",
                    "route to a provider",
                    "mutate topology",
                ],
                "status": "proposed_proxy_not_runtime_authorized",
            },
            {
                "proxy_id": "terminal.krk.safe_preservation_confidence_proxy",
                "proxy_type": "visible_runtime_proxy_candidate",
                "meaning": (
                    "The selected owner is a protected/current-profile owner and should be "
                    "preserved unless visible failure-risk evidence is strong."
                ),
                "candidate_visible_terms": [
                    "selected owner is normal-routing owner",
                    "selected owner provider family/provenance/maturity",
                    "protected stage/profile scope",
                    "selected move safety/progress context",
                    "alternative is only capacity/proposal evidence unless normal selected failure is visible",
                ],
                "forbidden_terms": [
                    "owner_a_positive",
                    "owner_b_positive",
                    "selected_owner_converted label",
                    "forced_capacity_positive label as direct runtime preference",
                    "DTM/tablebase label",
                ],
                "forbidden_causal_uses": [
                    "hard lock current owner",
                    "hide competing suggestions",
                    "skip guardrails",
                    "mutate topology",
                ],
                "status": "proposed_proxy_not_runtime_authorized",
            },
        ],
        "feature_classes": {
            "runtime_visible_candidate": [
                "provider family/provenance",
                "active landmark label",
                "terminal-space buckets",
                "move-shape/post-move proxy terms",
                "future visible same-state proposal membership",
            ],
            "lab_evidence_source_only": [
                "forced_capacity_alternative_lab_visible",
                "owner_b_source_artifact",
                "evidence_channel",
            ],
            "offline_outcome_forbidden": [
                "owner_a_positive",
                "owner_b_positive",
                "comparison_label",
                "selected playout outcome",
                "forced-provider playout outcome",
            ],
        },
        "decision": {
            "status": "proxy_design_ready_for_replay_free_validation",
            "runtime_work_allowed": False,
            "selector_training_allowed": False,
            "recommended_next_step": "build_runtime_proxy_dataset_and_probe_visible_candidate_features",
        },
    }
    _validate_non_causal(design)
    return design


def _build_dataset(design: dict[str, Any]) -> dict[str, Any]:
    inventory = _load(INVENTORY)
    if inventory.get("causal_status") != "non_causal_pair_inventory":
        raise ValueError("inventory must remain non-causal")
    rows = []
    for row in inventory.get("rows") or []:
        if row.get("source_stage") == "stage7":
            continue
        if row.get("comparison_label") not in {
            "prefer_capacity_alternative",
            "prefer_selected_owner",
            "equivalent_positive_or_preserve_selected",
            "abstain_or_insufficient_safe_owner",
        }:
            continue
        proxy_terms = _proxy_terms(row)
        runtime_feature_values = {
            key: proxy_terms[key]
            for key in (
                "selected_owner_family",
                "alternative_owner_family",
                "family_pair",
                "source_stage",
                "active_landmark_label",
                "black_king_edge_bucket",
                "box_area_relevance",
                "white_king_support_bucket",
                "rook_safe_proxy",
                "selected_piece",
                "king_distance_delta",
                "rook_distance_delta",
                "box_area_delta",
                "rook_safe_after_proxy",
                "normal_selected_owner_visible",
                "selected_provider_validated_family",
                "protected_stage",
            )
        }
        lab_only_values = {
            "forced_capacity_alternative_lab_visible": proxy_terms["forced_capacity_alternative_lab_visible"],
            "owner_b_evidence_channel": row.get("owner_b_evidence_channel"),
            "evidence_channel": row.get("evidence_channel"),
            "pair_strength": row.get("pair_strength"),
        }
        offline_forbidden_values = {
            "owner_a_positive": row.get("owner_a_positive"),
            "owner_b_positive": row.get("owner_b_positive"),
            "owner_a_outcome": row.get("owner_a_outcome"),
            "owner_b_outcome": row.get("owner_b_outcome"),
            "comparison_label": row.get("comparison_label"),
        }
        rows.append(
            {
                "schema_version": "krk_state_local_paired_runtime_proxy_row.v0",
                "causal_status": "non_causal_proxy_validation_row",
                "state_id": row.get("state_id"),
                "frame_id": row.get("frame_id"),
                "source_stage": row.get("source_stage"),
                "active_landmark_label": row.get("active_landmark_label"),
                "owner_a": row.get("owner_a"),
                "owner_b": row.get("owner_b"),
                "comparison_label": row.get("comparison_label"),
                "selected_owner_failure_risk_target": _target_failure_risk(row),
                "safe_preservation_confidence_target": _target_safe_preservation(row),
                "safe_preservation_pair": row.get("safe_preservation_pair") is True,
                "stage7_training_row": False,
                "runtime_visible_candidate_features": runtime_feature_values,
                "lab_evidence_source_only_features": lab_only_values,
                "offline_outcome_forbidden_features": offline_forbidden_values,
                "runtime_behavior_allowed": False,
                "usable_for_selector_training": False,
            }
        )
    summary = {
        "row_count": len(rows),
        "state_count": len({row.get("state_id") for row in rows}),
        "failure_risk_target_count": sum(1 for row in rows if row["selected_owner_failure_risk_target"]),
        "safe_preservation_target_count": sum(1 for row in rows if row["safe_preservation_confidence_target"]),
        "safe_preservation_pair_count": sum(1 for row in rows if row["safe_preservation_pair"]),
        "source_stage_counts": dict(Counter(str(row.get("source_stage")) for row in rows)),
        "comparison_label_counts": dict(Counter(str(row.get("comparison_label")) for row in rows)),
        "stage7_row_count": sum(1 for row in rows if row.get("source_stage") == "stage7"),
        "selector_training_row_count": sum(1 for row in rows if row.get("usable_for_selector_training")),
    }
    payload = {
        "schema_version": "krk_state_local_paired_runtime_proxy_dataset.v0",
        "causal_status": "non_causal_proxy_validation_dataset",
        **_runtime_false_block(),
        "implementation_allowed_by_this_dataset": False,
        "source_artifacts": [str(INVENTORY), str(OUT_DESIGN_JSON)],
        "summary": summary,
        "rows": rows,
        "decision": {
            "status": "runtime_proxy_dataset_ready_for_non_causal_probe",
            "runtime_work_allowed": False,
            "selector_training_allowed": False,
            "recommended_next_step": "probe_runtime_visible_proxy_candidates",
        },
    }
    _validate_non_causal(payload)
    if payload["summary"]["stage7_row_count"] != 0:
        raise ValueError("Stage 7 rows must remain excluded from proxy validation")
    if design.get("implementation_allowed_by_this_design") is not False:
        raise ValueError("design must not authorize implementation")
    return payload


def _row_feature(row: dict[str, Any], key: str) -> str:
    if key.startswith("runtime:"):
        return str(_nested(row, "runtime_visible_candidate_features." + key.split(":", 1)[1]))
    if key.startswith("lab:"):
        return str(_nested(row, "lab_evidence_source_only_features." + key.split(":", 1)[1]))
    if key.startswith("offline:"):
        return str(_nested(row, "offline_outcome_forbidden_features." + key.split(":", 1)[1]))
    return str(row.get(key))


def _feature_key(row: dict[str, Any], keys: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(_row_feature(row, key) for key in keys)


def _target(row: dict[str, Any], target_name: str) -> bool:
    return bool(row.get(target_name))


def _score(train: list[dict[str, Any]], row: dict[str, Any], keys: tuple[str, ...], target_name: str) -> float:
    if not train:
        return 0.5
    global_rate = sum(1 for item in train if _target(item, target_name)) / len(train)
    counts: dict[tuple[str, ...], Counter[str]] = defaultdict(Counter)
    for item in train:
        counts[_feature_key(item, keys)]["positive" if _target(item, target_name) else "negative"] += 1
    counter = counts.get(_feature_key(row, keys))
    if not counter:
        return global_rate
    total = counter["positive"] + counter["negative"]
    return counter["positive"] / total if total else global_rate


def _classification_metrics(
    predictions: list[dict[str, Any]],
    *,
    positive_key: str = "predicted_positive",
    target_key: str = "target_positive",
) -> dict[str, Any]:
    tp = sum(1 for item in predictions if item[positive_key] and item[target_key])
    fp = sum(1 for item in predictions if item[positive_key] and not item[target_key])
    tn = sum(1 for item in predictions if not item[positive_key] and not item[target_key])
    fn = sum(1 for item in predictions if not item[positive_key] and item[target_key])
    return {
        "row_count": len(predictions),
        "true_positive": tp,
        "false_positive": fp,
        "true_negative": tn,
        "false_negative": fn,
        "accuracy": (tp + tn) / len(predictions) if predictions else None,
        "precision": tp / (tp + fp) if tp + fp else None,
        "recall": tp / (tp + fn) if tp + fn else None,
        "negative_recall": tn / (tn + fp) if tn + fp else None,
    }


def _lso_model(
    rows: list[dict[str, Any]],
    *,
    model_id: str,
    target_name: str,
    keys: tuple[str, ...],
    threshold: float,
    runtime_feature_eligible: bool,
    notes: str,
) -> dict[str, Any]:
    predictions = []
    for state_id in sorted({str(row.get("state_id")) for row in rows}):
        train = [row for row in rows if str(row.get("state_id")) != state_id]
        test = [row for row in rows if str(row.get("state_id")) == state_id]
        for row in test:
            score = _score(train, row, keys, target_name)
            predictions.append(
                {
                    "state_id": row.get("state_id"),
                    "source_stage": row.get("source_stage"),
                    "owner_a": row.get("owner_a"),
                    "owner_b": row.get("owner_b"),
                    "comparison_label": row.get("comparison_label"),
                    "feature_key": list(_feature_key(row, keys)),
                    "score": score,
                    "threshold": threshold,
                    "predicted_positive": score >= threshold,
                    "target_positive": _target(row, target_name),
                    "model_id": model_id,
                }
            )
    return {
        "model_id": model_id,
        "model_kind": "leave_state_out_proxy_feature_model",
        "target": target_name,
        "features": list(keys),
        "threshold": threshold,
        "runtime_feature_eligible": runtime_feature_eligible,
        "notes": notes,
        **_classification_metrics(predictions),
        "predictions": predictions,
    }


def _rule_model(
    rows: list[dict[str, Any]],
    *,
    model_id: str,
    target_name: str,
    runtime_feature_eligible: bool,
    notes: str,
) -> dict[str, Any]:
    predictions = []
    for row in rows:
        if model_id == "offline_semantic_selected_failed_alt_positive":
            predicted = (
                _nested(row, "offline_outcome_forbidden_features.owner_a_positive") is False
                and _nested(row, "offline_outcome_forbidden_features.owner_b_positive") is True
            )
        elif model_id == "safe_preservation_caution_proxy":
            predicted = (
                _nested(row, "runtime_visible_candidate_features.normal_selected_owner_visible") is True
                and _nested(row, "runtime_visible_candidate_features.selected_provider_validated_family") is True
                and _nested(row, "runtime_visible_candidate_features.protected_stage") is True
            )
        else:
            raise ValueError(f"unknown rule model: {model_id}")
        predictions.append(
            {
                "state_id": row.get("state_id"),
                "source_stage": row.get("source_stage"),
                "owner_a": row.get("owner_a"),
                "owner_b": row.get("owner_b"),
                "comparison_label": row.get("comparison_label"),
                "predicted_positive": predicted,
                "target_positive": _target(row, target_name),
                "model_id": model_id,
            }
        )
    return {
        "model_id": model_id,
        "model_kind": "proxy_rule_model",
        "target": target_name,
        "runtime_feature_eligible": runtime_feature_eligible,
        "notes": notes,
        **_classification_metrics(predictions),
        "predictions": predictions,
    }


def _build_probe(dataset: dict[str, Any]) -> dict[str, Any]:
    rows = dataset.get("rows") or []
    failure_models = [
        _lso_model(
            rows,
            model_id="failure_risk_visible_family_stage_context@0.5",
            target_name="selected_owner_failure_risk_target",
            keys=(
                "runtime:source_stage",
                "runtime:active_landmark_label",
                "runtime:selected_owner_family",
                "runtime:alternative_owner_family",
                "runtime:black_king_edge_bucket",
                "runtime:white_king_support_bucket",
            ),
            threshold=0.5,
            runtime_feature_eligible=True,
            notes="Uses only proxy candidate terms visible in the current state/proposal context.",
        ),
        _lso_model(
            rows,
            model_id="failure_risk_visible_pair_context@0.25",
            target_name="selected_owner_failure_risk_target",
            keys=(
                "runtime:family_pair",
                "runtime:source_stage",
                "runtime:box_area_relevance",
                "runtime:selected_piece",
                "runtime:box_area_delta",
            ),
            threshold=0.25,
            runtime_feature_eligible=True,
            notes="Lower threshold visible proxy model, useful for sensitivity but risky for preservation.",
        ),
        _rule_model(
            rows,
            model_id="offline_semantic_selected_failed_alt_positive",
            target_name="selected_owner_failure_risk_target",
            runtime_feature_eligible=False,
            notes="Forbidden outcome semantics ceiling; validates the target, not a runtime proxy.",
        ),
    ]
    preservation_models = [
        _lso_model(
            rows,
            model_id="safe_preservation_visible_owner_context@0.5",
            target_name="safe_preservation_confidence_target",
            keys=(
                "runtime:source_stage",
                "runtime:active_landmark_label",
                "runtime:selected_owner_family",
                "runtime:selected_provider_validated_family",
                "runtime:protected_stage",
                "runtime:selected_piece",
            ),
            threshold=0.5,
            runtime_feature_eligible=True,
            notes="Visible selected-owner provenance and context only.",
        ),
        _lso_model(
            rows,
            model_id="safe_preservation_visible_pair_context@0.5",
            target_name="safe_preservation_confidence_target",
            keys=(
                "runtime:family_pair",
                "runtime:source_stage",
                "runtime:black_king_edge_bucket",
                "runtime:white_king_support_bucket",
                "runtime:box_area_delta",
            ),
            threshold=0.5,
            runtime_feature_eligible=True,
            notes="Visible pair/context preservation confidence model.",
        ),
        _rule_model(
            rows,
            model_id="safe_preservation_caution_proxy",
            target_name="safe_preservation_confidence_target",
            runtime_feature_eligible=True,
            notes=(
                "Conservative runtime-candidate proxy: preserve protected normal-routing owners "
                "unless a separate failure-risk proxy fires."
            ),
        ),
    ]
    failure_visible = [model for model in failure_models if model.get("runtime_feature_eligible")]
    preservation_visible = [model for model in preservation_models if model.get("runtime_feature_eligible")]
    best_failure_visible = max(
        failure_visible,
        key=lambda item: (
            item.get("recall") or 0.0,
            item.get("precision") or 0.0,
            item.get("negative_recall") or 0.0,
        ),
    )
    best_preservation_visible = max(
        preservation_visible,
        key=lambda item: (
            item.get("recall") or 0.0,
            item.get("precision") or 0.0,
            item.get("negative_recall") or 0.0,
        ),
    )
    visible_proxy_review_ready = (
        (best_failure_visible.get("recall") or 0.0) >= 0.70
        and (best_failure_visible.get("precision") or 0.0) >= 0.70
        and (best_preservation_visible.get("recall") or 0.0) >= 0.80
        and dataset["summary"]["stage7_row_count"] == 0
    )
    failure_false_negative_examples = [
        {
            "state_id": prediction.get("state_id"),
            "source_stage": prediction.get("source_stage"),
            "owner_a": prediction.get("owner_a"),
            "owner_b": prediction.get("owner_b"),
            "comparison_label": prediction.get("comparison_label"),
            "feature_key": prediction.get("feature_key"),
            "score": prediction.get("score"),
        }
        for prediction in best_failure_visible.get("predictions") or []
        if prediction.get("target_positive") is True and prediction.get("predicted_positive") is False
    ][:10]
    payload = {
        "schema_version": "krk_state_local_paired_runtime_proxy_probe.v0",
        "causal_status": "non_causal_proxy_probe",
        **_runtime_false_block(),
        "implementation_allowed_by_this_probe": False,
        "source_artifacts": [str(OUT_DATASET_JSON), str(PROBE_V1)],
        "summary": {
            **dataset["summary"],
            "runtime_visible_failure_proxy_model_count": len(failure_visible),
            "runtime_visible_preservation_proxy_model_count": len(preservation_visible),
            "visible_proxy_review_ready": visible_proxy_review_ready,
        },
        "failure_risk_models": {
            model["model_id"]: {key: value for key, value in model.items() if key != "predictions"}
            for model in failure_models
        },
        "safe_preservation_models": {
            model["model_id"]: {key: value for key, value in model.items() if key != "predictions"}
            for model in preservation_models
        },
        "best_visible_failure_risk_proxy": {
            key: value for key, value in best_failure_visible.items() if key != "predictions"
        },
        "best_visible_safe_preservation_proxy": {
            key: value for key, value in best_preservation_visible.items() if key != "predictions"
        },
        "proxy_gap_analysis": {
            "selected_owner_failure_risk_false_negative_count": len(failure_false_negative_examples),
            "selected_owner_failure_risk_false_negative_examples": failure_false_negative_examples,
            "missing_visible_failure_risk_terms": [
                "selected_owner_progress_stagnation_visible",
                "selected_owner_repeated_failure_family_visible",
                "selected_owner_score_conflict_or_scale_gap_visible",
                "alternative_provider_live_proposal_with_role_license",
                "selected_owner_handoff_gap_visible",
                "normal_routing_selected_owner_failure_risk_prior_by_context",
            ],
            "interpretation": (
                "The available visible proxy terms mostly describe board context and owner families. "
                "They do not expose why the selected owner is failing in the current local control "
                "window, so leave-state-out failure-risk recall collapses to zero."
            ),
        },
        "decision": {
            "status": (
                "visible_runtime_proxy_candidates_review_ready"
                if visible_proxy_review_ready
                else "visible_runtime_proxy_features_insufficient"
            ),
            "runtime_work_allowed": False,
            "selector_training_allowed": False,
            "recommended_next_step": (
                "prepare_explicit_runtime_proxy_architecture_review"
                if visible_proxy_review_ready
                else "review_proxy_feature_gaps_before_runtime"
            ),
        },
    }
    _validate_non_causal(payload)
    return payload


def _build_review(design: dict[str, Any], dataset: dict[str, Any], probe: dict[str, Any]) -> dict[str, Any]:
    review_ready = probe["decision"]["status"] == "visible_runtime_proxy_candidates_review_ready"
    status = (
        "visible_proxy_candidates_review_ready_but_runtime_not_authorized"
        if review_ready
        else "runtime_proxy_translation_still_blocked"
    )
    payload = {
        "schema_version": "krk_state_local_paired_runtime_proxy_review.v0",
        "causal_status": "non_causal_architecture_review",
        **_runtime_false_block(),
        "implementation_allowed_by_this_review": False,
        "source_artifacts": [str(OUT_DESIGN_JSON), str(OUT_DATASET_JSON), str(OUT_PROBE_JSON)],
        "summary": {
            "proxy_spec_count": len(design.get("proxy_specs") or []),
            "dataset_row_count": dataset["summary"]["row_count"],
            "stage7_row_count": dataset["summary"]["stage7_row_count"],
            "best_visible_failure_risk_recall": probe["best_visible_failure_risk_proxy"].get("recall"),
            "best_visible_failure_risk_precision": probe["best_visible_failure_risk_proxy"].get("precision"),
            "best_visible_safe_preservation_recall": probe["best_visible_safe_preservation_proxy"].get("recall"),
            "best_visible_safe_preservation_precision": probe["best_visible_safe_preservation_proxy"].get("precision"),
            "visible_proxy_review_ready": probe["summary"]["visible_proxy_review_ready"],
        },
        "interpretation": [
            "The offline semantic gate remains the clean target but uses forbidden outcome labels.",
            "Selected-owner failure risk needs a visible proxy before any runtime selector can be reviewed.",
            "Safe-preservation confidence can be approximated conservatively by protected normal-routing owner context, but this is not a selector.",
            "Current visible terms describe context and provider family, but not selected-owner progress failure inside the control window.",
            "The review does not authorize runtime behavior, selector training, topology mutation, or Stage 7 promotion.",
        ],
        "proxy_gap_analysis": probe.get("proxy_gap_analysis"),
        "future_runtime_review_requirements": [
            "default-off sandbox only after explicit approval",
            "trace every proxy firing and every downstream selector decision",
            "prove default-off equivalence",
            "guardrail Stage 4/5/6 and M1-M4 preservation",
            "keep Stage 7 as held-out challenge evaluation only",
            "no DTM/tablebase runtime lookup",
            "no direct provider routing from proxy metadata",
        ],
        "decision": {
            "status": status,
            "runtime_work_allowed": False,
            "selector_training_allowed": False,
            "recommended_next_step": (
                "explicit_runtime_proxy_architecture_review"
                if review_ready
                else "collect_or_design_more_visible_selected_owner_failure_risk_features"
            ),
        },
    }
    _validate_non_causal(payload)
    return payload


def _validate_non_causal(payload: dict[str, Any]) -> None:
    if not str(payload.get("causal_status") or "").startswith("non_causal"):
        raise ValueError("payload must remain non-causal")
    for key in RUNTIME_FALSE_KEYS:
        if payload.get(key) is not False:
            raise ValueError(f"{key} must be false")
    for key, value in payload.items():
        if key.startswith("implementation_allowed") and value is not False:
            raise ValueError(f"{key} must be false")


def _write_json(repo_root: Path, path: Path, payload: dict[str, Any]) -> None:
    (repo_root / path).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _render_design_md(payload: dict[str, Any]) -> str:
    lines = [
        "# KRK State-Local Paired Runtime Proxy Design v0",
        "",
        "Non-causal design for visible proxy candidates. This does not add runtime terminals or selector behavior.",
        "",
        "## Proxy Specs",
        "",
    ]
    for spec in payload["proxy_specs"]:
        lines.extend(
            [
                f"### {spec['proxy_id']}",
                "",
                f"- `type`: `{spec['proxy_type']}`",
                f"- `status`: `{spec['status']}`",
                f"- `meaning`: {spec['meaning']}",
                f"- `candidate_visible_terms`: `{', '.join(spec['candidate_visible_terms'])}`",
                f"- `forbidden_terms`: `{', '.join(spec['forbidden_terms'])}`",
                "",
            ]
        )
    lines.extend(["## Decision", ""])
    for key, value in payload["decision"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.append("")
    return "\n".join(lines)


def _render_dataset_md(payload: dict[str, Any]) -> str:
    lines = [
        "# KRK State-Local Paired Runtime Proxy Dataset v0",
        "",
        "Replay-free proxy validation rows. Outcome labels are retained only as forbidden offline targets.",
        "",
        "## Summary",
        "",
    ]
    for key, value in payload["summary"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Feature Classes", ""])
    lines.append("- `runtime_visible_candidate_features`: candidate proxy inputs for future review.")
    lines.append("- `lab_evidence_source_only_features`: evidence-source metadata; not runtime selector inputs.")
    lines.append("- `offline_outcome_forbidden_features`: labels/targets; never runtime inputs.")
    lines.extend(["", "## Decision", ""])
    for key, value in payload["decision"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.append("")
    return "\n".join(lines)


def _render_probe_md(payload: dict[str, Any]) -> str:
    lines = [
        "# KRK State-Local Paired Runtime Proxy Probe v0",
        "",
        "Non-causal check of visible proxy candidates against the paired-ownership semantic targets.",
        "",
        "## Summary",
        "",
    ]
    for key, value in payload["summary"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Best Visible Failure-Risk Proxy", ""])
    for key, value in payload["best_visible_failure_risk_proxy"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Best Visible Safe-Preservation Proxy", ""])
    for key, value in payload["best_visible_safe_preservation_proxy"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Proxy Gap Analysis", ""])
    gap = payload["proxy_gap_analysis"]
    lines.append(
        f"- `selected_owner_failure_risk_false_negative_count`: `{gap['selected_owner_failure_risk_false_negative_count']}`"
    )
    lines.append(f"- `interpretation`: {gap['interpretation']}")
    lines.append("- `missing_visible_failure_risk_terms`:")
    for term in gap["missing_visible_failure_risk_terms"]:
        lines.append(f"- `{term}`")
    lines.extend(["", "## Decision", ""])
    for key, value in payload["decision"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.append("")
    return "\n".join(lines)


def _render_review_md(payload: dict[str, Any]) -> str:
    lines = [
        "# KRK State-Local Paired Runtime Proxy Review v0",
        "",
        "Architecture review of visible proxy candidates. This does not authorize runtime implementation.",
        "",
        "## Summary",
        "",
    ]
    for key, value in payload["summary"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Interpretation", ""])
    for item in payload["interpretation"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Proxy Gap Analysis", ""])
    gap = payload.get("proxy_gap_analysis") or {}
    lines.append(
        f"- `selected_owner_failure_risk_false_negative_count`: `{gap.get('selected_owner_failure_risk_false_negative_count')}`"
    )
    lines.append("- `missing_visible_failure_risk_terms`:")
    for term in gap.get("missing_visible_failure_risk_terms") or []:
        lines.append(f"- `{term}`")
    lines.extend(["", "## Future Runtime Review Requirements", ""])
    for item in payload["future_runtime_review_requirements"]:
        lines.append(f"- `{item}`")
    lines.extend(["", "## Decision", ""])
    for key, value in payload["decision"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.append("")
    return "\n".join(lines)


def write_outputs(repo_root: Path, design: dict[str, Any], dataset: dict[str, Any], probe: dict[str, Any], review: dict[str, Any]) -> None:
    _write_json(repo_root, OUT_DESIGN_JSON, design)
    (repo_root / OUT_DESIGN_MD).write_text(_render_design_md(design), encoding="utf-8")
    _write_json(repo_root, OUT_DATASET_JSON, dataset)
    (repo_root / OUT_DATASET_MD).write_text(_render_dataset_md(dataset), encoding="utf-8")
    _write_json(repo_root, OUT_PROBE_JSON, probe)
    (repo_root / OUT_PROBE_MD).write_text(_render_probe_md(probe), encoding="utf-8")
    _write_json(repo_root, OUT_REVIEW_JSON, review)
    (repo_root / OUT_REVIEW_MD).write_text(_render_review_md(review), encoding="utf-8")


def build_all() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    design = _build_design()
    dataset = _build_dataset(design)
    probe = _build_probe(dataset)
    review = _build_review(design, dataset, probe)
    return design, dataset, probe, review


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=ROOT)
    args = parser.parse_args()
    repo_root = args.repo_root.resolve()
    design, dataset, probe, review = build_all()
    write_outputs(repo_root, design, dataset, probe, review)
    print(json.dumps(review["decision"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
