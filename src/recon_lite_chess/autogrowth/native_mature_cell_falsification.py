"""Bounded viewed-data package for graph-local revocation of mature cells."""
from __future__ import annotations

from collections import Counter
from concurrent.futures import ProcessPoolExecutor, as_completed
import copy
import gzip
import hashlib
import json
from pathlib import Path
import pickle
import subprocess
from time import perf_counter
from typing import Any, Mapping, Sequence

import chess

from recon_lite import FrameContext, FrameKind
from recon_lite_hector.nodes import StemCellState

from .native_authority_handover import NativeR0Organism, native_authority_tripwires
from .native_competence_envelope import (
    AvailabilityState,
    CompetenceEvidenceRecord,
    GraphNativeCompetenceEnvelope,
    MatureCorrectionEmission,
)
from .native_competence_envelope_formal_or_corrected_replication import (
    validation_rows_from_preserved_v3c,
)
from .native_competence_envelope_v3c_heldout import (
    SOURCE_R0,
    _real_reference_row,
    organism_metrics,
)


SOURCE_COMMIT = "cebe92a5651ba293acd26bced22e39f7c19e4417"
SOURCE_RESULT = (
    "reports/autogrowth/native_authority/"
    "native_competence_envelope_v3b_formal_or_corrected_replication.json"
)
SOURCE_RESULT_SHA256 = (
    "9325e5d076e328f85fe6b8dbb495d5f26ae3f503156e38463912972fa766b1a3"
)
SOURCE_V3C = (
    "reports/autogrowth/native_authority/"
    "native_competence_envelope_v3c_heldout_generalization.json"
)
SOURCE_V3C_SHA256 = (
    "5ec16c0a775ec14ceb3d1daf3952a8944a4a298daa0648566ef06a8036f50bbb"
)
SOURCE_R0_SHA256 = (
    "bb58b7d64bd3ab5b696713a7253555e051bd0e9fdef4637db7c27e7517495eaf"
)
PREREGISTRATION = (
    "docs/autogrowth/NATIVE_MATURE_CELL_FALSIFICATION_PREREGISTRATION.md"
)
CONTROL_MANIFEST = (
    "reports/autogrowth/native_authority/"
    "native_mature_cell_falsification_control_manifest.json"
)
RESULT_PATH = (
    "reports/autogrowth/native_authority/"
    "native_mature_cell_falsification.json"
)
ORGANISM_DIRECTORY = (
    "reports/autogrowth/native_authority/"
    "native_mature_cell_falsification_organisms"
)
ARM_NAMES = (
    "local_responsibility",
    "shuffled_responsibility",
    "immutable_maturity",
)
MASTER_CONTROL_SEED_LABEL = (
    f"{SOURCE_COMMIT}|NATIVE_MATURE_CELL_FALSIFICATION|shuffled_responsibility.v1"
)


def generate_control_manifest(
    preregistration_commit: str,
    *,
    output: str = CONTROL_MANIFEST,
) -> dict[str, Any]:
    if _git_head() != preregistration_commit:
        raise RuntimeError("manifest must be generated from exact preregistration HEAD")
    source = _load_json(SOURCE_RESULT)
    _verify_source_result(source)
    entries = _connected_entries(source)
    seed = hashlib.sha256(MASTER_CONTROL_SEED_LABEL.encode("utf-8")).hexdigest()
    rows = []
    for entry in entries:
        envelope = _load_envelope(entry)
        mature_ids = tuple(sorted(
            cell.cell_id for cell in envelope.cells.values() if cell.is_mature
        ))
        targets = tuple(sorted(
            mature_ids,
            key=lambda cell_id: hashlib.sha256(
                f"{seed}|{entry['ordinal']}|{cell_id}".encode("utf-8")
            ).digest(),
        ))
        mapping = dict(zip(mature_ids, targets, strict=True))
        rows.append({
            "ordinal": entry["ordinal"],
            "genome_seed": entry["genome_seed"],
            "source_artifact": dict(entry["artifact"]),
            "mature_cell_ids": list(mature_ids),
            "permutation": mapping,
            "permutation_sha256": _hash_json(mapping),
        })
    payload = {
        "schema_version": "native_mature_cell_falsification_control_manifest.v1",
        "preregistration_commit": preregistration_commit,
        "source_commit": SOURCE_COMMIT,
        "master_control_seed_sha256": seed,
        "derivation": "sha256(master_seed|ordinal|cell_id), sorted rank",
        "organism_count": len(rows),
        "rows": rows,
        "source_freeze": {
            SOURCE_RESULT: _file_sha256(SOURCE_RESULT),
            SOURCE_V3C: _file_sha256(SOURCE_V3C),
            SOURCE_R0: _file_sha256(SOURCE_R0),
            PREREGISTRATION: _file_sha256(PREREGISTRATION),
            "src/recon_lite_chess/autogrowth/native_competence_envelope.py": (
                _file_sha256(
                    "src/recon_lite_chess/autogrowth/native_competence_envelope.py"
                )
            ),
            "src/recon_lite_chess/autogrowth/native_mature_cell_falsification.py": (
                _file_sha256(__file__)
            ),
            "tests/autogrowth/test_native_competence_envelope.py": _file_sha256(
                "tests/autogrowth/test_native_competence_envelope.py"
            ),
            "tests/autogrowth/test_native_mature_cell_falsification.py": (
                _file_sha256(
                    "tests/autogrowth/test_native_mature_cell_falsification.py"
                )
            ),
        },
    }
    payload["manifest_payload_sha256"] = _hash_json(payload)
    return _write_json(output, payload)


def run_package(
    *,
    output: str = RESULT_PATH,
    organism_directory: str = ORGANISM_DIRECTORY,
    max_workers: int = 4,
) -> dict[str, Any]:
    started = perf_counter()
    source = _load_json(SOURCE_RESULT)
    manifest = _load_json(CONTROL_MANIFEST)
    source_freeze = _verify_run_sources(source, manifest)
    entries = _connected_entries(source)
    references, reference_integrity = _build_reference_rows(source)
    baseline = _run_baseline(entries, references, max_workers=max_workers)
    baseline_metrics = _cohort_metrics(baseline)
    baseline_exact = bool(
        baseline_metrics["total_tp"] == 313
        and baseline_metrics["total_fp"] == 39
        and baseline_metrics["safe_narrow_passes"] == 6
        and all(row["state_identical"] for row in baseline)
    )
    result: dict[str, Any] = {
        "schema_version": "native_mature_cell_falsification.v1",
        "preregistered": True,
        "source_freeze": source_freeze,
        "data_firewall": _data_firewall(),
        "reference_integrity": reference_integrity,
        "baseline": {
            "organisms": baseline,
            "metrics": baseline_metrics,
            "exact_reproduction": baseline_exact,
        },
        "completed_organism_count": 0,
        "organisms": [],
        "integrity_passed": False,
        "mechanism_passed": False,
        "scientific_passed": False,
        "stage": "baseline_complete",
    }
    _write_json(output, result)
    if not reference_integrity["passed"] or not baseline_exact:
        result.update({
            "stage": "baseline_instrument_abort",
            "stop_reason": "reference_or_baseline_checksum_mismatch",
            "duration_seconds": perf_counter() - started,
        })
        return _write_json(output, result)

    manifest_lookup = {int(row["ordinal"]): row for row in manifest["rows"]}
    output_dir = Path(organism_directory)
    output_dir.mkdir(parents=True, exist_ok=True)
    tasks = [
        {
            "entry": entry,
            "control": manifest_lookup[int(entry["ordinal"])],
            "references": references,
            "organism_directory": organism_directory,
        }
        for entry in entries
    ]
    completed: list[dict[str, Any]] = []
    if max_workers == 1:
        iterator = map(_adapt_organism_worker, tasks)
        for row in iterator:
            completed.append(row)
            result["organisms"] = sorted(completed, key=lambda item: item["ordinal"])
            result["completed_organism_count"] = len(completed)
            result["stage"] = "adaptation_running"
            _write_json(output, result)
    else:
        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(_adapt_organism_worker, task) for task in tasks]
            for future in as_completed(futures):
                completed.append(future.result())
                result["organisms"] = sorted(
                    completed, key=lambda item: item["ordinal"]
                )
                result["completed_organism_count"] = len(completed)
                result["stage"] = "adaptation_running"
                _write_json(output, result)
    completed.sort(key=lambda item: item["ordinal"])
    adjudication = _adjudicate(completed, entries, references)
    result.update({
        "organisms": completed,
        "completed_organism_count": len(completed),
        "adjudication": adjudication,
        "integrity_passed": adjudication["integrity_passed"],
        "mechanism_passed": adjudication["mechanism_passed"],
        "scientific_passed": adjudication["scientific_passed"],
        "stage": (
            "closed_after_adjudication"
            if adjudication["integrity_passed"]
            else "implementation_instrument_abort"
        ),
        "stop_reason": "package_closed_no_automatic_refinement",
        "duration_seconds": perf_counter() - started,
    })
    return _write_json(output, result)


def _run_baseline(
    entries: Sequence[Mapping[str, Any]],
    references: Sequence[Mapping[str, Any]],
    *,
    max_workers: int,
) -> list[dict[str, Any]]:
    args = [{"entry": dict(entry), "references": list(references)} for entry in entries]
    if max_workers == 1:
        rows = [_baseline_worker(item) for item in args]
    else:
        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            rows = list(executor.map(_baseline_worker, args))
    return sorted(rows, key=lambda row: row["ordinal"])


def _baseline_worker(args: Mapping[str, Any]) -> dict[str, Any]:
    envelope = _load_envelope(args["entry"])
    before = _pickle_sha256(envelope)
    rows = [_classify_reference(envelope, row) for row in args["references"]]
    after = _pickle_sha256(envelope)
    return {
        "ordinal": int(args["entry"]["ordinal"]),
        "genome_seed": int(args["entry"]["genome_seed"]),
        "metrics": organism_metrics(rows),
        "state_before_sha256": before,
        "state_after_sha256": after,
        "state_identical": before == after,
    }


def _adapt_organism_worker(args: Mapping[str, Any]) -> dict[str, Any]:
    entry = args["entry"]
    control = args["control"]
    references = args["references"]
    source = _load_envelope(entry)
    source_mature_ids = tuple(sorted(
        cell.cell_id for cell in source.cells.values() if cell.is_mature
    ))
    if tuple(control["mature_cell_ids"]) != source_mature_ids:
        raise RuntimeError("control mature-cell identity mismatch")
    permutation = {str(key): str(value) for key, value in control["permutation"].items()}
    arms: dict[str, Any] = {}
    for arm in ARM_NAMES:
        envelope = copy.deepcopy(source)
        envelope.rebuild_graph()
        start = _pickle_sha256(envelope)
        prequential_rows = []
        control_transition_count = 0
        for reference in references:
            before_classification = envelope.classify(
                reference["active_competence_signal_ids"], policy_response=True
            )
            record = _record_from_reference(reference)
            frame = FrameContext(
                frame_id=f"mature-falsification:{entry['ordinal']}:{arm}:{reference['row_index']}",
                kind=FrameKind.REAL,
                values={"board": chess.Board(str(reference["fen"]))},
            )
            emission = envelope.observe_real_outcome(
                frame,
                record,
                lifecycle_connected=arm == "local_responsibility",
            )
            control_transitions: tuple[str, ...] = ()
            if arm == "shuffled_responsibility":
                control_transitions = _apply_shuffled_control(
                    envelope, emission, permutation
                )
                control_transition_count += len(control_transitions)
            prequential_rows.append({
                "row_index": int(reference["row_index"]),
                "state_before_outcome": before_classification.state.value,
                "available_cell_ids_before_outcome": list(
                    before_classification.available_cell_ids
                ),
                "refuted_cell_ids_before_outcome": list(
                    before_classification.refuted_cell_ids
                ),
                "actual_completion": bool(reference["actual_completion"]),
                "evidence_key": record.evidence_key,
                "evidence_inserted": emission.evidence_inserted,
                "matching_cell_ids": list(emission.matching_cell_ids),
                "supporting_cell_ids": list(emission.supporting_cell_ids),
                "contradiction_cell_ids": list(emission.contradiction_cell_ids),
                "graph_transitioned_cell_ids": list(emission.transitioned_cell_ids),
                "control_transitioned_cell_ids": list(control_transitions),
                "root_state": emission.root_state,
                "state_sha256": _pickle_sha256(envelope),
            })
        serialized = pickle.dumps(envelope, protocol=pickle.HIGHEST_PROTOCOL)
        restored = pickle.loads(serialized)
        if not isinstance(restored, GraphNativeCompetenceEnvelope):
            raise TypeError("restored adapted organism has wrong type")
        post_rows = [_classify_reference(restored, row) for row in references]
        compressed = gzip.compress(
            pickle.dumps(restored, protocol=pickle.HIGHEST_PROTOCOL), mtime=0
        )
        artifact_path = Path(args["organism_directory"]) / (
            f"{int(entry['ordinal']):02d}_{int(entry['genome_seed'])}_{arm}.pkl.gz"
        )
        artifact_path.write_bytes(compressed)
        final_cells = [
            {
                "cell_id": cell.cell_id,
                "members": list(cell.members),
                "polarity": None if cell.polarity is None else cell.polarity.value,
                "state": cell.state.name,
                "support": cell.support,
                "successes": cell.successes,
                "failures": cell.failures,
                "revoked_evidence_key": cell.revoked_evidence_key,
            }
            for cell in sorted(restored.cells.values(), key=lambda item: item.cell_id)
            if cell.cell_id in source_mature_ids
        ]
        arms[arm] = {
            "start_state_sha256": start,
            "prequential_rows": prequential_rows,
            "unique_real_observations": (
                restored.correction_audit.unique_real_observations
            ),
            "contradiction_hits": restored.correction_audit.contradiction_hits,
            "graph_transition_count": (
                restored.correction_audit.mature_to_probation_transitions
            ),
            "control_transition_count": control_transition_count,
            "post_metrics": organism_metrics(post_rows),
            "post_rows": post_rows,
            "source_mature_cell_count": len(source_mature_ids),
            "final_cells": final_cells,
            "serialized_restore_identical": (
                pickle.dumps(restored, protocol=pickle.HIGHEST_PROTOCOL)
                == serialized
            ),
            "artifact": {
                "path": str(artifact_path),
                "compressed_sha256": hashlib.sha256(compressed).hexdigest(),
                "uncompressed_sha256": hashlib.sha256(
                    gzip.decompress(compressed)
                ).hexdigest(),
            },
        }
    return {
        "ordinal": int(entry["ordinal"]),
        "genome_seed": int(entry["genome_seed"]),
        "source_artifact": dict(entry["artifact"]),
        "control_permutation_sha256": str(control["permutation_sha256"]),
        "arms": arms,
    }


def _apply_shuffled_control(
    envelope: GraphNativeCompetenceEnvelope,
    emission: MatureCorrectionEmission,
    permutation: Mapping[str, str],
) -> tuple[str, ...]:
    """Laboratory-only identity shuffle; never used by connected inference."""

    transitioned = []
    for responsible_id in emission.contradiction_cell_ids:
        if responsible_id not in permutation:
            raise RuntimeError("graph-emitted responsible cell absent from permutation")
        target_id = permutation[responsible_id]
        target = envelope.cells[target_id]
        if target.state != StemCellState.MATURE:
            continue
        target.stem_cell.state = StemCellState.PROBATION
        target.stem_cell.metadata["laboratory_shuffled_revocation"] = True
        target.stem_cell.metadata["shuffled_source_cell_id"] = responsible_id
        target.revoked_evidence_key = emission.evidence_key
        target.revocation_count += 1
        transitioned.append(target_id)
    if transitioned:
        envelope.rebuild_graph()
    return tuple(transitioned)


def _adjudicate(
    organisms: Sequence[Mapping[str, Any]],
    entries: Sequence[Mapping[str, Any]],
    references: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    metrics = {
        arm: _cohort_metrics([
            {
                "metrics": organism["arms"][arm]["post_metrics"]
            }
            for organism in organisms
        ])
        for arm in ARM_NAMES
    }
    totals = {
        arm: {
            "contradiction_hits": sum(
                organism["arms"][arm]["contradiction_hits"]
                for organism in organisms
            ),
            "transitions": sum(
                (
                    organism["arms"][arm]["graph_transition_count"]
                    if arm == "local_responsibility"
                    else organism["arms"][arm]["control_transition_count"]
                )
                for organism in organisms
            ),
        }
        for arm in ARM_NAMES
    }
    safe_specs = _validation_safe_mature_specs(entries, references)
    local_final = [
        cell
        for organism in organisms
        for cell in organism["arms"]["local_responsibility"]["final_cells"]
    ]
    retained_safe_specs = {
        tuple(sorted(cell["members"]))
        for cell in local_final
        if tuple(sorted(cell["members"])) in safe_specs
        and cell["state"] == StemCellState.MATURE.name
    }
    local_transition_provenance = all(
        set(row["graph_transitioned_cell_ids"]).issubset(
            set(row["contradiction_cell_ids"])
        )
        for organism in organisms
        for row in organism["arms"]["local_responsibility"]["prequential_rows"]
    )
    all_restored = all(
        organism["arms"][arm]["serialized_restore_identical"]
        for organism in organisms for arm in ARM_NAMES
    )
    local = metrics["local_responsibility"]
    shuffled = metrics["shuffled_responsibility"]
    immutable = metrics["immutable_maturity"]
    integrity_gates = {
        "all_32_organisms_completed": len(organisms) == 32,
        "all_96_arms_serialize_restore_exactly": all_restored,
        "all_arms_receive_32_unique_real_observations": all(
            organism["arms"][arm]["unique_real_observations"] == 32
            for organism in organisms for arm in ARM_NAMES
        ),
        "local_exact_37_transitions": totals["local_responsibility"]["transitions"] == 37,
        "local_exact_47_contradiction_hits": totals["local_responsibility"]["contradiction_hits"] == 47,
        "local_exact_119_tp_0_fp": local["total_tp"] == 119 and local["total_fp"] == 0,
        "local_exact_17_safe_narrow_1_strict": (
            local["safe_narrow_passes"] == 17 and local["strict_passes"] == 1
        ),
        "immutable_exact_313_tp_39_fp_6_safe": (
            immutable["total_tp"] == 313
            and immutable["total_fp"] == 39
            and immutable["safe_narrow_passes"] == 6
        ),
        "exact_21_validation_safe_mature_specs": len(safe_specs) == 21,
        "all_21_safe_specs_remain_mature": retained_safe_specs == safe_specs,
        "only_graph_confirmed_local_cells_transition": local_transition_provenance,
        "shuffled_transition_and_hit_parity": (
            totals["shuffled_responsibility"]["transitions"]
            == totals["local_responsibility"]["transitions"]
            and totals["shuffled_responsibility"]["contradiction_hits"]
            == totals["local_responsibility"]["contradiction_hits"]
        ),
    }
    integrity_passed = all(integrity_gates.values())
    mechanism_gates = {
        "integrity_passed": integrity_passed,
        "local_eliminates_false_positives_vs_immutable": (
            local["total_fp"] == 0 and immutable["total_fp"] == 39
        ),
        "local_retains_nonzero_coverage": local["total_tp"] > 0,
    }
    mechanism_passed = all(mechanism_gates.values())
    scientific_gates = {
        "mechanism_passed": mechanism_passed,
        "local_has_fewer_fp_than_shuffled": local["total_fp"] < shuffled["total_fp"],
        "local_has_more_tp_than_shuffled": local["total_tp"] > shuffled["total_tp"],
        "local_has_more_safe_narrow_than_shuffled": (
            local["safe_narrow_passes"] > shuffled["safe_narrow_passes"]
        ),
    }
    return {
        "metrics": metrics,
        "event_totals": totals,
        "validation_safe_mature_spec_count": len(safe_specs),
        "retained_validation_safe_mature_spec_count": len(retained_safe_specs),
        "integrity_gates": integrity_gates,
        "mechanism_gates": mechanism_gates,
        "scientific_gates": scientific_gates,
        "integrity_passed": integrity_passed,
        "mechanism_passed": mechanism_passed,
        "scientific_passed": all(scientific_gates.values()),
    }


def _validation_safe_mature_specs(
    entries: Sequence[Mapping[str, Any]],
    references: Sequence[Mapping[str, Any]],
) -> set[tuple[str, ...]]:
    safe: set[tuple[str, ...]] = set()
    for entry in entries:
        envelope = _load_envelope(entry)
        for cell in envelope.cells.values():
            if not cell.is_mature:
                continue
            positive = False
            negative = False
            for reference in references:
                record = _record_from_reference(reference)
                if not envelope._cell_pattern_matches(cell, record, set()):
                    continue
                positive |= bool(reference["actual_completion"])
                negative |= not bool(reference["actual_completion"])
            if positive and not negative:
                safe.add(tuple(sorted(cell.members)))
    return safe


def _build_reference_rows(
    source: Mapping[str, Any],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    source_v3c = _load_json(SOURCE_V3C)
    split_rows = validation_rows_from_preserved_v3c(source_v3c)
    r0 = NativeR0Organism.load(SOURCE_R0)
    before = dict(r0.persistent_state_audit())
    with native_authority_tripwires() as tripwires:
        references = [
            _real_reference_row(r0, row, "validation") for row in split_rows
        ]
    after = dict(r0.persistent_state_audit())
    canonical = source["corrected_validation"]["reference_rows"]
    mismatches = []
    for actual, expected in zip(references, canonical, strict=True):
        for field in (
            "row_index",
            "fen",
            "actual_completion",
            "observed_terminal",
            "action_signal_sha256",
        ):
            if actual[field] != expected[field]:
                mismatches.append({
                    "row_index": actual["row_index"],
                    "field": field,
                    "actual": actual[field],
                    "expected": expected[field],
                })
    gates = {
        "rows_32": len(references) == 32,
        "positive_16": sum(row["actual_completion"] for row in references[:16]) == 16,
        "negative_16": sum(not row["actual_completion"] for row in references[16:]) == 16,
        "exact_committed_reference_parity": not mismatches,
        "r0_persistent_state_identical": before == after,
        "zero_authority_tripwires": all(value == 0 for value in tripwires.values()),
        "zero_fabricated_reward": all(
            not row["fabricated_terminal_reward"] for row in references
        ),
    }
    return references, {
        "gates": gates,
        "mismatch_rows": mismatches,
        "r0_before": before,
        "r0_after": after,
        "authority_tripwires": dict(tripwires),
        "passed": all(gates.values()),
    }


def _classify_reference(
    envelope: GraphNativeCompetenceEnvelope,
    reference: Mapping[str, Any],
) -> dict[str, Any]:
    result = envelope.classify(
        reference["active_competence_signal_ids"], policy_response=True
    )
    return {
        "row_index": int(reference["row_index"]),
        "actual_completion": bool(reference["actual_completion"]),
        "state": result.state.value,
        "available_cell_ids": list(result.available_cell_ids),
        "refuted_cell_ids": list(result.refuted_cell_ids),
    }


def _record_from_reference(
    reference: Mapping[str, Any],
) -> CompetenceEvidenceRecord:
    action = reference["actuation"]
    payload = (
        f"{reference['fen']}|{action['actuator_identity']}|"
        f"{reference['observed_terminal']}"
    ).encode("utf-8")
    return CompetenceEvidenceRecord(
        evidence_key=hashlib.sha256(payload).hexdigest(),
        active_signal_ids=tuple(map(str, reference["active_competence_signal_ids"])),
        policy_response=True,
        observed_completion=bool(reference["actual_completion"]),
        actuator_identity=str(action["actuator_identity"]),
        completion_terminal_identity=str(reference["observed_terminal"]),
    )


def _cohort_metrics(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    matrices = [dict(row["metrics"]) for row in rows]
    return {
        "organism_count": len(matrices),
        "total_tp": sum(row["tp"] for row in matrices),
        "total_fp": sum(row["fp"] for row in matrices),
        "safe_narrow_passes": sum(row["safe_narrow_pass"] for row in matrices),
        "strict_passes": sum(row["strict_pass"] for row in matrices),
        "organisms_with_any_tp": sum(row["tp"] > 0 for row in matrices),
        "confusion_matrices": matrices,
    }


def _connected_entries(source: Mapping[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for seed_row in source["seed_results"]:
        arm = seed_row["connected"]
        rows.append({
            "ordinal": int(seed_row["ordinal"]),
            "genome_seed": int(seed_row["seed"]),
            "artifact": dict(arm["organism_artifact"]),
        })
    if len(rows) != 32:
        raise RuntimeError("corrected connected cohort is incomplete")
    return rows


def _load_envelope(entry: Mapping[str, Any]) -> GraphNativeCompetenceEnvelope:
    artifact = entry["artifact"]
    compressed = Path(str(artifact["path"])).read_bytes()
    if hashlib.sha256(compressed).hexdigest() != artifact["compressed_sha256"]:
        raise RuntimeError("source envelope compressed hash mismatch")
    raw = gzip.decompress(compressed)
    if hashlib.sha256(raw).hexdigest() != artifact["uncompressed_sha256"]:
        raise RuntimeError("source envelope uncompressed hash mismatch")
    envelope = pickle.loads(raw)
    if not isinstance(envelope, GraphNativeCompetenceEnvelope):
        raise TypeError("source artifact is not a competence envelope")
    return envelope


def _verify_source_result(source: Mapping[str, Any]) -> None:
    if _file_sha256(SOURCE_RESULT) != SOURCE_RESULT_SHA256:
        raise RuntimeError("corrected source result hash mismatch")
    if source.get("regression_opened") is not False:
        raise RuntimeError("corrected source regression firewall changed")
    if source.get("stage") != "closed_after_corrected_validation":
        raise RuntimeError("corrected source stage changed")


def _verify_run_sources(
    source: Mapping[str, Any], manifest: Mapping[str, Any]
) -> dict[str, Any]:
    _verify_source_result(source)
    expected = {
        SOURCE_RESULT: SOURCE_RESULT_SHA256,
        SOURCE_V3C: SOURCE_V3C_SHA256,
        SOURCE_R0: SOURCE_R0_SHA256,
        **{str(path): str(digest) for path, digest in manifest["source_freeze"].items()},
    }
    mismatches = {
        path: {"expected": digest, "observed": _file_sha256(path)}
        for path, digest in expected.items()
        if _file_sha256(path) != digest
    }
    payload = dict(manifest)
    digest = payload.pop("manifest_payload_sha256")
    if _hash_json(payload) != digest:
        raise RuntimeError("control manifest payload hash mismatch")
    if mismatches:
        raise RuntimeError(f"frozen source mismatch: {mismatches}")
    return {
        "source_commit": SOURCE_COMMIT,
        "preregistration_commit": manifest["preregistration_commit"],
        "control_manifest": {
            "path": CONTROL_MANIFEST,
            "sha256": _file_sha256(CONTROL_MANIFEST),
            "payload_sha256": digest,
        },
        "files": {path: {"sha256": digest} for path, digest in sorted(expected.items())},
    }


def _data_firewall() -> dict[str, bool]:
    return {
        "fresh_data_accessed": False,
        "regression_accessed": False,
        "retired_65_successors_accessed": False,
        "r1_accessed": False,
        "topology_growth_run": False,
        "proposal_counters_reset": False,
        "child_refinement_implemented": False,
        "renewable_proposal_budget_implemented": False,
        "terminal_trace_provenance_repaired": False,
    }


def _git_head() -> str:
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"], text=True
    ).strip()


def _pickle_sha256(value: Any) -> str:
    return hashlib.sha256(
        pickle.dumps(value, protocol=pickle.HIGHEST_PROTOCOL)
    ).hexdigest()


def _file_sha256(path: str | Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _hash_json(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _load_json(path: str | Path) -> Mapping[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _write_json(path: str | Path, value: Mapping[str, Any]) -> dict[str, Any]:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return dict(value)
