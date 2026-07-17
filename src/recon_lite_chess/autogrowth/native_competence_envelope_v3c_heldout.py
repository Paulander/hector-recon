"""Preregistered inference-only V3C held-out cohort generalization."""
from __future__ import annotations

from collections import Counter, defaultdict
from concurrent.futures import ProcessPoolExecutor
from contextlib import ExitStack, contextmanager
from dataclasses import asdict, dataclass, replace
import gzip
import hashlib
import json
from pathlib import Path
import pickle
import struct
from time import perf_counter
from typing import Any, Iterator, Mapping, Sequence
from unittest.mock import patch

import chess

from recon_lite import ChildResponse, FrameContext, FrameKind

from .native_authority_handover import (
    ChildQuery,
    GraphActuation,
    NativeR0Organism,
    native_authority_tripwires,
)
from .native_authority_lab import _config_from_prior_artifact
from .native_child_availability import observe_query_completion
from .native_competence_envelope import (
    AvailabilityState,
    GraphNativeCompetenceEnvelope,
    NativeCompetenceSessionAudit,
    NativeR0CompetenceOrganism,
    extract_active_competence_signals,
)
from .native_intrinsic_curriculum import _build_pools, _r1_orbit_key


SOURCE_COMMIT = "152fc01c165f64d9fe87e3d9ddf2fb0dd2c2151a"
SOURCE_V3B = (
    "reports/autogrowth/native_authority/"
    "native_competence_envelope_v3b_seed_robustness.json"
)
SOURCE_V3B_SHA256 = (
    "90a5393e92516256b25f35f43c1a9b2355b15b0e450c2b8836989f1a9c5ce920"
)
ORGANISM_INDEX_SHA256 = (
    "8762aab81cbf72440371d40fef3e4a297bf312f7754d8afb30b372ed34ce2f3e"
)
SOURCE_SEED_MANIFEST = (
    "reports/autogrowth/native_authority/"
    "native_competence_envelope_v3b_seed_manifest.json"
)
SOURCE_SEED_MANIFEST_SHA256 = (
    "4e9faa8700645de174cd8c552cf51bee4d517aa79833bff250fe789dd1530098"
)
SOURCE_R0 = "snapshots/autogrowth/native_authority/r0_organism.pkl"
SOURCE_R0_SHA256 = (
    "bb58b7d64bd3ab5b696713a7253555e051bd0e9fdef4637db7c27e7517495eaf"
)
SOURCE_R0_METADATA = "snapshots/autogrowth/native_authority/r0_organism.pkl.json"
SOURCE_R0_METADATA_SHA256 = (
    "d594fe8de89dee3b99b7c57a1cddb84949470fd91253d81f0a71a657147a348b"
)
SOURCE_CURRICULUM = (
    "reports/autogrowth/native_from_scratch/"
    "r0_r1_balanced96_240_seed_20260719_compact.json"
)
SOURCE_CURRICULUM_SHA256 = (
    "c55a4097547713edb5d9ef27a250bbfac62fb9886d86afae87b387b72869c792"
)
SOURCE_LEARNER = "src/recon_lite_chess/autogrowth/native_competence_envelope.py"
SOURCE_LEARNER_SHA256 = (
    "65dda4f09bc1181a6fe3780c27b56da4fc888a377ae3cfffe3c728e9d11d2a7b"
)
SOURCE_V3 = (
    "reports/autogrowth/native_authority/"
    "touched_r0_competence_envelope_v3_training_only.json"
)
SOURCE_V3_SHA256 = (
    "91b3ae80773f2c2dd20cd00b82f5a1fde8190deef670623ea9ba39db9d514d94"
)
PREREGISTRATION = (
    "docs/autogrowth/"
    "NATIVE_R0_COMPETENCE_ENVELOPE_V3C_HELDOUT_PREREGISTRATION.md"
)
RUNNER_MODULE = (
    "src/recon_lite_chess/autogrowth/"
    "native_competence_envelope_v3c_heldout.py"
)
OUTPUT = (
    "reports/autogrowth/native_authority/"
    "native_competence_envelope_v3c_heldout_generalization.json"
)

POOL_SPECS: Mapping[str, Mapping[str, Any]] = {
    "r0_validation": {
        "count": 16,
        "sha256": "2100368431445bf95f045f4387858f662c4510320b12a6907cdeca1d46022599",
    },
    "gate_validation_decoys": {
        "count": 16,
        "sha256": "196c5bfec16b1d5efa1f41d1a868ebf90f0401d5cc5b353c05cd4a204a5ab44f",
    },
    "r0_regression": {
        "count": 16,
        "sha256": "964c8d543e03cc6d756eb0f52218133e9af95fdb6c97dc9c0aff8b8e58858f69",
    },
    "gate_regression_decoys": {
        "count": 16,
        "sha256": "acdafa01d92b7ee77053de438168c828bbf94d5006cc6dfe5d0cf42299ee64e8",
    },
}
SPLIT_POOL_NAMES = {
    "validation": ("r0_validation", "gate_validation_decoys"),
    "regression": ("r0_regression", "gate_regression_decoys"),
}
ROW_ORDER_COMMITMENTS = {
    "validation": "f531156e7630950587e149c435f31994340f7eb4aeb0c31667502bfcf4ac7d76",
    "regression": "24899b4a004cf68d5e4a4105ea479496d26fea884d447a105e339cf783bffee4",
}
ACTUATION_FIELDS = (
    "actuator_identity",
    "move_uci",
    "option_identity",
    "activation",
    "candidate_count",
    "formal_ticks",
    "graph_owned",
    "host_fallback",
)
ARM_NAMES = ("connected", "outcome_shuffled")


@dataclass(frozen=True)
class V3CConfig:
    output: str = OUTPUT
    source_v3b: str = SOURCE_V3B
    source_r0: str = SOURCE_R0
    source_curriculum: str = SOURCE_CURRICULUM
    max_workers: int = 4


def row_order_commitment(split: str) -> str:
    names = SPLIT_POOL_NAMES[split]
    rows = [
        {
            "segment_ordinal": segment_ordinal,
            "pool_name": name,
            "pool_sha256": POOL_SPECS[name]["sha256"],
            "count": POOL_SPECS[name]["count"],
            "indices": list(range(int(POOL_SPECS[name]["count"]))),
        }
        for segment_ordinal, name in enumerate(names)
    ]
    return _hash_json(rows)


def run_v3c(config: V3CConfig | None = None) -> Mapping[str, Any]:
    cfg = config or V3CConfig()
    started = perf_counter()
    if Path(cfg.output).exists():
        raise FileExistsError("canonical V3C output already exists")
    source = _verify_and_load_sources(cfg)
    entries = _organism_entries(source)
    pools = _load_and_verify_pool_source(cfg.source_curriculum)
    validation_rows = _split_rows("validation", pools)
    training_provenance = _training_provenance(source)

    result: dict[str, Any] = {
        "schema_version": "native_r0_competence_envelope_v3c_heldout.v1",
        "preregistered": True,
        "inference_only": True,
        "source_commit": SOURCE_COMMIT,
        "source_freeze": _source_freeze_manifest(cfg),
        "cohort": {
            "connected_count": 32,
            "outcome_shuffled_count": 32,
            "all_organisms_retained": True,
            "ordinal_13_connected_retained": any(
                entry["arm"] == "connected" and entry["ordinal"] == 13
                for entry in entries
            ),
            "selection_or_ensemble": False,
        },
        "architectural_debt": {
            "mechanism": "extract_active_competence_signals",
            "unchanged": True,
            "terminal_trace_native": False,
            "current_source": "board_action_and_graph_map_reconstruction",
        },
        "pool_freeze": _pool_freeze_manifest(pools),
        "validation": None,
        "regression": None,
        "regression_inference_opened": False,
        "validation_or_regression_rows_used_for_learning": 0,
        "evidence_insertions": 0,
        "reward_or_grounding_updates": 0,
        "fresh_pool_accessed": False,
        "retired_65_successors_accessed": False,
        "r1_accessed": False,
    }

    validation = _evaluate_split(
        split="validation",
        split_rows=validation_rows,
        entries=entries,
        cfg=cfg,
        training_provenance=training_provenance,
    )
    result["validation"] = validation
    if not validation["admission"]["passed"]:
        result.update({
            "stage": "instrument_abort_validation_admission",
            "interpretation": "instrument_abort",
            "binding_boundary": "integrity_or_parity",
            "regression_inference_opened": False,
            "passed": False,
            "next_action": "stop_no_in_package_repair",
            "duration_seconds": perf_counter() - started,
        })
        return _write_json(cfg.output, result)

    validation_verdicts = validation["verdicts"]
    open_regression = bool(
        validation_verdicts["strict_generalization"]["passed"]
        or validation_verdicts["safe_narrow_transfer"]["passed"]
    )
    if not open_regression:
        result.update({
            "stage": "closed_after_validation",
            "interpretation": _validation_interpretation(validation),
            "binding_boundary": _validation_boundary(validation),
            "regression_inference_opened": False,
            "passed": False,
            "next_action": "stop_no_in_package_repair",
            "duration_seconds": perf_counter() - started,
        })
        return _write_json(cfg.output, result)

    result["regression_inference_opened"] = True
    regression_rows = _split_rows("regression", pools)
    regression = _evaluate_split(
        split="regression",
        split_rows=regression_rows,
        entries=entries,
        cfg=cfg,
        training_provenance=training_provenance,
        validation=validation,
    )
    result["regression"] = regression
    if not regression["admission"]["passed"]:
        result.update({
            "stage": "instrument_abort_regression_admission",
            "interpretation": "instrument_abort",
            "binding_boundary": "integrity_or_parity",
            "passed": False,
            "next_action": "stop_no_in_package_repair",
            "duration_seconds": perf_counter() - started,
        })
        return _write_json(cfg.output, result)

    replication = regression["verdicts"]
    if replication["strict_replication"]["passed"]:
        interpretation = "robust_envelope_heldout_competence_generalization"
        boundary = None
        passed = True
    elif replication["safe_narrow_replication"]["passed"]:
        interpretation = "safe_narrow_replication_coverage_is_binding"
        boundary = "ecological_coverage_or_generalization"
        passed = True
    elif _any_connected_fp(validation, regression):
        interpretation = "training_pure_conjunctions_overgeneralize"
        boundary = "selectivity_or_representation"
        passed = False
    else:
        interpretation = "validation_transfer_did_not_replicate"
        boundary = "cross_split_coverage_or_equivalence"
        passed = False
    result.update({
        "stage": "closed_after_conditional_regression",
        "interpretation": interpretation,
        "binding_boundary": boundary,
        "passed": passed,
        "next_action": "stop_no_in_package_repair",
        "duration_seconds": perf_counter() - started,
    })
    return _write_json(cfg.output, result)


def _verify_and_load_sources(cfg: V3CConfig) -> Mapping[str, Any]:
    expected = {
        cfg.source_v3b: SOURCE_V3B_SHA256,
        SOURCE_SEED_MANIFEST: SOURCE_SEED_MANIFEST_SHA256,
        cfg.source_r0: SOURCE_R0_SHA256,
        SOURCE_R0_METADATA: SOURCE_R0_METADATA_SHA256,
        cfg.source_curriculum: SOURCE_CURRICULUM_SHA256,
        SOURCE_LEARNER: SOURCE_LEARNER_SHA256,
        SOURCE_V3: SOURCE_V3_SHA256,
    }
    for path, digest in expected.items():
        if _file_sha256(path) != digest:
            raise RuntimeError(f"V3C frozen source changed: {path}")
    source = _load_json(cfg.source_v3b)
    if source.get("passed_integrity") is not True:
        raise RuntimeError("V3B source integrity did not pass")
    return source


def _source_freeze_manifest(cfg: V3CConfig) -> Mapping[str, Any]:
    return {
        "v3b_result": {"path": cfg.source_v3b, "sha256": SOURCE_V3B_SHA256},
        "organism_index_sha256": ORGANISM_INDEX_SHA256,
        "seed_manifest": {
            "path": SOURCE_SEED_MANIFEST,
            "sha256": SOURCE_SEED_MANIFEST_SHA256,
        },
        "r0_organism": {"path": cfg.source_r0, "sha256": SOURCE_R0_SHA256},
        "r0_metadata": {
            "path": SOURCE_R0_METADATA,
            "sha256": SOURCE_R0_METADATA_SHA256,
        },
        "curriculum": {
            "path": cfg.source_curriculum,
            "sha256": SOURCE_CURRICULUM_SHA256,
        },
        "learner": {"path": SOURCE_LEARNER, "sha256": SOURCE_LEARNER_SHA256},
        "v3_training_provenance": {
            "path": SOURCE_V3,
            "sha256": SOURCE_V3_SHA256,
        },
        "preregistration": {
            "path": PREREGISTRATION,
            "sha256": _file_sha256(PREREGISTRATION),
        },
        "runner": {"path": RUNNER_MODULE, "sha256": _file_sha256(RUNNER_MODULE)},
    }


def _organism_entries(source: Mapping[str, Any]) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    index_rows: list[dict[str, Any]] = []
    for seed_row in source["seed_results"]:
        for arm in ARM_NAMES:
            arm_result = seed_row[arm]
            artifact = arm_result["organism_artifact"]
            entry = {
                "ordinal": int(seed_row["ordinal"]),
                "seed": int(seed_row["seed"]),
                "arm": arm,
                "engaged": bool(arm_result["engaged"]),
                "mature_cell_count": int(arm_result["mature_cell_count"]),
                "artifact": dict(artifact),
            }
            entries.append(entry)
            index_rows.append({
                "ordinal": entry["ordinal"],
                "seed": entry["seed"],
                "arm": arm,
                "path": artifact["path"],
                "compressed_sha256": artifact["compressed_sha256"],
                "uncompressed_sha256": artifact["uncompressed_sha256"],
            })
    entries.sort(key=lambda row: (row["ordinal"], ARM_NAMES.index(row["arm"])))
    index_rows.sort(key=lambda row: (row["ordinal"], ARM_NAMES.index(row["arm"])))
    if len(entries) != 64:
        raise RuntimeError("V3C source does not contain all 64 organisms")
    if Counter(entry["arm"] for entry in entries) != Counter({
        "connected": 32,
        "outcome_shuffled": 32,
    }):
        raise RuntimeError("V3C source arm counts changed")
    if _hash_json(index_rows) != ORGANISM_INDEX_SHA256:
        raise RuntimeError("V3C organism-index digest mismatch")
    for entry in entries:
        _verify_organism_artifact(entry)
    return entries


def _verify_organism_artifact(entry: Mapping[str, Any]) -> None:
    artifact = entry["artifact"]
    compressed = Path(artifact["path"]).read_bytes()
    if hashlib.sha256(compressed).hexdigest() != artifact["compressed_sha256"]:
        raise RuntimeError("V3C compressed organism hash mismatch")
    raw = gzip.decompress(compressed)
    if hashlib.sha256(raw).hexdigest() != artifact["uncompressed_sha256"]:
        raise RuntimeError("V3C uncompressed organism hash mismatch")
    envelope = pickle.loads(raw)
    if not isinstance(envelope, GraphNativeCompetenceEnvelope):
        raise TypeError("V3C source organism is not a competence envelope")
    if _hash_json(envelope.to_manifest()) != artifact["source_manifest_sha256"]:
        raise RuntimeError("V3C source organism manifest mismatch")
    mature = sum(cell.is_mature for cell in envelope.cells.values())
    if mature != int(entry["mature_cell_count"]):
        raise RuntimeError("V3C source maturity count mismatch")


def _load_and_verify_pool_source(source_path: str) -> Any:
    artifact = _load_json(source_path)
    historical = _config_from_prior_artifact(artifact)
    pools = _build_pools(replace(historical, run_r1=False))
    for name, spec in POOL_SPECS.items():
        values = tuple(getattr(pools, name))
        if len(values) != int(spec["count"]):
            raise RuntimeError(f"V3C pool count changed: {name}")
        if _hash_json(values) != spec["sha256"]:
            raise RuntimeError(f"V3C pool hash changed: {name}")
    for split, expected in ROW_ORDER_COMMITMENTS.items():
        if row_order_commitment(split) != expected:
            raise RuntimeError(f"V3C row-order commitment changed: {split}")
    return pools


def _pool_freeze_manifest(pools: Any) -> Mapping[str, Any]:
    return {
        "terminology": "envelope-held-out historical pools",
        "pool_hashes": {
            name: {
                "count": len(tuple(getattr(pools, name))),
                "sha256": _hash_json(tuple(getattr(pools, name))),
            }
            for name in POOL_SPECS
        },
        "row_order_commitments": dict(ROW_ORDER_COMMITMENTS),
        "fresh_pool": False,
        "rows_removed_or_regenerated": 0,
    }


def _split_rows(split: str, pools: Any) -> list[dict[str, Any]]:
    positive_name, negative_name = SPLIT_POOL_NAMES[split]
    rows: list[dict[str, Any]] = []
    for segment, pool_name in (("positive", positive_name), ("decoy", negative_name)):
        for source_index, fen in enumerate(tuple(getattr(pools, pool_name))):
            rows.append({
                "row_index": len(rows),
                "segment": segment,
                "source_pool": pool_name,
                "source_index": source_index,
                "fen": fen,
            })
    if len(rows) != 32:
        raise RuntimeError(f"V3C {split} row count changed")
    return rows


def _training_provenance(source: Mapping[str, Any]) -> Mapping[str, tuple[str, ...]]:
    if source["source_v3_artifact"]["sha256"] != SOURCE_V3_SHA256:
        raise RuntimeError("V3C source V3 provenance changed")
    v3 = _load_json(SOURCE_V3)
    positive = tuple(
        row["fen"] for row in v3["training_rows"]
        if row["historical_pool_name"] == "r0_train"
    )
    decoy = tuple(
        row["fen"] for row in v3["training_rows"]
        if row["historical_pool_name"] == "train_decoy"
    )
    return {"positive": positive, "decoy": decoy}


def _evaluate_split(
    *,
    split: str,
    split_rows: Sequence[Mapping[str, Any]],
    entries: Sequence[Mapping[str, Any]],
    cfg: V3CConfig,
    training_provenance: Mapping[str, Sequence[str]],
    validation: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    r0 = NativeR0Organism.load(cfg.source_r0)
    r0_before = dict(r0.persistent_state_audit())
    with native_authority_tripwires() as real_tripwires:
        reference_rows = [
            _real_reference_row(r0, row, split) for row in split_rows
        ]
    r0_after = dict(r0.persistent_state_audit())
    worker_args = [
        {
            "entry": dict(entry),
            "split": split,
            "split_rows": list(map(dict, split_rows)),
            "reference_rows": reference_rows,
            "source_r0": cfg.source_r0,
        }
        for entry in entries
    ]
    if cfg.max_workers == 1:
        organisms = [_evaluate_organism_worker(arg) for arg in worker_args]
    else:
        with ProcessPoolExecutor(max_workers=cfg.max_workers) as executor:
            organisms = list(executor.map(_evaluate_organism_worker, worker_args))
    organisms.sort(key=lambda row: (row["ordinal"], ARM_NAMES.index(row["arm"])))
    overlap = _overlap_report(
        training_provenance,
        split_rows,
        validation_rows=(None if validation is None else validation["reference_rows"]),
        split=split,
    )
    admission = _split_admission(
        split_rows=split_rows,
        reference_rows=reference_rows,
        organisms=organisms,
        r0_identity=r0_before == r0_after,
        real_tripwires=real_tripwires,
    )
    cohort = _cohort_metrics(organisms)
    result = {
        "split": split,
        "row_order_commitment": ROW_ORDER_COMMITMENTS[split],
        "concrete_row_order_sha256": _hash_json([
            {
                "row_index": row["row_index"],
                "segment": row["segment"],
                "source_pool": row["source_pool"],
                "source_index": row["source_index"],
                "fen": row["fen"],
            }
            for row in split_rows
        ]),
        "reference_rows": reference_rows,
        "organisms": organisms,
        "per_row_cohort_counts": _per_row_cohort_counts(organisms, reference_rows),
        "cohort_metrics": cohort,
        "overlap_provenance": overlap,
        "r0_persistent_state": {
            "before": r0_before,
            "after": r0_after,
            "identical": r0_before == r0_after,
        },
        "real_authority_tripwires": dict(real_tripwires),
        "admission": admission,
    }
    if split == "validation":
        result["verdicts"] = _validation_verdicts(cohort, admission)
    else:
        if validation is None:
            raise RuntimeError("regression requires closed validation evidence")
        result["verdicts"] = _regression_verdicts(
            cohort, admission, validation["cohort_metrics"]
        )
    return result


def _real_reference_row(
    r0: NativeR0Organism,
    row: Mapping[str, Any],
    split: str,
) -> dict[str, Any]:
    board = chess.Board(str(row["fen"]))
    actuation = r0.emit_action(board)
    if actuation is None:
        raise RuntimeError("V3C real R0 emitted no policy response")
    signals = extract_active_competence_signals(r0, board, actuation)
    raw = ChildQuery(
        response=ChildResponse(
            child_id=r0.provenance.child_id,
            confirmed=False,
            expected_value=0.0,
            uncertainty=r0.provenance.uncertainty,
            grounded=r0.provenance.grounded,
            grounding_source=r0.provenance.grounding_source,
            policy_response=True,
            available=False,
        ),
        actuation=actuation,
        frame_id=f"v3c-real:{split}:{row['row_index']}",
        persistent_mutation_count=0,
        effect_attempts=(),
        active_competence_signal_ids=tuple(signals),
    )
    observed = observe_query_completion(r0, board.copy(stack=False), raw)
    action = _actuation_manifest(actuation)
    signal_ids = list(map(str, signals))
    return {
        **dict(row),
        "actuation": action,
        "active_competence_signal_ids": signal_ids,
        "action_signal_sha256": _action_signal_digest(action, signal_ids),
        "actual_completion": observed.completion_confirmed,
        "observed_terminal": observed.observed_terminal,
        "local_competence_failure": observed.local_competence_failure,
        "fabricated_terminal_reward": observed.fabricated_terminal_reward,
    }


def _evaluate_organism_worker(args: Mapping[str, Any]) -> dict[str, Any]:
    entry = args["entry"]
    envelope = _load_envelope(entry)
    r0 = NativeR0Organism.load(args["source_r0"])
    wrapper = NativeR0CompetenceOrganism(r0=r0, envelope=envelope)
    serialized = wrapper.dumps()
    restored = NativeR0CompetenceOrganism.loads(serialized)
    before = _wrapper_state_bundle(restored)
    audit = NativeCompetenceSessionAudit()
    rows: list[dict[str, Any]] = []
    injection_counts = {"boolean_availability": 0, "host_classification": 0}
    with _v3c_authority_tripwires(injection_counts) as native_tripwires:
        session = restored.dream_session(audit=audit)
        try:
            for row, reference in zip(
                args["split_rows"], args["reference_rows"], strict=True
            ):
                frame = FrameContext(
                    frame_id=(
                        f"v3c:{args['split']}:{entry['ordinal']}:"
                        f"{entry['arm']}:{row['row_index']}"
                    ),
                    kind=FrameKind.VIRTUAL,
                    values={"board": chess.Board(str(row["fen"]))},
                )
                query = session.request(frame)
                query_action = _actuation_manifest(query.actuation)
                query_signals = list(map(str, query.active_competence_signal_ids))
                mismatches = _parity_mismatches(
                    reference["actuation"],
                    reference["active_competence_signal_ids"],
                    query_action,
                    query_signals,
                )
                classification, provenance = classification_from_query(query)
                state = str(classification["state"])
                rows.append({
                    "row_index": int(row["row_index"]),
                    "fen": str(row["fen"]),
                    "actual_completion": bool(reference["actual_completion"]),
                    "state": state,
                    "probability": float(classification["probability"]),
                    "uncertainty": float(classification["uncertainty"]),
                    "available_cell_ids": list(classification["available_cell_ids"]),
                    "refuted_cell_ids": list(classification["refuted_cell_ids"]),
                    "formal_available": bool(classification["formal_available"]),
                    "formal_refuted": bool(classification["formal_refuted"]),
                    "policy_response": bool(classification["policy_response"]),
                    "consumed_available": bool(query.response.available),
                    "actuation": query_action,
                    "active_competence_signal_ids": query_signals,
                    "action_signal_sha256": _action_signal_digest(
                        query_action, query_signals
                    ),
                    "reference_action_signal_sha256": reference[
                        "action_signal_sha256"
                    ],
                    "parity_mismatch_rows": mismatches,
                    "persistent_mutation_count": int(
                        query.persistent_mutation_count
                    ),
                    "effect_attempts": [dict(item) for item in query.effect_attempts],
                    "availability_provenance": {
                        key: value for key, value in provenance.items()
                        if key != "classification"
                    },
                })
        finally:
            session.close()
    after = _wrapper_state_bundle(restored)
    metrics = organism_metrics(rows)
    return {
        "ordinal": int(entry["ordinal"]),
        "seed": int(entry["seed"]),
        "arm": str(entry["arm"]),
        "source_engaged": bool(entry["engaged"]),
        "source_mature_cell_count": int(entry["mature_cell_count"]),
        "source_artifact": dict(entry["artifact"]),
        "serialized_wrapper_sha256": hashlib.sha256(serialized).hexdigest(),
        "serialized_wrapper_bytes": len(serialized),
        "rows": rows,
        "metrics": metrics,
        "per_cell_heldout_hits": _per_cell_hits(rows),
        "state_digests": {
            "before": before,
            "after": after,
            "identical": before == after,
        },
        "session_audit": {
            "session_open_count": audit.session_open_count,
            "request_count": audit.request_count,
            "session_close_count": audit.session_close_count,
            "close_events": list(audit.close_events),
        },
        "authority_tripwires": {
            **dict(native_tripwires),
            **injection_counts,
        },
    }


def classification_from_query(
    query: ChildQuery,
) -> tuple[Mapping[str, Any], Mapping[str, Any]]:
    """Consume only classification provenance emitted by the wrapper session."""

    provenance = dict(query.availability_provenance or {})
    classification = provenance.get("classification")
    if not isinstance(classification, Mapping):
        raise RuntimeError("V3C wrapper emitted no classification provenance")
    state = str(classification["state"])
    if bool(query.response.available) != (
        state == AvailabilityState.AVAILABLE.value
    ):
        raise RuntimeError("V3C response and classification disagree")
    return dict(classification), provenance


def _load_envelope(entry: Mapping[str, Any]) -> GraphNativeCompetenceEnvelope:
    artifact = entry["artifact"]
    compressed = Path(artifact["path"]).read_bytes()
    if hashlib.sha256(compressed).hexdigest() != artifact["compressed_sha256"]:
        raise RuntimeError("V3C worker compressed envelope mismatch")
    raw = gzip.decompress(compressed)
    if hashlib.sha256(raw).hexdigest() != artifact["uncompressed_sha256"]:
        raise RuntimeError("V3C worker raw envelope mismatch")
    envelope = pickle.loads(raw)
    if not isinstance(envelope, GraphNativeCompetenceEnvelope):
        raise TypeError("V3C worker source is not an envelope")
    return envelope


@contextmanager
def _v3c_authority_tripwires(
    counts: dict[str, int],
) -> Iterator[Mapping[str, int]]:
    def boolean_injection(*_args: Any, **_kwargs: Any) -> Any:
        counts["boolean_availability"] += 1
        raise RuntimeError("V3C Boolean availability injection is forbidden")

    def host_classification(*_args: Any, **_kwargs: Any) -> Any:
        counts["host_classification"] += 1
        raise RuntimeError("V3C experiment-level classification is forbidden")

    with native_authority_tripwires() as native_counts, ExitStack() as stack:
        stack.enter_context(patch(
            "recon_lite_chess.autogrowth.native_child_availability."
            "response_with_availability",
            boolean_injection,
        ))
        stack.enter_context(patch(
            "recon_lite_chess.autogrowth.native_competence_envelope_experiment."
            "response_with_availability",
            boolean_injection,
        ))
        stack.enter_context(patch(
            "recon_lite_chess.autogrowth.native_competence_envelope_experiment."
            "_metrics_envelope",
            host_classification,
        ))
        yield native_counts


def _wrapper_state_bundle(
    wrapper: NativeR0CompetenceOrganism,
) -> Mapping[str, Any]:
    envelope_pickle = pickle.dumps(
        wrapper.envelope, protocol=pickle.HIGHEST_PROTOCOL
    )
    return {
        "r0": dict(wrapper.r0.persistent_state_audit()),
        "envelope": {
            "pickle_sha256": hashlib.sha256(envelope_pickle).hexdigest(),
            "manifest_sha256": _hash_json(wrapper.envelope.to_manifest()),
            "evidence_count": len(wrapper.envelope.evidence),
            "cell_count": len(wrapper.envelope.cells),
            "mature_cell_count": sum(
                cell.is_mature for cell in wrapper.envelope.cells.values()
            ),
        },
        "combined_wrapper": dict(wrapper.persistent_state_audit()),
    }


def _actuation_manifest(
    actuation: GraphActuation | None,
) -> Mapping[str, Any] | None:
    if actuation is None:
        return None
    result = asdict(actuation)
    result["activation_ieee754"] = struct.pack(">d", actuation.activation).hex()
    return result


def _parity_mismatches(
    reference_action: Mapping[str, Any],
    reference_signals: Sequence[str],
    query_action: Mapping[str, Any] | None,
    query_signals: Sequence[str],
) -> list[dict[str, Any]]:
    mismatches: list[dict[str, Any]] = []
    if query_action is None:
        return [{
            "field": "GraphActuation.presence",
            "real_value": True,
            "virtual_value": False,
        }]
    for field in ACTUATION_FIELDS:
        real_value = reference_action[field]
        virtual_value = query_action[field]
        equal = (
            reference_action["activation_ieee754"]
            == query_action["activation_ieee754"]
            if field == "activation"
            else real_value == virtual_value
        )
        if not equal:
            row = {
                "field": f"GraphActuation.{field}",
                "real_value": real_value,
                "virtual_value": virtual_value,
            }
            if field == "activation":
                row.update({
                    "real_ieee754": reference_action["activation_ieee754"],
                    "virtual_ieee754": query_action["activation_ieee754"],
                })
            mismatches.append(row)
    if list(reference_signals) != list(query_signals):
        mismatches.append({
            "field": "active_competence_signal_ids",
            "real_value": list(reference_signals),
            "virtual_value": list(query_signals),
        })
    return mismatches


def _action_signal_digest(
    action: Mapping[str, Any] | None,
    signals: Sequence[str],
) -> str:
    return _hash_json({"actuation": action, "active_signal_ids": list(signals)})


def organism_metrics(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    counts = Counter()
    for row in rows:
        outcome = bool(row["actual_completion"])
        state = str(row["state"])
        if state == AvailabilityState.AVAILABLE.value:
            counts["tp" if outcome else "fp"] += 1
        elif state == AvailabilityState.UNKNOWN.value:
            counts["positive_abstention" if outcome else "safe_abstention"] += 1
        elif state == AvailabilityState.REFUTED.value:
            counts["refuted_positive" if outcome else "refuted_negative"] += 1
        else:
            raise ValueError(f"unknown envelope state: {state}")
    tp = counts["tp"]
    fp = counts["fp"]
    available = tp + fp
    return {
        "tp": tp,
        "fp": fp,
        "positive_abstention": counts["positive_abstention"],
        "safe_abstention": counts["safe_abstention"],
        "refuted_positive": counts["refuted_positive"],
        "refuted_negative": counts["refuted_negative"],
        "positive_coverage": tp / 16,
        "selective_precision": None if available == 0 else tp / available,
        "strict_pass": tp >= 14 and fp == 0,
        "safe_narrow_pass": tp >= 1 and fp == 0,
    }


def _per_cell_hits(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    hits: dict[tuple[str, str], Counter[str]] = defaultdict(Counter)
    for row in rows:
        outcome = "completion" if row["actual_completion"] else "noncompletion"
        for cell_id in row["available_cell_ids"]:
            hits[("available", str(cell_id))][outcome] += 1
        for cell_id in row["refuted_cell_ids"]:
            hits[("refuted", str(cell_id))][outcome] += 1
    return [
        {
            "role": role,
            "cell_id": cell_id,
            "completion_hits": counts["completion"],
            "noncompletion_hits": counts["noncompletion"],
            "total_hits": sum(counts.values()),
        }
        for (role, cell_id), counts in sorted(hits.items())
    ]


def _split_admission(
    *,
    split_rows: Sequence[Mapping[str, Any]],
    reference_rows: Sequence[Mapping[str, Any]],
    organisms: Sequence[Mapping[str, Any]],
    r0_identity: bool,
    real_tripwires: Mapping[str, int],
) -> dict[str, Any]:
    positives = [
        row for row in reference_rows if row["segment"] == "positive"
    ]
    negatives = [row for row in reference_rows if row["segment"] == "decoy"]
    mismatch_rows = [
        {
            "ordinal": organism["ordinal"],
            "seed": organism["seed"],
            "arm": organism["arm"],
            "row_index": row["row_index"],
            **mismatch,
        }
        for organism in organisms
        for row in organism["rows"]
        for mismatch in row["parity_mismatch_rows"]
    ]
    gates = {
        "row_count_32": len(split_rows) == len(reference_rows) == 32,
        "graph_owned_policy_responses_32": all(
            row["actuation"] is not None
            and row["actuation"]["graph_owned"]
            and not row["actuation"]["host_fallback"]
            for row in reference_rows
        ),
        "positive_actual_completions_16": (
            len(positives) == 16 and all(row["actual_completion"] for row in positives)
        ),
        "decoy_actual_noncompletions_16": (
            len(negatives) == 16
            and all(not row["actual_completion"] for row in negatives)
        ),
        "zero_fabricated_terminal_reward": all(
            not row["fabricated_terminal_reward"] for row in reference_rows
        ),
        "all_64_organisms_present": len(organisms) == 64,
        "zero_real_virtual_mismatch": not mismatch_rows,
        "exact_r0_persistent_identity": bool(r0_identity),
        "exact_wrapper_state_identity": all(
            organism["state_digests"]["before"]
            == organism["state_digests"]["after"]
            and organism["state_digests"]["identical"]
            for organism in organisms
        ),
        "zero_query_mutation": all(
            row["persistent_mutation_count"] == 0
            for organism in organisms for row in organism["rows"]
        ),
        "zero_effect_attempts": all(
            not row["effect_attempts"]
            for organism in organisms for row in organism["rows"]
        ),
        "complete_session_authority": all(
            organism["session_audit"]["session_open_count"] == 1
            and organism["session_audit"]["request_count"] == 32
            and organism["session_audit"]["session_close_count"] == 1
            for organism in organisms
        ),
        "zero_authority_tripwires": (
            all(value == 0 for value in real_tripwires.values())
            and all(
                value == 0
                for organism in organisms
                for value in organism["authority_tripwires"].values()
            )
        ),
    }
    return {
        "counts_before_gates": {
            "rows": len(reference_rows),
            "positive_completions": sum(
                row["actual_completion"] for row in positives
            ),
            "decoy_noncompletions": sum(
                not row["actual_completion"] for row in negatives
            ),
            "organisms": len(organisms),
            "virtual_queries": sum(
                len(organism["rows"]) for organism in organisms
            ),
            "parity_mismatches": len(mismatch_rows),
        },
        "mismatch_rows": mismatch_rows,
        "gates": gates,
        "passed": all(gates.values()),
    }


def _cohort_metrics(organisms: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    by_arm = {
        arm: [row for row in organisms if row["arm"] == arm]
        for arm in ARM_NAMES
    }
    result: dict[str, Any] = {"arms": {}}
    for arm, rows in by_arm.items():
        result["arms"][arm] = {
            "organism_count": len(rows),
            "strict_passes": sum(row["metrics"]["strict_pass"] for row in rows),
            "safe_narrow_passes": sum(
                row["metrics"]["safe_narrow_pass"] for row in rows
            ),
            "organisms_with_any_tp": sum(row["metrics"]["tp"] > 0 for row in rows),
            "total_tp": sum(row["metrics"]["tp"] for row in rows),
            "total_fp": sum(row["metrics"]["fp"] for row in rows),
            "confusion_matrices": [
                {
                    "ordinal": row["ordinal"],
                    "seed": row["seed"],
                    **row["metrics"],
                }
                for row in rows
            ],
        }
    for pass_name in ("strict_pass", "safe_narrow_pass"):
        paired = _paired_pass_counts(organisms, pass_name)
        result[f"paired_{pass_name}"] = paired
    return result


def _paired_pass_counts(
    organisms: Sequence[Mapping[str, Any]],
    pass_name: str,
) -> Mapping[str, int]:
    lookup = {
        (row["ordinal"], row["arm"]): bool(row["metrics"][pass_name])
        for row in organisms
    }
    counts = Counter()
    for ordinal in range(32):
        connected = lookup[(ordinal, "connected")]
        shuffled = lookup[(ordinal, "outcome_shuffled")]
        if connected and not shuffled:
            counts["connected_only"] += 1
        elif shuffled and not connected:
            counts["shuffled_only"] += 1
        elif connected:
            counts["both"] += 1
        else:
            counts["neither"] += 1
    return {
        "connected_only": counts["connected_only"],
        "shuffled_only": counts["shuffled_only"],
        "both": counts["both"],
        "neither": counts["neither"],
        "connected_only_minus_shuffled_only": (
            counts["connected_only"] - counts["shuffled_only"]
        ),
    }


def _validation_verdicts(
    cohort: Mapping[str, Any], admission: Mapping[str, Any]
) -> Mapping[str, Any]:
    connected = cohort["arms"]["connected"]
    shuffled = cohort["arms"]["outcome_shuffled"]
    strict_pair = cohort["paired_strict_pass"]
    safe_pair = cohort["paired_safe_narrow_pass"]
    strict_gates = {
        "zero_connected_fp_across_512_negatives": connected["total_fp"] == 0,
        "connected_strict_passes_at_least_28_of_32": (
            connected["strict_passes"] >= 28
        ),
        "shuffled_strict_passes_at_most_4_of_32": shuffled["strict_passes"] <= 4,
        "paired_strict_margin_at_least_24": (
            strict_pair["connected_only_minus_shuffled_only"] >= 24
        ),
        "integrity_and_authority": bool(admission["passed"]),
    }
    safe_gates = {
        "zero_connected_fp_across_512_negatives": connected["total_fp"] == 0,
        "connected_any_tp_at_least_24_of_32": (
            connected["organisms_with_any_tp"] >= 24
        ),
        "paired_safe_margin_at_least_20": (
            safe_pair["connected_only_minus_shuffled_only"] >= 20
        ),
        "integrity_and_authority": bool(admission["passed"]),
    }
    return {
        "strict_generalization": {
            "gates": strict_gates,
            "passed": all(strict_gates.values()),
        },
        "safe_narrow_transfer": {
            "gates": safe_gates,
            "passed": all(safe_gates.values()),
        },
    }


def _regression_verdicts(
    cohort: Mapping[str, Any],
    admission: Mapping[str, Any],
    validation_cohort: Mapping[str, Any],
) -> Mapping[str, Any]:
    connected = cohort["arms"]["connected"]
    shuffled = cohort["arms"]["outcome_shuffled"]
    strict_pair = cohort["paired_strict_pass"]
    safe_pair = cohort["paired_safe_narrow_pass"]
    validation_connected = {
        row["ordinal"]: row
        for row in validation_cohort["arms"]["connected"]["confusion_matrices"]
    }
    regression_connected = {
        row["ordinal"]: row
        for row in connected["confusion_matrices"]
    }
    combined_strict = sum(
        validation_connected[ordinal]["tp"]
        + regression_connected[ordinal]["tp"] >= 29
        and validation_connected[ordinal]["fp"]
        + regression_connected[ordinal]["fp"] == 0
        for ordinal in range(32)
    )
    nonzero_both = sum(
        validation_connected[ordinal]["tp"] > 0
        and regression_connected[ordinal]["tp"] > 0
        for ordinal in range(32)
    )
    strict_gates = {
        "zero_connected_regression_fp": connected["total_fp"] == 0,
        "connected_regression_strict_passes_at_least_28_of_32": (
            connected["strict_passes"] >= 28
        ),
        "combined_tp_at_least_29_zero_fp_at_least_28_of_32": combined_strict >= 28,
        "shuffled_regression_strict_passes_at_most_4_of_32": (
            shuffled["strict_passes"] <= 4
        ),
        "paired_regression_strict_margin_at_least_24": (
            strict_pair["connected_only_minus_shuffled_only"] >= 24
        ),
        "integrity_and_authority": bool(admission["passed"]),
    }
    safe_gates = {
        "zero_connected_regression_fp": connected["total_fp"] == 0,
        "connected_regression_any_tp_at_least_24_of_32": (
            connected["organisms_with_any_tp"] >= 24
        ),
        "connected_nonzero_tp_on_both_splits_at_least_24_of_32": nonzero_both >= 24,
        "shuffled_regression_safe_passes_at_most_4_of_32": (
            shuffled["safe_narrow_passes"] <= 4
        ),
        "paired_regression_safe_margin_at_least_20": (
            safe_pair["connected_only_minus_shuffled_only"] >= 20
        ),
        "integrity_and_authority": bool(admission["passed"]),
    }
    return {
        "combined_connected_strict_count": combined_strict,
        "connected_nonzero_tp_both_splits_count": nonzero_both,
        "strict_replication": {
            "gates": strict_gates,
            "passed": all(strict_gates.values()),
        },
        "safe_narrow_replication": {
            "gates": safe_gates,
            "passed": all(safe_gates.values()),
        },
    }


def _per_row_cohort_counts(
    organisms: Sequence[Mapping[str, Any]],
    reference_rows: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    result = []
    for reference in reference_rows:
        index = reference["row_index"]
        row = {
            "row_index": index,
            "fen": reference["fen"],
            "actual_completion": reference["actual_completion"],
            "action_signal_sha256": reference["action_signal_sha256"],
            "arms": {},
        }
        for arm in ARM_NAMES:
            states = Counter(
                organism["rows"][index]["state"]
                for organism in organisms if organism["arm"] == arm
            )
            row["arms"][arm] = {
                "available": states[AvailabilityState.AVAILABLE.value],
                "unknown": states[AvailabilityState.UNKNOWN.value],
                "refuted": states[AvailabilityState.REFUTED.value],
            }
        result.append(row)
    return result


def _overlap_report(
    training: Mapping[str, Sequence[str]],
    split_rows: Sequence[Mapping[str, Any]],
    *,
    validation_rows: Sequence[Mapping[str, Any]] | None,
    split: str,
) -> Mapping[str, Any]:
    current_positive = tuple(
        row["fen"] for row in split_rows if row["segment"] == "positive"
    )
    current_decoy = tuple(
        row["fen"] for row in split_rows if row["segment"] == "decoy"
    )
    positive_splits: dict[str, Sequence[str]] = {
        "training": tuple(training["positive"]),
        split: current_positive,
    }
    decoy_splits: dict[str, Sequence[str]] = {
        "training": tuple(training["decoy"]),
        split: current_decoy,
    }
    if validation_rows is not None and split == "regression":
        positive_splits["validation"] = tuple(
            row["fen"] for row in validation_rows if row["segment"] == "positive"
        )
        decoy_splits["validation"] = tuple(
            row["fen"] for row in validation_rows if row["segment"] == "decoy"
        )
    return {
        "positive": _pairwise_overlap(positive_splits),
        "decoy": _pairwise_overlap(decoy_splits),
        "rows_removed_or_regenerated": 0,
        "gating_use": "descriptive_provenance_only",
    }


def _pairwise_overlap(groups: Mapping[str, Sequence[str]]) -> Mapping[str, Any]:
    names = sorted(groups)
    pairs = []
    for left_index, left in enumerate(names):
        left_fens = set(groups[left])
        left_orbits = {_r1_orbit_key(fen) for fen in groups[left]}
        for right in names[left_index + 1:]:
            right_fens = set(groups[right])
            right_orbits = {_r1_orbit_key(fen) for fen in groups[right]}
            pairs.append({
                "left": left,
                "right": right,
                "exact_overlap_count": len(left_fens & right_fens),
                "d4_orbit_overlap_count": len(left_orbits & right_orbits),
            })
    return {
        "groups": {
            name: {
                "count": len(values),
                "exact_unique_count": len(set(values)),
                "d4_unique_count": len({_r1_orbit_key(fen) for fen in values}),
            }
            for name, values in sorted(groups.items())
        },
        "pairs": pairs,
        "all_pairwise_exact_disjoint": all(
            row["exact_overlap_count"] == 0 for row in pairs
        ),
        "all_pairwise_d4_disjoint": all(
            row["d4_orbit_overlap_count"] == 0 for row in pairs
        ),
    }


def _validation_interpretation(validation: Mapping[str, Any]) -> str:
    connected = validation["cohort_metrics"]["arms"]["connected"]
    if connected["total_fp"] > 0:
        return "training_pure_conjunctions_overgeneralize"
    if connected["organisms_with_any_tp"] < 24:
        return "cells_are_mostly_training_local"
    return "validation_transfer_gate_not_met"


def _validation_boundary(validation: Mapping[str, Any]) -> str:
    connected = validation["cohort_metrics"]["arms"]["connected"]
    if connected["total_fp"] > 0:
        return "selectivity_or_representation"
    if connected["organisms_with_any_tp"] < 24:
        return "representation_equivalence_or_terminal_provenance"
    return "coverage_or_control_discrimination"


def _any_connected_fp(
    validation: Mapping[str, Any], regression: Mapping[str, Any]
) -> bool:
    return any(
        split["cohort_metrics"]["arms"]["connected"]["total_fp"] > 0
        for split in (validation, regression)
    )


def _file_sha256(path: str | Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _hash_json(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


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
