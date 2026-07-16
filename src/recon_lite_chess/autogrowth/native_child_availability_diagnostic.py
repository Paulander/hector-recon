"""Retired-only selectivity decomposition for native R0 child availability."""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import pickle
from time import perf_counter
from typing import Any, Mapping, Sequence

import chess

from recon_lite import FrameContext, FrameKind, LinkType
from recon_lite_hector.learning import OutcomeCalibratedPrototypeGate

from .native_authority_handover import (
    ChildQuery,
    NativeHandoverGenome,
    NativeR0Organism,
    measure_prediction_residual,
)
from .native_authority_lab import (
    NativeAuthorityLabConfig,
    load_retired_r0_build,
)
from .native_child_availability import (
    FailClosedNativeHandoverGenome,
    any_action_confirms_completion,
    observe_query_completion,
    observe_real_child,
    response_with_availability,
)
from .native_intrinsic_curriculum import _fit_r0_gate, _policy_response
from .native_single_graph_curriculum import ROOT_ID, _triplet_keys


@dataclass(frozen=True)
class AvailabilityDiagnosticConfig:
    source_artifact: str = (
        "reports/autogrowth/native_from_scratch/"
        "r0_r1_balanced96_240_seed_20260719_compact.json"
    )
    organism_path: str = "snapshots/autogrowth/native_authority/r0_organism.pkl"
    build_report_path: str = "reports/autogrowth/native_authority/r0_organism_build.json"
    output_path: str = (
        "reports/autogrowth/native_authority/"
        "retired_r0_child_availability_diagnostic.json"
    )
    r1_row_index: int = 0
    shuffle_seed: int = 20260719


def run_retired_availability_diagnostic(
    config: AvailabilityDiagnosticConfig | None = None,
) -> Mapping[str, Any]:
    cfg = config or AvailabilityDiagnosticConfig()
    started = perf_counter()
    build = load_retired_r0_build(NativeAuthorityLabConfig(
        source_artifact=cfg.source_artifact,
        organism_path=cfg.organism_path,
        build_report_path=cfg.build_report_path,
    ))
    organism = build.organism
    organism_before = _learned_digest(organism)
    r1_fen = build.pools.r1_validation[cfg.r1_row_index]
    parent = chess.Board(r1_fen)
    measuring_genome = NativeHandoverGenome()
    base_slots, frames = measuring_genome.query_child_slots(parent, organism)
    slot_count = sum(len(values) for values in base_slots.values())
    if slot_count != 65:
        raise RuntimeError(f"retired diagnostic expected 65 successors, got {slot_count}")

    successor_rows: list[dict[str, Any]] = []
    masks: dict[str, dict[str, tuple[ChildQuery, ...]]] = {
        "any_policy_response": {},
        "policy_success": {},
        "any_action_success": {},
    }
    for action_uci in sorted(base_slots):
        action_queries = base_slots[action_uci]
        after_parent = parent.copy(stack=False)
        after_parent.push(chess.Move.from_uci(action_uci))
        replies = sorted(after_parent.legal_moves, key=lambda move: move.uci())
        any_rows: list[ChildQuery] = []
        policy_rows: list[ChildQuery] = []
        upper_rows: list[ChildQuery] = []
        for reply_index, (reply, query) in enumerate(zip(replies, action_queries, strict=True)):
            successor = after_parent.copy(stack=False)
            successor.push(reply)
            policy_observation = observe_query_completion(
                organism, successor.copy(stack=False), query
            )
            upper = any_action_confirms_completion(organism, successor)
            any_available = bool(query.response.policy_response)
            any_rows.append(response_with_availability(
                organism, query, available=any_available
            ))
            policy_rows.append(ChildQuery(
                response=policy_observation.response,
                actuation=query.actuation, frame_id=query.frame_id,
                persistent_mutation_count=query.persistent_mutation_count,
                effect_attempts=query.effect_attempts,
            ))
            upper_rows.append(response_with_availability(
                organism, query, available=upper
            ))
            successor_rows.append({
                "parent_action": action_uci,
                "black_reply": reply.uci(),
                "reply_index": reply_index,
                "successor_fen": successor.fen(),
                "policy_response": bool(query.response.policy_response),
                "policy_action": (
                    None if query.actuation is None else query.actuation.move_uci
                ),
                "policy_success": policy_observation.completion_confirmed,
                "policy_observed_terminal": policy_observation.observed_terminal,
                "any_action_success": upper,
                "response_strength": query.response.selection_strength,
                "graph_context": _graph_context_audit(organism, successor, query),
            })
        masks["any_policy_response"][action_uci] = tuple(any_rows)
        masks["policy_success"][action_uci] = tuple(policy_rows)
        masks["any_action_success"][action_uci] = tuple(upper_rows)

    masks["shuffled_policy_success"] = _shuffled_mask(
        organism, base_slots, masks["policy_success"], seed=cfg.shuffle_seed
    )
    masks["disconnected_child"] = {
        key: tuple(value) for key, value in masks["policy_success"].items()
    }

    handover = FailClosedNativeHandoverGenome()
    mask_results: dict[str, Any] = {}
    for name in (
        "any_policy_response", "policy_success", "any_action_success",
        "shuffled_policy_success", "disconnected_child",
    ):
        decision = handover.decide_from_available_slots(
            parent, masks[name], frames,
            disconnected=name == "disconnected_child",
        )
        mask_results[name] = _evaluate_parent_decision(
            organism, parent, decision, masks[name]
        )

    retained_rows = _decompose_pool(
        organism, (*build.pools.r0_validation, *build.pools.r0_regression),
        group="retained_r0",
    )
    decoy_rows = _decompose_pool(
        organism, (
            *build.pools.gate_train_decoys,
            *build.pools.gate_validation_decoys,
            *build.pools.gate_regression_decoys,
        ), group="touched_decoy",
    )
    prototype = _prototype_gate_upper_bound(
        organism, build.pools,
        [row["successor_fen"] for row in successor_rows],
        retained_rows, decoy_rows,
    )
    retention_success = sum(int(row["policy_success"]) for row in retained_rows)
    gates = {
        "policy_success_selects_d8c8": (
            mask_results["policy_success"]["selected_parent_action"] == "d8c8"
            and mask_results["policy_success"]["selection_mode"] == "exploit"
        ),
        "policy_success_converts": mask_results["policy_success"]["converted"],
        "one_failed_reply_eliminates_leg": _one_failed_reply_gate(
            organism, parent, masks["policy_success"], frames
        ),
        "no_qualified_leg_zero_exploit_actuator": (
            mask_results["disconnected_child"]["exploit_actuator"] is None
            and mask_results["disconnected_child"]["selection_mode"] == "explore"
        ),
        "shuffled_does_not_convert": not mask_results["shuffled_policy_success"]["converted"],
        "disconnected_does_not_convert": not mask_results["disconnected_child"]["converted"],
        "zero_host_fallback": all(
            row["host_fallback_count"] == 0 for row in mask_results.values()
        ),
        "zero_dream_mutation": all(
            query.persistent_mutation_count == 0
            for values in base_slots.values() for query in values
        ),
        "r0_retention_32_of_32": retention_success == 32,
    }
    policy_converts = bool(
        gates["policy_success_selects_d8c8"]
        and gates["policy_success_converts"]
    )
    result = {
        "schema_version": "native_r0_child_availability_diagnostic.v1",
        "development_only": True,
        "fresh_data_touched": False,
        "learning_or_weight_updates": 0,
        "source_commit_preserved": "5b6d2c1",
        "design_commit_required_before_run": True,
        "design_commit": "8ec994d",
        "duration_seconds": perf_counter() - started,
        "retired_r1_fen": r1_fen,
        "successor_count": slot_count,
        "mask_results": mask_results,
        "gates": gates,
        "policy_success_diagnostic_sufficient": policy_converts,
        "next_action": (
            "write_preregistered_graph_native_competence_envelope_design_only"
            if policy_converts
            else "stop_at_all_reply_choice_or_R0_coverage"
        ),
        "spawning_boundary": "untested_learned_R1_topology_not_connected",
        "credit_boundary": "untested_learned_R1_topology_not_connected",
        "successor_decomposition": successor_rows,
        "retained_r0_decomposition": retained_rows,
        "touched_decoy_decomposition": decoy_rows,
        "prototype_gate_laboratory_upper_bound": prototype,
        "organism_persistent_mutation_count": int(_learned_digest(organism) != organism_before),
    }
    _write_json(cfg.output_path, result)
    return result


def _evaluate_parent_decision(
    organism: NativeR0Organism, parent: chess.Board, decision: Any,
    predicted_slots: Mapping[str, tuple[ChildQuery, ...]],
) -> Mapping[str, Any]:
    selected = decision.actuation.move_uci
    after = parent.copy(stack=False)
    after.push(chess.Move.from_uci(selected))
    reply_rows = []
    for index, reply in enumerate(sorted(after.legal_moves, key=lambda move: move.uci())):
        successor = after.copy(stack=False)
        successor.push(reply)
        observed = observe_real_child(organism, successor)
        predicted = predicted_slots.get(selected, ())
        residual = None
        if index < len(predicted):
            residual = measure_prediction_residual(
                predicted[index].response, observed.response
            )
        reply_rows.append({
            "black_reply": reply.uci(),
            "real_child_action": (
                None if observed.actuation is None else observed.actuation.move_uci
            ),
            "completion_confirmed": observed.completion_confirmed,
            "local_competence_failure": observed.local_competence_failure,
            "observed_terminal": observed.observed_terminal,
            "fabricated_terminal_reward": observed.fabricated_terminal_reward,
            "prediction_residual": residual,
        })
    converted = bool(reply_rows and all(row["completion_confirmed"] for row in reply_rows))
    return {
        "selected_parent_action": selected,
        "selection_mode": decision.selection_mode,
        "exploit_actuator": (
            None if decision.exploit_actuation is None
            else decision.exploit_actuation.move_uci
        ),
        "exploration_actuator": (
            None if decision.exploration_actuation is None
            else decision.exploration_actuation.move_uci
        ),
        "exploit_root_state": decision.exploit_root_state,
        "exploit_actuator_multiplicity": decision.exploit_actuator_multiplicity,
        "host_fallback_count": decision.host_fallback_count,
        "converted": converted,
        "reply_rows": reply_rows,
    }


def _one_failed_reply_gate(
    organism: NativeR0Organism, parent: chess.Board,
    policy_slots: Mapping[str, tuple[ChildQuery, ...]],
    frames: Mapping[tuple[str, int], FrameContext],
) -> bool:
    target = "d8c8"
    queries = list(policy_slots[target])
    if not queries or not all(query.response.available for query in queries):
        return False
    queries[0] = response_with_availability(
        organism, queries[0], available=False
    )
    masked = {key: tuple(value) for key, value in policy_slots.items()}
    masked[target] = tuple(queries)
    decision = FailClosedNativeHandoverGenome().decide_from_available_slots(
        parent, masked, frames
    )
    return not (
        decision.exploit_actuation is not None
        and decision.exploit_actuation.move_uci == target
    )


def _shuffled_mask(
    organism: NativeR0Organism,
    base: Mapping[str, tuple[ChildQuery, ...]],
    policy: Mapping[str, tuple[ChildQuery, ...]], *, seed: int,
) -> dict[str, tuple[ChildQuery, ...]]:
    ordered = sorted(base)
    values = [
        bool(query.response.available)
        for action in ordered for query in policy[action]
    ]
    if len(values) > 1:
        offset = 1 + abs(int(seed)) % (len(values) - 1)
        values = values[offset:] + values[:offset]
    result: dict[str, tuple[ChildQuery, ...]] = {}
    cursor = 0
    for action in ordered:
        rows = []
        for query in base[action]:
            rows.append(response_with_availability(
                organism, query, available=values[cursor]
            ))
            cursor += 1
        result[action] = tuple(rows)
    return result


def _decompose_pool(
    organism: NativeR0Organism, fens: Sequence[str], *, group: str,
) -> list[dict[str, Any]]:
    rows = []
    session = organism.dream_session()
    try:
        for index, fen in enumerate(fens):
            board = chess.Board(fen)
            frame = FrameContext(
                frame_id=f"decomposition:{group}:{index}", kind=FrameKind.VIRTUAL,
                values={"board": board},
            )
            query = session.request(frame)
            observed = observe_query_completion(
                organism, board.copy(stack=False), query
            )
            rows.append({
                "group": group, "index": index, "fen": fen,
                "policy_response": bool(query.response.policy_response),
                "policy_action": (
                    None if query.actuation is None else query.actuation.move_uci
                ),
                "policy_success": observed.completion_confirmed,
                "observed_terminal": observed.observed_terminal,
                "any_action_success": any_action_confirms_completion(organism, board),
                "response_strength": query.response.selection_strength,
                "graph_context": _graph_context_audit(organism, board, query),
            })
    finally:
        session.close()
    return rows


def _graph_context_audit(
    organism: NativeR0Organism, board: chess.Board, query: ChildQuery
) -> Mapping[str, Any]:
    if query.actuation is None:
        return {"active_atoms": [], "active_composites": [], "local_history": {}}
    move = chess.Move.from_uci(query.actuation.move_uci)
    triplet_id = query.actuation.option_identity.rsplit(":", 1)[0]
    keys = _triplet_keys(board, move, key_mode=organism.graph.config.key_mode)
    active = organism.graph._shared_atom_ids_for_keys(keys)
    relevant = sorted(active.intersection(
        organism.graph.triplet_nodes.get(triplet_id, set())
    ))
    atom_rows = []
    for node_id in relevant:
        node = organism.graph.graph.nodes[node_id]
        atom_rows.append({
            "node_id": node_id,
            "role": node.meta.get("role"),
            "terminal_key": node.meta.get("terminal_key"),
            "local_weight": float(node.meta.get("local_weight", 0.0)),
            "activation_count": int(node.meta.get("activation_count", 0)),
            "confirm_count": int(node.meta.get("confirm_count", 0)),
            "negative_confirm_count": int(node.meta.get("negative_confirm_count", 0)),
            "false_positive_count": int(node.meta.get("false_positive_count", 0)),
            "request_exposures": int(node.meta.get("request_exposures", 0)),
        })
    composites = []
    for composite_id, members in organism.graph.composite_member_ids.items():
        if triplet_id in organism.graph.composite_triplets.get(composite_id, set()):
            composites.append({
                "composite_id": composite_id,
                "members": list(members),
                "all_members_active": set(members).issubset(active),
                "state": organism.graph.composite_cells[composite_id].state.name,
            })
    triplet = organism.graph.graph.nodes.get(triplet_id)
    root_edge = organism.graph.graph.get_edge(ROOT_ID, triplet_id, LinkType.SUB)
    history = {} if triplet is None else {
        "triplet_id": triplet_id,
        "root_weight": 0.0 if root_edge is None else float(root_edge.w),
        "local_weight": float(triplet.meta.get("local_weight", 0.0)),
        "confirm_count": int(triplet.meta.get("confirm_count", 0)),
        "negative_confirm_count": int(triplet.meta.get("negative_confirm_count", 0)),
        "request_exposures": int(triplet.meta.get("request_exposures", 0)),
    }
    return {
        "selected_option_identity": query.actuation.option_identity,
        "selected_response_strength": query.actuation.activation,
        "active_atoms": atom_rows,
        "active_composites": composites,
        "local_history": history,
    }


def _prototype_gate_upper_bound(
    organism: NativeR0Organism, pools: Any, successor_fens: Sequence[str],
    retained_rows: Sequence[Mapping[str, Any]],
    decoy_rows: Sequence[Mapping[str, Any]],
) -> Mapping[str, Any]:
    gate, selection = _fit_r0_gate(
        organism.graph,
        train_positive=pools.r0_train,
        train_negative=pools.gate_train_decoys,
        validation_positive=pools.r0_validation,
        validation_negative=pools.gate_validation_decoys,
        regression_positive=pools.r0_regression,
        regression_negative=pools.gate_regression_decoys,
    )
    groups = {
        "retired_successors": list(successor_fens),
        "retained_r0": [str(row["fen"]) for row in retained_rows],
        "touched_decoy": [str(row["fen"]) for row in decoy_rows],
    }
    result = {}
    for name, fens in groups.items():
        rows = []
        for fen in fens:
            response = _policy_response(
                organism.graph, chess.Board(fen), observe_outcome=False,
                allowed_triplets=organism.frozen_triplet_ids,
            )
            probability = gate.probability(response["features"])
            rows.append({"fen": fen, "probability": probability,
                         "above_threshold": probability >= gate.threshold})
        result[name] = {
            "count": len(rows),
            "above_threshold_count": sum(int(row["above_threshold"]) for row in rows),
            "rows": rows,
        }
    return {
        "runtime_connected": False,
        "host_weighted_selector_used_only_here": True,
        "gate_mature": gate.mature,
        "threshold": gate.threshold,
        "selection": selection,
        "groups": result,
    }


def _learned_digest(organism: NativeR0Organism) -> str:
    nodes = tuple(
        (node_id, float(node.meta.get("local_weight", 0.0)),
         node.meta.get("tier"), node.meta.get("stem_cell_state"))
        for node_id, node in sorted(organism.graph.graph.nodes.items())
    )
    edges = tuple(
        (edge.src, edge.dst, edge.ltype.name, float(edge.w),
         edge.meta.get("tier"), edge.meta.get("stem_cell_state"))
        for edge in organism.graph.graph.edges
    )
    payload = (
        nodes, edges, tuple(sorted(organism.graph.triplet_ids)),
        organism.credit.snapshot()["states"],
    )
    return hashlib.sha256(
        pickle.dumps(payload, protocol=pickle.HIGHEST_PROTOCOL)
    ).hexdigest()


def _write_json(path: str | Path, value: Mapping[str, Any]) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
