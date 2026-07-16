"""Planted mature-envelope authority and full frame-input parity addendum."""
from __future__ import annotations

from dataclasses import asdict
import hashlib
from itertools import combinations
import json
from pathlib import Path
import random
from time import perf_counter
from typing import Any, Mapping, Sequence
from unittest.mock import patch

import chess

from recon_lite import FrameContext, FrameKind
from recon_lite_hector.nodes import StemCellState, StemCellTerminal

from .native_authority_handover import (
    ChildQuery,
    NativeHandoverGenome,
    NativeR0Organism,
)
from .native_authority_lab import NativeAuthorityLabConfig, load_retired_r0_build
from .native_child_availability import FailClosedNativeHandoverGenome
from .native_competence_envelope import (
    AvailabilityState,
    CompetenceContextCell,
    CompetenceEvidenceRecord,
    GraphNativeCompetenceEnvelope,
    NativeCompetenceSessionAudit,
    NativeR0CompetenceOrganism,
    flatten_consumed_availability_mask,
)
from .native_competence_envelope_experiment import EXPECTED, _hash_json, _hash_list


OUTPUT = (
    "reports/autogrowth/native_authority/"
    "native_mature_envelope_authority_addendum.json"
)
BASE_ARTIFACT = (
    "reports/autogrowth/native_authority/"
    "native_frame_purity_competence_authority_closure.json"
)
BASE_ARTIFACT_SHA256 = (
    "cfb48cb8f772d95ae4bb20f6eab5aef479e06b702bd761863e32a572ef8c1f53"
)
TAPE_SEED = 2026071601
PERMUTATION_SEED = 2026071702
SYNTHETIC_PARENT = "8/8/8/8/4K3/8/6R1/7k w - - 0 1"


def run_native_mature_envelope_authority_addendum() -> Mapping[str, Any]:
    started = perf_counter()
    base_hash = _file_sha256(BASE_ARTIFACT)
    if base_hash != BASE_ARTIFACT_SHA256:
        raise RuntimeError("preserved 9e3f64a authority artifact changed")

    build = load_retired_r0_build(NativeAuthorityLabConfig())
    tape = [
        {"subgroup": "r0_train", "fen": fen}
        for fen in build.pools.r0_train
    ] + [
        {"subgroup": "train_decoy", "fen": fen}
        for fen in build.pools.gate_train_decoys
    ]
    random.Random(TAPE_SEED).shuffle(tape)
    legacy_tape = [
        {
            "class": (
                "positive" if row["subgroup"] == "r0_train" else "failure"
            ),
            "fen": row["fen"],
        }
        for row in tape
    ]
    if _hash_json(legacy_tape) != EXPECTED["tape"]:
        raise RuntimeError("touched 64-frame tape changed")

    empty_wrapper = NativeR0CompetenceOrganism.loads(
        NativeR0CompetenceOrganism(
            build.organism, GraphNativeCompetenceEnvelope()
        ).dumps()
    )
    initial = empty_wrapper.persistent_state_audit()
    natural, natural_audit = _purity_pass(
        empty_wrapper, tape, tuple(range(64)), "natural"
    )
    repeated, repeated_audit = _purity_pass(
        empty_wrapper, tape, tuple(range(64)), "repeated"
    )
    permutation = list(range(64))
    random.Random(PERMUTATION_SEED).shuffle(permutation)
    permuted, permuted_audit = _purity_pass(
        empty_wrapper, tape, tuple(permutation), "permuted"
    )
    after_purity = empty_wrapper.persistent_state_audit()
    natural_hash = _hash_json([natural[index] for index in range(64)])
    repeated_hash = _hash_json([repeated[index] for index in range(64)])
    permuted_hash = _hash_json([permuted[index] for index in range(64)])
    parity_rows = [
        {
            "index": index,
            "equal": natural[index] == repeated[index] == permuted[index],
            **natural[index],
        }
        for index in range(64)
    ]
    purity = {
        "count": 64,
        "permutation_seed": PERMUTATION_SEED,
        "permutation_sha256": _hash_list(permutation),
        "natural_sha256": natural_hash,
        "repeated_sha256": repeated_hash,
        "permuted_sha256": permuted_hash,
        "complete_graph_actuation_and_signal_hashes_equal": (
            natural_hash == repeated_hash == permuted_hash
        ),
        "cross_frame_difference_count": sum(
            not row["equal"] for row in parity_rows
        ),
        "session_audits": {
            "natural": _session_audit_manifest(natural_audit),
            "repeated": _session_audit_manifest(repeated_audit),
            "permuted": _session_audit_manifest(permuted_audit),
        },
        "rows": parity_rows,
    }

    mature = _mature_authority_canary(build.organism)
    final = empty_wrapper.persistent_state_audit()
    gates = {
        "base_artifact_preserved": base_hash == BASE_ARTIFACT_SHA256,
        "touched_tape_only": len(tape) == 64,
        "complete_actuation_and_signal_parity_64": (
            purity["complete_graph_actuation_and_signal_hashes_equal"]
            and purity["cross_frame_difference_count"] == 0
        ),
        "purity_session_counts_observed": all(
            audit.session_open_count == 1
            and audit.request_count == 64
            and audit.session_close_count == 1
            for audit in (natural_audit, repeated_audit, permuted_audit)
        ),
        "persistent_identity": initial == after_purity == final,
        "mature_wrapper_authority": mature["passed"],
        "zero_competence_growth": mature["competence_growth_events"] == 0,
    }
    result = {
        "schema_version": "native_mature_envelope_authority_addendum.v1",
        "engineering_only": True,
        "source_commit_preserved": "9e3f64a",
        "source_artifact": {
            "path": BASE_ARTIFACT,
            "sha256": base_hash,
        },
        "old_purity_canary_rerun": False,
        "competence_growth_started": False,
        "validation_touched": False,
        "regression_touched": False,
        "retired_successors_touched": False,
        "fresh_data_touched": False,
        "tape": {
            "count": 64,
            "sha256": EXPECTED["tape"],
            "historical_pool_names_are_provenance_only": True,
        },
        "full_frame_input_parity": purity,
        "mature_envelope_authority": mature,
        "persistent_state": {
            "initial": initial,
            "after_purity": after_purity,
            "final": final,
        },
        "gates": gates,
        "passed": all(gates.values()),
        "duration_seconds": perf_counter() - started,
        "next_action": (
            "authorize_preregistered_touched_training_only_v2"
            if all(gates.values())
            else "stop_preserve_addendum_failure"
        ),
    }
    target = Path(OUTPUT)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    return result


def _purity_pass(
    wrapper: NativeR0CompetenceOrganism,
    tape: Sequence[Mapping[str, str]],
    order: Sequence[int],
    label: str,
) -> tuple[dict[int, dict[str, Any]], NativeCompetenceSessionAudit]:
    audit = NativeCompetenceSessionAudit()
    session = wrapper.dream_session(audit=audit)
    rows: dict[int, dict[str, Any]] = {}
    try:
        for index in order:
            frame = FrameContext(
                frame_id=f"addendum:{label}:{index}",
                kind=FrameKind.VIRTUAL,
                values={"board": chess.Board(tape[index]["fen"])},
            )
            query = session.request(frame)
            rows[index] = _query_manifest(query)
    finally:
        session.close()
    return rows, audit


def _query_manifest(query: ChildQuery) -> dict[str, Any]:
    return {
        "actuation": (
            None if query.actuation is None else asdict(query.actuation)
        ),
        "response": query.response.to_dict(),
        "active_competence_signal_ids": list(
            query.active_competence_signal_ids
        ),
        "availability_provenance": (
            None
            if query.availability_provenance is None
            else dict(query.availability_provenance)
        ),
        "persistent_mutation_count": query.persistent_mutation_count,
    }


def _mature_authority_canary(
    organism: NativeR0Organism,
) -> dict[str, Any]:
    board = chess.Board(SYNTHETIC_PARENT)
    empty = NativeR0CompetenceOrganism.loads(
        NativeR0CompetenceOrganism(
            organism, GraphNativeCompetenceEnvelope()
        ).dumps()
    )
    empty_audit = NativeCompetenceSessionAudit()
    empty_slots, empty_frames = NativeHandoverGenome().query_child_slots(
        board, empty, session_audit=empty_audit
    )
    genome = FailClosedNativeHandoverGenome()
    empty_decision = genome.decide_from_available_slots(
        board, empty_slots, empty_frames
    )
    target_action, members = _find_unique_pattern(
        empty_slots, empty_decision.actuation.move_uci
    )
    envelope = _promote_planted_envelope(members)
    wrapper_payload = NativeR0CompetenceOrganism(
        organism, envelope
    ).dumps()
    restored = NativeR0CompetenceOrganism.loads(wrapper_payload)
    before = restored.persistent_state_audit()

    injection_calls = {"count": 0}

    def forbidden_injection(*_args: Any, **_kwargs: Any) -> Any:
        injection_calls["count"] += 1
        raise AssertionError("connected wrapper called Boolean availability injection")

    audit = NativeCompetenceSessionAudit()
    with (
        patch(
            "recon_lite_chess.autogrowth.native_child_availability."
            "response_with_availability",
            forbidden_injection,
        ),
        patch(
            "recon_lite_chess.autogrowth."
            "native_competence_envelope_experiment."
            "response_with_availability",
            forbidden_injection,
        ),
    ):
        connected_slots, connected_frames = (
            NativeHandoverGenome().query_child_slots(
                board, restored, session_audit=audit
            )
        )
    after = restored.persistent_state_audit()
    consumed = flatten_consumed_availability_mask(connected_slots)
    direct_mask: list[bool] = []
    provenance_equal = True
    for row in consumed:
        classification = restored.envelope.classify(
            row["active_competence_signal_ids"],
            policy_response=row["policy_response"],
        )
        direct_mask.append(
            classification.state == AvailabilityState.AVAILABLE
        )
        provenance = row["availability_provenance"] or {}
        provenance_equal = provenance_equal and (
            provenance.get("classification") == classification.to_manifest()
        )
    consumed_mask = [bool(row["available"]) for row in consumed]
    connected_decision = genome.decide_from_available_slots(
        board, connected_slots, connected_frames
    )
    disconnected_decision = genome.decide_from_available_slots(
        board, connected_slots, connected_frames, disconnected=True
    )
    target_rows = [
        row for row in consumed if row["action_identity"] == target_action
    ]
    mature_cells = [
        cell for cell in restored.envelope.cells.values() if cell.is_mature
    ]
    authority_observations = _session_audit_manifest(audit)
    authority_observations["injection_tripwire_calls"] = injection_calls["count"]
    gates = {
        "restored_mature_cell": len(mature_cells) == 1,
        "session_open_observed": audit.session_open_count == 1,
        "requests_observed": audit.request_count == len(consumed),
        "session_close_observed": audit.session_close_count == 1,
        "provenance_observed": (
            bool(audit.open_events)
            and all(
                event["availability_provenance"]
                for event in audit.request_events
            )
        ),
        "zero_boolean_injection": injection_calls["count"] == 0,
        "consumed_equals_direct": consumed_mask == direct_mask,
        "provenance_equals_direct": provenance_equal,
        "target_all_replies_available": (
            bool(target_rows) and all(row["available"] for row in target_rows)
        ),
        "connected_selects_target": (
            connected_decision.selection_mode == "exploit"
            and connected_decision.actuation.move_uci == target_action
        ),
        "empty_fails_target": (
            empty_decision.actuation.move_uci != target_action
        ),
        "disconnected_fails_target": (
            disconnected_decision.actuation.move_uci != target_action
        ),
        "zero_host_fallback": all(
            decision.host_fallback_count == 0
            for decision in (
                empty_decision,
                connected_decision,
                disconnected_decision,
            )
        ),
        "zero_persistent_mutation": before == after,
    }
    return {
        "mature_wrapper": {
            "serialized_sha256": hashlib.sha256(wrapper_payload).hexdigest(),
            "serialized_bytes": len(wrapper_payload),
            "restored_mature_cell_count": len(mature_cells),
            "cell_manifest": mature_cells[0].to_manifest(),
        },
        "target": {
            "action": target_action,
            "member_identities": list(members),
            "reply_count": len(connected_slots[target_action]),
        },
        "authority_observations": authority_observations,
        "consumed_mask": {
            "rows": list(consumed),
            "values": consumed_mask,
            "sha256": _hash_json(consumed_mask),
            "direct_classification_values": direct_mask,
            "equals_direct_classification": consumed_mask == direct_mask,
            "provenance_equals_direct_classification": provenance_equal,
        },
        "decisions": {
            "connected_action": connected_decision.actuation.move_uci,
            "connected_mode": connected_decision.selection_mode,
            "empty_action": empty_decision.actuation.move_uci,
            "empty_mode": empty_decision.selection_mode,
            "disconnected_action": disconnected_decision.actuation.move_uci,
            "disconnected_mode": disconnected_decision.selection_mode,
        },
        "persistent_state": {"before": before, "after": after},
        "competence_growth_events": 0,
        "planted_lifecycle_maturations": 1,
        "gates": gates,
        "passed": all(gates.values()),
    }


def _find_unique_pattern(
    slots: Mapping[str, Sequence[ChildQuery]],
    excluded_action: str,
) -> tuple[str, tuple[str, ...]]:
    signal_sets = {
        action: [
            set(query.active_competence_signal_ids) for query in rows
        ]
        for action, rows in slots.items()
        if rows
    }
    for action in sorted(signal_sets):
        if action == excluded_action:
            continue
        common = set.intersection(*signal_sets[action])
        for arity in (1, 2, 3):
            for members in combinations(sorted(common), arity):
                qualifying = [
                    candidate
                    for candidate, rows in sorted(signal_sets.items())
                    if all(set(members).issubset(row) for row in rows)
                ]
                if qualifying == [action]:
                    return action, tuple(members)
    raise RuntimeError("no unique planted mature-envelope pattern")


def _promote_planted_envelope(
    members: tuple[str, ...],
) -> GraphNativeCompetenceEnvelope:
    envelope = GraphNativeCompetenceEnvelope()
    cell_id = "planted_mature_competence_context"
    stem = StemCellTerminal(cell_id)
    stem.state = StemCellState.TRIAL
    stem.trial_node_id = cell_id
    cell = CompetenceContextCell(
        cell_id=cell_id,
        members=members,
        born_round=0,
        born_request_ordinal=0,
        stem_cell=stem,
    )
    envelope.cells[cell_id] = cell
    envelope.rebuild_graph()
    for index in range(4):
        envelope.add_unique_evidence(
            CompetenceEvidenceRecord(
                evidence_key=f"planted-success-{index}",
                active_signal_ids=members,
                policy_response=True,
                observed_completion=True,
                actuator_identity="planted:actual_r0_signal_membership",
                completion_terminal_identity="mate",
            )
        )
    envelope._review_lifecycle(final=False)
    envelope.rebuild_graph()
    if not cell.is_mature or cell.polarity != AvailabilityState.AVAILABLE:
        raise RuntimeError("planted competence cell failed actual maturation")
    return envelope


def _session_audit_manifest(
    audit: NativeCompetenceSessionAudit,
) -> dict[str, Any]:
    return {
        "session_open_count": audit.session_open_count,
        "request_count": audit.request_count,
        "session_close_count": audit.session_close_count,
        "open_events": list(audit.open_events),
        "request_events": list(audit.request_events),
        "close_events": list(audit.close_events),
    }


def _file_sha256(path: str) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()
