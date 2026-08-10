"""Focused development canary for deferred shadow-origin specialization."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

import chess

from recon_lite import FrameContext, FrameKind
from recon_lite_hector.nodes import StemCellState, StemCellTerminal

from .native_competence_envelope import (
    AvailabilityState,
    CompetenceContextCell,
    CompetenceContextGrowthGenome,
    DormantOrigin,
    GraphNativeCompetenceEnvelope,
    SpecializationMode,
)
from .native_prospective_evidence_authority_v2 import (
    NativeProspectiveAuthorityV2,
    V2Mode,
    _GraphSpecializationRequest,
    _run_authority_graph,
    AuthorityMeasurementSnapshot,
)
from .native_residual_consensus_candidate_allocation_run import (
    REGRESSION,
    REGRESSION_SHA,
    _bind_semantic_reference_digests,
    _load_regression,
    _load_source,
    _trace_parity_failures,
)
from .native_shadow_hypothesis_development_canary import (
    R0_SEMANTIC_FIELDS,
    _r0_projection,
    _source_item,
)
from .native_trace_competence_authority import TraceNativeCompetenceOrganism


STARTING_COMMIT = "59903b744078150a3b65c7166a0de8cfe45edf40"
DEFAULT_OUTPUT = Path(
    "reports/autogrowth/native_authority/"
    "native_deferred_specialization_development_canary.json"
)
ARMS = (
    SpecializationMode.LOCAL_CONTRAST,
    SpecializationMode.DISCONNECTED,
    SpecializationMode.COUNTEREXAMPLE_BLIND,
)


def _controlled_discovery_source(
    source: TraceNativeCompetenceOrganism,
) -> TraceNativeCompetenceOrganism:
    base = TraceNativeCompetenceOrganism.empty(
        copy.deepcopy(source.r0),
        envelope_config=copy.deepcopy(source.envelope.config),
        learning_config=copy.deepcopy(source.learning_config),
    )
    discovery = tuple(sorted(
        source.receipts.values(),
        key=lambda item: (item.event_ordinal, item.event_id),
    ))[:64]
    if tuple(item.event_ordinal for item in discovery) != tuple(range(64)):
        raise RuntimeError("development discovery region is not exact 0..63")
    for receipt in discovery:
        record, inserted = base._accept_receipt(receipt)
        if not inserted or not base.envelope.add_unique_evidence(record):
            raise RuntimeError("discovery receipt was not uniquely accepted")
    cell_id = "canary_mixed_shadow_parent"
    stem = StemCellTerminal(cell_id)
    stem.state = StemCellState.DORMANT
    stem.trial_node_id = cell_id
    stem.trial_parent_id = "competence_shadow_root"
    stem.children = ["internal:policy_response"]
    stem.is_composition = True
    parent = CompetenceContextCell(
        cell_id=cell_id,
        members=("internal:policy_response",),
        born_round=0,
        born_request_ordinal=0,
        stem_cell=stem,
        polarity=AvailabilityState.AVAILABLE,
        evidence_keys=tuple(sorted(base.receipts)),
        prune_reason="mixed_outcomes",
        dormant_origin=DormantOrigin.MIXED_OUTCOME_SHADOW,
    )
    base.envelope.cells = {cell_id: parent}
    base.envelope._member_specs = {parent.members}
    base.envelope.rebuild_graph()
    return base


def _reference_traces(
    base: TraceNativeCompetenceOrganism,
    references: Sequence[Mapping[str, Any]],
) -> tuple[tuple[str, ...], ...]:
    del base
    return tuple(
        tuple(map(str, reference["ordered_signal_identities"]))
        for reference in references
    )


def _process_reference(
    authority: NativeProspectiveAuthorityV2,
    reference: Mapping[str, Any],
    *,
    frame_id: str,
) -> tuple[Any, Any, Any]:
    board = chess.Board(str(reference["fen"]))
    pending, trace = authority.open_real_event(FrameContext(
        frame_id, FrameKind.REAL, values={"board": board}
    ))
    failures = _trace_parity_failures(trace, reference)
    if failures:
        raise RuntimeError("REAL semantic parity failed: " + ",".join(failures))
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
    return pending, receipt, emission


def _roundtrip(
    authority: NativeProspectiveAuthorityV2, stage: str,
    checks: list[str],
) -> NativeProspectiveAuthorityV2:
    restored = NativeProspectiveAuthorityV2.loads(authority.dumps())
    if restored.continuation_manifest() != authority.continuation_manifest():
        raise RuntimeError(f"serialization changed {stage}")
    checks.append(stage)
    return restored


def _id_set_check(ids: Sequence[str]) -> dict[str, Any]:
    canonical = tuple(sorted(set(ids)))
    return {
        "count": len(canonical),
        "sha256": hashlib.sha256(
            json.dumps(list(canonical), separators=(",", ":")).encode("utf-8")
        ).hexdigest(),
    }


def _choose_matched_genome_seed(
    local_request: Any,
    blind_request: Any,
    traces: Sequence[tuple[str, ...]],
) -> tuple[int, dict[str, str], dict[str, tuple[int, ...]]]:
    for seed in range(100_000):
        selections: dict[str, str] = {}
        matches: dict[str, tuple[int, ...]] = {}
        usable = True
        for name, request in (
            ("local_contrast", local_request),
            ("counterexample_blind", blind_request),
        ):
            proposal = CompetenceContextGrowthGenome(seed).propose_specialization(
                _GraphSpecializationRequest(
                    context_member=f"context:{request.parent_cell_id}",
                    eligible_base_ids=request.eligible_base_ids,
                    request_ordinal=0,
                )
            )
            if proposal is None:
                usable = False
                break
            identity = proposal.members[1]
            occurrences = tuple(
                index for index in range(4, 16)
                if identity in traces[index]
            )
            if len(occurrences) < 5:
                usable = False
                break
            selections[name] = identity
            matches[name] = occurrences
        if usable:
            return seed, selections, matches
    raise RuntimeError("no matched-budget development genome seed found")


def _metric_row(
    *,
    mode: SpecializationMode,
    raw_tp: int,
    raw_fp: int,
    abstentions: int,
    positive_rows: int,
    trigger_false_prediction: int,
    post_contradiction_parent_influence: int,
    pre_certification_child_influence: int,
    child_certified: bool,
    request_count: int,
    genome_calls: int,
) -> dict[str, Any]:
    return {
        "mode": mode.value,
        "raw_tp": raw_tp,
        "raw_fp": raw_fp,
        "abstention": abstentions,
        "safe_deployable_positive_coverage": (
            0.0 if raw_fp else (
                0.0 if positive_rows == 0 else raw_tp / positive_rows
            )
        ),
        "triggering_parent_false_prediction": trigger_false_prediction,
        "post_contradiction_parent_influence": (
            post_contradiction_parent_influence
        ),
        "pre_certification_child_influence": (
            pre_certification_child_influence
        ),
        "child_certified": child_certified,
        "graph_request_count": request_count,
        "genome_call_count": genome_calls,
    }


def run_canary() -> dict[str, Any]:
    if hashlib.sha256(REGRESSION.read_bytes()).hexdigest() != REGRESSION_SHA:
        raise RuntimeError("already-viewed regression artifact changed")
    item = _source_item()
    source = _load_source(item)
    source_r0 = _r0_projection(source)
    references = tuple(_bind_semantic_reference_digests(
        _load_regression()["reference_rows"], item
    ))
    if [bool(item["actual_completion"]) for item in references] != (
        [True] * 16 + [False] * 16
    ):
        raise RuntimeError("already-viewed canary region outcome order changed")
    base = _controlled_discovery_source(source)
    traces = _reference_traces(base, references)
    parent_id = "canary_mixed_shadow_parent"
    template = NativeProspectiveAuthorityV2.from_organism(
        base,
        mode=V2Mode.PROSPECTIVE,
        specialization_mode=SpecializationMode.LOCAL_CONTRAST,
        structural_epoch_schedule=(69,),
    )
    arms = {mode: copy.deepcopy(template) for mode in ARMS}
    for mode, authority in arms.items():
        authority.specialization_mode = mode
    for authority in arms.values():
        authority.close_nomination()
        state = authority.states[parent_id]
        if state.prospectively_certified or state.support:
            raise RuntimeError("discovery evidence certified the shadow parent")

    serialization: dict[str, list[str]] = {mode.value: [] for mode in ARMS}
    discovery_physical_ids = {
        reference.stable_physical_interaction_id
        for receipt_id, reference in template.accepted_real_references.items()
        if receipt_id in base.receipts
    }
    if len(discovery_physical_ids) != len(base.receipts):
        raise RuntimeError("discovery physical identities are not one-to-one")
    region_ids: dict[str, dict[str, set[str]]] = {
        mode.value: {
            "parent_discovery": set(discovery_physical_ids),
            "parent_prospective": set(),
            "child_certification": set(),
            "evaluation": set(),
        }
        for mode in ARMS
    }
    region_receipt_ids: dict[str, dict[str, set[str]]] = {
        mode.value: {
            "parent_discovery": set(base.receipts),
            "parent_prospective": set(),
            "child_certification": set(),
            "evaluation": set(),
        }
        for mode in ARMS
    }
    for index in range(4):
        for mode, authority in arms.items():
            _pending, receipt, _emission = _process_reference(
                authority, references[index],
                frame_id=f"deferred:{mode.value}:parent-support:{index}",
            )
            region_ids[mode.value]["parent_prospective"].add(
                receipt.interaction_fingerprint
            )
            region_receipt_ids[mode.value]["parent_prospective"].add(
                receipt.receipt_id
            )
    for authority in arms.values():
        if not authority.states[parent_id].prospectively_certified:
            raise RuntimeError("parent did not earn prospective certification")

    trigger_false_prediction: dict[SpecializationMode, int] = {}
    old_materializer = GraphNativeCompetenceEnvelope._materialize_specialization
    def _forbidden_materializer(*_args: Any, **_kwargs: Any) -> None:
        raise RuntimeError("V2 invoked old immediate specialization path")
    GraphNativeCompetenceEnvelope._materialize_specialization = (
        _forbidden_materializer
    )
    try:
        for mode, authority in arms.items():
            state_count = len(authority.states)
            pending, receipt, emission = _process_reference(
                authority, references[16],
                frame_id=f"deferred:{mode.value}:parent-contradiction",
            )
            if len(authority.states) != state_count:
                raise RuntimeError("contradiction event created a child")
            region_ids[mode.value]["parent_prospective"].add(
                receipt.interaction_fingerprint
            )
            region_receipt_ids[mode.value]["parent_prospective"].add(
                receipt.receipt_id
            )
            trigger_false_prediction[mode] = int(
                parent_id in pending.pre_outcome_classification.available_cell_ids
            )
            if authority.states[parent_id].prospectively_certified:
                raise RuntimeError("contradiction did not revoke parent authority")
            expected_requests = (
                0 if mode is SpecializationMode.DISCONNECTED else 1
            )
            if len(emission.graph_specialization_request_ids) != expected_requests:
                raise RuntimeError("graph specialization request count mismatch")
            if not set(emission.graph_specialization_request_ids).issubset(
                emission.graph_revocation_ids
            ):
                raise RuntimeError("request was not paired with graph revocation")
            pre_virtual = authority.continuation_manifest()
            pre_virtual_state = copy.deepcopy(authority.states[parent_id])
            virtual = authority.open_virtual(FrameContext(
                f"deferred:{mode.value}:post-contradiction-virtual",
                FrameKind.VIRTUAL,
                values={"board": chess.Board(str(references[17]["fen"]))},
            ))
            virtual_graph = virtual["graph_emissions"]
            if (
                parent_id in virtual_graph["available"]
                or parent_id in virtual_graph["refuted"]
            ):
                raise RuntimeError("revoked parent influenced intervening VIRTUAL")
            if authority.states[parent_id] != pre_virtual_state:
                raise RuntimeError("VIRTUAL changed revoked parent evidence")
            if authority.continuation_manifest() != pre_virtual:
                raise RuntimeError("VIRTUAL changed continuation state")
            arms[mode] = _roundtrip(
                authority,
                "REVOCATION_AND_QUEUE_APPEND",
                serialization[mode.value],
            )
    finally:
        GraphNativeCompetenceEnvelope._materialize_specialization = (
            old_materializer
        )

    local = arms[SpecializationMode.LOCAL_CONTRAST]
    blind = arms[SpecializationMode.COUNTEREXAMPLE_BLIND]
    local_request = next(iter(local.deferred_requests.values()))
    blind_request = next(iter(blind.deferred_requests.values()))
    genome_seed, selected_identities, later_matches = (
        _choose_matched_genome_seed(local_request, blind_request, traces)
    )

    child_ids: dict[SpecializationMode, str] = {}
    child_birth_evidence: dict[str, Any] = {}
    for mode, authority in tuple(arms.items()):
        authority.seal_prospective_generation()
        authority = _roundtrip(
            authority, "QUEUE_SEAL", serialization[mode.value]
        )
        authority.open_structural_successor()
        if mode is not SpecializationMode.DISCONNECTED:
            request_id = authority.sealed_request_ids[0]
            consumption = authority.consume_structural_request(
                request_id, CompetenceContextGrowthGenome(genome_seed)
            )
            if consumption.genome_call_count != 1:
                raise RuntimeError("request did not consume exactly one genome call")
            authority = _roundtrip(
                authority, "REQUEST_CONSUMPTION", serialization[mode.value]
            )
            child_id = authority.materialize_deferred_child(request_id)
            child_ids[mode] = child_id
            authority = _roundtrip(
                authority, "CHILD_BIRTH", serialization[mode.value]
            )
            child = authority.states[child_id]
            if (
                child.prospectively_certified or child.support
                or child.successes or child.contradictions
                or child.certification_receipt_ids
            ):
                raise RuntimeError("new child inherited certification evidence")
            escrow = authority.deferred_child_escrows[child_id]
            categories = dict(escrow.categorized_reads)
            category_names = tuple(categories)
            expected_names = (
                "direct_child_matches",
                "parent_discovery_reads",
                "parent_discovery_support",
                "parent_prospective_support",
                "eligibility_reads",
                "contradiction_trigger",
                "transitive_ancestor_reads",
            )
            if category_names != expected_names:
                raise RuntimeError("child escrow evidence categories changed")
            categorized = {
                receipt_id
                for ids in categories.values()
                for receipt_id in ids
            }
            v_birth = set(escrow.discovery_exclusion_receipt_ids)
            visible_at_birth = set(authority.accepted_real_references)
            ordinal_by_id = {
                receipt_id: reference.ordinal
                for receipt_id, reference
                in authority.accepted_real_references.items()
            }
            if v_birth != visible_at_birth or not categorized.issubset(v_birth):
                raise RuntimeError("child escrow is not bounded by complete V_birth")
            categorized_frontier = max(
                (ordinal_by_id[item] for item in categorized), default=-1
            )
            v_birth_frontier = max(ordinal_by_id.values(), default=-1)
            if (
                escrow.nomination_read_frontier != categorized_frontier
                or escrow.birth_frontier != v_birth_frontier
                or escrow.certification_frontier != v_birth_frontier
            ):
                raise RuntimeError("child escrow frontier mismatch")
            child_birth_evidence[mode.value] = {
                "categories_in_exact_order": list(category_names),
                "categories": {
                    name: _id_set_check(ids)
                    for name, ids in categories.items()
                },
                "categorized_reads_subset_of_v_birth": True,
                "discovery_exclusion_equals_complete_v_birth": True,
                "v_birth": _id_set_check(tuple(v_birth)),
                "nomination_read_frontier": categorized_frontier,
                "birth_frontier": v_birth_frontier,
                "certification_frontier_at_birth": v_birth_frontier,
                "fixed_parent_polarity": child.hypothesis.polarity.value,
                "initial_support": child.support,
                "initial_successes": child.successes,
                "initial_contradictions": child.contradictions,
                "initial_certification_receipts": len(
                    child.certification_receipt_ids
                ),
                "initial_decision_influence": False,
            }
        authority.open_prospective_successor()
        arms[mode] = authority

    pre_certification_child_influence = {mode: 0 for mode in ARMS}
    certification_rows: dict[SpecializationMode, tuple[int, ...]] = {}
    for mode in ARMS:
        authority = arms[mode]
        chosen = later_matches[
            "counterexample_blind"
            if mode is SpecializationMode.COUNTEREXAMPLE_BLIND
            else "local_contrast"
        ][:4]
        certification_rows[mode] = chosen
        child_id = child_ids.get(mode)
        for index in chosen:
            pending, receipt, _emission = _process_reference(
                authority, references[index],
                frame_id=f"deferred:{mode.value}:child-support:{index}",
            )
            region_ids[mode.value]["child_certification"].add(
                receipt.interaction_fingerprint
            )
            region_receipt_ids[mode.value]["child_certification"].add(
                receipt.receipt_id
            )
            if (
                child_id is not None
                and not authority.states[child_id].prospectively_certified
                and child_id in pending.pre_outcome_classification.available_cell_ids
            ):
                pre_certification_child_influence[mode] += 1
        if (
            child_id is not None
            and not authority.states[child_id].prospectively_certified
        ):
            raise RuntimeError("child did not earn later prospective certification")
        arms[mode] = _roundtrip(
            authority, "CHILD_CERTIFICATION", serialization[mode.value]
        )

    metrics: dict[str, dict[str, Any]] = {}
    ablation: dict[str, Any] = {}
    for mode, authority in arms.items():
        authority.seal_read_only_evaluation()
        before = authority.continuation_digest()
        matched_rows = later_matches[
            "counterexample_blind"
            if mode is SpecializationMode.COUNTEREXAMPLE_BLIND
            else "local_contrast"
        ]
        evaluation_indexes = (matched_rows[4], 17, 18, 19)
        raw_tp = raw_fp = abstentions = positive_rows = 0
        parent_influence = 0
        last_result = None
        for index in evaluation_indexes:
            result = authority.evaluate_sealed_real(FrameContext(
                f"deferred:{mode.value}:sealed-eval:{index}",
                FrameKind.REAL,
                values={"board": chess.Board(str(references[index]["fen"]))},
            ))
            last_result = result
            failures = _trace_parity_failures(
                result["commitment"].trace, references[index]
            )
            if failures:
                raise RuntimeError(
                    "sealed evaluation parity failed: " + ",".join(failures)
                )
            physical_id = result["commitment"].interaction_fingerprint
            region_ids[mode.value]["evaluation"].add(physical_id)
            predicted = (
                result["classification"].state
                is AvailabilityState.AVAILABLE
            )
            actual = bool(references[index]["actual_completion"])
            positive_rows += int(actual)
            raw_tp += int(predicted and actual)
            raw_fp += int(predicted and not actual)
            abstentions += int(not predicted)
            parent_influence += int(
                parent_id in result["classification"].available_cell_ids
                or parent_id in result["classification"].refuted_cell_ids
            )
        if authority.continuation_digest() != before:
            raise RuntimeError("sealed evaluation mutated authority")
        regions = region_ids[mode.value]
        if any(
            left & right
            for index, left in enumerate(regions.values())
            for right in tuple(regions.values())[index + 1:]
        ):
            raise RuntimeError("canary physical interaction regions overlap")
        receipt_regions = region_receipt_ids[mode.value]
        if any(
            left & right
            for index, left in enumerate(receipt_regions.values())
            for right in tuple(receipt_regions.values())[index + 1:]
        ):
            raise RuntimeError("canary receipt regions overlap")
        request_count = len(authority.request_queue)
        genome_calls = sum(
            item.genome_call_count
            for item in authority.request_consumptions.values()
        )
        metrics[mode.value] = _metric_row(
            mode=mode,
            raw_tp=raw_tp,
            raw_fp=raw_fp,
            abstentions=abstentions,
            positive_rows=positive_rows,
            trigger_false_prediction=trigger_false_prediction[mode],
            post_contradiction_parent_influence=parent_influence,
            pre_certification_child_influence=(
                pre_certification_child_influence[mode]
            ),
            child_certified=(
                mode in child_ids
                and authority.states[
                    child_ids[mode]
                ].prospectively_certified
            ),
            request_count=request_count,
            genome_calls=genome_calls,
        )
        if last_result is not None and mode in child_ids:
            active = dict(authority.states)
            child_id = child_ids[mode]
            del active[child_id]
            ablated = _run_authority_graph(
                active,
                AuthorityMeasurementSnapshot(
                    last_result["commitment"].trace, None
                ),
                accepted_real_references=authority.accepted_real_references,
                specialization_mode=mode,
                lifetime_requested_parent_ids=(
                    authority.lifetime_requested_parent_ids
                ),
            )
            ablation[mode.value] = {
                "parent_structural_commitment_retained": (
                    parent_id in ablated["commitment"]
                ),
                "child_decision_influence_removed": (
                    child_id not in ablated["available"]
                    and child_id not in ablated["refuted"]
                ),
            }

    if metrics[SpecializationMode.LOCAL_CONTRAST.value][
        "genome_call_count"
    ] != metrics[SpecializationMode.COUNTEREXAMPLE_BLIND.value][
        "genome_call_count"
    ]:
        raise RuntimeError("specialization genome budgets diverged")
    if any(
        row["post_contradiction_parent_influence"]
        or row["pre_certification_child_influence"]
        for row in metrics.values()
    ):
        raise RuntimeError("prequential influence boundary failed")
    r0_final = {mode.value: _r0_projection(item.base) for mode, item in arms.items()}
    if any(value != source_r0 for value in r0_final.values()):
        raise RuntimeError("R0 persistent state changed")

    return {
        "schema_version": (
            "native_deferred_specialization_development_canary.v1"
        ),
        "status": "PASS",
        "development_only": True,
        "scientific_claim": False,
        "starting_commit": STARTING_COMMIT,
        "scope": {
            "already_viewed_reference_rows": len(references),
            "fresh_data_opened": False,
            "scientific_runner_created": False,
            "scientific_execution_started": False,
            "regions": [
                "parent_discovery",
                "parent_prospective_and_child_nomination",
                "later_child_certification",
                "sealed_read_only_evaluation",
            ],
            "predetermined_structural_frontier": 69,
        },
        "selected_development_genome_seed": genome_seed,
        "selected_identities": selected_identities,
        "metrics": metrics,
        "evidence_separation": {
            mode: {
                "physical_interactions": {
                    name: _id_set_check(tuple(values))
                    for name, values in rows.items()
                },
                "accepted_receipts": {
                    name: _id_set_check(tuple(values))
                    for name, values
                    in region_receipt_ids[mode].items()
                },
                "all_regions_disjoint": True,
            }
            for mode, rows in region_ids.items()
        },
        "child_birth_evidence": child_birth_evidence,
        "serialization_boundaries": serialization,
        "ablation": ablation,
        "r0_parity": {
            "fields": list(R0_SEMANTIC_FIELDS),
            "all_arms_equal_source": True,
            "source": source_r0,
            "final": r0_final,
        },
        "queue_and_child_capacity": {
            "request_queue_capacity": 192,
            "dormant_child_capacity": 192,
            "focused_request_boundary": {
                "accepted_through": 192,
                "rejected_at": 193,
            },
            "specialization_arm_genome_calls_matched": True,
            "disconnected_dummy_requests": 0,
        },
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
        "metrics": result["metrics"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
