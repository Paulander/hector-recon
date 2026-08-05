"""One bounded 32-seed residual-consensus touched-data comparison."""
from __future__ import annotations

import argparse
import copy
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor
from dataclasses import asdict
import gzip
import hashlib
import json
from pathlib import Path
import subprocess
from time import perf_counter
import traceback
from typing import Any, Mapping, Sequence

import chess

from recon_lite import FrameContext, FrameKind

from .native_authority_lab import NativeAuthorityLabConfig, load_retired_r0_build
from .native_competence_envelope import AvailabilityState
from .native_prospective_evidence_authority_v2 import (
    NativeProspectiveAuthorityV2,
    V2Mode,
)
from .native_residual_consensus_candidate_allocation import (
    AllocationMode,
    ResidualConsensusCompetenceOrganism,
    ResidualConsensusGrowthGenome,
    ResidualConsensusMemory,
    bounded_derangement_statistic_probe,
    responsibility_derangement,
)
from .native_terminal_trace_historical_regression import (
    exact_sign_test,
    holm_two,
)
from .native_trace_competence_authority import TraceNativeCompetenceOrganism


REGRESSION = Path(
    "reports/autogrowth/native_authority/"
    "native_terminal_trace_historical_regression.json.gz"
)
REGRESSION_SHA = "eb60826db7269b1fb69cd2abe21d137bb1853503cd8177e69aeb36050a77ecf4"
STAGE0 = Path("/tmp/native_residual_consensus_stage0.json")
OUTPUT_GZ = Path(
    "reports/autogrowth/native_authority/"
    "native_residual_consensus_candidate_allocation_reclosure.json.gz"
)
OUTPUT_MD = Path(
    "reports/autogrowth/native_authority/"
    "native_residual_consensus_candidate_allocation_reclosure.md"
)
ARM_ORDER = (
    AllocationMode.TRUE_CONSENSUS,
    AllocationMode.RESPONSIBILITY_DERANGED,
    AllocationMode.HASH_WITHOUT_REPLACEMENT,
)
MATCHED_BUDGET_FIELDS = (
    "proposal_slots_consumed",
    "unique_candidate_tuples_examined",
    "candidate_score_evaluations",
    "duplicate_candidate_slots",
    "proposal_slots_by_tuple_width",
    "attempted_pattern_digest",
)
SOURCE_PATHS = (
    "src/recon_lite_chess/autogrowth/native_competence_envelope.py",
    "src/recon_lite_chess/autogrowth/native_trace_competence_authority.py",
    "src/recon_lite_chess/autogrowth/native_prospective_evidence_authority_v2.py",
    "src/recon_lite_chess/autogrowth/native_residual_consensus_candidate_allocation.py",
    "src/recon_lite_chess/autogrowth/native_residual_consensus_candidate_allocation_run.py",
)


def _json_bytes(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode()


def _sha_json(value: Any) -> str:
    return hashlib.sha256(_json_bytes(value)).hexdigest()


def _sha_file(path: str | Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _load_regression() -> dict[str, Any]:
    if _sha_file(REGRESSION) != REGRESSION_SHA:
        raise RuntimeError("frozen regression artifact changed")
    with gzip.open(REGRESSION, "rt", encoding="utf-8") as stream:
        result = json.load(stream)
    if len(result["reference_rows"]) != 32:
        raise RuntimeError("frozen prospective suffix is incomplete")
    return result


def _load_source(item: Mapping[str, Any]) -> TraceNativeCompetenceOrganism:
    compressed = Path(str(item["path"])).read_bytes()
    if hashlib.sha256(compressed).hexdigest() != item["compressed_sha256"]:
        raise RuntimeError("source compressed hash mismatch")
    raw = gzip.decompress(compressed)
    if hashlib.sha256(raw).hexdigest() != item["uncompressed_sha256"]:
        raise RuntimeError("source raw hash mismatch")
    source = TraceNativeCompetenceOrganism.loads(raw)
    if source.continuation_digest_v3() != item["continuation_v3_sha256"]:
        raise RuntimeError("source continuation mismatch")
    return source


def _memory(
    organism: TraceNativeCompetenceOrganism,
    discovery_receipts: Sequence[Any],
) -> ResidualConsensusMemory:
    memory = ResidualConsensusMemory()
    for receipt in discovery_receipts:
        trace = receipt.decision_trace
        classification = organism.envelope.classify(
            trace.ordered_signal_identities, policy_response=True
        )
        if classification.state is not AvailabilityState.UNKNOWN:
            raise RuntimeError("pre-nomination organism is not competence-empty")
        emission = organism.envelope.emit_growth_request(
            observed_completion=receipt.observed_terminal_result,
            classification=classification,
        )
        if not emission.emitted or emission.availability_error == 0.0:
            raise RuntimeError("discovery residual was not graph-emitted")
        memory.ingest(
            frame_kind=FrameKind.REAL,
            receipt=receipt,
            pre_outcome_state=classification.state,
            pre_outcome_probability=classification.probability,
            signed_availability_residual=emission.availability_error,
        )
    memory.freeze()
    return memory


def _frame_neutral_trace_manifest(trace: Any) -> dict[str, Any] | None:
    if trace is None:
        return None
    value = trace.canonical_manifest()
    value.pop("frame_id", None)
    value.pop("frame_kind", None)
    return value


def _trace_digest(trace: Any) -> str | None:
    value = _frame_neutral_trace_manifest(trace)
    return None if value is None else _sha_json(value)


def _trace_parity_failures(
    trace: Any, reference: Mapping[str, Any]
) -> tuple[str, ...]:
    failures = []
    if asdict(trace.actuation) != reference["actuation"]:
        failures.append("GraphActuation")
    if list(trace.ordered_signal_identities) != reference[
        "ordered_signal_identities"
    ]:
        failures.append("ordered_signal_identities")
    if [asdict(item) for item in trace.terminal_signals] != reference[
        "terminal_signals"
    ]:
        failures.append("typed_terminal_signals")
    if _trace_digest(trace) != reference["semantic_trace_digest"]:
        failures.append("frame_neutral_semantic_trace")
    return tuple(failures)


def _bind_semantic_reference_digests(
    references: Sequence[Mapping[str, Any]],
    source_item: Mapping[str, Any],
) -> tuple[dict[str, Any], ...]:
    """Bind stored raw hashes to exact traces, then derive neutral hashes."""

    source = _load_source(source_item)
    before = source.r0.persistent_state_audit()
    result = []
    for reference in references:
        board = chess.Board(str(reference["fen"]))
        _actuation, trace = source.r0.emit_action_with_trace(FrameContext(
            f"trace-regression-real:{reference['row_index']}",
            FrameKind.REAL,
            values={"board": board},
        ))
        if trace is None or trace.digest() != reference["trace_digest"]:
            raise RuntimeError("stored reference trace binding changed")
        bound = {
            **dict(reference),
            "semantic_trace_digest": _trace_digest(trace),
        }
        if _trace_parity_failures(trace, bound):
            raise RuntimeError("stored reference semantic fields changed")
        result.append(bound)
    if source.r0.persistent_state_audit() != before:
        raise RuntimeError("reference semantic binding mutated R0")
    return tuple(result)


def _typed_digest(trace: Any) -> str | None:
    if trace is None:
        return None
    return _sha_json([asdict(item) for item in trace.terminal_signals])


def _measure_rows(
    authority: NativeProspectiveAuthorityV2,
    rows: Sequence[tuple[str, str, bool]],
) -> list[dict[str, Any]]:
    before = authority.continuation_digest()
    result = []
    for index, (row_id, fen, outcome) in enumerate(rows):
        opened = authority.open_virtual(FrameContext(
            f"residual-consensus-eval:{index}", FrameKind.VIRTUAL,
            values={"board": chess.Board(fen)},
        ))
        query = opened["query"]
        graph = opened["graph_emissions"]
        result.append({
            "row_id": row_id,
            "observed_completion": bool(outcome),
            "state": opened["classification"].state.value,
            "available": query.response.available,
            "matching_cell_ids": list(graph["commitment"]),
            "available_cell_ids": list(graph["available"]),
            "refuted_cell_ids": list(graph["refuted"]),
            "action": None if query.actuation is None else query.actuation.move_uci,
            "trace_digest": _trace_digest(query.graph_signal_trace),
            "typed_trace_digest": _typed_digest(query.graph_signal_trace),
        })
    if authority.continuation_digest() != before:
        raise RuntimeError("VIRTUAL evaluation mutated authority")
    return result


def _metrics(rows: Sequence[Mapping[str, Any]], certified_pair: int) -> dict[str, Any]:
    tp = sum(row["observed_completion"] and row["available"] for row in rows)
    fp = sum(not row["observed_completion"] and row["available"] for row in rows)
    refuted_positive = sum(
        row["observed_completion"] and row["state"] == AvailabilityState.REFUTED.value
        for row in rows
    )
    abstentions = sum(row["state"] == AvailabilityState.UNKNOWN.value for row in rows)
    safe_narrow = fp == 0 and tp >= 29 and certified_pair > 0
    return {
        "tp": tp,
        "fp": fp,
        "refuted_positive": refuted_positive,
        "abstentions": abstentions,
        "safe_narrow": safe_narrow,
        "deployable_tp": tp if fp == 0 else 0,
    }


def _pair_or_triple(cell: Any) -> bool:
    return (
        len(cell.members) in {2, 3}
        and not any(member.startswith("context:") for member in cell.members)
    )


def _worker(arg: Mapping[str, Any]) -> dict[str, Any]:
    started = perf_counter()
    item = arg["source_item"]
    mode = AllocationMode(arg["mode"])
    references = arg["references"]
    evaluation_rows = tuple(tuple(row) for row in arg["evaluation_rows"])
    retention_fens = tuple(arg["retention_fens"])
    source = _load_source(item)
    source_state = source.r0.persistent_state_audit()
    receipts = tuple(sorted(source.receipts.values(), key=lambda row: row.event_ordinal))
    discovery = receipts[:64]
    if tuple(row.event_ordinal for row in discovery) != tuple(range(64)):
        raise RuntimeError("discovery prefix is not exact 0..63")

    organism = TraceNativeCompetenceOrganism.empty(
        source.r0,
        envelope_config=copy.deepcopy(source.envelope.config),
        learning_config=copy.deepcopy(source.learning_config),
    )
    organism.open_prospective_discovery_epoch()
    memory = _memory(organism, discovery)
    if memory.manifest()["config"] != arg["memory_config"]:
        raise RuntimeError("frozen residual-memory configuration mismatch")
    organism.envelope.consensus_memory = memory
    derangement, derangement_audit = responsibility_derangement(
        memory.ordered_events, seed=int(item["genome_seed"])
    )
    if (
        derangement_audit["mapping_digest"]
        != arg["expected_derangement_digest"]
    ):
        raise RuntimeError("frozen responsibility derangement changed")
    probe = bounded_derangement_statistic_probe(
        memory.ordered_events, derangement,
        seed=int(item["genome_seed"]),
    )
    if (
        derangement_audit["polarity_changes"]
        < memory.config.minimum_deranged_polarity_changes
        or not probe["changed"]
    ):
        raise RuntimeError("responsibility derangement is not engaged")
    allocator = ResidualConsensusGrowthGenome(
        seed=int(item["genome_seed"]),
        memory=memory,
        mode=mode,
        derangement=(
            derangement
            if mode is AllocationMode.RESPONSIBILITY_DERANGED else None
        ),
    )
    wrapper = ResidualConsensusCompetenceOrganism(organism, allocator)
    wrapper.grow_from_grounded_receipts(discovery)
    allocation = allocator.manifest()
    growth = organism.envelope.audit
    nominated_direct = [
        cell.cell_id for cell in organism.envelope.cells.values()
        if _pair_or_triple(cell)
    ]

    authority = NativeProspectiveAuthorityV2.from_organism(
        organism, mode=V2Mode.PROSPECTIVE
    )
    authority.close_nomination()
    activation_opportunities = {cell_id: 0 for cell_id in authority.states}
    prequential = []
    maturity = revocation = 0
    for index, reference in enumerate(references):
        board = chess.Board(str(reference["fen"]))
        pending, trace = authority.open_real_event(FrameContext(
            f"residual-consensus-prospective:{index}", FrameKind.REAL,
            values={"board": board},
        ))
        parity_failures = _trace_parity_failures(trace, reference)
        if parity_failures:
            raise RuntimeError(
                "frozen R0 action/trace parity failure: "
                + ",".join(parity_failures)
            )
        successor = board.copy(stack=False)
        successor.push(chess.Move.from_uci(trace.actuation.move_uci))
        if successor.is_checkmate() != bool(reference["actual_completion"]):
            raise RuntimeError("viewed prospective outcome parity failure")
        for cell_id in pending.matching_cell_ids:
            activation_opportunities[cell_id] += 1
        prequential.append({
            "row_index": index,
            "state": pending.pre_outcome_classification.state.value,
            "matching_cell_ids": list(pending.matching_cell_ids),
        })
        receipt = authority.mint_environment_receipt(
            pending_token=pending.pending_token,
            trace=trace,
            predecessor=board,
            successor=successor,
        )
        emission = authority.consume(receipt)
        maturity += len(emission.graph_maturity_ids)
        revocation += len(emission.graph_revocation_ids)

    certified_direct = [
        cell_id for cell_id, state in authority.states.items()
        if state.prospectively_certified
        and len(state.hypothesis.members) in {2, 3}
        and not any(
            member.startswith("context:")
            for member in state.hypothesis.members
        )
    ]
    later_eligible = [
        cell_id for cell_id in nominated_direct
        if activation_opportunities.get(cell_id, 0) >= 4
    ]
    live_rows = _measure_rows(authority, evaluation_rows)
    payload = authority.dumps()
    restored = NativeProspectiveAuthorityV2.loads(payload)
    restored_rows = _measure_rows(restored, evaluation_rows)
    if live_rows != restored_rows:
        raise RuntimeError("serialization changed VIRTUAL classifications")

    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in restored_rows:
        groups[str(row["typed_trace_digest"])].append(row)
    mixed = [
        values for values in groups.values()
        if {bool(row["observed_completion"]) for row in values} == {False, True}
    ]
    mixed_available = sum(
        any(row["available"] for row in values) for values in mixed
    )
    metrics = _metrics(restored_rows, len(certified_direct))

    retained = 0
    for index, fen in enumerate(retention_fens):
        source_action = source.r0.emit_action(chess.Board(fen))
        actual_action = restored.base.r0.emit_action(chess.Board(fen))
        retained += source_action == actual_action
    state_after = restored.base.r0.persistent_state_audit()
    r0_state_exact = source_state == state_after
    escrow_complete = all(
        (
            mode is AllocationMode.HASH_WITHOUT_REPLACEMENT
            or dict(cell.nomination_escrow.categorized_reads).get(
                "consensus_reads"
            ) == tuple(sorted(memory.events))
        )
        for cell in organism.envelope.cells.values()
        if cell.nomination_escrow is not None
    )
    frontier_exact = all(
        cell.nomination_escrow.birth_frontier
        == cell.nomination_escrow.certification_frontier
        == 63
        for cell in organism.envelope.cells.values()
        if cell.nomination_escrow is not None
    )
    engagement = {
        "distinct_residual_events": len(memory.events),
        "enough_distinct_residual_events": len(memory.events) == 64,
        "legal_pair_or_triple_request": (
            allocation["proposal_slots_by_tuple_width"]["2"] > 0
            or allocation["proposal_slots_by_tuple_width"]["3"] > 0
        ),
        "nominated_pair_or_triple_count": len(nominated_direct),
        "nominated_pair_or_triple": bool(nominated_direct),
        "nominated_pair_or_triple_with_four_later_opportunities_count": len(
            later_eligible
        ),
        "nominated_pair_or_triple_with_four_later_opportunities": bool(
            later_eligible
        ),
        "certified_pair_or_triple_count": len(certified_direct),
    }
    return {
        "ordinal": int(item["ordinal"]),
        "genome_seed": int(item["genome_seed"]),
        "arm": mode.value,
        "metrics": metrics,
        "engagement": engagement,
        "allocation": allocation,
        "growth": {
            "proposal_attempts": growth.proposal_attempts,
            "admitted_proposals": growth.admitted_proposals,
            "duplicate_rejections": growth.duplicate_rejections,
            "capacity_rejections": growth.capacity_rejections,
            "lifecycle_review_count": len(growth.lifecycle_reviews),
            "trial_capacity": organism.envelope.config.trial_capacity,
            "live_cell_count": sum(
                cell.state.name != "PRUNED"
                for cell in organism.envelope.cells.values()
            ),
        },
        "memory": memory.manifest(),
        "candidate_population": [
            cell.to_manifest()
            for cell in sorted(
                organism.envelope.cells.values(),
                key=lambda item: item.cell_id,
            )
        ],
        "derangement": derangement_audit,
        "derangement_statistic_probe": probe,
        "prospective": {
            "event_count": len(references),
            "event_tape_digest": _sha_json([
                {
                    "fen": row["fen"],
                    "actuation": row["actuation"],
                    "trace_digest": row["trace_digest"],
                    "actual_completion": row["actual_completion"],
                }
                for row in references
            ]),
            "maturity_emissions": maturity,
            "revocation_emissions": revocation,
            "activation_opportunity_digest": _sha_json(
                activation_opportunities
            ),
            "prequential_digest": _sha_json(prequential),
        },
        "rows": restored_rows,
        "integrity": {
            "serialization_virtual_parity": True,
            "serialized_sha256": hashlib.sha256(payload).hexdigest(),
            "r0_retention": retained,
            "r0_retention_total": len(retention_fens),
            "r0_persistent_state_exact": r0_state_exact,
            "mixed_outcome_identical_complete_trace_groups": len(mixed),
            "mixed_groups_emitting_available": mixed_available,
            "complete_consensus_read_escrow": escrow_complete,
            "birth_certification_frontier_exact": frontier_exact,
            "discovery_certification_overlap": 0,
            "virtual_memory_changes": memory.virtual_mutation_attempts,
            "physical_event_idempotence": (
                len(memory.events) == len(memory.physical_identities) == 64
            ),
            "structural_replay_evidence_count": len(organism.envelope.evidence),
            "host_candidate_selector": False,
        },
        "duration_seconds": perf_counter() - started,
    }


def _write_outputs(result: Mapping[str, Any]) -> None:
    if OUTPUT_GZ.exists() or OUTPUT_MD.exists():
        raise FileExistsError("refusing to overwrite bounded result")
    OUTPUT_GZ.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(OUTPUT_GZ, "wt", encoding="utf-8", compresslevel=9) as stream:
        json.dump(result, stream, sort_keys=True, separators=(",", ":"), allow_nan=False)
    gates = result.get("gates", {})
    conclusion = result.get("terminal_conclusion", "execution_failure")
    cohort = result.get("cohort", {})
    lines = [
        "# Residual-consensus candidate allocation",
        "",
        f"Terminal conclusion: `{conclusion}`.",
        "",
        (
            "Stage 0 found direct pair/triple and direct-triple opportunity in "
            f"{result['stage0']['seeds_with_legal_direct_pair_or_triple']}/32 and "
            f"{result['stage0']['seeds_with_legal_direct_triple']}/32 seeds."
        ),
        "",
    ]
    for mode in (item.value for item in ARM_ORDER):
        if mode in cohort:
            row = cohort[mode]
            lines.append(
                f"- `{mode}`: safe-narrow {row['safe_narrow']}/32; "
                f"TP {row['total_tp']}; FP {row['total_fp']}; "
                f"deployable TP {row['deployable_tp']}."
            )
    lines.extend(["", "Primary gates: " + json.dumps(gates, sort_keys=True) + "."])
    OUTPUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run(freeze_path: str, *, max_workers: int) -> dict[str, Any]:
    started = perf_counter()
    freeze = json.loads(Path(freeze_path).read_text(encoding="utf-8"))
    commit = subprocess.run(
        ["git", "rev-parse", "HEAD"], check=True,
        capture_output=True, text=True,
    ).stdout.strip()
    status = subprocess.run(
        ["git", "status", "--porcelain"], check=True,
        capture_output=True, text=True,
    ).stdout.strip()
    if commit != freeze["package_source_commit"] or status:
        raise RuntimeError("execution checkout differs from source freeze")
    for path, digest in freeze["source_hashes"].items():
        if _sha_file(path) != digest:
            raise RuntimeError(f"frozen source changed: {path}")
    stage0 = json.loads(STAGE0.read_text(encoding="utf-8"))
    if not stage0["passed"] or _sha_file(STAGE0) != freeze["stage0_sha256"]:
        raise RuntimeError("Stage 0 gate/freeze mismatch")
    regression = _load_regression()
    items = sorted(
        (row["source_artifact"] for row in regression["organisms"]
         if row["arm"] == "local_contrast_specialization"),
        key=lambda row: int(row["ordinal"]),
    )
    if len(items) != 32:
        raise RuntimeError("retained 32-seed cohort changed")
    if [int(item["genome_seed"]) for item in items] != freeze["genome_seeds"]:
        raise RuntimeError("frozen genome-seed cohort changed")
    references = _bind_semantic_reference_digests(
        tuple(regression["reference_rows"]), items[0]
    )
    build = load_retired_r0_build(NativeAuthorityLabConfig())
    evaluation_rows = tuple(
        [(f"validation_positive:{index:02d}", fen, True)
         for index, fen in enumerate(build.pools.r0_validation)]
        + [(f"validation_decoy:{index:02d}", fen, False)
           for index, fen in enumerate(build.pools.gate_validation_decoys)]
        + [(f"regression:{index:02d}", str(row["fen"]), bool(row["actual_completion"]))
           for index, row in enumerate(references)]
    )
    retention_fens = tuple((*build.pools.r0_validation, *build.pools.r0_regression))
    args = [
        {
            "source_item": item,
            "mode": mode.value,
            "references": references,
            "evaluation_rows": evaluation_rows,
            "retention_fens": retention_fens,
            "memory_config": freeze["configuration"]["memory"],
            "expected_derangement_digest": freeze["derangement_digests"][
                str(item["ordinal"])
            ],
        }
        for item in items for mode in ARM_ORDER
    ]
    result: dict[str, Any] = {
        "schema_version": "native_residual_consensus_candidate_allocation.v1",
        "package_freeze": freeze,
        "stage0": stage0,
        "scope": {
            "viewed_data_only": True,
            "retired_65_opened": False,
            "mate_in_2_handover_opened": False,
            "fresh_data_opened": False,
            "r1_learning": False,
            "seed_count": 32,
            "primary_arms": [mode.value for mode in ARM_ORDER],
        },
    }
    try:
        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            organisms = list(executor.map(_worker, args))
        organisms.sort(key=lambda row: (
            row["ordinal"], [mode.value for mode in ARM_ORDER].index(row["arm"])
        ))
        result["organisms"] = organisms
        cohort = {}
        for mode in (item.value for item in ARM_ORDER):
            rows = [item for item in organisms if item["arm"] == mode]
            cohort[mode] = {
                "safe_narrow": sum(row["metrics"]["safe_narrow"] for row in rows),
                "total_tp": sum(row["metrics"]["tp"] for row in rows),
                "total_fp": sum(row["metrics"]["fp"] for row in rows),
                "deployable_tp": sum(row["metrics"]["deployable_tp"] for row in rows),
                "per_seed_deployable_tp": [row["metrics"]["deployable_tp"] for row in rows],
                "engaged": sum(all((
                    row["engagement"]["enough_distinct_residual_events"],
                    row["engagement"]["legal_pair_or_triple_request"],
                    row["engagement"]["nominated_pair_or_triple"],
                    row["engagement"]["nominated_pair_or_triple_with_four_later_opportunities"],
                )) for row in rows),
            }
        result["cohort"] = cohort
        true = cohort[AllocationMode.TRUE_CONSENSUS.value]["per_seed_deployable_tp"]
        deranged = cohort[AllocationMode.RESPONSIBILITY_DERANGED.value]["per_seed_deployable_tp"]
        hashed = cohort[AllocationMode.HASH_WITHOUT_REPLACEMENT.value]["per_seed_deployable_tp"]
        comparisons = holm_two(
            {"control": AllocationMode.RESPONSIBILITY_DERANGED.value, **exact_sign_test(true, deranged)},
            {"control": AllocationMode.HASH_WITHOUT_REPLACEMENT.value, **exact_sign_test(true, hashed)},
        )
        result["comparisons"] = comparisons
        by_seed: dict[int, list[dict[str, Any]]] = defaultdict(list)
        for row in organisms:
            by_seed[row["ordinal"]].append(row)
        budgets_exact = all(
            len({
                _sha_json({field: row["allocation"][field] for field in MATCHED_BUDGET_FIELDS})
                for row in rows
            }) == 1
            for rows in by_seed.values()
        )
        matched_runtime_exposure = all(
            len({
                _sha_json({
                    "trial_capacity": row["growth"]["trial_capacity"],
                    "lifecycle_review_count": row["growth"]["lifecycle_review_count"],
                    "prospective_event_count": row["prospective"]["event_count"],
                    "prospective_event_tape_digest": row["prospective"]["event_tape_digest"],
                    "memory_config": row["memory"]["config"],
                    "genome_seed": row["genome_seed"],
                    "tie_breaking": row["allocation"]["tie_breaking"],
                })
                for row in rows
            }) == 1
            for rows in by_seed.values()
        )
        all_integrity = all(all((
            row["integrity"]["serialization_virtual_parity"],
            row["integrity"]["r0_retention"] == 32,
            row["integrity"]["r0_persistent_state_exact"],
            row["integrity"]["mixed_groups_emitting_available"] == 0,
            row["integrity"]["complete_consensus_read_escrow"],
            row["integrity"]["birth_certification_frontier_exact"],
            row["integrity"]["discovery_certification_overlap"] == 0,
            row["integrity"]["virtual_memory_changes"] == 0,
            row["integrity"]["physical_event_idempotence"],
            row["integrity"]["structural_replay_evidence_count"] == 64,
            not row["integrity"]["host_candidate_selector"],
        )) for row in organisms)
        true_cohort = cohort[AllocationMode.TRUE_CONSENSUS.value]
        deranged_cohort = cohort[AllocationMode.RESPONSIBILITY_DERANGED.value]
        hash_cohort = cohort[AllocationMode.HASH_WITHOUT_REPLACEMENT.value]
        gates = {
            "engagement_at_least_24_all_arms": all(row["engaged"] >= 24 for row in cohort.values()),
            "true_safe_narrow_at_least_24": true_cohort["safe_narrow"] >= 24,
            "zero_mixed_trace_available": all(row["integrity"]["mixed_groups_emitting_available"] == 0 for row in organisms),
            "true_deployable_tp_exceeds_hash": true_cohort["deployable_tp"] > hash_cohort["deployable_tp"],
            "true_deployable_tp_exceeds_deranged": true_cohort["deployable_tp"] > deranged_cohort["deployable_tp"],
            "paired_tests_holm_pass": all(row["holm_pass_0_05"] for row in comparisons),
            "at_least_17_favor_true_each": all(row["wins"] >= 17 for row in comparisons),
            "all_32_each_comparison": all(len(values) == 32 for values in (true, deranged, hashed)),
            "matched_primary_search_budgets": budgets_exact,
            "matched_runtime_exposure_and_capacity": matched_runtime_exposure,
            "all_integrity": all_integrity,
        }
        result["gates"] = gates
        if not gates["engagement_at_least_24_all_arms"]:
            conclusion = "residual_consensus_engagement_or_evidence_starvation"
        elif all(gates.values()):
            conclusion = "residual_local_ranking_improves_seed_robust_growth"
        else:
            conclusion = "residual_consensus_primary_gate_failure"
        result["terminal_conclusion"] = conclusion
        result["passed"] = all(gates.values())
        result["duration_seconds"] = perf_counter() - started
    except Exception as exc:
        result.update({
            "passed": False,
            "terminal_conclusion": "execution_failure_preserved",
            "failure": {
                "type": type(exc).__name__,
                "message": str(exc),
                "traceback": traceback.format_exc(),
            },
            "duration_seconds": perf_counter() - started,
        })
        _write_outputs(result)
        raise
    _write_outputs(result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--freeze", required=True)
    parser.add_argument("--max-workers", type=int, default=4)
    args = parser.parse_args()
    result = run(args.freeze, max_workers=args.max_workers)
    print(json.dumps({
        "passed": result["passed"],
        "terminal_conclusion": result["terminal_conclusion"],
        "output_gz": str(OUTPUT_GZ),
        "output_md": str(OUTPUT_MD),
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
