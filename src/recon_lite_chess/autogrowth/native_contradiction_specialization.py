"""Contradiction-triggered one-level specialization on the viewed R0 tape."""
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

from .native_competence_envelope import (
    AvailabilityState, CompetenceContextGrowthGenome,
    GraphNativeCompetenceEnvelope, SpecializationMode,
)
from .native_competence_envelope_v3c_heldout import organism_metrics
from .native_mature_cell_falsification import (
    RESULT_PATH as MATURE_RESULT_PATH, SOURCE_RESULT, SOURCE_RESULT_SHA256,
    _build_reference_rows, _classify_reference, _cohort_metrics,
    _connected_entries, _file_sha256, _hash_json, _load_envelope, _load_json,
    _record_from_reference,
)

PREREGISTRATION = (
    "docs/autogrowth/"
    "NATIVE_CONTRADICTION_TRIGGERED_SPECIALIZATION_PREREGISTRATION.md"
)
MANIFEST_PATH = (
    "reports/autogrowth/native_authority/"
    "native_contradiction_specialization_manifest_v3.json"
)
RESULT_PATH = (
    "reports/autogrowth/native_authority/"
    "native_contradiction_specialization.json"
)
ORGANISM_DIRECTORY = (
    "reports/autogrowth/native_authority/"
    "native_contradiction_specialization_organisms"
)
ARM_MODES = {
    "local_contrast_specialization": SpecializationMode.LOCAL_CONTRAST,
    "demotion_only": SpecializationMode.DISCONNECTED,
    "counterexample_blind_specialization": (
        SpecializationMode.COUNTEREXAMPLE_BLIND
    ),
}


def _artifact_envelope(artifact: Mapping[str, Any]) -> GraphNativeCompetenceEnvelope:
    compressed = Path(str(artifact["path"])).read_bytes()
    if hashlib.sha256(compressed).hexdigest() != artifact["compressed_sha256"]:
        raise RuntimeError("envelope compressed hash mismatch")
    raw = gzip.decompress(compressed)
    if hashlib.sha256(raw).hexdigest() != artifact["uncompressed_sha256"]:
        raise RuntimeError("envelope uncompressed hash mismatch")
    envelope = pickle.loads(raw)
    if not isinstance(envelope, GraphNativeCompetenceEnvelope):
        raise TypeError("artifact does not contain a competence envelope")
    return envelope


def learner_invisible_ceiling() -> dict[str, Any]:
    """Aggregate-only oracle union; candidate identities never leave this call."""

    source = _load_json(SOURCE_RESULT)
    references, integrity = _build_reference_rows(source)
    closed = _load_json(MATURE_RESULT_PATH)
    rows = []
    safe_descendant_count = 0
    for organism in sorted(closed["organisms"], key=lambda row: row["ordinal"]):
        envelope = _artifact_envelope(
            organism["arms"]["local_responsibility"]["artifact"]
        )
        safe_descendants = []
        for parent in envelope.cells.values():
            if (
                parent.state != StemCellState.PROBATION
                or parent.polarity not in {
                    AvailabilityState.AVAILABLE, AvailabilityState.REFUTED
                }
            ):
                continue
            for base_id in envelope._supporting_base_vocabulary(parent):
                matched = [
                    record for record in envelope.evidence.values()
                    if envelope._cell_pattern_matches(parent, record, set())
                    and base_id in record.active_signal_ids
                ]
                successes = sum(record.observed_completion for record in matched)
                failures = len(matched) - successes
                pure = (
                    parent.polarity == AvailabilityState.AVAILABLE
                    and len(matched) >= envelope.config.min_maturity_support
                    and failures == 0
                ) or (
                    parent.polarity == AvailabilityState.REFUTED
                    and len(matched) >= envelope.config.min_maturity_support
                    and successes == 0
                )
                if pure:
                    safe_descendants.append((parent, base_id))
        safe_descendant_count += len(safe_descendants)
        tp = fp = 0
        for reference in references:
            classification = envelope.classify(
                reference["active_competence_signal_ids"], policy_response=True
            )
            available = classification.state == AvailabilityState.AVAILABLE
            if not available:
                record = _record_from_reference(reference)
                available = any(
                    parent.polarity == AvailabilityState.AVAILABLE
                    and envelope._cell_pattern_matches(parent, record, set())
                    and base_id in record.active_signal_ids
                    for parent, base_id in safe_descendants
                )
            if available and reference["actual_completion"]:
                tp += 1
            elif available and not reference["actual_completion"]:
                fp += 1
        rows.append({"tp": tp, "fp": fp})
    total_tp = sum(row["tp"] for row in rows)
    total_fp = sum(row["fp"] for row in rows)
    safe_narrow = sum(row["tp"] > 0 and row["fp"] == 0 for row in rows)
    strict = sum(row["tp"] >= 14 and row["fp"] == 0 for row in rows)
    result = {
        "contract": "aggregate_only_no_candidate_identities",
        "organism_count": len(rows),
        "safe_descendants_exist": safe_descendant_count > 0,
        "safe_descendant_count": safe_descendant_count,
        "oracle_union_tp": total_tp,
        "oracle_union_fp": total_fp,
        "oracle_union_safe_narrow": safe_narrow,
        "oracle_union_strict": strict,
        "reference_integrity_passed": integrity["passed"],
    }
    result["admission_passed"] = bool(
        integrity["passed"] and safe_descendant_count > 0
        and total_fp == 0 and total_tp > 119 and safe_narrow > 17
    )
    return result


def generate_manifest(preregistration_commit: str, *, output: str = MANIFEST_PATH):
    if _git_head() != preregistration_commit:
        raise RuntimeError("manifest requires exact pushed preregistration HEAD")
    source = _load_json(SOURCE_RESULT)
    entries = _connected_entries(source)
    mature_result = _load_json(MATURE_RESULT_PATH)
    payload = {
        "schema_version": "native_contradiction_specialization_manifest.v1",
        "preregistration_commit": preregistration_commit,
        "source_result_sha256": _file_sha256(SOURCE_RESULT),
        "source_result_expected_sha256": SOURCE_RESULT_SHA256,
        "mature_falsification_result_sha256": _file_sha256(MATURE_RESULT_PATH),
        "preregistration_sha256": _file_sha256(PREREGISTRATION),
        "runner_sha256": _file_sha256(__file__),
        "envelope_source_sha256": _file_sha256(
            "src/recon_lite_chess/autogrowth/native_competence_envelope.py"
        ),
        "reference_rows_sha256": _hash_json(
            source["corrected_validation"]["reference_rows"]
        ),
        "arms": [
            {"name": name, "specialization_mode": mode.value}
            for name, mode in ARM_MODES.items()
        ],
        "organisms": [
            {
                "ordinal": row["ordinal"], "genome_seed": row["genome_seed"],
                "source_artifact": dict(row["artifact"]),
            }
            for row in entries
        ],
        "source_organism_count": len(entries),
        "closed_mature_result_stage": mature_result["stage"],
        "frozen_rules": {
            "one_opportunity_per_first_parent_revocation": True,
            "specialization_depth": 1,
            "child_arity": 2,
            "minimum_support": 4,
            "wilson_lower_bound": 0.55,
            "zero_opposite_outcome": True,
            "capacity_and_genome_unchanged": True,
            "tape_order": "closed_validation_reference_order",
        },
    }
    payload["manifest_payload_sha256"] = _hash_json(payload)
    return _write_json(output, payload)


def _git_head() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()


def _write_json(path: str | Path, value: Mapping[str, Any]) -> dict[str, Any]:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return dict(value)


def run_package(
    *, output: str = RESULT_PATH, organism_directory: str = ORGANISM_DIRECTORY,
    max_workers: int = 4,
) -> dict[str, Any]:
    started = perf_counter()
    manifest = _verify_manifest()
    source = _load_json(SOURCE_RESULT)
    references, reference_integrity = _build_reference_rows(source)
    ceiling = learner_invisible_ceiling()
    result: dict[str, Any] = {
        "schema_version": "native_contradiction_specialization.v1",
        "preregistered": True, "manifest": manifest,
        "learner_invisible_ceiling": ceiling,
        "reference_integrity": reference_integrity,
        "data_firewall": {
            "fresh_data_accessed": False, "regression_accessed": False,
            "retired_65_successors_accessed": False, "r1_accessed": False,
            "second_refinement_depth": False, "virtual_evidence": False,
        },
        "stage": "admission", "completed_organism_count": 0,
        "organisms": [],
    }
    _write_json(output, result)
    if not ceiling["admission_passed"] or not reference_integrity["passed"]:
        result.update({
            "stage": "admission_abort",
            "stop_reason": "ceiling_or_reference_integrity_failed",
            "duration_seconds": perf_counter() - started,
        })
        return _write_json(output, result)
    tasks = [
        {
            "entry": row, "references": references,
            "organism_directory": organism_directory,
        }
        for row in manifest["organisms"]
    ]
    completed = []
    if max_workers == 1:
        iterator = map(_worker, tasks)
        for row in iterator:
            completed.append(row)
            result["organisms"] = sorted(completed, key=lambda item: item["ordinal"])
            result["completed_organism_count"] = len(completed)
            result["stage"] = "adaptation_running"
            _write_json(output, result)
    else:
        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(_worker, task) for task in tasks]
            for future in as_completed(futures):
                completed.append(future.result())
                result["organisms"] = sorted(
                    completed, key=lambda item: item["ordinal"]
                )
                result["completed_organism_count"] = len(completed)
                result["stage"] = "adaptation_running"
                _write_json(output, result)
    completed.sort(key=lambda item: item["ordinal"])
    adjudication = _adjudicate(completed)
    result.update({
        "organisms": completed, "completed_organism_count": len(completed),
        "adjudication": adjudication,
        "integrity_passed": adjudication["integrity_passed"],
        "scientific_passed": adjudication["scientific_passed"],
        "stage": "closed_after_adjudication",
        "stop_reason": "bounded_package_closed_no_automatic_refinement",
        "duration_seconds": perf_counter() - started,
    })
    return _write_json(output, result)


def _verify_manifest() -> Mapping[str, Any]:
    manifest = _load_json(MANIFEST_PATH)
    payload = dict(manifest)
    expected_digest = payload.pop("manifest_payload_sha256")
    if _hash_json(payload) != expected_digest:
        raise RuntimeError("specialization manifest payload mismatch")
    checks = {
        SOURCE_RESULT: manifest["source_result_sha256"],
        MATURE_RESULT_PATH: manifest["mature_falsification_result_sha256"],
        PREREGISTRATION: manifest["preregistration_sha256"],
        __file__: manifest["runner_sha256"],
        "src/recon_lite_chess/autogrowth/native_competence_envelope.py": (
            manifest["envelope_source_sha256"]
        ),
    }
    mismatches = {
        path: {"expected": digest, "actual": _file_sha256(path)}
        for path, digest in checks.items() if _file_sha256(path) != digest
    }
    if mismatches:
        raise RuntimeError(f"frozen specialization source mismatch: {mismatches}")
    if manifest["source_result_sha256"] != SOURCE_RESULT_SHA256:
        raise RuntimeError("source result no longer matches frozen upstream hash")
    return manifest


def _worker(args: Mapping[str, Any]) -> dict[str, Any]:
    entry = args["entry"]
    references = args["references"]
    source = _artifact_envelope(entry["source_artifact"])
    source.rebuild_graph()
    source_cells = _preservation_index(source)
    arms = {}
    for arm_name, mode in ARM_MODES.items():
        envelope = copy.deepcopy(source)
        genome = CompetenceContextGrowthGenome(int(entry["genome_seed"]))
        prequential = []
        for reference in references:
            record = _record_from_reference(reference)
            before = envelope.classify(
                reference["active_competence_signal_ids"], policy_response=True
            )
            emission = envelope.observe_real_outcome(
                FrameContext(
                    f"specialization:{entry.get("ordinal")}:{arm_name}:{reference.get("row_index")}",
                    FrameKind.REAL,
                    values={"board": chess.Board(str(reference["fen"]))},
                ),
                record, lifecycle_connected=True, specialization_mode=mode,
                specialization_genome=genome,
            )
            prequential.append({
                "row_index": int(reference["row_index"]),
                "actual_completion": bool(reference["actual_completion"]),
                "state_before": before.state.value,
                "evidence_inserted": emission.evidence_inserted,
                "contradiction_cell_ids": list(emission.contradiction_cell_ids),
                "transitioned_cell_ids": list(emission.transitioned_cell_ids),
                "specialization_request_parent_ids": list(
                    emission.specialization_request_parent_ids
                ),
                "specialization_child_ids": list(
                    emission.specialization_child_ids
                ),
            })
        manifest_before = envelope.continuation_manifest_v2()
        serialized = pickle.dumps(envelope, protocol=pickle.HIGHEST_PROTOCOL)
        restored = pickle.loads(serialized)
        manifest_after = restored.continuation_manifest_v2()
        post_rows = [_classify_reference(restored, row) for row in references]
        post_metrics = organism_metrics(post_rows)
        safe_tp = post_metrics["tp"] if post_metrics["fp"] == 0 else 0
        compressed = gzip.compress(
            pickle.dumps(restored, protocol=pickle.HIGHEST_PROTOCOL), mtime=0
        )
        artifact_path = Path(args["organism_directory"]) / (
            f"{int(entry.get("ordinal")):02d}_{int(entry.get("genome_seed"))}_{arm_name}.pkl.gz"
        )
        artifact_path.parent.mkdir(parents=True, exist_ok=True)
        artifact_path.write_bytes(compressed)
        direct_authority_violations = []
        for row in post_rows:
            for cell_id in (*row["available_cell_ids"], *row["refuted_cell_ids"]):
                cell = restored.cells[cell_id]
                if not cell.is_mature:
                    direct_authority_violations.append(cell_id)
        final_preservation = _preservation_index(restored)
        preserved = all(
            final_preservation.get(key, {}).get("pattern_fingerprint")
            == value["pattern_fingerprint"]
            and final_preservation.get(key, {}).get("polarity") == value["polarity"]
            for key, value in source_cells.items()
        )
        child_rows = [
            {
                "cell_id": cell.cell_id, "lineage_parent_id": cell.lineage_parent_id,
                "state": cell.state.name,
                "polarity": None if cell.polarity is None else cell.polarity.value,
                "support": cell.support, "successes": cell.successes,
                "failures": cell.failures,
                "specialization_depth": cell.specialization_depth,
                "request_ordinal": cell.specialization_request_ordinal,
                "proposal_ordinal": cell.specialization_proposal_ordinal,
                "pattern_fingerprint": _pattern_fingerprint(restored, cell.cell_id),
            }
            for cell in sorted(restored.cells.values(), key=lambda item: item.cell_id)
            if cell.lineage_parent_id is not None
        ]
        arms[arm_name] = {
            "prequential_rows": prequential, "post_rows": post_rows,
            "post_metrics": post_metrics, "safe_tp": safe_tp,
            "specialization_audit": copy.deepcopy(
                restored.continuation_manifest_v2()["specialization_audit"]
            ),
            "correction_audit": copy.deepcopy(
                restored.continuation_manifest_v2()["correction_audit"]
            ),
            "children": child_rows,
            "mature_child_count": sum(
                row["state"] == StemCellState.MATURE.name for row in child_rows
            ),
            "continuation_v2_identical": manifest_before == manifest_after,
            "continuation_v2_sha256": restored.continuation_digest_v2(),
            "direct_authority_violations": sorted(set(direct_authority_violations)),
            "source_cell_pattern_preservation": preserved,
            "source_cell_preservation": source_cells,
            "final_cell_preservation": final_preservation,
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
        "source_artifact": dict(entry["source_artifact"]),
        "arms": arms,
    }


def _pattern_fingerprint(
    envelope: GraphNativeCompetenceEnvelope, cell_id: str, visiting=None
) -> str:
    visiting = set() if visiting is None else set(visiting)
    if cell_id in visiting:
        raise RuntimeError("cyclic specialization lineage")
    visiting.add(cell_id)
    cell = envelope.cells[cell_id]
    members = []
    for member in cell.members:
        if member.startswith("context:"):
            nested_id = member.split(":", 1)[1]
            members.append({"context_fingerprint": _pattern_fingerprint(
                envelope, nested_id, visiting
            )})
        else:
            members.append({"base": member})
    return _hash_json({"members": members})


def _preservation_index(envelope: GraphNativeCompetenceEnvelope):
    return {
        cell.cell_id: {
            "cell_id": cell.cell_id,
            "polarity": None if cell.polarity is None else cell.polarity.value,
            "lineage_parent_id": cell.lineage_parent_id,
            "specialization_depth": cell.specialization_depth,
            "pattern_fingerprint": _pattern_fingerprint(envelope, cell.cell_id),
        }
        for cell in sorted(envelope.cells.values(), key=lambda item: item.cell_id)
    }


def _adjudicate(organisms: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    arm_metrics = {}
    for arm in ARM_MODES:
        matrices = [row["arms"][arm]["post_metrics"] for row in organisms]
        arm_metrics[arm] = {
            **_cohort_metrics([{"metrics": item} for item in matrices]),
            "deployable_tp": sum(
                item["tp"] if item["fp"] == 0 else 0 for item in matrices
            ),
        }
    local = arm_metrics["local_contrast_specialization"]
    demotion = arm_metrics["demotion_only"]
    blind = arm_metrics["counterexample_blind_specialization"]
    all_arms = [
        arm for organism in organisms for arm in organism["arms"].values()
    ]
    request_budget_parity = all(
        organism["arms"]["local_contrast_specialization"][
            "specialization_audit"
        ]["request_opportunities"]
        == organism["arms"]["counterexample_blind_specialization"][
            "specialization_audit"
        ]["request_opportunities"]
        and organism["arms"]["local_contrast_specialization"][
            "specialization_audit"
        ]["proposal_attempts"]
        == organism["arms"]["counterexample_blind_specialization"][
            "specialization_audit"
        ]["proposal_attempts"]
        for organism in organisms
    )
    provenance = all(
        set(event["transitioned_cell_ids"]).issubset(
            event["contradiction_cell_ids"]
        )
        and set(event["specialization_request_parent_ids"]).issubset(
            event["transitioned_cell_ids"]
        )
        for organism in organisms
        for arm_name, arm in organism["arms"].items()
        for event in arm["prequential_rows"]
        if arm_name != "demotion_only"
    )
    integrity_gates = {
        "all_32_organisms_completed": len(organisms) == 32,
        "demotion_only_exact_119_tp_0_fp": (
            demotion["total_tp"] == 119 and demotion["total_fp"] == 0
        ),
        "demotion_only_exact_17_safe_1_strict": (
            demotion["safe_narrow_passes"] == 17
            and demotion["strict_passes"] == 1
        ),
        "local_blind_request_and_proposal_budget_parity": request_budget_parity,
        "only_graph_confirmed_parents_transition_and_request": provenance,
        "probation_and_trial_cells_never_emit_direct_authority": all(
            not arm["direct_authority_violations"] for arm in all_arms
        ),
        "all_96_continuation_v2_restores_exact": all(
            arm["continuation_v2_identical"] for arm in all_arms
        ),
        "all_source_patterns_preserved_per_ordinal_and_cell": all(
            arm["source_cell_pattern_preservation"] for arm in all_arms
        ),
        "all_arms_have_32_paired_outcomes": all(
            len(arm["post_rows"]) == 32 for arm in all_arms
        ),
        "all_children_are_one_level": all(
            child["specialization_depth"] == 1
            for arm in all_arms for child in arm["children"]
        ),
    }
    integrity_passed = all(integrity_gates.values())
    scientific_gates = {
        "integrity_passed": integrity_passed,
        "local_zero_fp": local["total_fp"] == 0,
        "local_tp_greater_than_119": local["total_tp"] > 119,
        "local_safe_narrow_at_least_17": local["safe_narrow_passes"] >= 17,
        "local_deployable_tp_exceeds_demotion": (
            local["deployable_tp"] > demotion["deployable_tp"]
        ),
        "local_deployable_tp_exceeds_blind": (
            local["deployable_tp"] > blind["deployable_tp"]
        ),
        "local_safe_narrow_exceeds_blind": (
            local["safe_narrow_passes"] > blind["safe_narrow_passes"]
        ),
        "at_least_one_local_child_matures": any(
            organism["arms"]["local_contrast_specialization"][
                "mature_child_count"
            ] > 0 for organism in organisms
        ),
    }
    if local["total_fp"] > 0:
        interpretation = "refinement_failed_safety_boundary"
    elif (
        local["total_tp"] > demotion["total_tp"]
        and local["deployable_tp"] == blind["deployable_tp"]
    ):
        interpretation = "specialization_works_local_contrast_unproven"
    elif not scientific_gates["at_least_one_local_child_matures"]:
        interpretation = "ceiling_passed_nomination_or_lifecycle_failed"
    elif all(scientific_gates.values()):
        interpretation = "local_contrast_specialization_passed"
    else:
        interpretation = "bounded_specialization_package_negative"
    return {
        "metrics": arm_metrics, "integrity_gates": integrity_gates,
        "scientific_gates": scientific_gates,
        "integrity_passed": integrity_passed,
        "scientific_passed": all(scientific_gates.values()),
        "interpretation": interpretation,
    }

