"""Preregistered trace-native historical regression; inference only.

Importing this module does not construct any regression row.  The sealed pool
loader is called only by run_regression(), after the pre-data freeze is pushed.
"""
from __future__ import annotations

from collections import Counter
from concurrent.futures import ProcessPoolExecutor
from dataclasses import asdict, dataclass
import gzip
import hashlib
from math import comb
import json
from pathlib import Path
import pickle
from time import perf_counter
from typing import Any, Mapping, Sequence

import chess

from recon_lite import FrameContext, FrameKind

from .native_authority_handover import NativeR0Organism, native_authority_tripwires
from .native_competence_envelope import AvailabilityState, NativeCompetenceSessionAudit
from .native_competence_envelope_v3c_heldout import (
    ROW_ORDER_COMMITMENTS,
    SOURCE_CURRICULUM,
    _load_and_verify_pool_source,
    _split_rows,
)
from .native_terminal_trace_authority_closure import RESULT_PATH as STAGE1_RESULT
from .native_trace_competence_authority import TraceNativeCompetenceOrganism


SOURCE_STAGE1_COMMIT = "50d57fa41088d7dd6c0e0c82d8b6b3c1dd21354d"
SOURCE_STAGE1_SHA256 = "2cd0010559599b10b7ff3cd5246cae96a8587b274513417201d882d640bf8bef"
SOURCE_R0 = "snapshots/autogrowth/native_authority/r0_organism.pkl"
PREREGISTRATION = (
    "docs/autogrowth/"
    "NATIVE_TERMINAL_TRACE_HISTORICAL_REGRESSION_PREREGISTRATION_20260720.md"
)
FREEZE_MANIFEST = (
    "reports/autogrowth/native_authority/"
    "native_terminal_trace_historical_regression_freeze.json"
)
RUNNER_MODULE = (
    "src/recon_lite_chess/autogrowth/"
    "native_terminal_trace_historical_regression.py"
)
OUTPUT = (
    "reports/autogrowth/native_authority/"
    "native_terminal_trace_historical_regression.json"
)
ARM_NAMES = (
    "local_contrast_specialization",
    "demotion_only",
    "counterexample_blind_specialization",
)
ACTUATION_FIELDS = tuple(asdict.__annotations__) if False else (
    "actuator_identity", "move_uci", "option_identity", "activation",
    "candidate_count", "formal_ticks", "graph_owned", "host_fallback",
)


@dataclass(frozen=True)
class RegressionConfig:
    output: str = OUTPUT
    max_workers: int = 4


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


def _hash_file(path: str | Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _hash_json(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"),
                   allow_nan=False).encode()
    ).hexdigest()


def build_predata_manifest() -> dict[str, Any]:
    """Freeze sources and organisms without importing or constructing pool rows."""

    if _hash_file(STAGE1_RESULT) != SOURCE_STAGE1_SHA256:
        raise RuntimeError("Stage 1 result changed")
    source = _load_json(STAGE1_RESULT)
    if source.get("passed") is not True or len(source["organisms"]) != 32:
        raise RuntimeError("Stage 1 source did not pass")
    artifacts = []
    for organism in source["organisms"]:
        for arm in ARM_NAMES:
            item = organism["arms"][arm]["artifact"]
            if _hash_file(item["path"]) != item["compressed_sha256"]:
                raise RuntimeError("Stage 1 organism artifact changed")
            artifacts.append({
                "ordinal": organism["ordinal"],
                "genome_seed": organism["genome_seed"],
                "arm": arm,
                **item,
            })
    if len(artifacts) != 96:
        raise RuntimeError("freeze requires all 96 organisms")
    manifest = {
        "schema_version": "native_terminal_trace_regression_freeze.v1",
        "regression_opened": False,
        "source_stage1_commit": SOURCE_STAGE1_COMMIT,
        "source_stage1": {
            "path": STAGE1_RESULT,
            "sha256": SOURCE_STAGE1_SHA256,
        },
        "organisms": artifacts,
        "organism_index_sha256": _hash_json(artifacts),
        "source_hashes": {
            RUNNER_MODULE: _hash_file(RUNNER_MODULE),
            PREREGISTRATION: _hash_file(PREREGISTRATION),
            "src/recon_lite_chess/autogrowth/native_authority_handover.py":
                _hash_file("src/recon_lite_chess/autogrowth/native_authority_handover.py"),
            "src/recon_lite_chess/autogrowth/native_competence_envelope.py":
                _hash_file("src/recon_lite_chess/autogrowth/native_competence_envelope.py"),
            "src/recon_lite_chess/autogrowth/native_trace_competence_authority.py":
                _hash_file("src/recon_lite_chess/autogrowth/native_trace_competence_authority.py"),
            SOURCE_R0: _hash_file(SOURCE_R0),
            SOURCE_CURRICULUM: _hash_file(SOURCE_CURRICULUM),
        },
        "regression_commitments": {
            "r0_regression": "964c8d543e03cc6d756eb0f52218133e9af95fdb6c97dc9c0aff8b8e58858f69",
            "regression_decoys": "acdafa01d92b7ee77053de438168c828bbf94d5006cc6dfe5d0cf42299ee64e8",
            "row_order": ROW_ORDER_COMMITMENTS["regression"],
            "count": 32,
        },
        "metrics": {
            "deployable_tp": "TP when organism FP == 0, otherwise 0",
            "primary_family": [
                "local_vs_demotion_deployable_tp",
                "local_vs_counterexample_blind_deployable_tp",
            ],
            "test": "one-sided exact paired sign test; Holm alpha 0.05",
        },
        "stop_rule": "one inference-only opening; no tuning, retraining, correction, new pool, selected organism, R1, retired-65, or fresh data",
    }
    return _write_json(FREEZE_MANIFEST, manifest)


def _load_artifact(item: Mapping[str, Any]) -> TraceNativeCompetenceOrganism:
    compressed = Path(item["path"]).read_bytes()
    if hashlib.sha256(compressed).hexdigest() != item["compressed_sha256"]:
        raise RuntimeError("compressed organism mismatch")
    raw = gzip.decompress(compressed)
    if hashlib.sha256(raw).hexdigest() != item["uncompressed_sha256"]:
        raise RuntimeError("raw organism mismatch")
    wrapper = TraceNativeCompetenceOrganism.loads(raw)
    if wrapper.continuation_digest_v3() != item["continuation_v3_sha256"]:
        raise RuntimeError("organism V3 mismatch")
    return wrapper


def _reference_rows(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    r0 = NativeR0Organism.load(SOURCE_R0)
    before = r0.persistent_state_audit()
    result = []
    with native_authority_tripwires() as tripwires:
        for row in rows:
            board = chess.Board(str(row["fen"]))
            actuation, trace = r0.emit_action_with_trace(FrameContext(
                f"trace-regression-real:{row['row_index']}",
                FrameKind.REAL, values={"board": board},
            ))
            if actuation is None or trace is None:
                raise RuntimeError("R0 emitted no graph action/trace")
            successor = board.copy(stack=False)
            successor.push(chess.Move.from_uci(actuation.move_uci))
            result.append({
                **dict(row),
                "actuation": asdict(actuation),
                "ordered_signal_identities": list(trace.ordered_signal_identities),
                "terminal_signals": [asdict(item) for item in trace.terminal_signals],
                "trace_digest": trace.digest(),
                "actual_completion": successor.is_checkmate(),
            })
    if r0.persistent_state_audit() != before:
        raise RuntimeError("real reference mutated R0")
    if any(tripwires.values()):
        raise RuntimeError("real reference used forbidden host authority")
    return result


def _evaluate_worker(arg: Mapping[str, Any]) -> dict[str, Any]:
    item = arg["artifact"]
    wrapper = _load_artifact(item)
    restored = TraceNativeCompetenceOrganism.loads(wrapper.dumps())
    before = restored.continuation_digest_v3()
    audit = NativeCompetenceSessionAudit()
    rows = []
    session = restored.dream_session(audit=audit)
    try:
        for reference in arg["reference_rows"]:
            frame = FrameContext(
                f"trace-regression-virtual:{item['ordinal']}:{item['arm']}:{reference['row_index']}",
                FrameKind.VIRTUAL,
                values={"board": chess.Board(str(reference["fen"]))},
            )
            query = session.request(frame)
            trace = query.graph_signal_trace
            classification = dict((query.availability_provenance or {})["classification"])
            mismatches = []
            actual = None if query.actuation is None else asdict(query.actuation)
            if actual != reference["actuation"]:
                mismatches.append("GraphActuation")
            if trace is None:
                mismatches.append("GraphSignalTrace.presence")
                signal_ids = []
                terminal_signals = []
                trace_digest = None
            else:
                signal_ids = list(trace.ordered_signal_identities)
                terminal_signals = [asdict(value) for value in trace.terminal_signals]
                trace_digest = trace.digest()
                if signal_ids != reference["ordered_signal_identities"]:
                    mismatches.append("ordered_signal_identities")
                if terminal_signals != reference["terminal_signals"]:
                    mismatches.append("terminal_signals")
            matching = []
            for cell_id in (
                list(classification["available_cell_ids"])
                + list(classification["refuted_cell_ids"])
            ):
                cell = restored.envelope.cells[str(cell_id)]
                matching.append({
                    "cell_id": cell.cell_id,
                    "state": cell.state.name,
                    "polarity": None if cell.polarity is None else cell.polarity.value,
                    "specialization_depth": cell.specialization_depth,
                    "lineage_parent_id": cell.lineage_parent_id,
                    "members": list(cell.members),
                })
            rows.append({
                "row_index": reference["row_index"],
                "fen": reference["fen"],
                "actual_completion": reference["actual_completion"],
                "classification": classification,
                "matching_cells": matching,
                "actuation": actual,
                "ordered_signal_identities": signal_ids,
                "terminal_signals": terminal_signals,
                "trace_digest": trace_digest,
                "reference_trace_digest": reference["trace_digest"],
                "parity_mismatches": mismatches,
                "persistent_mutation_count": query.persistent_mutation_count,
                "effect_attempts": list(query.effect_attempts),
            })
    finally:
        session.close()
    after = restored.continuation_digest_v3()
    metrics = organism_metrics(rows)
    return {
        "ordinal": item["ordinal"],
        "genome_seed": item["genome_seed"],
        "arm": item["arm"],
        "source_artifact": item,
        "rows": rows,
        "metrics": metrics,
        "state_before": before,
        "state_after": after,
        "state_identical": before == after,
        "session_audit": asdict(audit),
    }


def organism_metrics(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    counts = Counter()
    for row in rows:
        state = row["classification"]["state"]
        outcome = bool(row["actual_completion"])
        if state == AvailabilityState.AVAILABLE.value:
            counts["tp" if outcome else "fp"] += 1
        elif state == AvailabilityState.UNKNOWN.value:
            counts["positive_abstention" if outcome else "safe_abstention"] += 1
        else:
            counts["refuted_positive" if outcome else "refuted_negative"] += 1
    tp, fp = counts["tp"], counts["fp"]
    return {
        **{key: counts[key] for key in (
            "tp", "fp", "positive_abstention", "safe_abstention",
            "refuted_positive", "refuted_negative",
        )},
        "safe_narrow": tp > 0 and fp == 0,
        "strict": tp >= 14 and fp == 0,
        "deployable_tp": tp if fp == 0 else 0,
    }


def exact_sign_test(left: Sequence[int], right: Sequence[int]) -> dict[str, Any]:
    differences = [a - b for a, b in zip(left, right, strict=True)]
    wins = sum(value > 0 for value in differences)
    losses = sum(value < 0 for value in differences)
    ties = len(differences) - wins - losses
    n = wins + losses
    p = 1.0 if n == 0 else sum(comb(n, k) for k in range(wins, n + 1)) / (2 ** n)
    return {"wins": wins, "losses": losses, "ties": ties, "p_value": p}


def holm_two(first: Mapping[str, Any], second: Mapping[str, Any]) -> list[dict[str, Any]]:
    rows = [dict(first), dict(second)]
    order = sorted(range(2), key=lambda index: rows[index]["p_value"])
    running = 0.0
    for rank, index in enumerate(order):
        adjusted = min(1.0, (2 - rank) * rows[index]["p_value"])
        running = max(running, adjusted)
        rows[index]["holm_adjusted_p"] = running
        rows[index]["holm_pass_0_05"] = running <= 0.05
    return rows


def _cohort(organisms: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    result = {}
    for arm in ARM_NAMES:
        rows = sorted((x for x in organisms if x["arm"] == arm),
                      key=lambda x: x["ordinal"])
        result[arm] = {
            "total_tp": sum(x["metrics"]["tp"] for x in rows),
            "total_fp": sum(x["metrics"]["fp"] for x in rows),
            "safe_narrow": sum(x["metrics"]["safe_narrow"] for x in rows),
            "strict": sum(x["metrics"]["strict"] for x in rows),
            "deployable_tp": sum(x["metrics"]["deployable_tp"] for x in rows),
            "per_organism_deployable_tp": [
                x["metrics"]["deployable_tp"] for x in rows
            ],
        }
    return result


def _depth_one_advantage(organisms: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    lookup = {(row["ordinal"], row["arm"]): row for row in organisms}
    found = []
    for ordinal in range(32):
        local = lookup[(ordinal, ARM_NAMES[0])]
        control = lookup[(ordinal, ARM_NAMES[1])]
        for left, right in zip(local["rows"], control["rows"], strict=True):
            if (
                left["actual_completion"]
                and left["classification"]["state"] == AvailabilityState.AVAILABLE.value
                and right["classification"]["state"] != AvailabilityState.AVAILABLE.value
                and any(
                    cell["state"] == "MATURE"
                    and cell["specialization_depth"] == 1
                    and cell["polarity"] == AvailabilityState.AVAILABLE.value
                    for cell in left["matching_cells"]
                )
            ):
                found.append({"ordinal": ordinal, "row_index": left["row_index"]})
    return found


def run_regression(config: RegressionConfig | None = None) -> dict[str, Any]:
    cfg = config or RegressionConfig()
    started = perf_counter()
    if Path(cfg.output).exists():
        raise FileExistsError("canonical regression output already exists")
    freeze = _load_json(FREEZE_MANIFEST)
    for path, digest in freeze["source_hashes"].items():
        if _hash_file(path) != digest:
            raise RuntimeError(f"pre-data frozen source changed: {path}")
    source = _load_json(STAGE1_RESULT)
    if _hash_file(STAGE1_RESULT) != SOURCE_STAGE1_SHA256:
        raise RuntimeError("Stage 1 result changed after freeze")

    # First and only regression opening occurs here, after frozen-source checks.
    pools = _load_and_verify_pool_source(SOURCE_CURRICULUM)
    rows = _split_rows("regression", pools)
    references = _reference_rows(rows)
    args = [
        {"artifact": item, "reference_rows": references}
        for item in freeze["organisms"]
    ]
    with ProcessPoolExecutor(max_workers=cfg.max_workers) as executor:
        organisms = list(executor.map(_evaluate_worker, args))
    organisms.sort(key=lambda row: (row["ordinal"], ARM_NAMES.index(row["arm"])))
    cohort = _cohort(organisms)
    comparisons = holm_two(
        {"control": ARM_NAMES[1], **exact_sign_test(
            cohort[ARM_NAMES[0]]["per_organism_deployable_tp"],
            cohort[ARM_NAMES[1]]["per_organism_deployable_tp"],
        )},
        {"control": ARM_NAMES[2], **exact_sign_test(
            cohort[ARM_NAMES[0]]["per_organism_deployable_tp"],
            cohort[ARM_NAMES[2]]["per_organism_deployable_tp"],
        )},
    )
    stage1_by_ordinal = {
        row["ordinal"]: row for row in source["organisms"]
    }
    local = [row for row in organisms if row["arm"] == ARM_NAMES[0]]
    both_nonzero = sum(
        row["metrics"]["tp"] > 0
        and stage1_by_ordinal[row["ordinal"]]["arms"][ARM_NAMES[0]][
            "post_metrics"
        ]["tp"] > 0
        for row in local
    )
    depth_one = _depth_one_advantage(organisms)
    integrity = {
        "rows_32": len(rows) == len(references) == 32,
        "positive_completions_16": sum(r["actual_completion"] for r in references[:16]) == 16,
        "decoy_noncompletions_16": sum(not r["actual_completion"] for r in references[16:]) == 16,
        "organisms_96": len(organisms) == 96,
        "zero_parity_mismatch": all(
            not row["parity_mismatches"] for item in organisms for row in item["rows"]
        ),
        "zero_mutation": all(
            item["state_identical"]
            and all(row["persistent_mutation_count"] == 0 and not row["effect_attempts"]
                    for row in item["rows"])
            for item in organisms
        ),
        "complete_sessions": all(
            item["session_audit"]["session_open_count"] == 1
            and item["session_audit"]["request_count"] == 32
            and item["session_audit"]["session_close_count"] == 1
            for item in organisms
        ),
    }
    gates = {
        "zero_local_fp_512": cohort[ARM_NAMES[0]]["total_fp"] == 0,
        "local_safe_narrow_at_least_24": cohort[ARM_NAMES[0]]["safe_narrow"] >= 24,
        "local_nonzero_viewed_and_regression_at_least_24": both_nonzero >= 24,
        "local_deployable_exceeds_demotion": cohort[ARM_NAMES[0]]["deployable_tp"] > cohort[ARM_NAMES[1]]["deployable_tp"],
        "local_deployable_exceeds_blind": cohort[ARM_NAMES[0]]["deployable_tp"] > cohort[ARM_NAMES[2]]["deployable_tp"],
        "paired_holm_superiority_both": all(row["holm_pass_0_05"] for row in comparisons),
        "depth_one_child_advantage": bool(depth_one),
        "integrity": all(integrity.values()),
    }
    if not integrity["rows_32"] or not all(integrity.values()):
        interpretation = "instrument_abort"
    elif cohort[ARM_NAMES[0]]["total_fp"]:
        interpretation = "specialized_contexts_overgeneralize"
    elif all(gates.values()):
        interpretation = "trace_native_historical_generalization_of_safe_contradiction_triggered_specialization"
    elif gates["local_deployable_exceeds_demotion"] and not gates["local_deployable_exceeds_blind"]:
        interpretation = "specialization_transfers_but_local_contrast_advantage_does_not_replicate"
    elif not gates["local_deployable_exceeds_demotion"]:
        interpretation = "safety_transfers_but_recovered_coverage_does_not"
    elif not gates["depth_one_child_advantage"]:
        interpretation = "learned_refinement_itself_did_not_transfer"
    else:
        interpretation = "historical_regression_gates_not_met"
    result = {
        "schema_version": "native_terminal_trace_historical_regression.v1",
        "inference_only": True,
        "regression_opened_once": True,
        "fresh": False,
        "retired_65_accessed": False,
        "r1_accessed": False,
        "row_order_commitment": ROW_ORDER_COMMITMENTS["regression"],
        "reference_rows": references,
        "organisms": organisms,
        "cohort": cohort,
        "paired_comparisons": comparisons,
        "both_nonzero_count": both_nonzero,
        "depth_one_advantage_rows": depth_one,
        "integrity": integrity,
        "gates": gates,
        "passed": all(gates.values()),
        "interpretation": interpretation,
        "duration_seconds": perf_counter() - started,
        "stop_rule": "closed_no_tuning_or_follow_on",
    }
    return _write_json(cfg.output, result)


if __name__ == "__main__":
    run_regression()
