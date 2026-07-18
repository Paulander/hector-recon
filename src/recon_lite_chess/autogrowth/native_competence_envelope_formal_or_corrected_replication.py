"""Formal-OR repair replay and corrected V3B/V3C development replication."""
from __future__ import annotations

from collections import Counter
from dataclasses import asdict, replace
import gzip
import hashlib
from itertools import combinations
import json
from pathlib import Path
import pickle
from time import perf_counter
from typing import Any, Iterable, Mapping, Sequence

from recon_lite_hector.nodes import StemCellState

from .native_competence_envelope import (
    CompetenceContextGrowthGenome,
    CompetenceEnvelopeConfig,
    CompetenceEvidenceRecord,
    GraphNativeCompetenceEnvelope,
)
from .native_competence_envelope_experiment import _hash_json, _hash_list
from .native_competence_envelope_v3b_seed_robustness import (
    LEARNER_MODULE,
    LEARNER_SHA256,
    SEED_COUNT,
    SHUFFLE_SHA256,
    SOURCE_ROWS_SHA256,
    SOURCE_V3_ARTIFACT,
    SOURCE_V3_SHA256,
    V3BConfig,
    _cohort_counts,
    _records_from_v3,
    _run_arm,
    adjudicate_cohort,
    validate_seed_manifest,
)
from .native_competence_envelope_v3c_heldout import (
    ARM_NAMES,
    SOURCE_R0,
    SOURCE_R0_SHA256,
    SOURCE_SEED_MANIFEST,
    SOURCE_SEED_MANIFEST_SHA256,
    SOURCE_V3B,
    SOURCE_V3B_SHA256,
    V3CConfig,
    _evaluate_split,
    _organism_entries,
    _training_provenance,
)


REPAIR_SOURCE_COMMIT = "7ea7f4317483047a5330a74d826f56d907b9c2a3"
FORMAL_ENGINE = "libs/recon-lite/src/recon_lite/formal_engine.py"
FORMAL_ENGINE_SHA256 = (
    "28199a3199de7335725b2b119909862356a494743fd37c794e3da9b4cee58aa7"
)
SOURCE_V3C = (
    "reports/autogrowth/native_authority/"
    "native_competence_envelope_v3c_heldout_generalization.json"
)
SOURCE_V3C_SHA256 = (
    "5ec16c0a775ec14ceb3d1daf3952a8944a4a298daa0648566ef06a8036f50bbb"
)
PREREGISTRATION = (
    "docs/autogrowth/"
    "NATIVE_R0_COMPETENCE_ENVELOPE_FORMAL_OR_CORRECTED_REPLICATION_PREREGISTRATION.md"
)
RUNNER_MODULE = (
    "src/recon_lite_chess/autogrowth/"
    "native_competence_envelope_formal_or_corrected_replication.py"
)
REPLAY_OUTPUT = (
    "reports/autogrowth/native_authority/"
    "native_competence_envelope_formal_or_repair_replay.json"
)
CORRECTED_OUTPUT = (
    "reports/autogrowth/native_authority/"
    "native_competence_envelope_v3b_formal_or_corrected_replication.json"
)
CORRECTED_ORGANISM_DIRECTORY = (
    "reports/autogrowth/native_authority/"
    "native_competence_envelope_v3b_formal_or_corrected_organisms"
)
INTERNAL_POLICY_RESPONSE = "internal:policy_response"
EXPECTED_REPLAY = {
    "connected_total_tp": 313,
    "connected_total_fp": 39,
    "connected_any_tp": 31,
    "connected_safe_narrow": 6,
    "connected_strict": 0,
    "shuffled_total_tp": 0,
    "shuffled_total_fp": 0,
}
EXPECTED_CEILING = {
    "training_pure_validation_safe_pairs": 80,
    "training_pure_validation_safe_triples": 10_622,
    "best_pair_validation_positive_coverage": 12,
    "best_triple_validation_positive_coverage": 14,
    "combined_pure_pairs": 102,
    "combined_pure_triples": 13_265,
    "combined_pure_negative_arity_1_to_3": 0,
}


def run_repair_replay(
    *,
    output: str = REPLAY_OUTPUT,
    max_workers: int = 4,
) -> Mapping[str, Any]:
    """Replay frozen V3B organisms on viewed V3C validation under fixed OR."""

    target = Path(output)
    if target.exists():
        raise FileExistsError("formal-OR repair replay output already exists")
    started = perf_counter()
    sources = verify_frozen_sources()
    old_v3b = _load_json(SOURCE_V3B)
    old_v3c = _load_json(SOURCE_V3C)
    entries = _organism_entries(old_v3b)
    rows = validation_rows_from_preserved_v3c(old_v3c)
    evaluation = _evaluate_split(
        split="validation",
        split_rows=rows,
        entries=entries,
        cfg=V3CConfig(source_r0=SOURCE_R0, max_workers=max_workers),
        training_provenance=_training_provenance(old_v3b),
    )
    observed = replay_expectation_values(evaluation)
    invariants = classification_invariants(evaluation["organisms"])
    expectation_match = observed == EXPECTED_REPLAY
    result = {
        "schema_version": "native_competence_formal_or_repair_replay.v1",
        "diagnostic_only": True,
        "learning": False,
        "source_repair_commit": REPAIR_SOURCE_COMMIT,
        "source_freeze": sources,
        "expected": dict(EXPECTED_REPLAY),
        "observed": observed,
        "expectation_match": expectation_match,
        "classification_invariants": invariants,
        "evaluation": evaluation,
        "data_firewall": data_firewall_manifest(),
        "duration_seconds": perf_counter() - started,
        "stage": (
            "closed_repair_replay_passed"
            if expectation_match and all(invariants.values())
            else "repair_replay_discrepancy_abort"
        ),
        "passed": bool(expectation_match and all(invariants.values())),
    }
    return _write_json(target, result)


def run_corrected_replication(
    *,
    output: str = CORRECTED_OUTPUT,
    organism_directory: str = CORRECTED_ORGANISM_DIRECTORY,
    max_workers: int = 4,
) -> Mapping[str, Any]:
    """Regrow all V3B organisms under repaired OR, then conditionally develop."""

    target = Path(output)
    started = perf_counter()
    sources = verify_frozen_sources()
    replay = _load_json(REPLAY_OUTPUT)
    if _file_sha256(REPLAY_OUTPUT) != sources["repair_replay"]["sha256"]:
        raise RuntimeError("formal-OR repair replay changed")
    if replay.get("passed") is not True:
        raise RuntimeError("formal-OR repair replay did not pass")

    source = _load_json(SOURCE_V3_ARTIFACT)
    if _hash_json(source["training_rows"]) != SOURCE_ROWS_SHA256:
        raise RuntimeError("corrected replication training rows changed")
    permutation = tuple(map(int, source["outcome_shuffle"]["permutation"]))
    if _hash_list(permutation) != SHUFFLE_SHA256:
        raise RuntimeError("corrected replication outcome permutation changed")
    manifest = _load_json(SOURCE_SEED_MANIFEST)
    validate_seed_manifest(manifest)
    records = _records_from_v3(source["training_rows"])
    outcomes = tuple(record.observed_completion for record in records)
    shuffled_records = tuple(
        replace(record, observed_completion=outcomes[permutation[index]])
        for index, record in enumerate(records)
    )
    base_config = CompetenceEnvelopeConfig(**source["frozen_config"])
    cfg = V3BConfig(
        output=output,
        organism_directory=organism_directory,
    )
    if target.exists():
        result = dict(_load_json(target))
        if result.get("source_freeze") != sources:
            raise RuntimeError("corrected replication checkpoint source mismatch")
    else:
        result = {
            "schema_version": (
                "native_competence_envelope_v3b_formal_or_corrected.v1"
            ),
            "preregistered": True,
            "source_repair_commit": REPAIR_SOURCE_COMMIT,
            "source_freeze": sources,
            "frozen_factor_law": {
                "training_rows": 64,
                "seed_manifest_sha256": SOURCE_SEED_MANIFEST_SHA256,
                "outcome_shuffle_sha256": SHUFFLE_SHA256,
                "learner_thresholds_capacities_rounds_request_order_unchanged": True,
                "only_runtime_change": "explicit_formal_or_semantic_repair",
                "no_seed_retry_selection_or_ensemble": True,
            },
            "completed_seed_count": 0,
            "seed_results": [],
            "stage": "corrected_v3b_running",
            "data_firewall": data_firewall_manifest(),
        }
        _write_json(target, result)

    completed = list(result["seed_results"])
    _validate_checkpoint_prefix(completed, manifest["seeds"])
    for seed_row in manifest["seeds"][len(completed):]:
        ordinal = int(seed_row["ordinal"])
        seed = int(seed_row["seed"])
        connected = _run_arm(
            records, seed, "connected", base_config, cfg, ordinal
        )
        shuffled = _run_arm(
            shuffled_records,
            seed,
            "outcome_shuffled",
            base_config,
            cfg,
            ordinal,
        )
        connected["proposal_identity_audit"] = proposal_identity_audit(
            connected["organism_artifact"]
        )
        shuffled["proposal_identity_audit"] = proposal_identity_audit(
            shuffled["organism_artifact"]
        )
        connected_engaged = bool(connected["engaged"])
        shuffled_engaged = bool(shuffled["engaged"])
        if connected_engaged and not shuffled_engaged:
            paired = "connected_only"
        elif shuffled_engaged and not connected_engaged:
            paired = "shuffled_only"
        elif connected_engaged:
            paired = "both"
        else:
            paired = "neither"
        completed.append({
            "ordinal": ordinal,
            "seed": seed,
            "connected": connected,
            "outcome_shuffled": shuffled,
            "paired_outcome": paired,
        })
        result.update({
            "seed_results": completed,
            "completed_seed_count": len(completed),
            "running_summary": _cohort_counts(completed),
        })
        _write_json(target, result)

    adjudication = adjudicate_cohort(completed)
    result.update({
        "completed_seed_count": len(completed),
        "cohort_counts": _cohort_counts(completed),
        "adjudication": adjudication,
        "organism_index": corrected_organism_index(completed),
        "corrected_validation": None,
        "representation_ceiling": None,
    })
    gates_pass = bool(
        adjudication["mechanism_discrimination"]["passed"]
        and adjudication["reliability"]["passed"]
    )
    if not gates_pass:
        result.update({
            "stage": "closed_after_corrected_v3b_gates",
            "passed": False,
            "corrected_validation_opened": False,
            "next_action": "stop_no_rescue",
            "duration_seconds": perf_counter() - started,
        })
        return _write_json(target, result)

    result["corrected_validation_opened"] = True
    _write_json(target, result)
    old_v3c = _load_json(SOURCE_V3C)
    validation_rows = validation_rows_from_preserved_v3c(old_v3c)
    entries = corrected_organism_entries(completed)
    validation = _evaluate_split(
        split="validation",
        split_rows=validation_rows,
        entries=entries,
        cfg=V3CConfig(source_r0=SOURCE_R0, max_workers=max_workers),
        training_provenance=_training_provenance(_load_json(SOURCE_V3B)),
    )
    ceiling = representation_ceiling(
        records,
        validation["reference_rows"],
        completed,
    )
    result.update({
        "corrected_validation": validation,
        "representation_ceiling": ceiling,
        "stage": (
            "closed_after_corrected_validation"
            if ceiling["integrity"]["passed"]
            else "representation_ceiling_integrity_abort"
        ),
        "passed": bool(ceiling["integrity"]["passed"]),
        "regression_opened": False,
        "next_action": "stop_recommend_continual_competence_correction_only",
        "duration_seconds": perf_counter() - started,
    })
    return _write_json(target, result)


def verify_frozen_sources() -> dict[str, Any]:
    expected = {
        FORMAL_ENGINE: FORMAL_ENGINE_SHA256,
        LEARNER_MODULE: LEARNER_SHA256,
        SOURCE_V3_ARTIFACT: SOURCE_V3_SHA256,
        SOURCE_V3B: SOURCE_V3B_SHA256,
        SOURCE_V3C: SOURCE_V3C_SHA256,
        SOURCE_SEED_MANIFEST: SOURCE_SEED_MANIFEST_SHA256,
        SOURCE_R0: SOURCE_R0_SHA256,
    }
    for path, digest in expected.items():
        if _file_sha256(path) != digest:
            raise RuntimeError(f"corrected replication source changed: {path}")
    result = {
        "repair_commit": REPAIR_SOURCE_COMMIT,
        "sources": {
            path: {"sha256": digest} for path, digest in sorted(expected.items())
        },
        "preregistration": {
            "path": PREREGISTRATION,
            "sha256": _file_sha256(PREREGISTRATION),
        },
        "runner": {"path": RUNNER_MODULE, "sha256": _file_sha256(RUNNER_MODULE)},
    }
    if Path(REPLAY_OUTPUT).exists():
        result["repair_replay"] = {
            "path": REPLAY_OUTPUT,
            "sha256": _file_sha256(REPLAY_OUTPUT),
        }
    return result


def validation_rows_from_preserved_v3c(
    source: Mapping[str, Any],
) -> list[dict[str, Any]]:
    if source.get("regression_inference_opened") is not False:
        raise RuntimeError("preserved V3C regression firewall changed")
    rows = source["validation"]["reference_rows"]
    return [{
        "row_index": int(row["row_index"]),
        "segment": str(row["segment"]),
        "source_pool": str(row["source_pool"]),
        "source_index": int(row["source_index"]),
        "fen": str(row["fen"]),
    } for row in rows]


def replay_expectation_values(evaluation: Mapping[str, Any]) -> dict[str, int]:
    arms = evaluation["cohort_metrics"]["arms"]
    connected = arms["connected"]
    shuffled = arms["outcome_shuffled"]
    return {
        "connected_total_tp": int(connected["total_tp"]),
        "connected_total_fp": int(connected["total_fp"]),
        "connected_any_tp": int(connected["organisms_with_any_tp"]),
        "connected_safe_narrow": int(connected["safe_narrow_passes"]),
        "connected_strict": int(connected["strict_passes"]),
        "shuffled_total_tp": int(shuffled["total_tp"]),
        "shuffled_total_fp": int(shuffled["total_fp"]),
    }


def classification_invariants(
    organisms: Sequence[Mapping[str, Any]],
) -> dict[str, bool]:
    rows = [row for organism in organisms for row in organism["rows"]]
    return {
        "formal_available_equals_policy_and_available_ids": all(
            bool(row["formal_available"])
            == (bool(row["policy_response"]) and bool(row["available_cell_ids"]))
            for row in rows
        ),
        "formal_refuted_equals_policy_and_refuted_ids": all(
            bool(row["formal_refuted"])
            == (bool(row["policy_response"]) and bool(row["refuted_cell_ids"]))
            for row in rows
        ),
    }


def proposal_identity_audit(artifact: Mapping[str, Any]) -> dict[str, Any]:
    compressed = Path(str(artifact["path"])).read_bytes()
    envelope = pickle.loads(gzip.decompress(compressed))
    if not isinstance(envelope, GraphNativeCompetenceEnvelope):
        raise TypeError("corrected organism is not a competence envelope")
    attempted = sorted({
        tuple(sorted(map(str, row.get("members", ()))))
        for row in envelope.audit.proposal_rows
        if row.get("members")
        and not any(
            str(member).startswith("context:")
            for member in row.get("members", ())
        )
    })
    admitted = sorted({
        tuple(sorted(map(str, cell.members)))
        for cell in envelope.cells.values()
        if not any(member.startswith("context:") for member in cell.members)
    })
    matured = sorted({
        tuple(sorted(map(str, cell.members)))
        for cell in envelope.cells.values()
        if cell.state == StemCellState.MATURE
        and not any(member.startswith("context:") for member in cell.members)
    })
    return {
        "attempted_count": len(attempted),
        "admitted_count": len(admitted),
        "matured_count": len(matured),
        "attempted_member_specs": [list(row) for row in attempted],
        "admitted_member_specs": [list(row) for row in admitted],
        "matured_member_specs": [list(row) for row in matured],
        "digest": _hash_json({
            "attempted": attempted,
            "admitted": admitted,
            "matured": matured,
        }),
    }


def corrected_organism_index(
    completed: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    rows = []
    for seed_row in completed:
        for arm in ARM_NAMES:
            artifact = seed_row[arm]["organism_artifact"]
            rows.append({
                "ordinal": int(seed_row["ordinal"]),
                "seed": int(seed_row["seed"]),
                "arm": arm,
                "path": str(artifact["path"]),
                "compressed_sha256": str(artifact["compressed_sha256"]),
                "uncompressed_sha256": str(artifact["uncompressed_sha256"]),
            })
    rows.sort(key=lambda row: (row["ordinal"], ARM_NAMES.index(row["arm"])))
    return {"count": len(rows), "sha256": _hash_json(rows), "rows": rows}


def corrected_organism_entries(
    completed: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    entries = []
    for seed_row in completed:
        for arm in ARM_NAMES:
            arm_result = seed_row[arm]
            entries.append({
                "ordinal": int(seed_row["ordinal"]),
                "seed": int(seed_row["seed"]),
                "arm": arm,
                "engaged": bool(arm_result["engaged"]),
                "mature_cell_count": int(arm_result["mature_cell_count"]),
                "artifact": dict(arm_result["organism_artifact"]),
            })
    entries.sort(key=lambda row: (row["ordinal"], ARM_NAMES.index(row["arm"])))
    if len(entries) != 2 * SEED_COUNT:
        raise RuntimeError("corrected organism cohort is incomplete")
    return entries


def representation_ceiling(
    training: Sequence[CompetenceEvidenceRecord],
    validation_rows: Sequence[Mapping[str, Any]],
    completed: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    rows = [
        (
            frozenset(record.active_signal_ids) - {INTERNAL_POLICY_RESPONSE},
            bool(record.observed_completion),
        )
        for record in training
    ] + [
        (
            frozenset(map(str, row["active_competence_signal_ids"]))
            - {INTERNAL_POLICY_RESPONSE},
            bool(row["actual_completion"]),
        )
        for row in validation_rows
    ]
    if len(training) != 64 or len(validation_rows) != 32:
        raise RuntimeError("representation ceiling row count changed")
    signal_masks: dict[str, int] = {}
    success_mask = 0
    for index, (signals, outcome) in enumerate(rows):
        bit = 1 << index
        if outcome:
            success_mask |= bit
        for signal in signals:
            signal_masks[signal] = signal_masks.get(signal, 0) | bit
    full_mask = (1 << len(rows)) - 1
    failure_mask = full_mask ^ success_mask
    training_mask = (1 << len(training)) - 1
    validation_positive_mask = sum(
        1 << (len(training) + index)
        for index, row in enumerate(validation_rows)
        if bool(row["actual_completion"])
    )
    validation_negative_mask = sum(
        1 << (len(training) + index)
        for index, row in enumerate(validation_rows)
        if not bool(row["actual_completion"])
    )
    eligible = tuple(sorted(
        signal
        for signal, mask in signal_masks.items()
        if (mask & training_mask).bit_count() >= 4
    ))
    attempted, admitted, matured = cohort_member_specs(completed)
    counts: dict[str, Any] = {}
    digest = hashlib.sha256()
    total_negative = 0
    for arity in (1, 2, 3):
        safe = 0
        combined_pure = 0
        combined_negative = 0
        safe_attempted = 0
        safe_admitted = 0
        safe_matured = 0
        best_coverage = 0
        coverage_hist = Counter()
        examples = []
        for members in combinations(eligible, arity):
            mask = full_mask
            for member in members:
                mask &= signal_masks[member]
            training_hits = mask & training_mask
            train_success = (training_hits & success_mask).bit_count()
            train_failure = (training_hits & failure_mask).bit_count()
            validation_tp = (mask & validation_positive_mask).bit_count()
            validation_fp = (mask & validation_negative_mask).bit_count()
            training_pure_validation_safe = bool(
                training_hits.bit_count() >= 4
                and train_success
                and not train_failure
                and validation_tp
                and not validation_fp
            )
            combined_success = (mask & success_mask).bit_count()
            combined_failure = (mask & failure_mask).bit_count()
            combined_is_pure = bool(
                mask.bit_count() >= 4
                and (
                    (combined_success and not combined_failure)
                    or (combined_failure and not combined_success)
                )
            )
            if combined_is_pure:
                combined_pure += 1
                if combined_failure and not combined_success:
                    combined_negative += 1
            if not training_pure_validation_safe:
                continue
            safe += 1
            coverage_hist[str(validation_tp)] += 1
            best_coverage = max(best_coverage, validation_tp)
            safe_attempted += int(members in attempted)
            safe_admitted += int(members in admitted)
            safe_matured += int(members in matured)
            row = {
                "members": list(members),
                "arity": arity,
                "training_support": training_hits.bit_count(),
                "validation_tp": validation_tp,
                "validation_fp": validation_fp,
                "attempted": members in attempted,
                "admitted": members in admitted,
                "matured": members in matured,
            }
            encoded = json.dumps(
                row, sort_keys=True, separators=(",", ":")
            ).encode("utf-8")
            digest.update(len(encoded).to_bytes(8, "big"))
            digest.update(encoded)
            if len(examples) < 8:
                examples.append(row)
        total_negative += combined_negative
        counts[str(arity)] = {
            "training_pure_validation_safe": safe,
            "best_zero_fp_validation_positive_coverage": best_coverage,
            "combined_data_pure": combined_pure,
            "combined_data_pure_negative": combined_negative,
            "safe_attempted_by_connected_cohort": safe_attempted,
            "safe_admitted_by_connected_cohort": safe_admitted,
            "safe_matured_by_connected_cohort": safe_matured,
            "safe_validation_coverage_histogram": dict(sorted(coverage_hist.items())),
            "bounded_examples": examples,
        }
    observed = {
        "training_pure_validation_safe_pairs": counts["2"][
            "training_pure_validation_safe"
        ],
        "training_pure_validation_safe_triples": counts["3"][
            "training_pure_validation_safe"
        ],
        "best_pair_validation_positive_coverage": counts["2"][
            "best_zero_fp_validation_positive_coverage"
        ],
        "best_triple_validation_positive_coverage": counts["3"][
            "best_zero_fp_validation_positive_coverage"
        ],
        "combined_pure_pairs": counts["2"]["combined_data_pure"],
        "combined_pure_triples": counts["3"]["combined_data_pure"],
        "combined_pure_negative_arity_1_to_3": total_negative,
    }
    mismatches = {
        key: {"expected": value, "observed": observed[key]}
        for key, value in EXPECTED_CEILING.items()
        if observed[key] != value
    }
    return {
        "laboratory_only": True,
        "read_only": True,
        "learner_feedback": False,
        "internal_policy_response_excluded": True,
        "training_rows": 64,
        "viewed_validation_rows": 32,
        "eligible_signal_count": len(eligible),
        "counts_by_arity": counts,
        "safe_pattern_digest": digest.hexdigest(),
        "cohort_member_spec_counts": {
            "attempted": len(attempted),
            "admitted": len(admitted),
            "matured": len(matured),
        },
        "integrity": {
            "expected": dict(EXPECTED_CEILING),
            "observed": observed,
            "mismatches": mismatches,
            "passed": not mismatches,
        },
    }


def cohort_member_specs(
    completed: Sequence[Mapping[str, Any]],
) -> tuple[set[tuple[str, ...]], set[tuple[str, ...]], set[tuple[str, ...]]]:
    buckets = [set(), set(), set()]
    keys = (
        "attempted_member_specs",
        "admitted_member_specs",
        "matured_member_specs",
    )
    for seed_row in completed:
        audit = seed_row["connected"]["proposal_identity_audit"]
        for bucket, key in zip(buckets, keys, strict=True):
            bucket.update(tuple(map(str, members)) for members in audit[key])
    return buckets[0], buckets[1], buckets[2]


def data_firewall_manifest() -> dict[str, Any]:
    return {
        "regression_accessed": False,
        "fresh_pool_accessed": False,
        "r1_accessed": False,
        "retired_65_successors_accessed": False,
        "new_krk_cohort_generated": False,
        "continual_competence_correction_implemented": False,
        "terminal_trace_closure_implemented": False,
    }


def _validate_checkpoint_prefix(
    completed: Sequence[Mapping[str, Any]],
    seeds: Sequence[Mapping[str, Any]],
) -> None:
    for ordinal, row in enumerate(completed):
        if int(row["ordinal"]) != ordinal:
            raise RuntimeError("corrected replication checkpoint is not contiguous")
        if int(row["seed"]) != int(seeds[ordinal]["seed"]):
            raise RuntimeError("corrected replication checkpoint seed mismatch")


def _file_sha256(path: str | Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _load_json(path: str | Path) -> Mapping[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _write_json(path: str | Path, value: Mapping[str, Any]) -> Mapping[str, Any]:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return value
