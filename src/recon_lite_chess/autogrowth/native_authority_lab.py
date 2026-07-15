"""Laboratory-only builder and retired R1 development evaluation."""
from __future__ import annotations

from dataclasses import asdict, dataclass, fields
import copy
import hashlib
import json
from pathlib import Path
from time import perf_counter
from typing import Any, Mapping, Sequence

import chess

from recon_lite_hector.learning import IntrinsicCreditEngine, Responsibility

from .native_authority_handover import (
    FrozenCompetenceProvenance,
    NativeHandoverGenome,
    NativeR0Organism,
    measure_prediction_residual,
    native_authority_tripwires,
    run_dream_firewall_canary,
)
from .native_intrinsic_curriculum import (
    R0_COMPETENCE_ID,
    R1_COMPETENCE_ID,
    NativeIntrinsicCurriculumConfig,
    _build_pools,
    _credit_config,
    _evaluate_r0,
    _graph_config,
    _hash_json,
    _train_r0,
)
from .native_single_graph_curriculum import NativeReConKRKGraph


@dataclass(frozen=True)
class NativeAuthorityLabConfig:
    source_artifact: str = (
        "reports/autogrowth/native_from_scratch/"
        "r0_r1_balanced96_240_seed_20260719_compact.json"
    )
    organism_path: str = "snapshots/autogrowth/native_authority/r0_organism.pkl"
    build_report_path: str = "reports/autogrowth/native_authority/r0_organism_build.json"
    result_path: str = "reports/autogrowth/native_authority/retired_r1_handover_development.json"
    train_rows: int = 8
    evaluation_rows: int = 8
    train_epochs: int = 1
    shuffle_seed: int = 20260719


@dataclass(frozen=True)
class NativeAuthorityBuildResult:
    organism: NativeR0Organism
    pools: Any
    report: Mapping[str, Any]


def load_retired_r0_build(config: NativeAuthorityLabConfig) -> NativeAuthorityBuildResult:
    """Load the frozen organism while reconstructing only the touched pool manifest."""

    artifact = json.loads(Path(config.source_artifact).read_text(encoding="utf-8"))
    pools = _build_pools(_config_from_prior_artifact(artifact))
    if pools.manifest()["combined_sha256"] != artifact["pool_manifest"]["combined_sha256"]:
        raise RuntimeError("retired pool reconstruction hash mismatch")
    report = json.loads(Path(config.build_report_path).read_text(encoding="utf-8"))
    organism = NativeR0Organism.load(config.organism_path)
    return NativeAuthorityBuildResult(organism=organism, pools=pools, report=report)


def build_retired_r0_organism(config: NativeAuthorityLabConfig) -> NativeAuthorityBuildResult:
    started = perf_counter()
    source = Path(config.source_artifact)
    artifact = json.loads(source.read_text(encoding="utf-8"))
    cfg = _config_from_prior_artifact(artifact)
    pools = _build_pools(cfg)
    expected_manifest = artifact["pool_manifest"]["combined_sha256"]
    actual_manifest = pools.manifest()["combined_sha256"]
    if actual_manifest != expected_manifest:
        raise RuntimeError("retired pool reconstruction hash mismatch")

    graph = NativeReConKRKGraph(config=_graph_config(cfg))
    credit = IntrinsicCreditEngine(_credit_config(cfg))
    credit.register(R0_COMPETENCE_ID, mature=False, hierarchy_depth=0)
    initial = graph.learned_state_audit()
    if initial["triplet_count"] != 0:
        raise RuntimeError("R0 reproduction did not start from an empty learned graph")
    training = _train_r0(
        graph,
        credit,
        pools.r0_train,
        pools.r0_validation,
        pools.r0_regression,
        config=cfg,
    )
    validation = _evaluate_r0(graph, pools.r0_validation, max_samples=cfg.max_samples)
    regression = _evaluate_r0(graph, pools.r0_regression, max_samples=cfg.max_samples)
    if validation["accuracy"] != 1.0 or regression["accuracy"] != 1.0:
        raise RuntimeError("retired R0 reproduction failed the prior 100% gate")
    credit.set_mature(R0_COMPETENCE_ID)
    disabled = _evaluate_r0(
        graph,
        pools.r0_validation,
        masked_triplets=set(graph.triplet_ids),
        max_samples=0,
    )["accuracy"]
    intervention = credit.record_paired_intervention(
        R0_COMPETENCE_ID,
        enabled_return=validation["accuracy"],
        disabled_return=disabled,
    )
    consolidation = credit.consolidate((R0_COMPETENCE_ID,))
    maturation = graph.mature_existing_graph()
    freeze = graph.freeze_existing_parameters(reason="retired_R0_authority_extraction")
    provenance = FrozenCompetenceProvenance.from_credit(credit, R0_COMPETENCE_ID)
    organism = NativeR0Organism(
        graph=graph,
        credit=credit,
        provenance=provenance,
        frozen_triplet_ids=frozenset(graph.triplet_ids),
        source_manifest={
            "source_artifact": str(source),
            "source_sha256": _file_sha256(source),
            "pool_manifest_sha256": actual_manifest,
            "development_or_retired_only": True,
        },
    )
    metadata = organism.save(config.organism_path)
    restored = NativeR0Organism.load(config.organism_path)
    parity_rows = []
    for fen in pools.r0_regression:
        board = chess.Board(fen)
        original = organism.emit_action(board)
        loaded = restored.emit_action(board)
        parity_rows.append({
            "fen": fen,
            "original": None if original is None else original.move_uci,
            "loaded": None if loaded is None else loaded.move_uci,
            "equal": original == loaded,
        })
    report = {
        "schema_version": "native_r0_authority_build.v1",
        "development_only": True,
        "fresh_data_touched": False,
        "duration_seconds": perf_counter() - started,
        "source_artifact": str(source),
        "source_pool_manifest_expected": expected_manifest,
        "source_pool_manifest_reconstructed": actual_manifest,
        "initial_graph": initial,
        "training": training,
        "validation": validation,
        "regression": regression,
        "paired_intervention": asdict(intervention),
        "consolidation": consolidation,
        "maturation": maturation,
        "freeze": freeze,
        "provenance": asdict(provenance),
        "organism_artifact": {"path": config.organism_path, **dict(metadata)},
        "serialization_parity": {
            "row_count": len(parity_rows),
            "all_equal": all(row["equal"] for row in parity_rows),
            "rows": parity_rows,
        },
        "trainer_required_for_loaded_inference": False,
    }
    _write_json(config.build_report_path, report)
    return NativeAuthorityBuildResult(organism=organism, pools=pools, report=report)


def run_retired_handover_development(
    build: NativeAuthorityBuildResult,
    config: NativeAuthorityLabConfig,
) -> Mapping[str, Any]:
    started = perf_counter()
    train_fens = tuple(build.pools.r1_train[: max(0, config.train_rows)])
    evaluation_fens = tuple(
        (*build.pools.r1_validation, *build.pools.r1_regression)
    )[: max(0, config.evaluation_rows)]
    r0_retention_fens = tuple(
        (*build.pools.r0_validation, *build.pools.r0_regression)
    )
    arms: dict[str, Any] = {}
    measured: dict[str, tuple[Any, Any]] = {}
    measurement_genome = NativeHandoverGenome()
    with native_authority_tripwires() as tripwires:
        for fen in dict.fromkeys((*train_fens, *evaluation_fens)):
            measured[fen] = measurement_genome.query_child_slots(
                chess.Board(fen),
                build.organism,
            )
        for arm in ("actual_child", "disconnected", "shuffled"):
            organism = copy.deepcopy(build.organism)
            arms[arm] = _run_arm(
                organism,
                arm=arm,
                train_fens=train_fens,
                evaluation_fens=evaluation_fens,
                retention_fens=r0_retention_fens,
                measured=measured,
                epochs=config.train_epochs,
                shuffle_seed=config.shuffle_seed,
            )
    action_rows = {
        arm: {row["fen"]: row["selected_first"] for row in payload["evaluation"]["rows"]}
        for arm, payload in arms.items()
    }
    discordance = {
        control: sum(
            action_rows["actual_child"].get(fen) != action_rows[control].get(fen)
            for fen in action_rows["actual_child"]
        )
        for control in ("disconnected", "shuffled")
    }
    full_rate = arms["actual_child"]["evaluation"]["conversion_rate"]
    disconnected_rate = arms["disconnected"]["evaluation"]["conversion_rate"]
    shuffled_rate = arms["shuffled"]["evaluation"]["conversion_rate"]
    gate = {
        "graph_owned_real_actions_100_percent": all(
            payload["authority"]["graph_owned_action_fraction"] == 1.0
            for payload in arms.values()
        ),
        "exactly_one_actuator": all(
            payload["authority"]["actuator_multiplicity_failures"] == 0
            for payload in arms.values()
        ),
        "zero_host_fallback": all(
            payload["authority"]["host_fallback_count"] == 0
            for payload in arms.values()
        ),
        "zero_planted_or_oracle_child_responses": all(
            payload["authority"]["planted_response_count"] == 0
            for payload in arms.values()
        ),
        "zero_persistent_dream_leakage": all(
            payload["authority"]["persistent_dream_mutation_count"] == 0
            for payload in arms.values()
        ),
        "nonzero_child_caused_action_changes": all(value > 0 for value in discordance.values()),
        "full_directionally_better_than_both_controls": (
            full_rate > disconnected_rate and full_rate > shuffled_rate
        ),
        "exact_r0_retention": all(
            payload["r0_retention"]["accuracy"] == 1.0
            for payload in arms.values()
        ),
        "empty_to_grown_r1_topology": all(
            payload["topology"]["initial_r1_triplet_count"] == 0
            and payload["topology"]["final_r1_triplet_count"] > 0
            for payload in arms.values()
        ),
    }
    passed = all(gate.values())
    availability_rows = arms["actual_child"]["evaluation"]["rows"]
    child_availability_nonselective = bool(
        availability_rows
        and all(
            row["all_reply_confirmed_action_count"]
            == row["actions_with_required_replies"]
            and row["actions_with_required_replies"] > 1
            for row in availability_rows
        )
    )
    if passed:
        binding_boundary = None
    elif not gate["exactly_one_actuator"] or not gate["graph_owned_real_actions_100_percent"]:
        binding_boundary = "graph_choice"
    elif child_availability_nonselective:
        binding_boundary = "actual_child_availability"
    elif not gate["nonzero_child_caused_action_changes"]:
        binding_boundary = "all_reply_composition"
    elif not gate["empty_to_grown_r1_topology"]:
        binding_boundary = "spawning"
    else:
        binding_boundary = "credit"
    canary = run_dream_firewall_canary(
        build.organism,
        chess.Board(build.pools.r0_regression[0]),
    )
    result = {
        "schema_version": "native_r0_r1_authority_development.v1",
        "development_only": True,
        "confirmation_claim": False,
        "fresh_data_touched": False,
        "source_artifact": config.source_artifact,
        "organism_artifact": config.organism_path,
        "duration_seconds": perf_counter() - started,
        "rows": {
            "train_count": len(train_fens),
            "evaluation_count": len(evaluation_fens),
            "r0_retention_count": len(r0_retention_fens),
            "train_sha256": _hash_json(train_fens),
            "evaluation_sha256": _hash_json(evaluation_fens),
            "source_pool_manifest_sha256": build.pools.manifest()["combined_sha256"],
            "all_rows_previously_touched": True,
        },
        "authority_tripwires": dict(tripwires),
        "dream_firewall_canary": asdict(canary),
        "arms": arms,
        "paired_action_discordance": discordance,
        "development_gate": gate,
        "passed": passed,
        "binding_boundary": binding_boundary,
        "actual_child_availability_nonselective": child_availability_nonselective,
        "advance": (
            "draft_fresh_multiseed_R1_preregistration_do_not_run"
            if passed
            else f"preserve_failure_binding_boundary:{binding_boundary}"
        ),
    }
    _write_json(config.result_path, result)
    return result


def _run_arm(
    organism: NativeR0Organism,
    *,
    arm: str,
    train_fens: Sequence[str],
    evaluation_fens: Sequence[str],
    retention_fens: Sequence[str],
    measured: Mapping[str, tuple[Any, Any]],
    epochs: int,
    shuffle_seed: int,
) -> Mapping[str, Any]:
    credit = organism.credit
    if R1_COMPETENCE_ID not in credit.states:
        credit.register(R1_COMPETENCE_ID, mature=False, hierarchy_depth=1)
    initial_triplets = set(organism.graph.triplet_ids)
    genome = NativeHandoverGenome()
    training_rows = []
    graph_actions = host_fallbacks = multiplicity_failures = planted = dream_mutations = 0
    for epoch in range(max(0, epochs)):
        for fen in train_fens:
            board = chess.Board(fen)
            measured_slots, measured_frames = measured[fen]
            decision = genome.decide_from_measured_slots(
                board,
                measured_slots,
                measured_frames,
                arm=arm,
                shuffle_seed=shuffle_seed,
            )
            graph_actions += int(decision.actuation.graph_owned)
            host_fallbacks += decision.host_fallback_count
            multiplicity_failures += int(decision.actuator_multiplicity != 1)
            planted += decision.planted_response_count
            dream_mutations += sum(
                query.persistent_mutation_count
                for queries in decision.response_slots.values()
                for query in queries
            )
            move = chess.Move.from_uci(decision.actuation.move_uci)
            before_triplets = set(organism.graph.triplet_ids)
            after_first = board.copy(stack=False)
            after_first.push(move)
            terminal = _observed_terminal(after_first)
            observed_query = None
            residual = None
            actual_reply = None
            successor_ids: tuple[str, ...] = ()
            if terminal is None:
                replies = sorted(after_first.legal_moves, key=lambda item: item.uci())
                if replies:
                    reply = replies[0]
                    actual_reply = reply.uci()
                    successor = after_first.copy(stack=False)
                    successor.push(reply)
                    terminal = _observed_terminal(successor)
                    if terminal is None:
                        reply_index = replies.index(reply)
                        observed_slots = measured_slots.get(move.uci(), ())
                        observed_query = (
                            observed_slots[reply_index]
                            if reply_index < len(observed_slots)
                            else None
                        )
                        if observed_query is not None and observed_query.response.confirmed:
                            successor_ids = (R0_COMPETENCE_ID,)
                        imagined_slots = decision.response_slots.get(move.uci(), ())
                        if reply_index < len(imagined_slots):
                            imagined = imagined_slots[reply_index].response
                            if (
                                imagined.grounded
                                and observed_query is not None
                                and observed_query.response.grounded
                            ):
                                residual = measure_prediction_residual(
                                    imagined,
                                    observed_query.response,
                                )
            event = credit.transition(
                R1_COMPETENCE_ID,
                responsibilities=(Responsibility(R1_COMPETENCE_ID),),
                successor_ids=successor_ids,
                terminal_kind=terminal,
                real_step=True,
                prediction_override=decision.actuation.activation,
            )
            triplet_id = organism.graph.apply_intrinsic_td(
                board,
                move,
                td_error=event.td_error,
                stage_diagnostic="native_R1_authority_development",
            )
            born = triplet_id not in before_triplets
            training_rows.append({
                "epoch": epoch + 1,
                "fen": fen,
                "selected_first": move.uci(),
                "actual_black_reply": actual_reply,
                "observed_terminal": terminal,
                "observed_child_confirmed": bool(
                    observed_query is not None and observed_query.response.confirmed
                ),
                "prediction_residual": residual,
                "td_error": event.td_error,
                "triplet_id": triplet_id,
                "r1_triplet_born": born,
                "stem_cell_transition": "ABSENT->TRIAL" if born else "TRIAL->TRIAL",
            })
    evaluation = _evaluate_r1(
        organism,
        evaluation_fens,
        measured=measured,
        arm=arm,
        shuffle_seed=shuffle_seed,
    )
    retention = _evaluate_r0_retention(organism, retention_fens)
    host_fallbacks += sum(row["host_fallback_count"] for row in evaluation["rows"])
    multiplicity_failures += sum(
        int(row["actuator_multiplicity"] != 1) for row in evaluation["rows"]
    )
    graph_actions += len(evaluation["rows"])
    final_r1 = set(organism.graph.triplet_ids) - initial_triplets
    total_real = len(training_rows) + len(evaluation["rows"])
    return {
        "arm": arm,
        "training": {
            "epochs": epochs,
            "episode_count": len(training_rows),
            "rows": training_rows,
        },
        "evaluation": evaluation,
        "r0_retention": retention,
        "authority": {
            "graph_owned_action_fraction": (0.0 if total_real == 0 else graph_actions / total_real),
            "host_fallback_count": host_fallbacks,
            "actuator_multiplicity_failures": multiplicity_failures,
            "planted_response_count": planted,
            "persistent_dream_mutation_count": dream_mutations,
        },
        "topology": {
            "initial_r1_triplet_count": 0,
            "final_r1_triplet_count": len(final_r1),
            "r1_triplet_ids": sorted(final_r1),
            "stem_cell_transitions": [row["stem_cell_transition"] for row in training_rows],
        },
        "child_provenance": asdict(organism.provenance),
    }


def _evaluate_r1(
    organism: NativeR0Organism,
    fens: Sequence[str],
    *,
    measured: Mapping[str, tuple[Any, Any]],
    arm: str,
    shuffle_seed: int,
) -> Mapping[str, Any]:
    rows = []
    genome = NativeHandoverGenome()
    for fen in fens:
        board = chess.Board(fen)
        measured_slots, measured_frames = measured[fen]
        decision = genome.decide_from_measured_slots(
            board,
            measured_slots,
            measured_frames,
            arm=arm,
            shuffle_seed=shuffle_seed,
        )
        first = chess.Move.from_uci(decision.actuation.move_uci)
        after_first = board.copy(stack=False)
        after_first.push(first)
        reply_rows = []
        for reply in sorted(after_first.legal_moves, key=lambda item: item.uci()):
            successor = after_first.copy(stack=False)
            successor.push(reply)
            second = organism.emit_action(successor)
            terminal = None
            if second is not None:
                successor.push(chess.Move.from_uci(second.move_uci))
                terminal = _observed_terminal(successor)
            reply_rows.append({
                "reply": reply.uci(),
                "child_actuator": None if second is None else second.move_uci,
                "observed_terminal": terminal,
                "mated": terminal == "mate",
            })
        converted = bool(reply_rows and all(row["mated"] for row in reply_rows))
        confirmed_slots = sum(
            int(query.response.confirmed)
            for queries in decision.response_slots.values()
            for query in queries
        )
        actions_with_replies = sum(
            int(bool(queries)) for queries in decision.response_slots.values()
        )
        all_reply_confirmed = sum(
            int(bool(queries) and all(query.response.confirmed for query in queries))
            for queries in decision.response_slots.values()
        )
        rows.append({
            "fen": fen,
            "selected_first": first.uci(),
            "converted": converted,
            "reply_rows": reply_rows,
            "actual_child_confirmed_slot_count": confirmed_slots,
            "actions_with_required_replies": actions_with_replies,
            "all_reply_confirmed_action_count": all_reply_confirmed,
            "child_all_reply_availability_fraction": (
                0.0 if actions_with_replies == 0 else all_reply_confirmed / actions_with_replies
            ),
            "actuator_multiplicity": decision.actuator_multiplicity,
            "host_fallback_count": decision.host_fallback_count,
        })
    return {
        "position_count": len(rows),
        "conversion_count": sum(int(row["converted"]) for row in rows),
        "conversion_rate": (
            0.0 if not rows else sum(int(row["converted"]) for row in rows) / len(rows)
        ),
        "rows": rows,
    }


def _evaluate_r0_retention(
    organism: NativeR0Organism,
    fens: Sequence[str],
) -> Mapping[str, Any]:
    rows = []
    for fen in fens:
        board = chess.Board(fen)
        actuation = organism.emit_action(board)
        terminal = None
        if actuation is not None:
            board.push(chess.Move.from_uci(actuation.move_uci))
            terminal = _observed_terminal(board)
        rows.append({
            "fen": fen,
            "actuator": None if actuation is None else actuation.move_uci,
            "observed_terminal": terminal,
            "retained": terminal == "mate",
        })
    return {
        "position_count": len(rows),
        "retained_count": sum(int(row["retained"]) for row in rows),
        "accuracy": 0.0 if not rows else sum(int(row["retained"]) for row in rows) / len(rows),
        "rows": rows,
    }


def _observed_terminal(board: chess.Board) -> str | None:
    if board.is_checkmate():
        return "mate"
    if board.is_stalemate():
        return "stalemate"
    if not board.pieces(chess.ROOK, chess.WHITE):
        return "rook_loss"
    if board.is_insufficient_material():
        return "draw"
    return None


def _config_from_prior_artifact(artifact: Mapping[str, Any]) -> NativeIntrinsicCurriculumConfig:
    available = {field.name for field in fields(NativeIntrinsicCurriculumConfig)}
    values = {key: value for key, value in artifact["config"].items() if key in available}
    if "r0_excluded_fens" in values:
        values["r0_excluded_fens"] = tuple(values["r0_excluded_fens"])
    values.update({
        # Preserve the historical full pool manifest. The builder below still
        # executes only R0 training and never enters the legacy R1 runner.
        "run_r1": True,
        "resume_r1_snapshots": False,
        "r1_keep_checkpoint_history": False,
    })
    return NativeIntrinsicCurriculumConfig(**values)


def _file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_json(path: str | Path, value: Mapping[str, Any]) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
