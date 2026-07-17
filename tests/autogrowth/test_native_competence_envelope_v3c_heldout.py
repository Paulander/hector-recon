from __future__ import annotations

import ast
from pathlib import Path

import pytest

from recon_lite import ChildResponse

from recon_lite_chess.autogrowth.native_authority_handover import ChildQuery
from recon_lite_chess.autogrowth.native_competence_envelope import (
    AvailabilityState,
)
from recon_lite_chess.autogrowth.native_competence_envelope_v3c_heldout import (
    ROW_ORDER_COMMITMENTS,
    RUNNER_MODULE,
    _cohort_metrics,
    _pairwise_overlap,
    _parity_mismatches,
    _regression_verdicts,
    _split_admission,
    _validation_verdicts,
    classification_from_query,
    organism_metrics,
    row_order_commitment,
)


def _metric_rows(tp: int, fp: int) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for index in range(16):
        rows.append({
            "actual_completion": True,
            "state": (
                AvailabilityState.AVAILABLE.value
                if index < tp else AvailabilityState.UNKNOWN.value
            ),
        })
    for index in range(16):
        rows.append({
            "actual_completion": False,
            "state": (
                AvailabilityState.AVAILABLE.value
                if index < fp else AvailabilityState.UNKNOWN.value
            ),
        })
    return rows


def _organism(ordinal: int, arm: str, tp: int, fp: int) -> dict[str, object]:
    return {
        "ordinal": ordinal,
        "seed": 10_000 + ordinal,
        "arm": arm,
        "metrics": organism_metrics(_metric_rows(tp, fp)),
    }


def _synthetic_cohort(
    connected: tuple[int, int],
    shuffled: tuple[int, int],
    *,
    connected_count: int = 32,
    shuffled_count: int = 32,
) -> list[dict[str, object]]:
    rows = []
    for ordinal in range(32):
        rows.append(_organism(
            ordinal,
            "connected",
            *(connected if ordinal < connected_count else (0, 0)),
        ))
        rows.append(_organism(
            ordinal,
            "outcome_shuffled",
            *(shuffled if ordinal < shuffled_count else (0, 0)),
        ))
    return rows


def test_row_order_commitments_are_frozen_without_row_access() -> None:
    assert row_order_commitment("validation") == ROW_ORDER_COMMITMENTS[
        "validation"
    ]
    assert row_order_commitment("regression") == ROW_ORDER_COMMITMENTS[
        "regression"
    ]


def test_metrics_distinguish_unknown_and_refuted_by_outcome() -> None:
    rows = [
        {"actual_completion": True, "state": "available"},
        {"actual_completion": False, "state": "available"},
        {"actual_completion": True, "state": "unknown"},
        {"actual_completion": False, "state": "unknown"},
        {"actual_completion": True, "state": "refuted"},
        {"actual_completion": False, "state": "refuted"},
    ]
    metrics = organism_metrics(rows)
    assert metrics["tp"] == metrics["fp"] == 1
    assert metrics["positive_abstention"] == 1
    assert metrics["safe_abstention"] == 1
    assert metrics["refuted_positive"] == 1
    assert metrics["refuted_negative"] == 1
    assert metrics["selective_precision"] == 0.5


def test_validation_strict_and_safe_verdicts_are_independent() -> None:
    strict_cohort = _cohort_metrics(_synthetic_cohort(
        (14, 0), (0, 0), connected_count=28, shuffled_count=0
    ))
    strict = _validation_verdicts(strict_cohort, {"passed": True})
    assert strict["strict_generalization"]["passed"] is True
    assert strict["safe_narrow_transfer"]["passed"] is True

    safe_cohort = _cohort_metrics(_synthetic_cohort(
        (1, 0), (0, 0), connected_count=24, shuffled_count=0
    ))
    safe = _validation_verdicts(safe_cohort, {"passed": True})
    assert safe["strict_generalization"]["passed"] is False
    assert safe["safe_narrow_transfer"]["passed"] is True

    fp_cohort = _cohort_metrics(_synthetic_cohort(
        (16, 1), (0, 0), connected_count=32, shuffled_count=0
    ))
    blocked = _validation_verdicts(fp_cohort, {"passed": True})
    assert blocked["strict_generalization"]["passed"] is False
    assert blocked["safe_narrow_transfer"]["passed"] is False


def test_regression_requires_combined_29_and_safe_cross_split_coverage() -> None:
    validation = _cohort_metrics(_synthetic_cohort(
        (15, 0), (0, 0), connected_count=28, shuffled_count=0
    ))
    regression = _cohort_metrics(_synthetic_cohort(
        (14, 0), (0, 0), connected_count=28, shuffled_count=0
    ))
    verdicts = _regression_verdicts(
        regression, {"passed": True}, validation
    )
    assert verdicts["combined_connected_strict_count"] == 28
    assert verdicts["strict_replication"]["passed"] is True
    assert verdicts["safe_narrow_replication"]["passed"] is True


def test_wrapper_classification_provenance_is_the_only_consumed_state() -> None:
    classification = {
        "state": "available",
        "probability": 0.9,
        "uncertainty": 0.1,
        "available_cell_ids": ["cell-1"],
        "refuted_cell_ids": [],
        "formal_available": True,
        "formal_refuted": False,
        "policy_response": True,
    }
    query = ChildQuery(
        response=ChildResponse(
            child_id="r0",
            confirmed=True,
            expected_value=1.0,
            uncertainty=0.1,
            grounded=True,
            grounding_source="synthetic",
            policy_response=True,
            available=True,
        ),
        actuation=None,
        frame_id="synthetic",
        persistent_mutation_count=0,
        effect_attempts=(),
        availability_provenance={"classification": classification},
    )
    observed, provenance = classification_from_query(query)
    assert observed == classification
    assert provenance["classification"] == classification

    inconsistent = ChildQuery(
        response=ChildResponse(
            child_id="r0",
            confirmed=False,
            expected_value=0.0,
            uncertainty=0.1,
            grounded=True,
            grounding_source="synthetic",
            policy_response=True,
            available=False,
        ),
        actuation=None,
        frame_id="synthetic-inconsistent",
        persistent_mutation_count=0,
        effect_attempts=(),
        availability_provenance={"classification": classification},
    )
    with pytest.raises(RuntimeError, match="classification disagree"):
        classification_from_query(inconsistent)


def test_float_parity_is_bit_exact() -> None:
    real = {
        "actuator_identity": "chess_move:a1a2",
        "move_uci": "a1a2",
        "option_identity": "option:a1a2",
        "activation": 0.25,
        "activation_ieee754": "3fd0000000000000",
        "candidate_count": 1,
        "formal_ticks": 3,
        "graph_owned": True,
        "host_fallback": False,
    }
    virtual = dict(real)
    virtual.update({
        "activation": 0.25000000000000006,
        "activation_ieee754": "3fd0000000000001",
    })
    mismatch = _parity_mismatches(real, ["a"], virtual, ["a"])
    assert mismatch == [{
        "field": "GraphActuation.activation",
        "real_value": 0.25,
        "virtual_value": 0.25000000000000006,
        "real_ieee754": "3fd0000000000000",
        "virtual_ieee754": "3fd0000000000001",
    }]


def test_admission_uses_actual_before_after_digests() -> None:
    split_rows = [{"row_index": index} for index in range(32)]
    action = {"graph_owned": True, "host_fallback": False}
    references = [
        {
            "row_index": index,
            "segment": "positive" if index < 16 else "decoy",
            "actuation": action,
            "actual_completion": index < 16,
            "fabricated_terminal_reward": False,
        }
        for index in range(32)
    ]
    organisms = []
    for ordinal in range(32):
        for arm in ("connected", "outcome_shuffled"):
            organisms.append({
                "ordinal": ordinal,
                "seed": 10_000 + ordinal,
                "arm": arm,
                "rows": [
                    {
                        "row_index": index,
                        "parity_mismatch_rows": [],
                        "persistent_mutation_count": 0,
                        "effect_attempts": [],
                    }
                    for index in range(32)
                ],
                "state_digests": {
                    "before": {"exact": "same"},
                    "after": {"exact": "same"},
                    "identical": True,
                },
                "session_audit": {
                    "session_open_count": 1,
                    "request_count": 32,
                    "session_close_count": 1,
                },
                "authority_tripwires": {
                    "weighted_selector": 0,
                    "provider_fallback": 0,
                    "child_priority": 0,
                    "boolean_availability": 0,
                    "host_classification": 0,
                },
            })
    admission = _split_admission(
        split_rows=split_rows,
        reference_rows=references,
        organisms=organisms,
        r0_identity=True,
        real_tripwires={
            "weighted_selector": 0,
            "provider_fallback": 0,
            "child_priority": 0,
        },
    )
    assert admission["passed"] is True
    organisms[0]["state_digests"]["after"] = {"exact": "changed"}
    changed = _split_admission(
        split_rows=split_rows,
        reference_rows=references,
        organisms=organisms,
        r0_identity=True,
        real_tripwires={
            "weighted_selector": 0,
            "provider_fallback": 0,
            "child_priority": 0,
        },
    )
    assert changed["gates"]["exact_wrapper_state_identity"] is False


def test_d4_overlap_reporting_is_descriptive_and_exact() -> None:
    original = "7k/8/8/8/8/8/8/KR6 w - - 0 1"
    reflected = "k7/8/8/8/8/8/8/6RK w - - 0 1"
    report = _pairwise_overlap({"left": [original], "right": [reflected]})
    assert report["pairs"][0]["exact_overlap_count"] == 0
    assert report["pairs"][0]["d4_orbit_overlap_count"] == 1


def test_runner_has_no_growth_direct_classifier_or_residual_mechanism() -> None:
    source = Path(RUNNER_MODULE).read_text(encoding="utf-8")
    tree = ast.parse(source)
    called_attributes = {
        node.func.attr
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
    }
    assert "grow" not in called_attributes
    assert "add_unique_evidence" not in called_attributes
    assert "classify" not in called_attributes
    assert "residual_responsibility" not in source
    assert "retired_r0_child_availability_diagnostic" not in source
