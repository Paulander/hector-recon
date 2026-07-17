"""Bit-exact native activation closure on the already-touched 64-frame tape."""
from __future__ import annotations

from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import random
import struct
from time import perf_counter
from typing import Any, Mapping, Sequence

import chess

from recon_lite import FrameContext, FrameKind

from .native_authority_lab import NativeAuthorityLabConfig, load_retired_r0_build
from .native_competence_envelope import (
    GraphNativeCompetenceEnvelope,
    NativeR0CompetenceOrganism,
)
from .native_competence_envelope_experiment import EXPECTED, _hash_json
from .native_competence_envelope_v2_training import _observe
from .native_mature_envelope_authority_addendum import _mature_authority_canary


OUTPUT = (
    "reports/autogrowth/native_authority/"
    "deterministic_native_activation_closure.json"
)
V2_ARTIFACT = (
    "reports/autogrowth/native_authority/"
    "touched_r0_competence_envelope_v2_training_only.json"
)
V2_SHA256 = "dc0b5a7df130295b83075e5211f8237263fd1d59c271c39d47ee3996c4fcdb6b"
ADDENDUM_ARTIFACT = (
    "reports/autogrowth/native_authority/"
    "native_mature_envelope_authority_addendum.json"
)
ADDENDUM_SHA256 = "4edca9472129a855fe7ec539f655da141b59e0b9d5136668ed5294095f4b3c46"
PURITY_ARTIFACT = (
    "reports/autogrowth/native_authority/"
    "native_frame_purity_competence_authority_closure.json"
)
PURITY_SHA256 = "cfb48cb8f772d95ae4bb20f6eab5aef479e06b702bd761863e32a572ef8c1f53"
TAPE_SEED = 2026071601
ACTUATION_FIELDS = (
    "actuator_identity", "move_uci", "option_identity", "activation",
    "candidate_count", "formal_ticks", "graph_owned", "host_fallback",
)
DISCRETE_FIELDS = tuple(field for field in ACTUATION_FIELDS if field != "activation")


def run_deterministic_native_activation_closure(
    output: str = OUTPUT,
) -> Mapping[str, Any]:
    started = perf_counter()
    preserved_hashes = {
        V2_ARTIFACT: _file_sha256(V2_ARTIFACT),
        ADDENDUM_ARTIFACT: _file_sha256(ADDENDUM_ARTIFACT),
        PURITY_ARTIFACT: _file_sha256(PURITY_ARTIFACT),
    }
    expected_hashes = {
        V2_ARTIFACT: V2_SHA256,
        ADDENDUM_ARTIFACT: ADDENDUM_SHA256,
        PURITY_ARTIFACT: PURITY_SHA256,
    }
    if preserved_hashes != expected_hashes:
        raise RuntimeError("a preserved deterministic-closure input changed")

    addendum = _load_json(ADDENDUM_ARTIFACT)
    purity = _load_json(PURITY_ARTIFACT)
    build = load_retired_r0_build(NativeAuthorityLabConfig())
    organism = build.organism
    tape = [
        {"historical_pool_name": "r0_train", "fen": fen}
        for fen in build.pools.r0_train
    ] + [
        {"historical_pool_name": "train_decoy", "fen": fen}
        for fen in build.pools.gate_train_decoys
    ]
    random.Random(TAPE_SEED).shuffle(tape)
    legacy_tape = [{
        "class": (
            "positive"
            if row["historical_pool_name"] == "r0_train"
            else "failure"
        ),
        "fen": row["fen"],
    } for row in tape]
    if _hash_json(legacy_tape) != EXPECTED["tape"]:
        raise RuntimeError("the already-touched 64-frame tape changed")

    persistent_initial = organism.persistent_state_audit()
    direct_rows = [
        _observe(
            organism, row["fen"], row["historical_pool_name"], index
        )
        for index, row in enumerate(tape)
    ]
    persistent_after_direct = organism.persistent_state_audit()

    wrapper = NativeR0CompetenceOrganism.loads(
        NativeR0CompetenceOrganism(
            organism, GraphNativeCompetenceEnvelope()
        ).dumps()
    )
    wrapper_before = wrapper.persistent_state_audit()
    wrapper_rows = _wrapper_pass(wrapper, tape)
    wrapper_after = wrapper.persistent_state_audit()

    field_rows = _field_mismatch_rows(direct_rows, wrapper_rows)
    baseline_rows = addendum["full_frame_input_parity"]["rows"]
    old_real_rows = purity["real_rows"]
    baseline_changes = _baseline_change_rows(
        direct_rows, baseline_rows, old_real_rows
    )
    counts = {
        "total": len(direct_rows),
        "success": sum(bool(row["completion"]) for row in direct_rows),
        "failure": sum(not bool(row["completion"]) for row in direct_rows),
    }
    result: dict[str, Any] = {
        "schema_version": "deterministic_native_activation_closure.v1",
        "engineering_only": True,
        "source_commit_preserved": "dd5728d",
        "v2_abort_unchanged": True,
        "preserved_artifacts": preserved_hashes,
        "localization": {
            "independent_process_mismatch_range": [57, 59],
            "frames": 64,
            "exclusive_field": "GraphActuation.activation",
            "maximum_reported_absolute_delta_approximately": 4e-16,
            "all_discrete_fields_exact": True,
            "all_competence_signals_exact": True,
        },
        "forbidden_remedies_used": [],
        "tape": {"count": 64, "sha256": EXPECTED["tape"]},
        "stage": "comparisons_persisted_before_gates",
        "counts_before_gates": counts,
        "field_level_mismatch_rows": field_rows,
        "field_level_mismatch_count": len(field_rows),
        "baseline_change_rows": baseline_changes,
        "persistent_state": {
            "direct_initial": persistent_initial,
            "direct_after": persistent_after_direct,
            "wrapper_before": wrapper_before,
            "wrapper_after": wrapper_after,
        },
        "planted_mature_envelope_authority": None,
        "validation_touched": False,
        "regression_touched": False,
        "retired_successors_touched": False,
        "fresh_data_touched": False,
        "r1_touched": False,
        "v3_started": False,
    }
    # This write is deliberately before gate construction. A failed gate can
    # never erase or suppress the complete field-level mismatch evidence.
    _write_json(output, result)

    signals_exact = all(
        direct_rows[index]["active_competence_signal_ids"]
        == wrapper_rows[index]["active_competence_signal_ids"]
        for index in range(64)
    )
    baseline_discrete_exact = not any(
        row["kind"] == "discrete" for row in baseline_changes
    )
    baseline_signals_exact = not any(
        row["kind"] == "signals" for row in baseline_changes
    )
    baseline_outcomes_exact = not any(
        row["kind"] == "outcome" for row in baseline_changes
    )
    baseline_evidence_exact = not any(
        row["kind"] == "evidence_identity" for row in baseline_changes
    )
    pre_regression_gates = {
        "field_rows_persisted_before_gates": True,
        "bit_exact_complete_graph_actuation_64": not field_rows,
        "bit_exact_signal_parity_64": signals_exact,
        "discrete_actions_options_unchanged_64": baseline_discrete_exact,
        "competence_signals_unchanged_64": baseline_signals_exact,
        "exact_40_successes_24_failures": counts == {
            "total": 64, "success": 40, "failure": 24,
        },
        "outcomes_unchanged_64": baseline_outcomes_exact,
        "evidence_identities_unchanged_64": baseline_evidence_exact,
        "direct_persistent_identity": persistent_initial == persistent_after_direct,
        "wrapper_persistent_identity": wrapper_before == wrapper_after,
        "zero_fabricated_reward": all(
            not row["fabricated_reward"] for row in direct_rows
        ),
    }
    protected_behavior_unchanged = all((
        baseline_discrete_exact,
        baseline_signals_exact,
        baseline_outcomes_exact,
        baseline_evidence_exact,
    ))
    if all(pre_regression_gates.values()) and protected_behavior_unchanged:
        result["planted_mature_envelope_authority"] = (
            _mature_authority_canary(organism)
        )
    regression_passed = bool(
        result["planted_mature_envelope_authority"]
        and result["planted_mature_envelope_authority"]["passed"]
    )
    gates = {
        **pre_regression_gates,
        "planted_mature_envelope_authority_regression": regression_passed,
    }
    result.update({
        "stage": "closed",
        "gates": gates,
        "passed": all(gates.values()),
        "duration_seconds": perf_counter() - started,
        "next_action": (
            "await_missing_frozen_v3_specification"
            if all(gates.values())
            else "stop_preserve_deterministic_closure_failure"
        ),
    })
    _write_json(output, result)
    return result


def _wrapper_pass(
    wrapper: NativeR0CompetenceOrganism,
    tape: Sequence[Mapping[str, str]],
) -> list[dict[str, Any]]:
    session = wrapper.dream_session()
    rows: list[dict[str, Any]] = []
    try:
        for index, item in enumerate(tape):
            query = session.request(FrameContext(
                frame_id=f"deterministic-wrapper:{index}",
                kind=FrameKind.VIRTUAL,
                values={"board": chess.Board(item["fen"])},
            ))
            if query.actuation is None:
                raise RuntimeError("serialized wrapper emitted no policy response")
            rows.append({
                "index": index,
                "actuation": asdict(query.actuation),
                "active_competence_signal_ids": list(
                    query.active_competence_signal_ids
                ),
            })
    finally:
        session.close()
    return rows


def _field_mismatch_rows(
    direct_rows: Sequence[Mapping[str, Any]],
    wrapper_rows: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    mismatches: list[dict[str, Any]] = []
    for index, (direct, wrapper) in enumerate(zip(direct_rows, wrapper_rows)):
        left = direct["actuation"]
        right = wrapper["actuation"]
        for field in ACTUATION_FIELDS:
            if field == "activation":
                left_bits = _float_bits(left[field])
                right_bits = _float_bits(right[field])
                equal = left_bits == right_bits
            else:
                left_bits = right_bits = None
                equal = left[field] == right[field]
            if not equal:
                mismatches.append({
                    "index": index,
                    "field": field,
                    "direct": left[field],
                    "serialized_wrapper": right[field],
                    "direct_ieee754": left_bits,
                    "serialized_wrapper_ieee754": right_bits,
                })
        if (
            direct["active_competence_signal_ids"]
            != wrapper["active_competence_signal_ids"]
        ):
            mismatches.append({
                "index": index,
                "field": "active_competence_signal_ids",
                "direct": direct["active_competence_signal_ids"],
                "serialized_wrapper": wrapper["active_competence_signal_ids"],
            })
    return mismatches


def _baseline_change_rows(direct_rows, baseline_rows, old_real_rows):
    changes: list[dict[str, Any]] = []
    for index, row in enumerate(direct_rows):
        current = row["actuation"]
        old = baseline_rows[index]["actuation"]
        for field in DISCRETE_FIELDS:
            if current[field] != old[field]:
                changes.append({
                    "index": index, "kind": "discrete", "field": field,
                    "preserved": old[field], "current": current[field],
                })
        if row["active_competence_signal_ids"] != baseline_rows[index][
            "active_competence_signal_ids"
        ]:
            changes.append({"index": index, "kind": "signals"})
        if bool(row["completion"]) != bool(old_real_rows[index]["success"]):
            changes.append({"index": index, "kind": "outcome"})
        if row["evidence"].evidence_key != old_real_rows[index]["evidence_key"]:
            changes.append({"index": index, "kind": "evidence_identity"})
    return changes


def _float_bits(value: float) -> str:
    return struct.pack("!d", float(value)).hex()


def _file_sha256(path: str) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _load_json(path: str) -> Mapping[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _write_json(path: str, result: Mapping[str, Any]) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

