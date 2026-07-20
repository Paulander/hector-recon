"""Behavior-preserving terminal-trace and learning-authority closure.

This runner is intentionally limited to the historical 64-event training tape
and the already-viewed 32-row development tape.  The sealed regression loader is
not imported here.
"""
from __future__ import annotations

from dataclasses import asdict, replace
import copy
import gzip
import hashlib
import json
from pathlib import Path
import pickle
from time import perf_counter
from typing import Any, Mapping, Sequence

import chess

from recon_lite import FrameContext, FrameKind
from recon_lite_hector.nodes import StemCellState

from .native_authority_handover import NativeR0Organism
from .native_competence_envelope import (
    AvailabilityState,
    CompetenceEnvelopeConfig,
    SpecializationMode,
    extract_active_competence_signals,
)
from .native_competence_envelope_v3c_heldout import SOURCE_R0, organism_metrics
from .native_contradiction_specialization import (
    ARM_MODES,
    RESULT_PATH as LEGACY_RESULT_PATH,
    _artifact_envelope,
    _pattern_fingerprint,
)
from .native_mature_cell_falsification import (
    SOURCE_RESULT,
    _connected_entries,
    _load_envelope,
    _record_from_reference,
)
from .native_trace_competence_authority import (
    GroundedOutcomeReceipt,
    TraceNativeCompetenceOrganism,
    TraceNativeLearningConfig,
)


TRAINING_TAPE_PATH = (
    "reports/autogrowth/native_authority/"
    "touched_r0_competence_envelope_v3_training_only.json"
)
RESULT_PATH = (
    "reports/autogrowth/native_authority/"
    "native_terminal_trace_authority_closure.json"
)
ORGANISM_DIRECTORY = (
    "reports/autogrowth/native_authority/"
    "native_terminal_trace_authority_closure_organisms"
)
EXPECTED = {
    "local_contrast_specialization": (220, 0, 30, 3),
    "demotion_only": (119, 0, 17, 1),
    "counterexample_blind_specialization": (169, 0, 22, 3),
}


def _load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _write_json(path: str | Path, value: Mapping[str, Any]) -> dict[str, Any]:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    return dict(value)


def _hash_json(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(
            value, sort_keys=True, separators=(",", ":"), allow_nan=False
        ).encode("utf-8")
    ).hexdigest()


def _replace_event_ids(
    value: Any, mapping: Mapping[str, str],
    terminal_mapping: Mapping[str, str] | None = None,
) -> Any:
    if isinstance(value, str):
        return mapping.get(value, value)
    if isinstance(value, list):
        return [_replace_event_ids(item, mapping, terminal_mapping) for item in value]
    if isinstance(value, tuple):
        return tuple(_replace_event_ids(item, mapping, terminal_mapping) for item in value)
    if isinstance(value, dict):
        original_evidence_key = value.get("evidence_key")
        normalized = {
            _replace_event_ids(key, mapping, terminal_mapping): _replace_event_ids(item, mapping, terminal_mapping)
            for key, item in value.items()
        }
        if (
            isinstance(original_evidence_key, str)
            and terminal_mapping is not None
            and original_evidence_key in terminal_mapping
            and "completion_terminal_identity" in normalized
        ):
            normalized["completion_terminal_identity"] = (
                terminal_mapping[original_evidence_key]
            )
        if isinstance(normalized.get("evidence_keys"), list):
            normalized["evidence_keys"] = sorted(normalized["evidence_keys"])
        if isinstance(normalized.get("evidence_records"), list):
            normalized["evidence_records"] = sorted(
                normalized["evidence_records"],
                key=lambda item: item["evidence_key"],
            )
        return normalized
    return value


def _canonical_v2(envelope) -> dict[str, Any]:
    canonical = copy.deepcopy(envelope)
    canonical.rebuild_graph()
    manifest = canonical.continuation_manifest_v2()
    for review in manifest["growth_audit"]["lifecycle_reviews"]:
        for cell in review.get("cells", []):
            cell.pop("revoked_evidence_key", None)
            cell.pop("revocation_count", None)
    return manifest


def _trace_tape(
    r0: NativeR0Organism,
    template: TraceNativeCompetenceOrganism,
    training_rows: Sequence[Mapping[str, Any]],
    development_rows: Sequence[Mapping[str, Any]],
) -> tuple[
    tuple[GroundedOutcomeReceipt, ...],
    tuple[GroundedOutcomeReceipt, ...],
    tuple[dict[str, Any], ...],
    dict[str, str],
]:
    terminal = template.completion_terminal()
    receipts = []
    development_receipts = []
    development_trace_rows = []
    event_to_legacy: dict[str, str] = {}
    event_to_legacy_terminal: dict[str, str] = {}
    mismatch_rows = []

    def evaluate(
        row: Mapping[str, Any],
        *,
        segment: str,
        ordinal: int,
        expected_signals: Sequence[str],
        expected_actuation: Mapping[str, Any],
        expected_completion: bool,
        legacy_evidence_key: str,
        legacy_completion_terminal_identity: str,
    ):
        board = chess.Board(str(row["fen"]))
        frame_id = f"trace-closure:{segment}:{ordinal}"
        real_frame = FrameContext(
            frame_id, FrameKind.REAL, values={"board": board}
        )
        actuation, trace = r0.emit_action_with_trace(real_frame)
        if actuation is None or trace is None:
            raise RuntimeError("touched authority tape lost its R0 policy response")
        shadow = extract_active_competence_signals(r0, board, actuation)
        actual_actuation = asdict(actuation)
        for field in actual_actuation:
            expected = expected_actuation[field]
            if actual_actuation[field] != expected:
                mismatch_rows.append({
                    "segment": segment,
                    "ordinal": ordinal,
                    "field": "actuation." + field,
                    "actual": actual_actuation[field],
                    "expected": expected,
                })
        if trace.ordered_signal_identities != tuple(expected_signals):
            mismatch_rows.append({
                "segment": segment,
                "ordinal": ordinal,
                "field": "ordered_signal_identities",
                "actual_sha256": _hash_json(trace.ordered_signal_identities),
                "expected_sha256": _hash_json(list(expected_signals)),
            })
        if trace.ordered_signal_identities != shadow:
            mismatch_rows.append({
                "segment": segment,
                "ordinal": ordinal,
                "field": "legacy_shadow_signal_parity",
            })
        successor = board.copy(stack=False)
        successor.push(chess.Move.from_uci(actuation.move_uci))
        if successor.is_checkmate() != bool(expected_completion):
            mismatch_rows.append({
                "segment": segment,
                "ordinal": ordinal,
                "field": "completion",
                "actual": successor.is_checkmate(),
                "expected": bool(expected_completion),
            })
        receipt = terminal.mint(trace, board, successor)
        event_to_legacy[receipt.event_id] = legacy_evidence_key
        event_to_legacy_terminal[receipt.event_id] = (
            legacy_completion_terminal_identity
        )

        virtual_frame = FrameContext(
            frame_id, FrameKind.VIRTUAL, values={"board": board}
        )
        virtual_actuation, virtual_trace = r0.emit_action_with_trace(virtual_frame)
        if (
            virtual_actuation != actuation
            or virtual_trace is None
            or virtual_trace.terminal_signals != trace.terminal_signals
            or virtual_trace.confirmed_base_terminal_node_ids
            != trace.confirmed_base_terminal_node_ids
            or virtual_trace.confirmed_mature_composite_ids
            != trace.confirmed_mature_composite_ids
        ):
            mismatch_rows.append({
                "segment": segment,
                "ordinal": ordinal,
                "field": "real_virtual_graph_output",
            })
        return receipt, {
            "ordinal": ordinal,
            "real_trace": trace,
            "virtual_trace": virtual_trace,
            "trace_digest": trace.digest(),
            "virtual_trace_digest": virtual_trace.digest(),
        }

    for index, row in enumerate(training_rows):
        receipt, _ = evaluate(
            row,
            segment="training",
            ordinal=index,
            expected_signals=row["active_competence_signal_ids"],
            expected_actuation=row["actuation"],
            expected_completion=bool(row["completion"]),
            legacy_evidence_key=str(row["evidence_key"]),
            legacy_completion_terminal_identity="mate",
        )
        receipts.append(receipt)

    for index, row in enumerate(development_rows):
        legacy_record = _record_from_reference(row)
        receipt, trace_row = evaluate(
            row,
            segment="viewed_development",
            ordinal=index,
            expected_signals=row["active_competence_signal_ids"],
            expected_actuation=row["actuation"],
            expected_completion=bool(row["actual_completion"]),
            legacy_evidence_key=legacy_record.evidence_key,
            legacy_completion_terminal_identity=(
                legacy_record.completion_terminal_identity
            ),
        )
        development_receipts.append(receipt)
        development_trace_rows.append(trace_row)

    return (
        tuple(receipts),
        tuple(development_receipts),
        tuple(development_trace_rows),
        event_to_legacy,
        event_to_legacy_terminal,
        tuple(mismatch_rows),
    )


def _post_row(wrapper, trace, reference):
    result = wrapper.classify_trace(trace)
    return {
        "row_index": int(reference["row_index"]),
        "actual_completion": bool(reference["actual_completion"]),
        "state": result.state.value,
        "available_cell_ids": list(result.available_cell_ids),
        "refuted_cell_ids": list(result.refuted_cell_ids),
    }


def _children(wrapper):
    envelope = wrapper.envelope
    return [
        {
            "cell_id": cell.cell_id,
            "lineage_parent_id": cell.lineage_parent_id,
            "state": cell.state.name,
            "polarity": None if cell.polarity is None else cell.polarity.value,
            "support": cell.support,
            "successes": cell.successes,
            "failures": cell.failures,
            "specialization_depth": cell.specialization_depth,
            "request_ordinal": cell.specialization_request_ordinal,
            "proposal_ordinal": cell.specialization_proposal_ordinal,
            "pattern_fingerprint": _pattern_fingerprint(envelope, cell.cell_id),
        }
        for cell in sorted(envelope.cells.values(), key=lambda item: item.cell_id)
        if cell.lineage_parent_id is not None
    ]


def _persist(wrapper, ordinal: int, seed: int, arm: str) -> dict[str, Any]:
    raw = wrapper.dumps()
    compressed = gzip.compress(raw, mtime=0)
    path = Path(ORGANISM_DIRECTORY) / f"{ordinal:02d}_{seed}_{arm}.pkl.gz"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(compressed)
    restored = TraceNativeCompetenceOrganism.loads(gzip.decompress(compressed))
    return {
        "path": str(path),
        "compressed_sha256": hashlib.sha256(compressed).hexdigest(),
        "uncompressed_sha256": hashlib.sha256(raw).hexdigest(),
        "continuation_v3_sha256": wrapper.continuation_digest_v3(),
        "restore_v3_exact": (
            restored.continuation_manifest_v3()
            == wrapper.continuation_manifest_v3()
        ),
    }


def _arm_metrics(rows):
    return organism_metrics(rows)


def run_stage1(*, output: str = RESULT_PATH) -> dict[str, Any]:
    started = perf_counter()
    training_source = _load_json(TRAINING_TAPE_PATH)
    training_rows = training_source["training_rows"]
    source_result = _load_json(SOURCE_RESULT)
    development_rows = list(
        source_result["corrected_validation"]["reference_rows"]
    )
    development_integrity = {
        "source": "already_viewed_canonical_reference_rows",
        "rows_32": len(development_rows) == 32,
        "positive_16": sum(
            bool(row["actual_completion"]) for row in development_rows
        ) == 16,
        "negative_16": sum(
            not bool(row["actual_completion"]) for row in development_rows
        ) == 16,
    }
    development_integrity["passed"] = all(
        value for key, value in development_integrity.items()
        if key != "source"
    )
    legacy_result = _load_json(LEGACY_RESULT_PATH)
    entries = _connected_entries(source_result)
    r0 = NativeR0Organism.load(SOURCE_R0)
    first_seed = int(entries[0]["genome_seed"])
    first_config = CompetenceEnvelopeConfig(
        **{
            **training_source["frozen_config"],
            "selection_seed": first_seed,
        }
    )
    template = TraceNativeCompetenceOrganism.empty(
        r0,
        envelope_config=first_config,
        learning_config=TraceNativeLearningConfig(
            lifecycle_connected=True,
            specialization_mode=SpecializationMode.LOCAL_CONTRAST,
            genome_seed=first_seed,
        ),
    )
    (
        training_receipts,
        development_receipts,
        development_trace_rows,
        event_to_legacy,
        event_to_legacy_terminal,
        trace_mismatches,
    ) = _trace_tape(
        r0, template, training_rows, development_rows
    )
    result: dict[str, Any] = {
        "schema_version": "native_terminal_trace_authority_closure.v1",
        "stage": "trace_admission",
        "behavior_preserving_engineering_only": True,
        "data_firewall": {
            "training_64_touched": True,
            "viewed_development_32_touched": True,
            "regression_accessed": False,
            "retired_65_accessed": False,
            "fresh_accessed": False,
            "r1_accessed": False,
        },
        "trace_admission": {
            "training_receipts": len(training_receipts),
            "development_receipts": len(development_receipts),
            "mismatch_rows": list(trace_mismatches),
            "development_source_integrity": development_integrity,
            "passed": (
                not trace_mismatches
                and development_integrity["passed"]
                and len(training_receipts) == 64
                and len(development_receipts) == 32
            ),
        },
        "organisms": [],
    }
    _write_json(output, result)
    if not result["trace_admission"]["passed"]:
        result.update({
            "stage": "instrument_abort",
            "stop_reason": "trace_or_touched_source_mismatch",
        })
        return _write_json(output, result)

    legacy_by_ordinal = {
        int(row["ordinal"]): row for row in legacy_result["organisms"]
    }
    completed = []
    for entry in entries:
        ordinal = int(entry["ordinal"])
        seed = int(entry["genome_seed"])
        config = CompetenceEnvelopeConfig(
            **{
                **training_source["frozen_config"],
                "selection_seed": seed,
            }
        )
        source_wrapper = TraceNativeCompetenceOrganism.empty(
            r0,
            envelope_config=config,
            learning_config=TraceNativeLearningConfig(
                lifecycle_connected=True,
                specialization_mode=SpecializationMode.LOCAL_CONTRAST,
                genome_seed=seed,
            ),
        )
        source_wrapper.grow_from_grounded_receipts(training_receipts)
        legacy_source = _load_envelope(entry)
        normalized_source = _replace_event_ids(
            _canonical_v2(source_wrapper.envelope),
            event_to_legacy,
            event_to_legacy_terminal,
        )
        source_exact = (
            normalized_source == _canonical_v2(legacy_source)
        )
        organism_row = {
            "ordinal": ordinal,
            "genome_seed": seed,
            "source_reconstruction_exact": source_exact,
            "source_manifest_actual_sha256": _hash_json(normalized_source),
            "source_manifest_expected_sha256": _hash_json(
                _canonical_v2(legacy_source)
            ),
            "arms": {},
        }
        for arm_name, mode in ARM_MODES.items():
            wrapper = copy.deepcopy(source_wrapper)
            wrapper.learning_config = replace(
                wrapper.learning_config, specialization_mode=mode
            )
            legacy_arm = legacy_by_ordinal[ordinal]["arms"][arm_name]
            prequential = []
            for reference, receipt, trace_row in zip(
                development_rows,
                development_receipts,
                development_trace_rows,
                strict=True,
            ):
                trace = trace_row["real_trace"]
                before = wrapper.classify_trace(trace)
                emission = wrapper.observe_grounded(receipt)
                prequential.append({
                    "row_index": int(reference["row_index"]),
                    "actual_completion": bool(reference["actual_completion"]),
                    "state_before": before.state.value,
                    "evidence_inserted": emission.evidence_inserted,
                    "contradiction_cell_ids": list(
                        emission.contradiction_cell_ids
                    ),
                    "transitioned_cell_ids": list(emission.transitioned_cell_ids),
                    "specialization_request_parent_ids": list(
                        emission.specialization_request_parent_ids
                    ),
                    "specialization_child_ids": list(
                        emission.specialization_child_ids
                    ),
                })
            post_rows = [
                _post_row(wrapper, trace_row["real_trace"], reference)
                for reference, trace_row in zip(
                    development_rows, development_trace_rows, strict=True
                )
            ]
            metrics = _arm_metrics(post_rows)
            final_legacy_envelope = _artifact_envelope(legacy_arm["artifact"])
            normalized_final = _replace_event_ids(
                _canonical_v2(wrapper.envelope),
                event_to_legacy,
                event_to_legacy_terminal,
            )
            final_exact = (
                normalized_final
                == _canonical_v2(final_legacy_envelope)
            )
            direct_serialized_virtual_exact = True
            before_digest = wrapper.continuation_digest_v3()
            restored = TraceNativeCompetenceOrganism.loads(wrapper.dumps())
            for reference, trace_row, expected_row in zip(
                development_rows, development_trace_rows, post_rows, strict=True
            ):
                direct = wrapper.classify_trace(trace_row["real_trace"])
                serialized = restored.classify_trace(trace_row["real_trace"])
                virtual = restored.classify_trace(trace_row["virtual_trace"])
                if not (
                    direct == serialized == virtual
                    and direct.state.value == expected_row["state"]
                    and list(direct.available_cell_ids)
                    == expected_row["available_cell_ids"]
                    and list(direct.refuted_cell_ids)
                    == expected_row["refuted_cell_ids"]
                ):
                    direct_serialized_virtual_exact = False
                    break
            state_exact = (
                wrapper.continuation_digest_v3() == before_digest
                and restored.continuation_manifest_v3()
                == wrapper.continuation_manifest_v3()
            )
            artifact = _persist(wrapper, ordinal, seed, arm_name)
            children = _children(wrapper)
            organism_row["arms"][arm_name] = {
                "prequential_exact": prequential
                == legacy_arm["prequential_rows"],
                "post_rows_exact": post_rows == legacy_arm["post_rows"],
                "metrics_exact": metrics == legacy_arm["post_metrics"],
                "specialization_audit_exact": _replace_event_ids(
                    wrapper.envelope.continuation_manifest_v2()[
                        "specialization_audit"
                    ],
                    event_to_legacy,
                )
                == legacy_arm["specialization_audit"],
                "correction_audit_exact": _replace_event_ids(
                    wrapper.envelope.continuation_manifest_v2()[
                        "correction_audit"
                    ],
                    event_to_legacy,
                )
                == legacy_arm["correction_audit"],
                "children_exact": children == legacy_arm["children"],
                "final_continuation_semantic_exact": final_exact,
                "final_manifest_actual_sha256": _hash_json(normalized_final),
                "final_manifest_expected_sha256": _hash_json(
                    _canonical_v2(final_legacy_envelope)
                ),
                "direct_serialized_virtual_exact": (
                    direct_serialized_virtual_exact
                ),
                "persistent_state_exact": state_exact,
                "post_metrics": metrics,
                "specialization_counts": {
                    "requests": wrapper.envelope.specialization_audit.graph_request_emissions,
                    "attempts": wrapper.envelope.specialization_audit.proposal_attempts,
                    "admissions": wrapper.envelope.specialization_audit.admitted_proposals,
                },
                "children": {
                    "mature": sum(
                        item["state"] == StemCellState.MATURE.name
                        for item in children
                    ),
                    "probation": sum(
                        item["state"] == StemCellState.PROBATION.name
                        for item in children
                    ),
                },
                "artifact": artifact,
            }
        completed.append(organism_row)
        result["organisms"] = completed
        result["stage"] = "replay_running"
        _write_json(output, result)

    cohort = {}
    for arm_name in ARM_MODES:
        matrices = [
            row["arms"][arm_name]["post_metrics"] for row in completed
        ]
        cohort[arm_name] = {
            "total_tp": sum(item["tp"] for item in matrices),
            "total_fp": sum(item["fp"] for item in matrices),
            "safe_narrow": sum(item["safe_narrow_pass"] for item in matrices),
            "strict": sum(item["strict_pass"] for item in matrices),
        }
    all_exact = all(
        row["source_reconstruction_exact"]
        and all(
            value[key]
            for value in row["arms"].values()
            for key in (
                "prequential_exact",
                "post_rows_exact",
                "metrics_exact",
                "specialization_audit_exact",
                "correction_audit_exact",
                "children_exact",
                "final_continuation_semantic_exact",
                "direct_serialized_virtual_exact",
                "persistent_state_exact",
            )
        )
        for row in completed
    )
    expected_metrics = all(
        (
            cohort[arm]["total_tp"],
            cohort[arm]["total_fp"],
            cohort[arm]["safe_narrow"],
            cohort[arm]["strict"],
        )
        == EXPECTED[arm]
        for arm in ARM_MODES
    )
    requests = {
        arm: {
            key: sum(
                row["arms"][arm]["specialization_counts"][key]
                for row in completed
            )
            for key in ("requests", "attempts", "admissions")
        }
        for arm in ARM_MODES
    }
    local_child_counts = {
        key: sum(
            row["arms"]["local_contrast_specialization"]["children"][key]
            for row in completed
        )
        for key in ("mature", "probation")
    }
    blind_child_counts = {
        key: sum(
            row["arms"]["counterexample_blind_specialization"]["children"][key]
            for row in completed
        )
        for key in ("mature", "probation")
    }
    checksum_gates = {
        "all_32_organisms": len(completed) == 32,
        "all_semantic_equivalence_checks": all_exact,
        "exact_cohort_metrics": expected_metrics,
        "exact_37_local_requests_attempts_admissions": (
            set(requests["local_contrast_specialization"].values()) == {37}
        ),
        "exact_37_blind_requests_attempts_admissions": (
            set(requests["counterexample_blind_specialization"].values()) == {37}
        ),
        "local_children_34_mature_3_probation": (
            local_child_counts == {"mature": 34, "probation": 3}
        ),
        "blind_children_12_mature": (
            blind_child_counts["mature"] == 12
        ),
        "all_96_artifacts_restore_v3_exact": all(
            arm["artifact"]["restore_v3_exact"]
            for row in completed
            for arm in row["arms"].values()
        ),
    }
    result.update({
        "stage": (
            "closed_passed" if all(checksum_gates.values())
            else "instrument_abort"
        ),
        "cohort_metrics": cohort,
        "specialization_counts": requests,
        "local_child_counts": local_child_counts,
        "blind_child_counts": blind_child_counts,
        "checksum_gates": checksum_gates,
        "passed": all(checksum_gates.values()),
        "regression_accessed": False,
        "duration_seconds": perf_counter() - started,
        "stop_reason": (
            "stage1_behavior_preserving_authority_closure_passed"
            if all(checksum_gates.values())
            else "stage1_equivalence_mismatch_regression_remains_sealed"
        ),
    })
    return _write_json(output, result)


if __name__ == "__main__":
    run_stage1()
