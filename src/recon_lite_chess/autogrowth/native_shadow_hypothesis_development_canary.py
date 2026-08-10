"""One development-only shadow-retention canary on already-viewed R0 data."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

import chess

from recon_lite import FrameContext, FrameKind
from recon_lite_hector.nodes import StemCellState

from .native_competence_envelope import (
    AvailabilityState,
    MixedOutcomeDisposition,
)
from .native_prospective_evidence_authority_v2 import (
    NativeProspectiveAuthorityV2,
    V2Mode,
)
from .native_residual_consensus_candidate_allocation import (
    AllocationMode,
    ResidualConsensusCompetenceOrganism,
    ResidualConsensusGrowthGenome,
    responsibility_derangement,
)
from .native_residual_consensus_candidate_allocation_run import (
    MATCHED_BUDGET_FIELDS,
    REGRESSION,
    REGRESSION_SHA,
    _bind_semantic_reference_digests,
    _load_regression,
    _load_source,
    _memory,
    _trace_parity_failures,
)
from .native_trace_competence_authority import TraceNativeCompetenceOrganism


STARTING_COMMIT = "e35681f8acd436e56580819b177cb71e7e6cdc1b"
CANARY_SEED = 7875574914420937836
CANARY_ORDINAL = 1
SOURCE_FREEZE = Path(
    "reports/autogrowth/native_authority/"
    "native_terminal_trace_historical_regression_freeze.json"
)
EXECUTION_FREEZE = Path(
    "reports/autogrowth/native_authority/"
    "native_residual_consensus_copy_compatibility_result/execution_freeze.json"
)
DEFAULT_OUTPUT = Path(
    "reports/autogrowth/native_authority/"
    "native_shadow_hypothesis_development_canary.json"
)
R0_SEMANTIC_FIELDS = (
    "topology_sha256",
    "weights_sha256",
    "credit_sha256",
    "lifecycle_sha256",
)


def _sha_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _source_item() -> dict[str, Any]:
    freeze = json.loads(SOURCE_FREEZE.read_text(encoding="utf-8"))
    matches = [
        row for row in freeze["organisms"]
        if int(row["ordinal"]) == CANARY_ORDINAL
        and int(row["genome_seed"]) == CANARY_SEED
        and row["arm"] == "local_contrast_specialization"
    ]
    if len(matches) != 1:
        raise RuntimeError("exact canary source is absent or ambiguous")
    item = dict(matches[0])
    execution = json.loads(EXECUTION_FREEZE.read_text(encoding="utf-8"))
    cohort = [
        row for row in execution["cohort"]
        if int(row["ordinal"]) == CANARY_ORDINAL
        and int(row["genome_seed"]) == CANARY_SEED
    ]
    if len(cohort) != 1:
        raise RuntimeError("exact prior execution cohort row is absent")
    prior = cohort[0]
    expected = {
        "compressed_sha256": prior["source_compressed_sha256"],
        "continuation_v3_sha256": prior["source_continuation_v3_sha256"],
    }
    for key, value in expected.items():
        if item[key] != value:
            raise RuntimeError(f"canary source differs from prior freeze: {key}")
    return item


def _r0_projection(organism: TraceNativeCompetenceOrganism) -> dict[str, str]:
    audit = organism.r0.persistent_state_audit()
    return {key: str(audit[key]) for key in R0_SEMANTIC_FIELDS}


def _new_empty(source: TraceNativeCompetenceOrganism) -> TraceNativeCompetenceOrganism:
    return TraceNativeCompetenceOrganism.empty(
        copy.deepcopy(source.r0),
        envelope_config=copy.deepcopy(source.envelope.config),
        learning_config=copy.deepcopy(source.learning_config),
    )


def _grow_deferred(
    source: TraceNativeCompetenceOrganism,
    discovery: Sequence[Any],
    *,
    mode: AllocationMode,
) -> tuple[TraceNativeCompetenceOrganism, dict[str, Any], dict[str, Any]]:
    organism = _new_empty(source)
    organism.open_prospective_discovery_epoch()
    memory = _memory(organism, discovery)
    organism.envelope.consensus_memory = memory
    derangement, derangement_audit = responsibility_derangement(
        memory.ordered_events,
        seed=CANARY_SEED,
    )
    allocator = ResidualConsensusGrowthGenome(
        seed=CANARY_SEED,
        memory=memory,
        mode=mode,
        derangement=(
            derangement
            if mode is AllocationMode.RESPONSIBILITY_DERANGED
            else None
        ),
    )
    wrapper = ResidualConsensusCompetenceOrganism(organism, allocator)
    wrapper.grow_from_grounded_receipts(discovery, finalize=False)
    if not any(cell.is_trial for cell in organism.envelope.cells.values()):
        raise RuntimeError("deferred lifecycle boundary has no trials")
    return organism, allocator.manifest(), derangement_audit


def _cell_clone_boundary(
    shadow: TraceNativeCompetenceOrganism,
    tombstone: TraceNativeCompetenceOrganism,
) -> dict[str, Any]:
    shadow_cells = shadow.envelope.cells
    tombstone_cells = tombstone.envelope.cells
    if set(shadow_cells) != set(tombstone_cells):
        raise RuntimeError("lifecycle clones changed candidate identity")
    mixed_ids = []
    non_mixed_exact = 0
    for cell_id in sorted(shadow_cells):
        retained = shadow_cells[cell_id]
        removed = tombstone_cells[cell_id]
        if retained.is_shadow:
            mixed_ids.append(cell_id)
            if removed.state is not StemCellState.PRUNED:
                raise RuntimeError("tombstone control did not prune mixed candidate")
            if removed.prune_reason != "mixed_outcomes":
                raise RuntimeError("shadow/tombstone prune reasons diverged")
            retained_state = retained.stem_cell.state
            retained.stem_cell.state = removed.stem_cell.state
            try:
                if retained.to_manifest() != removed.to_manifest():
                    raise RuntimeError(
                        "shadow/tombstone candidate differs beyond structural state"
                    )
            finally:
                retained.stem_cell.state = retained_state
            if (
                retained.members != removed.members
                or retained.polarity is not removed.polarity
                or retained.lineage_parent_id != removed.lineage_parent_id
                or retained.specialization_depth != removed.specialization_depth
                or retained.nomination_escrow is None
                or removed.nomination_escrow is None
                or retained.nomination_escrow.manifest()
                != removed.nomination_escrow.manifest()
            ):
                raise RuntimeError("shadow did not preserve frozen nomination")
            if retained.competes_for_active_capacity:
                raise RuntimeError("shadow competes for active capacity")
        else:
            if retained.to_manifest() != removed.to_manifest():
                raise RuntimeError("non-mixed lifecycle result changed")
            non_mixed_exact += 1
    if not mixed_ids:
        raise RuntimeError("diagnostic-known canary produced no mixed shadow")
    return {
        "mixed_shadow_count": len(mixed_ids),
        "non_mixed_candidate_count_exact": non_mixed_exact,
        "mixed_cell_ids_sha256": hashlib.sha256(
            json.dumps(mixed_ids, separators=(",", ":")).encode()
        ).hexdigest(),
    }


def _matched_budget_projection(manifest: Mapping[str, Any]) -> dict[str, Any]:
    return {key: manifest[key] for key in MATCHED_BUDGET_FIELDS}


def run_canary() -> dict[str, Any]:
    if _sha_file(REGRESSION) != REGRESSION_SHA:
        raise RuntimeError("already-viewed regression artifact changed")
    item = _source_item()
    source = _load_source(item)
    source_r0 = _r0_projection(source)
    receipts = tuple(sorted(
        source.receipts.values(), key=lambda row: row.event_ordinal
    ))
    discovery = receipts[:64]
    if tuple(row.event_ordinal for row in discovery) != tuple(range(64)):
        raise RuntimeError("canary discovery prefix is not exact 0..63")
    references = _bind_semantic_reference_digests(
        _load_regression()["reference_rows"], item
    )

    true_pre, true_budget, derangement_audit = _grow_deferred(
        source, discovery, mode=AllocationMode.TRUE_CONSENSUS
    )
    true_pre_r0 = _r0_projection(true_pre)
    true_shadow = copy.deepcopy(true_pre)
    true_tombstone = copy.deepcopy(true_pre)
    true_shadow.envelope.finalize_growth(
        mixed_outcome_disposition=MixedOutcomeDisposition.RETAIN_SHADOW
    )
    true_tombstone.envelope.finalize_growth(
        mixed_outcome_disposition=MixedOutcomeDisposition.TOMBSTONE
    )
    clone_boundary = _cell_clone_boundary(true_shadow, true_tombstone)

    deranged_pre, deranged_budget, deranged_audit = _grow_deferred(
        source, discovery, mode=AllocationMode.RESPONSIBILITY_DERANGED
    )
    deranged_shadow = copy.deepcopy(deranged_pre)
    deranged_shadow.envelope.finalize_growth(
        mixed_outcome_disposition=MixedOutcomeDisposition.RETAIN_SHADOW
    )
    true_matched = _matched_budget_projection(true_budget)
    deranged_matched = _matched_budget_projection(deranged_budget)
    if true_matched != deranged_matched:
        raise RuntimeError("true and deranged proposal budgets diverged")
    if derangement_audit != deranged_audit:
        raise RuntimeError("derangement construction changed between arms")

    authority = NativeProspectiveAuthorityV2.from_organism(
        true_shadow, mode=V2Mode.PROSPECTIVE
    )
    authority.close_nomination()
    shadow_ids = tuple(sorted(
        cell.cell_id for cell in authority.base.envelope.cells.values()
        if cell.is_shadow
    ))
    if not shadow_ids or not set(shadow_ids).issubset(authority.states):
        raise RuntimeError("native shadow nominations did not enter V2 measurement")
    if any(
        authority.states[cell_id].support
        or authority.states[cell_id].successes
        or authority.states[cell_id].contradictions
        or authority.states[cell_id].prospectively_certified
        for cell_id in shadow_ids
    ):
        raise RuntimeError("discovery evidence granted prospective authority")

    before_virtual = authority.continuation_manifest()
    virtual_commitments = {cell_id: 0 for cell_id in shadow_ids}
    virtual_parity_checks = 0
    for index, reference in enumerate(references):
        opened = authority.open_virtual(FrameContext(
            f"shadow-canary-virtual:{index}",
            FrameKind.VIRTUAL,
            values={"board": chess.Board(str(reference["fen"]))},
        ))
        trace = opened["query"].graph_signal_trace
        failures = _trace_parity_failures(trace, reference)
        if failures:
            raise RuntimeError("VIRTUAL semantic parity failed: " + ",".join(failures))
        virtual_parity_checks += 1
        graph = opened["graph_emissions"]
        for cell_id in set(graph["commitment"]).intersection(shadow_ids):
            virtual_commitments[cell_id] += 1
        if graph["available"] or graph["refuted"]:
            raise RuntimeError("uncertified candidate influenced VIRTUAL decision")
        if opened["classification"].state is not AvailabilityState.UNKNOWN:
            raise RuntimeError("uncertified candidate escaped UNKNOWN")
    if authority.continuation_manifest() != before_virtual:
        raise RuntimeError("VIRTUAL canary mutated prospective authority")
    if any(authority.states[cell_id].support for cell_id in shadow_ids):
        raise RuntimeError("VIRTUAL activation counted as prospective evidence")
    virtual_support_after_scan = sum(
        authority.states[cell_id].support for cell_id in shadow_ids
    )

    restored_before = NativeProspectiveAuthorityV2.loads(authority.dumps())
    if restored_before.continuation_manifest() != authority.continuation_manifest():
        raise RuntimeError("pre-exposure serialization changed authority")
    authority = restored_before
    real_activations = {cell_id: 0 for cell_id in shadow_ids}
    shadow_maturity_ids: set[str] = set()
    shadow_revocation_ids: set[str] = set()
    pre_certification_false_influence = 0
    real_parity_checks = 0
    for index, reference in enumerate(references):
        board = chess.Board(str(reference["fen"]))
        pending, trace = authority.open_real_event(FrameContext(
            f"shadow-canary-real:{index}",
            FrameKind.REAL,
            values={"board": board},
        ))
        failures = _trace_parity_failures(trace, reference)
        if failures:
            raise RuntimeError("REAL semantic parity failed: " + ",".join(failures))
        real_parity_checks += 1
        matching_shadows = set(pending.matching_cell_ids).intersection(shadow_ids)
        for cell_id in matching_shadows:
            real_activations[cell_id] += 1
            if not authority.states[cell_id].prospectively_certified and (
                cell_id in pending.pre_outcome_classification.available_cell_ids
                or cell_id in pending.pre_outcome_classification.refuted_cell_ids
            ):
                pre_certification_false_influence += 1
        successor = board.copy(stack=False)
        successor.push(chess.Move.from_uci(trace.actuation.move_uci))
        if successor.is_checkmate() != bool(reference["actual_completion"]):
            raise RuntimeError("already-viewed outcome parity failed")
        receipt = authority.mint_environment_receipt(
            pending_token=pending.pending_token,
            trace=trace,
            predecessor=board,
            successor=successor,
        )
        emission = authority.consume(receipt)
        shadow_maturity_ids.update(set(emission.graph_maturity_ids).intersection(shadow_ids))
        shadow_revocation_ids.update(set(emission.graph_revocation_ids).intersection(shadow_ids))
    if pre_certification_false_influence:
        raise RuntimeError("shadow influenced a decision before certification")
    recurring = tuple(sorted(
        cell_id for cell_id, count in real_activations.items() if count >= 2
    ))
    exposed_four = tuple(sorted(
        cell_id for cell_id, count in real_activations.items() if count >= 4
    ))
    if not recurring:
        raise RuntimeError("mixed shadows did not repeatedly recur")
    if not shadow_maturity_ids:
        raise RuntimeError("existing V2 rule did not certify a qualifying shadow")
    if any(authority.states[cell_id].support < 4 for cell_id in shadow_maturity_ids):
        raise RuntimeError("shadow certification bypassed the four-support rule")

    restored_after = NativeProspectiveAuthorityV2.loads(authority.dumps())
    if restored_after.continuation_manifest() != authority.continuation_manifest():
        raise RuntimeError("post-exposure serialization changed authority")
    r0_stages = {
        "source": source_r0,
        "empty_after_deferred_growth": true_pre_r0,
        "true_shadow": _r0_projection(true_shadow),
        "true_tombstone": _r0_projection(true_tombstone),
        "deranged_shadow": _r0_projection(deranged_shadow),
        "v2_restored": _r0_projection(restored_after.base),
    }
    if any(value != source_r0 for value in r0_stages.values()):
        raise RuntimeError("R0 semantic persistent state changed")

    action_parity_checks = 0
    before_final_virtual = restored_after.continuation_manifest()
    for index, reference in enumerate(references):
        opened = restored_after.open_virtual(FrameContext(
            f"shadow-canary-action-parity:{index}",
            FrameKind.VIRTUAL,
            values={"board": chess.Board(str(reference["fen"]))},
        ))
        failures = _trace_parity_failures(
            opened["query"].graph_signal_trace, reference
        )
        if failures:
            raise RuntimeError("restored action/trace parity failed: " + ",".join(failures))
        action_parity_checks += 1
    if restored_after.continuation_manifest() != before_final_virtual:
        raise RuntimeError("final VIRTUAL action check mutated authority")

    return {
        "schema_version": "native_shadow_hypothesis_development_canary.v1",
        "status": "PASS",
        "scientific_claim": False,
        "development_only": True,
        "starting_commit": STARTING_COMMIT,
        "scope": {
            "seed": CANARY_SEED,
            "ordinal": CANARY_ORDINAL,
            "diagnostic_known_seed_selection_only": True,
            "already_viewed_reference_rows": len(references),
            "fresh_data_opened": False,
            "growth_rerun_count": 2,
            "hash_arm_omitted": True,
            "scientific_32_seed_execution_started": False,
        },
        "source_binding": {
            "path": item["path"],
            "compressed_sha256": item["compressed_sha256"],
            "uncompressed_sha256": item["uncompressed_sha256"],
            "continuation_v3_sha256": item["continuation_v3_sha256"],
            "regression_path": str(REGRESSION),
            "regression_sha256": REGRESSION_SHA,
        },
        "lifecycle_boundary": clone_boundary,
        "prospective_measurement": {
            "shadow_count": len(shadow_ids),
            "virtual_shadow_cells_recurred": sum(
                count > 0 for count in virtual_commitments.values()
            ),
            "virtual_support_after_scan": virtual_support_after_scan,
            "real_shadow_cells_recurred_twice": len(recurring),
            "real_shadow_cells_with_four_activations": len(exposed_four),
            "maximum_real_shadow_activations": max(real_activations.values()),
            "prospectively_certified_shadow_count": len(shadow_maturity_ids),
            "graph_locally_revoked_shadow_count": len(shadow_revocation_ids),
            "pre_certification_false_influence": pre_certification_false_influence,
            "certified_shadow_ids": sorted(shadow_maturity_ids),
            "revoked_shadow_ids": sorted(shadow_revocation_ids),
        },
        "budget_match": {
            "fields": list(MATCHED_BUDGET_FIELDS),
            "true_equals_deranged": true_matched == deranged_matched,
            "true": true_matched,
            "deranged": deranged_matched,
            "derangement_mapping_digest": derangement_audit["mapping_digest"],
        },
        "parity": {
            "virtual_semantic_trace_checks": virtual_parity_checks,
            "real_semantic_trace_checks": real_parity_checks,
            "restored_action_trace_checks": action_parity_checks,
            "pre_exposure_serialization_exact": True,
            "post_exposure_serialization_exact": True,
            "r0_semantic_fields": list(R0_SEMANTIC_FIELDS),
            "r0_all_stages_equal": True,
            "r0_stage_projections": r0_stages,
        },
        "engineering_conclusion": (
            "actual genome-nominated mixed candidates can remain dormant, recur "
            "on later REAL traces, and engage the unchanged prospective rule "
            "without pre-certification influence"
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    result = run_canary()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "status": result["status"],
        "output": str(args.output),
        "certified_shadow_count": result["prospective_measurement"][
            "prospectively_certified_shadow_count"
        ],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
