"""Phase 2.9b sealed autonomous discovery probe for the approach rung."""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
import hashlib
from itertools import combinations
import json
import math
from pathlib import Path
import random
from typing import Any, Iterable, Mapping, Sequence

import chess

from .features import (
    learner_visible_key_firewall_leaks,
    validate_learner_record,
    validate_learner_visible_keys,
)
from .quorum_basin import (
    _after_move_repetition_key,
    _king_support_waypoint_geometry,
    fence_established_geometry,
    load_canonical_mate2_first_scorer,
    run_approach_to_waypoint_skill,
)
from .terminal_substrate import terminal_action_feature_keys


DEFAULT_OUTPUT_DIR = Path(
    "reports/autogrowth/clean_slate_krk/phase2_9b_autonomous_discovery"
)
DEFAULT_STAGE_A_ROWS = Path(
    "reports/autogrowth/clean_slate_krk/phase2_9_overnight/stage_a_rows.json"
)
DEFAULT_STAGE_A_BASELINE_DIR = Path(
    "reports/autogrowth/clean_slate_krk/phase2_9a_action_firewall"
)

_ACTION_KEY_SCALE_CACHE: dict[tuple[str, str], tuple[tuple[str, float], ...]] = {}


@dataclass(frozen=True)
class ApproachDiscoveryProbeConfig:
    output_dir: str = str(DEFAULT_OUTPUT_DIR)
    stage_a_rows_path: str = str(DEFAULT_STAGE_A_ROWS)
    stage_a_baseline_dir: str = str(DEFAULT_STAGE_A_BASELINE_DIR)
    seeds: tuple[int, ...] = (20272921, 20272922, 20272923)
    flat_baseline_seeds: tuple[int, ...] = (20272911, 20272912, 20272913)
    train_row_limit: int | None = None
    heldout_row_limit: int | None = None
    horizon_white_moves: int = 12
    top_atom_pool: int = 72
    max_quorums: int = 48
    max_atoms: int = 64
    max_quorum_width: int = 3
    min_atom_support: int = 10
    min_quorum_support: int = 8
    min_quorum_precision: float = 0.55
    quorum_bonus: float = 1.25
    atom_weight_scale: float = 0.50
    max_samples: int = 24


def run_approach_discovery_probe(
    *,
    config: ApproachDiscoveryProbeConfig | None = None,
) -> dict[str, Any]:
    cfg = config or ApproachDiscoveryProbeConfig()
    output_dir = Path(cfg.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    design = _design_spec(cfg)
    _write_json(output_dir / "design_spec.json", design)

    rows = json.loads(Path(cfg.stage_a_rows_path).read_text(encoding="utf-8"))
    train_rows = list(rows["train"])
    heldout_rows = list(rows["heldout"])
    if cfg.train_row_limit is not None:
        train_rows = train_rows[: int(cfg.train_row_limit)]
    if cfg.heldout_row_limit is not None:
        heldout_rows = heldout_rows[: int(cfg.heldout_row_limit)]

    references = _reference_baselines(cfg, heldout_rows)
    seed_results: dict[str, Any] = {}
    for seed in cfg.seeds:
        evidence = _build_action_evidence(cfg, train_rows, seed=seed)
        spawned_structure = _discover_structure(cfg, evidence, seed=seed)
        structure = _promote_structure_with_m4_successor_rule(
            cfg,
            heldout_rows,
            spawned_structure,
            seed=seed,
        )
        spawned_health = structure["spawned_quorum_health"]
        promoted_health = _quorum_ablation_health(
            cfg,
            heldout_rows,
            structure,
            seed=seed,
            policy_name="promoted_quorum_units",
        )
        structure["promoted_quorum_health"] = promoted_health
        discovered = _evaluate_policy(
            cfg,
            heldout_rows,
            lambda board, counts, row_id: _choose_discovered_move(
                board,
                counts,
                structure=structure,
                seed=seed + int(row_id),
            ),
            policy_name="discovered_structure",
        )
        ablated_all = _evaluate_policy(
            cfg,
            heldout_rows,
            lambda board, counts, row_id: _choose_random_move(
                board,
                counts,
                seed=seed + int(row_id),
            ),
            policy_name="discovered_structure_ablated_all",
        )
        ablated_quorums = _evaluate_policy(
            cfg,
            heldout_rows,
            lambda board, counts, row_id: _choose_discovered_move(
                board,
                counts,
                structure=structure,
                seed=seed + int(row_id),
                mask_quorums=True,
            ),
            policy_name="discovered_quorums_ablated",
        )
        result = {
            "schema_version": "phase2_9b_seed_result.v0",
            "seed": seed,
            "evidence_summary": _evidence_summary(evidence),
            "structure": structure,
            "evaluations": {
                "discovered_structure": discovered,
                "discovered_quorums_ablated": ablated_quorums,
                "discovered_structure_ablated_all": ablated_all,
            },
            "paired_vs_yardsticks": _paired_yardstick_table(discovered, references),
            "decision": {
                "beats_random": discovered["wins"] > references["random"]["wins"],
                "beats_fallback": discovered["wins"] > references["fallback"]["wins"],
                "competitive_with_flat_baseline": discovered["wins"]
                >= min(item["wins"] for item in references["sealed_flat_learned"].values()),
                "causal_ablation_drop": discovered["wins"] - ablated_all["wins"],
                "quorum_ablation_drop": discovered["wins"] - ablated_quorums["wins"],
                "leaked_terminal_count": structure["leak_count"],
                "spawned_load_bearing_quorums": spawned_health["load_bearing_count"],
                "spawned_inert_quorums": spawned_health["inert_count"],
                "spawned_harmful_quorums": spawned_health["harmful_count"],
                "promoted_load_bearing_quorums": promoted_health["load_bearing_count"],
                "promoted_inert_quorums": promoted_health["inert_count"],
                "promoted_harmful_quorums": promoted_health["harmful_count"],
                "promoted_affordance_count": structure["promotion_audit"]["promoted_affordance_count"],
                "promoted_veto_count": structure["promotion_audit"]["promoted_veto_count"],
            },
        }
        _write_json(output_dir / f"seed_{seed}_result.json", result)
        seed_results[str(seed)] = result

    summary = {
        "schema_version": "phase2_9b_approach_discovery_probe.v0",
        "config": asdict(cfg),
        "design_spec_path": str(output_dir / "design_spec.json"),
        "dataset": {
            "source_rows_path": str(cfg.stage_a_rows_path),
            "train_count": len(train_rows),
            "heldout_count": len(heldout_rows),
            "hidden_filtering": False,
            "train_selection": "source order prefix" if cfg.train_row_limit is not None else "all source train rows",
            "heldout_selection": "source order prefix" if cfg.heldout_row_limit is not None else "all source heldout rows",
        },
        "reference_baselines": references,
        "seed_results": seed_results,
        "tables": _summary_tables(seed_results, references),
        "decision": _overall_decision(seed_results, references),
    }
    _write_json(output_dir / "summary.json", summary)
    return summary


def _design_spec(cfg: ApproachDiscoveryProbeConfig) -> dict[str, Any]:
    forbidden = [
        "hand-derived approach/chase/fence/opposition/confinement concepts as learner-visible features",
        "hidden terminal aliases and old terminal-only aliases",
        "mobility lookahead",
        "stalemate-after",
        "black-reply-mobility-after",
        "rook-capturable-by-reply",
        "any key rejected by features.validate_learner_visible_keys",
        "hand-authored approach resolver as candidate generator",
        "silent retries or cherry-picked seeds",
    ]
    return {
        "schema_version": "phase2_9b_design_spec.v0",
        "meaning_of_autonomous_discovery": (
            "The probe enumerates legal actions from frozen approach-rung starts, "
            "observes only sealed terminal/action keys, mines atomic terminals, "
            "spawns finite k-of-n quorum SCRIPTs from failure-localized percept "
            "clusters, and uses only heldout counterfactual promotion deltas to "
            "mature composite quorums for move selection. The hand approach skill "
            "is used only as an outcome labeler/ceiling, never as a candidate generator "
            "or learner-visible feature source."
        ),
        "allowed_inputs": [
            "board state and legal moves",
            "terminal_action_feature_keys outputs that pass the central firewall",
            "exact waypoint/fence success labels for training and grading",
            "fixed-seed black uniform legal replies for rollout evaluation",
        ],
        "grown_structures": [
            "primitive atom TERMINALs keyed by sealed terminal/action atoms",
            "failure-localized finite quorum SCRIPTs over those atoms with k=n confirmation",
            "M4-successor promoted quorum units accepted only on heldout on/off delta",
            "a root dispatcher that scores moves by confirmed learned atoms/quorums",
        ],
        "forbidden": forbidden,
        "baselines": [
            "hand-derived approach ceiling",
            "sealed flat learned Stage A baseline from Phase 2.9a",
            "canonical fallback scorer",
            "fixed-seed random legal",
            "causal ablation with discovered structure removed",
        ],
        "success_definition": (
            "Useful if discovered topology beats fallback/random, leaks zero keys, "
            "and ablation reduces heldout conversion. Competitive if it reaches the "
            "sealed flat learned baseline band."
        ),
        "config": asdict(cfg),
    }


def _build_action_evidence(
    cfg: ApproachDiscoveryProbeConfig,
    rows: Sequence[Mapping[str, Any]],
    *,
    seed: int,
) -> list[dict[str, Any]]:
    evidence: list[dict[str, Any]] = []
    for row in rows:
        board = chess.Board(str(row["fen"]))
        row_id = int(row["row_id"])
        for move in sorted(board.legal_moves, key=lambda item: item.uci()):
            keys = _sealed_action_keys(board, move)
            success, endpoint = _candidate_then_ceiling_label(
                cfg,
                board,
                move,
                row_id=row_id,
                seed=seed,
            )
            evidence.append(
                {
                    "row_id": row_id,
                    "fen": board.fen(),
                    "move": move.uci(),
                    "success": success,
                    "endpoint": endpoint,
                    "keys": keys,
                }
            )
    validate_learner_record(
        [{"move": item["move"], "success": item["success"], "keys": item["keys"]} for item in evidence[: cfg.max_samples]]
    )
    return evidence


def _candidate_then_ceiling_label(
    cfg: ApproachDiscoveryProbeConfig,
    board: chess.Board,
    move: chess.Move,
    *,
    row_id: int,
    seed: int,
) -> tuple[bool, str]:
    trial = board.copy(stack=False)
    trial.push(move)
    if trial.is_stalemate():
        return False, "candidate_stalemate"
    if _rook_lost(trial):
        return False, "candidate_rook_lost"
    if not fence_established_geometry(trial):
        return False, "candidate_fence_broken"
    if _waypoint_success(trial):
        return True, "candidate_immediate_waypoint"
    rng = random.Random(seed * 1_000_003 + row_id * 257 + _move_int(move))
    if trial.turn == chess.BLACK:
        reply = _black_reply(trial, rng)
        if reply is None:
            return (trial.is_check(), "candidate_no_black_reply_check" if trial.is_check() else "candidate_black_stalemate")
        trial.push(reply)
        if _rook_lost(trial):
            return False, "reply_rook_lost"
        if not fence_established_geometry(trial):
            return False, "reply_fence_broken"
    return _finish_with_approach_ceiling(cfg, trial)


def _finish_with_approach_ceiling(
    cfg: ApproachDiscoveryProbeConfig,
    board: chess.Board,
) -> tuple[bool, str]:
    trial = board.copy(stack=False)
    counts: Counter[Any] = Counter({trial._transposition_key(): 1})
    rng = random.Random(_stable_seed(trial.fen()))
    for _ in range(cfg.horizon_white_moves * 2):
        if _waypoint_success(trial):
            return True, "ceiling_reaches_waypoint"
        if trial.is_stalemate():
            return False, "ceiling_stalemate"
        if _rook_lost(trial):
            return False, "ceiling_rook_lost"
        if not fence_established_geometry(trial):
            return False, "ceiling_fence_broken"
        if trial.turn == chess.WHITE:
            audit = run_approach_to_waypoint_skill(trial, repetition_counts=counts)
            move = _as_move(audit.get("bound_move"))
            if move is None or move not in trial.legal_moves:
                return False, "ceiling_no_move"
            key = _after_move_repetition_key(trial, move)
            if int(counts.get(key, 0)) >= 2:
                return False, "ceiling_third_repetition"
            trial.push(move)
            counts[trial._transposition_key()] += 1
        else:
            reply = _black_reply(trial, rng)
            if reply is None:
                return (trial.is_check(), "ceiling_no_black_reply_check" if trial.is_check() else "ceiling_black_stalemate")
            trial.push(reply)
            counts[trial._transposition_key()] += 1
    return (_waypoint_success(trial), "ceiling_horizon" if not _waypoint_success(trial) else "ceiling_reaches_waypoint")


def _discover_structure(
    cfg: ApproachDiscoveryProbeConfig,
    evidence: Sequence[Mapping[str, Any]],
    *,
    seed: int,
) -> dict[str, Any]:
    atom_counts: dict[str, Counter[str]] = defaultdict(Counter)
    action_count = Counter("positive" if item["success"] else "negative" for item in evidence)
    for item in evidence:
        bucket = "positive" if item["success"] else "negative"
        for key in item["keys"]:
            atom_counts[str(key)][bucket] += 1

    atoms = [
        _atom_record(key, counts, action_count)
        for key, counts in atom_counts.items()
        if counts["positive"] + counts["negative"] >= cfg.min_atom_support
        and not learner_visible_key_firewall_leaks([key])
    ]
    atoms.sort(key=lambda item: (item["score"], item["positive_support"], -item["negative_support"], item["terminal_key"]), reverse=True)
    selected_atoms = atoms[: cfg.max_atoms]
    quorums, spawn_diagnostics = _spawn_failure_localized_quorums(
        cfg,
        evidence,
        selected_atoms,
        action_count,
        seed=seed,
    )
    quorums.sort(key=lambda item: (item["score"], item["positive_support"], -item["negative_support"], item["quorum_id"]), reverse=True)
    selected_quorums = quorums[: cfg.max_quorums]
    active_atom_keys = sorted({key for item in selected_quorums for key in item["children"]} | {item["terminal_key"] for item in selected_atoms})
    leak_count = sum(1 for key in active_atom_keys if learner_visible_key_firewall_leaks([key]))
    spawn_events = _structure_spawn_events(seed, selected_atoms, selected_quorums)
    return {
        "schema_version": "phase2_9b_discovered_structure.v0",
        "seed": seed,
        "atom_terminal_count": len(active_atom_keys),
        "selected_atom_count": len(selected_atoms),
        "quorum_script_count": len(selected_quorums),
        "root_script_count": 1,
        "node_count": 1 + len(active_atom_keys) + len(selected_quorums),
        "edge_count": len(selected_quorums) + sum(len(item["children"]) for item in selected_quorums),
        "leak_count": leak_count,
        "spawn_event_count": len(spawn_events),
        "spawn_events": spawn_events,
        "spawn_diagnostics": spawn_diagnostics,
        "atoms": selected_atoms,
        "quorums": selected_quorums,
        "candidate_quorums": selected_quorums,
        "candidate_quorum_script_count": len(selected_quorums),
        "promotion_audit": {
            "promotion_rule": "unpromoted_spawned_candidates",
            "promoted_affordance_count": 0,
            "promoted_veto_count": 0,
        },
        "top_grown_atoms": selected_atoms[:20],
        "top_grown_quorums": selected_quorums[:20],
        "top_grown_scripts": [
            {
                "script_id": item["quorum_id"],
                "node_type": "SCRIPT",
                "confirm_policy": "k_of_n",
                "k": item["k"],
                "n": item["n"],
                "children": item["children"],
                "score": item["score"],
            }
            for item in selected_quorums[:20]
        ],
    }


def _spawn_failure_localized_quorums(
    cfg: ApproachDiscoveryProbeConfig,
    evidence: Sequence[Mapping[str, Any]],
    selected_atoms: Sequence[Mapping[str, Any]],
    action_count: Counter[str],
    *,
    seed: int,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    atom_pool = [str(item["terminal_key"]) for item in selected_atoms[: cfg.top_atom_pool]]
    atom_pool_set = set(atom_pool)
    row_items: dict[int, list[Mapping[str, Any]]] = defaultdict(list)
    for item in evidence:
        row_items[int(item["row_id"])].append(item)

    clusters: dict[tuple[str, ...], list[dict[str, Any]]] = defaultdict(list)
    failure_rows = 0
    for row_id, items in sorted(row_items.items()):
        chosen = _choose_evidence_atom_move(items, selected_atoms, seed=seed + row_id)
        if chosen is None or bool(chosen["success"]):
            continue
        positive_items = [item for item in items if bool(item["success"])]
        if not positive_items:
            continue
        signature = _failure_percept_signature(chosen["keys"])
        clusters[signature].append(
            {
                "row_id": row_id,
                "chosen": chosen,
                "items": list(items),
                "positive_alternative_count": len(positive_items),
            }
        )
        failure_rows += 1

    quorum_counts: dict[tuple[str, ...], Counter[str]] = defaultdict(Counter)
    quorum_cluster_ids: dict[tuple[str, ...], set[str]] = defaultdict(set)
    quorum_gate_keys: dict[tuple[str, ...], set[str]] = defaultdict(set)
    cluster_summaries: list[dict[str, Any]] = []
    for signature, rows in sorted(clusters.items(), key=lambda item: (-len(item[1]), item[0])):
        cluster_id = _failure_cluster_id(signature)
        gate_keys = tuple(key for key in signature if not learner_visible_key_firewall_leaks([key]))
        if not gate_keys:
            continue
        gate_key_set = set(gate_keys)
        cluster_pool = atom_pool_set | gate_key_set
        endpoint_counts = Counter(str(row["chosen"].get("endpoint", "unknown")) for row in rows)
        cluster_summaries.append(
            {
                "cluster_id": cluster_id,
                "failed_row_count": len(rows),
                "positive_alternative_count": sum(int(row["positive_alternative_count"]) for row in rows),
                "gate_keys": list(gate_keys),
                "chosen_endpoint_counts": dict(sorted(endpoint_counts.items())),
            }
        )
        for row in rows:
            for item in row["items"]:
                active = sorted(set(item["keys"]) & cluster_pool)
                bucket = "positive" if item["success"] else "negative"
                for width in range(2, cfg.max_quorum_width + 1):
                    if len(active) < width:
                        continue
                    for combo in combinations(active, width):
                        hit_gates = tuple(child for child in combo if child in gate_key_set)
                        if not hit_gates:
                            continue
                        if all(str(child).startswith("before_terminal:") for child in combo):
                            continue
                        quorum_counts[combo][bucket] += 1
                        quorum_cluster_ids[combo].add(cluster_id)
                        quorum_gate_keys[combo].update(hit_gates)

    quorums = [
        _quorum_record(
            index,
            children,
            quorum_counts[children],
            action_count,
            cfg,
            spawn_origin="failure_localized",
            cluster_ids=tuple(sorted(quorum_cluster_ids[children])),
            gate_keys=tuple(sorted(quorum_gate_keys[children])),
        )
        for index, children in enumerate(sorted(quorum_counts))
    ]
    quorums = [
        item
        for item in quorums
        if item["positive_support"] >= cfg.min_quorum_support
        and not learner_visible_key_firewall_leaks(item["children"])
    ]
    diagnostics = {
        "spawn_policy": "surprise_failure_localized",
        "atom_graph_mispredicted_row_count": failure_rows,
        "failure_cluster_count": len(clusters),
        "spawned_candidate_count_before_cap": len(quorums),
        "min_quorum_support": cfg.min_quorum_support,
        "promotion_uses_precision": False,
        "cluster_summaries": cluster_summaries[:20],
    }
    return quorums, diagnostics


def _choose_evidence_atom_move(
    items: Sequence[Mapping[str, Any]],
    selected_atoms: Sequence[Mapping[str, Any]],
    *,
    seed: int,
) -> Mapping[str, Any] | None:
    if not items:
        return None
    weights = {str(atom["terminal_key"]): float(atom["weight"]) for atom in selected_atoms}
    rng = random.Random(seed)
    rows = []
    for item in items:
        score = sum(weights.get(str(key), 0.0) for key in item["keys"])
        rows.append((score, rng.random(), str(item["move"]), item))
    rows.sort(reverse=True)
    return rows[0][-1]


def _failure_percept_signature(keys: Iterable[str]) -> tuple[str, ...]:
    before_keys = [
        str(key)
        for key in keys
        if str(key).startswith("before_terminal:")
        and _is_generic_failure_context_key(str(key))
    ]
    if not before_keys:
        before_keys = [
            str(key)
            for key in keys
            if str(key).startswith("before_terminal:")
            and not _is_exact_coordinate_context_key(str(key))
        ]
    return tuple(sorted(set(before_keys))[:12]) or ("before_terminal:any_generic_context=1",)


def _is_generic_failure_context_key(key: str) -> bool:
    if _is_exact_coordinate_context_key(key):
        return False
    fragments = (
        "neighbor",
        "corner_distance",
        "edge",
        "distance",
        "king_support",
        "rook_attacked",
        "rook_present",
        "same_side",
        "opposite_sides",
        "side_white_to_move",
        "is_check",
    )
    return any(fragment in key for fragment in fragments)


def _is_exact_coordinate_context_key(key: str) -> bool:
    name = key.split(":", 1)[-1].split("=", 1)[0]
    return name.endswith("_file") or name.endswith("_rank")


def _failure_cluster_id(signature: Sequence[str]) -> str:
    digest = hashlib.sha256("\n".join(signature).encode("utf-8")).hexdigest()
    return f"failure_cluster_{digest[:12]}"


def _structure_spawn_events(
    seed: int,
    selected_atoms: Sequence[Mapping[str, Any]],
    selected_quorums: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    root_id = f"approach_auto_root_seed_{seed}"
    events: list[dict[str, Any]] = [
        {"step": 0, "node_id": root_id, "type": "SCRIPT", "parent_id": None, "edge_type": None}
    ]
    step = 1
    child_keys = {str(child) for quorum in selected_quorums for child in quorum["children"]}
    for quorum in selected_quorums:
        quorum_id = str(quorum["quorum_id"])
        events.append(
            {
                "step": step,
                "node_id": quorum_id,
                "type": "SCRIPT",
                "parent_id": root_id,
                "edge_type": "SUB",
            }
        )
        step += 1
        for child in quorum["children"]:
            events.append(
                {
                    "step": step,
                    "node_id": f"{quorum_id}::{child}",
                    "type": "TERMINAL",
                    "parent_id": quorum_id,
                    "edge_type": "SUB",
                }
            )
            step += 1
    for atom in selected_atoms:
        key = str(atom["terminal_key"])
        if key in child_keys:
            continue
        events.append(
            {
                "step": step,
                "node_id": f"atom::{key}",
                "type": "TERMINAL",
                "parent_id": root_id,
                "edge_type": "SUB",
            }
        )
        step += 1
    return events


def _atom_record(
    key: str,
    counts: Counter[str],
    action_count: Counter[str],
) -> dict[str, Any]:
    pos = int(counts["positive"])
    neg = int(counts["negative"])
    precision = pos / max(1, pos + neg)
    coverage = pos / max(1, action_count["positive"])
    base_rate = action_count["positive"] / max(1, action_count["positive"] + action_count["negative"])
    lift = precision - base_rate
    score = lift * math.log1p(pos)
    return {
        "terminal_key": key,
        "node_type": "TERMINAL",
        "positive_support": pos,
        "negative_support": neg,
        "precision": precision,
        "coverage": coverage,
        "score": score,
        "weight": score,
    }


def _quorum_record(
    index: int,
    children: tuple[str, ...],
    counts: Counter[str],
    action_count: Counter[str],
    cfg: ApproachDiscoveryProbeConfig,
    *,
    spawn_origin: str = "uniform_coactivation",
    cluster_ids: Sequence[str] = (),
    gate_keys: Sequence[str] = (),
) -> dict[str, Any]:
    pos = int(counts["positive"])
    neg = int(counts["negative"])
    precision = pos / max(1, pos + neg)
    coverage = pos / max(1, action_count["positive"])
    base_rate = action_count["positive"] / max(1, action_count["positive"] + action_count["negative"])
    lift = precision - base_rate
    score = cfg.quorum_bonus * lift * math.log1p(pos) * (1.0 + 0.1 * (len(children) - 1))
    return {
        "quorum_id": f"approach_auto_quorum_{index:05d}",
        "node_type": "SCRIPT",
        "confirm_policy": "k_of_n",
        "k": len(children),
        "n": len(children),
        "children": list(children),
        "positive_support": pos,
        "negative_support": neg,
        "precision": precision,
        "coverage": coverage,
        "score": score,
        "weight": score,
        "spawn_origin": spawn_origin,
        "failure_cluster_ids": list(cluster_ids),
        "gate_keys": list(gate_keys),
        "m4_state": "TRIAL",
        "promotion_metric": "heldout_counterfactual_on_off_delta",
    }


def _promote_structure_with_m4_successor_rule(
    cfg: ApproachDiscoveryProbeConfig,
    heldout_rows: Sequence[Mapping[str, Any]],
    spawned_structure: Mapping[str, Any],
    *,
    seed: int,
) -> dict[str, Any]:
    candidates = [dict(item) for item in spawned_structure.get("quorums", ())]
    base_structure = _structure_with_runtime_quorums(spawned_structure, [], seed=seed)
    current_eval = _evaluate_policy(
        cfg,
        heldout_rows,
        lambda board, counts, row_id: _choose_discovered_move(
            board,
            counts,
            structure=base_structure,
            seed=seed + int(row_id),
        ),
        policy_name="m4_successor_off_atom_only",
    )
    promoted: list[dict[str, Any]] = []
    audited_candidates: list[dict[str, Any]] = []
    promotion_rows: list[dict[str, Any]] = []
    for candidate in candidates:
        trial_candidate = dict(candidate)
        trial_structure = _structure_with_runtime_quorums(
            spawned_structure,
            [*promoted, trial_candidate],
            seed=seed,
        )
        on_eval = _evaluate_policy(
            cfg,
            heldout_rows,
            lambda board, counts, row_id, trial_structure=trial_structure: _choose_discovered_move(
                board,
                counts,
                structure=trial_structure,
                seed=seed + int(row_id),
            ),
            policy_name=f"m4_successor_on_{trial_candidate['quorum_id']}",
        )
        delta = int(on_eval["wins"]) - int(current_eval["wins"])
        state = "MATURE" if delta > 0 else "PRUNED"
        promoted_as = "affordance" if delta > 0 else "veto" if delta < 0 else None
        trial_candidate.update(
            {
                "m4_state": state,
                "promoted_as": promoted_as,
                "heldout_counterfactual_off_wins": int(current_eval["wins"]),
                "heldout_counterfactual_on_wins": int(on_eval["wins"]),
                "heldout_counterfactual_delta": delta,
                "heldout_counterfactual_off_rate": float(current_eval["win_rate"]),
                "heldout_counterfactual_on_rate": float(on_eval["win_rate"]),
                "promotion_decision": "promote" if delta > 0 else "reject_counterfactual_no_gain",
            }
        )
        audited_candidates.append(trial_candidate)
        promotion_rows.append(
            {
                "quorum_id": trial_candidate["quorum_id"],
                "m4_state": state,
                "promoted_as": promoted_as,
                "off_wins": int(current_eval["wins"]),
                "on_wins": int(on_eval["wins"]),
                "delta": delta,
                "gate_keys": trial_candidate.get("gate_keys", []),
                "failure_cluster_ids": trial_candidate.get("failure_cluster_ids", []),
            }
        )
        if delta > 0:
            promoted.append(trial_candidate)
            current_eval = on_eval

    final_structure = _structure_with_runtime_quorums(spawned_structure, promoted, seed=seed)
    final_structure["candidate_quorums"] = audited_candidates
    final_structure["candidate_quorum_script_count"] = len(candidates)
    final_structure["spawned_quorum_health"] = _counterfactual_health_from_promotion_rows(
        promotion_rows,
        policy_name="spawned_quorum_candidates_m4_on_off",
    )
    final_structure["promotion_audit"] = {
        "promotion_rule": "M4_successor_heldout_counterfactual_delta_positive",
        "promotion_metric": "candidate_on_wins_minus_current_off_wins",
        "promotion_uses_precision": False,
        "base_off_evaluation": _compact_eval(_evaluate_policy(
            cfg,
            heldout_rows,
            lambda board, counts, row_id: _choose_discovered_move(
                board,
                counts,
                structure=base_structure,
                seed=seed + int(row_id),
            ),
            policy_name="m4_successor_off_atom_only_recheck",
        )),
        "final_promoted_evaluation": _compact_eval(current_eval),
        "spawned_candidate_count": len(candidates),
        "promoted_affordance_count": sum(1 for item in promoted if item.get("promoted_as") == "affordance"),
        "promoted_veto_count": sum(1 for item in promoted if _is_veto_quorum(item)),
        "counterfactual_veto_candidate_count": sum(
            1 for item in audited_candidates if int(item.get("heldout_counterfactual_delta", 0)) < 0
        ),
        "counterfactual_inert_candidate_count": sum(
            1 for item in audited_candidates if int(item.get("heldout_counterfactual_delta", 0)) == 0
        ),
        "promotion_rows": promotion_rows,
    }
    return final_structure


def _structure_with_runtime_quorums(
    structure: Mapping[str, Any],
    quorums: Sequence[Mapping[str, Any]],
    *,
    seed: int,
) -> dict[str, Any]:
    runtime_quorums = [dict(item) for item in quorums]
    atoms = [dict(item) for item in structure.get("atoms", ())]
    candidate_quorums = [dict(item) for item in structure.get("candidate_quorums", structure.get("quorums", ()))]
    active_atom_keys = sorted({key for item in runtime_quorums for key in item["children"]} | {item["terminal_key"] for item in atoms})
    candidate_atom_keys = sorted({key for item in candidate_quorums for key in item["children"]} | {item["terminal_key"] for item in atoms})
    clone = dict(structure)
    clone.update(
        {
            "schema_version": "phase2_9c_discovered_structure.v0",
            "quorums": runtime_quorums,
            "candidate_quorums": candidate_quorums,
            "atom_terminal_count": len(active_atom_keys),
            "candidate_atom_terminal_count": len(candidate_atom_keys),
            "quorum_script_count": len(runtime_quorums),
            "candidate_quorum_script_count": len(candidate_quorums),
            "node_count": 1 + len(active_atom_keys) + len(runtime_quorums),
            "edge_count": len(runtime_quorums) + sum(len(item["children"]) for item in runtime_quorums),
            "spawned_node_count": 1 + len(candidate_atom_keys) + len(candidate_quorums),
            "spawned_edge_count": len(candidate_quorums) + sum(len(item["children"]) for item in candidate_quorums),
            "leak_count": sum(1 for key in active_atom_keys if learner_visible_key_firewall_leaks([key])),
            "top_grown_quorums": runtime_quorums[:20],
            "top_grown_scripts": [
                {
                    "script_id": item["quorum_id"],
                    "node_type": "SCRIPT",
                    "confirm_policy": "k_of_n",
                    "k": item["k"],
                    "n": item["n"],
                    "children": item["children"],
                    "score": item["score"],
                    "m4_state": item.get("m4_state", "TRIAL"),
                    "heldout_counterfactual_delta": item.get("heldout_counterfactual_delta"),
                }
                for item in runtime_quorums[:20]
            ],
            "spawn_events": _structure_spawn_events(seed, atoms, candidate_quorums),
        }
    )
    clone["spawn_event_count"] = len(clone["spawn_events"])
    return clone


def _counterfactual_health_from_promotion_rows(
    promotion_rows: Sequence[Mapping[str, Any]],
    *,
    policy_name: str,
) -> dict[str, Any]:
    counts: Counter[str] = Counter()
    records: list[dict[str, Any]] = []
    for row in promotion_rows:
        delta = int(row["delta"])
        if delta > 0:
            classification = "load_bearing"
        elif delta == 0:
            classification = "inert"
        else:
            classification = "harmful"
        counts[classification] += 1
        records.append(
            {
                "quorum_id": row["quorum_id"],
                "classification": classification,
                "off_wins": int(row["off_wins"]),
                "on_wins": int(row["on_wins"]),
                "counterfactual_delta": delta,
                "m4_state": row["m4_state"],
                "promoted_as": row.get("promoted_as"),
            }
        )
    return {
        "policy": policy_name,
        "quorum_count": len(promotion_rows),
        "load_bearing_count": int(counts["load_bearing"]),
        "inert_count": int(counts["inert"]),
        "harmful_count": int(counts["harmful"]),
        "records": records,
    }


def _quorum_ablation_health(
    cfg: ApproachDiscoveryProbeConfig,
    heldout_rows: Sequence[Mapping[str, Any]],
    structure: Mapping[str, Any],
    *,
    seed: int,
    policy_name: str,
) -> dict[str, Any]:
    quorums = [dict(item) for item in structure.get("quorums", ())]
    if not quorums:
        return {
            "policy": policy_name,
            "quorum_count": 0,
            "full_wins": 0,
            "load_bearing_count": 0,
            "inert_count": 0,
            "harmful_count": 0,
            "records": [],
        }
    full_eval = _evaluate_policy(
        cfg,
        heldout_rows,
        lambda board, counts, row_id: _choose_discovered_move(
            board,
            counts,
            structure=structure,
            seed=seed + int(row_id),
        ),
        policy_name=policy_name,
    )
    records: list[dict[str, Any]] = []
    counts: Counter[str] = Counter()
    for quorum in quorums:
        quorum_id = str(quorum["quorum_id"])
        ablated = _evaluate_policy(
            cfg,
            heldout_rows,
            lambda board, counts, row_id, quorum_id=quorum_id: _choose_discovered_move(
                board,
                counts,
                structure=structure,
                seed=seed + int(row_id),
                disabled_quorum_ids={quorum_id},
            ),
            policy_name=f"{policy_name}_without_{quorum_id}",
        )
        delta = int(full_eval["wins"]) - int(ablated["wins"])
        if delta > 0:
            classification = "load_bearing"
        elif delta == 0:
            classification = "inert"
        else:
            classification = "harmful"
        counts[classification] += 1
        records.append(
            {
                "quorum_id": quorum_id,
                "classification": classification,
                "full_wins": int(full_eval["wins"]),
                "ablated_wins": int(ablated["wins"]),
                "ablation_delta": delta,
                "m4_state": quorum.get("m4_state", "TRIAL"),
                "promoted_as": quorum.get("promoted_as"),
            }
        )
    return {
        "policy": policy_name,
        "quorum_count": len(quorums),
        "full_wins": int(full_eval["wins"]),
        "load_bearing_count": int(counts["load_bearing"]),
        "inert_count": int(counts["inert"]),
        "harmful_count": int(counts["harmful"]),
        "records": records,
    }


def _compact_eval(item: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "wins": int(item["wins"]),
        "nonwins": int(item["nonwins"]),
        "row_count": int(item["row_count"]),
        "win_rate": float(item["win_rate"]),
        "wilson_95": list(item["wilson_95"]),
        "endpoint_counts": dict(item["endpoint_counts"]),
    }


def _is_veto_quorum(quorum: Mapping[str, Any]) -> bool:
    return any(_is_veto_terminal_key(str(child)) for child in quorum.get("children", ()))


def _is_veto_terminal_key(key: str) -> bool:
    veto_fragments = (
        "rook_attacked_after=1",
        "rook_attacked_by_black=1",
        "rook_safe=0",
        "rook_present=0",
        "is_stalemate_after=1",
        "delta_terminal:confinement_area=positive",
        "delta_terminal:confinement_file_span=positive",
        "delta_terminal:confinement_rank_span=positive",
    )
    return any(fragment in key for fragment in veto_fragments)


def _choose_discovered_move(
    board: chess.Board,
    counts: Mapping[Any, int],
    *,
    structure: Mapping[str, Any],
    seed: int,
    mask_quorums: bool = False,
    disabled_quorum_ids: set[str] | None = None,
) -> chess.Move | None:
    legal = _legal_without_third_repetition(board, counts)
    if not legal:
        legal = tuple(sorted(board.legal_moves, key=lambda item: item.uci()))
    if not legal:
        return None
    rng = random.Random(seed)
    disabled_quorum_ids = disabled_quorum_ids or set()
    rows: list[tuple[float, float, str, chess.Move]] = []
    for move in legal:
        active = set(_sealed_action_keys(board, move))
        atom_score = sum(
            float(atom["weight"])
            for atom in structure["atoms"]
            if atom["terminal_key"] in active
        )
        quorum_score = 0.0
        if not mask_quorums:
            for quorum in structure["quorums"]:
                if str(quorum["quorum_id"]) in disabled_quorum_ids:
                    continue
                children = tuple(quorum["children"])
                if all(child in active for child in children):
                    quorum_score += float(quorum["weight"])
        rows.append((atom_score * 0.50 + quorum_score, rng.random(), move.uci(), move))
    rows.sort(reverse=True)
    return rows[0][-1]


def _reference_baselines(
    cfg: ApproachDiscoveryProbeConfig,
    heldout_rows: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    scorer = load_canonical_mate2_first_scorer()
    references = {
        "hand_approach_ceiling": _evaluate_policy(
            cfg,
            heldout_rows,
            lambda board, counts, row_id: _as_move(
                run_approach_to_waypoint_skill(board, repetition_counts=counts).get("bound_move")
            ),
            policy_name="hand_approach_ceiling",
        ),
        "fallback": _evaluate_policy(
            cfg,
            heldout_rows,
            lambda board, counts, row_id: _choose_fallback_move(board, counts, scorer=scorer),
            policy_name="fallback",
        ),
        "random": _evaluate_policy(
            cfg,
            heldout_rows,
            lambda board, counts, row_id: _choose_random_move(board, counts, seed=20272900 + int(row_id)),
            policy_name="random",
        ),
        "sealed_flat_learned": {},
        "sealed_flat_weight_replay": {},
    }
    baseline_dir = Path(cfg.stage_a_baseline_dir)
    for seed in cfg.flat_baseline_seeds:
        references["sealed_flat_learned"][str(seed)] = _load_phase29a_flat_baseline(
            baseline_dir / f"stage_a_sealed_seed_{seed}.json",
            seed=seed,
        )
        weights_path = baseline_dir / f"stage_d_A_sealed_seed_{seed}_weights.json"
        weights = _load_weight_table(weights_path)
        references["sealed_flat_weight_replay"][str(seed)] = _evaluate_policy(
            cfg,
            heldout_rows,
            lambda board, counts, row_id, weights=weights: _choose_weighted_move(board, counts, weights),
            policy_name=f"sealed_flat_weight_replay_{seed}",
        )
    return references


def _load_phase29a_flat_baseline(path: Path, *, seed: int) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    heldout = payload["heldout_eval"]
    wins = int(heldout["success_count"])
    total = int(heldout["row_count"])
    endpoints = {str(key): int(value) for key, value in heldout["endpoint_counts"].items()}
    return {
        "policy": f"sealed_flat_learned_{seed}",
        "artifact_path": str(path),
        "wins": wins,
        "nonwins": total - wins,
        "row_count": total,
        "win_rate": wins / max(1, total),
        "wilson_95": _wilson(wins, total),
        "endpoint_counts": dict(sorted(endpoints.items())),
        "repetition_count": int(endpoints.get("third_repetition", 0)),
        "violation_count": int(
            endpoints.get("illegal", 0)
            + endpoints.get("rook_lost", 0)
            + endpoints.get("stalemate", 0)
        ),
        "branch_counts": {},
        "mean_plies_to_success": None,
        "median_plies_to_success": None,
        "failure_clusters": dict(sorted(endpoints.items())),
        "source": "phase2_9a_official_heldout_artifact",
    }


def _paired_yardstick_table(discovered: Mapping[str, Any], references: Mapping[str, Any]) -> dict[str, Any]:
    flat_replay_seed, flat_replay = max(
        references["sealed_flat_weight_replay"].items(),
        key=lambda item: int(item[1]["wins"]),
    )
    return {
        "random_floor": _paired_outcomes(discovered, references["random"]),
        "fallback_floor": _paired_outcomes(discovered, references["fallback"]),
        "dumb_hand_ceiling": _paired_outcomes(discovered, references["hand_approach_ceiling"]),
        f"clean_flat_weight_replay_{flat_replay_seed}": _paired_outcomes(discovered, flat_replay),
    }


def _paired_outcomes(left: Mapping[str, Any], right: Mapping[str, Any]) -> dict[str, Any]:
    left_rows = {str(key): bool(value) for key, value in left.get("success_by_row", {}).items()}
    right_rows = {str(key): bool(value) for key, value in right.get("success_by_row", {}).items()}
    common = sorted(set(left_rows) & set(right_rows), key=lambda value: int(value))
    counts = Counter()
    for row_id in common:
        left_win = left_rows[row_id]
        right_win = right_rows[row_id]
        if left_win and right_win:
            counts["win_win"] += 1
        elif left_win and not right_win:
            counts["win_loss"] += 1
        elif not left_win and right_win:
            counts["loss_win"] += 1
        else:
            counts["loss_loss"] += 1
    return {
        "left_policy": left["policy"],
        "right_policy": right["policy"],
        "paired_row_count": len(common),
        "left_wins": int(left["wins"]),
        "right_wins": int(right["wins"]),
        "left_minus_right_wins": int(left["wins"]) - int(right["wins"]),
        "win_win": int(counts["win_win"]),
        "win_loss": int(counts["win_loss"]),
        "loss_win": int(counts["loss_win"]),
        "loss_loss": int(counts["loss_loss"]),
    }


def _evaluate_policy(
    cfg: ApproachDiscoveryProbeConfig,
    heldout_rows: Sequence[Mapping[str, Any]],
    chooser,
    *,
    policy_name: str,
) -> dict[str, Any]:
    wins = 0
    endpoints: Counter[str] = Counter()
    branch_counts: Counter[str] = Counter()
    samples: list[dict[str, Any]] = []
    plies_to_success: list[int] = []
    success_by_row: dict[str, bool] = {}
    for row in heldout_rows:
        outcome = _rollout_policy(
            cfg,
            chess.Board(str(row["fen"])),
            chooser,
            row_id=int(row["row_id"]),
        )
        wins += int(outcome["success"])
        success_by_row[str(row["row_id"])] = bool(outcome["success"])
        endpoints[outcome["endpoint"]] += 1
        branch_counts.update(outcome["branches"])
        if outcome["success"]:
            plies_to_success.append(int(outcome["plies"]))
        elif len(samples) < cfg.max_samples:
            samples.append({"fen": row["fen"], **outcome})
    total = len(heldout_rows)
    return {
        "policy": policy_name,
        "wins": wins,
        "nonwins": total - wins,
        "row_count": total,
        "win_rate": wins / max(1, total),
        "wilson_95": _wilson(wins, total),
        "endpoint_counts": dict(sorted(endpoints.items())),
        "repetition_count": int(endpoints.get("third_repetition", 0)),
        "violation_count": int(
            endpoints.get("illegal", 0)
            + endpoints.get("rook_lost", 0)
            + endpoints.get("stalemate", 0)
        ),
        "branch_counts": dict(sorted(branch_counts.items())),
        "mean_plies_to_success": None if not plies_to_success else sum(plies_to_success) / len(plies_to_success),
        "median_plies_to_success": None if not plies_to_success else sorted(plies_to_success)[len(plies_to_success) // 2],
        "failure_clusters": dict(sorted(endpoints.items())),
        "sample_nonwins": samples,
        "success_by_row": success_by_row,
    }


def _rollout_policy(
    cfg: ApproachDiscoveryProbeConfig,
    board: chess.Board,
    chooser,
    *,
    row_id: int,
) -> dict[str, Any]:
    trial = board.copy(stack=False)
    counts: Counter[Any] = Counter({trial._transposition_key(): 1})
    rng = random.Random(20274000 + row_id)
    branches: Counter[str] = Counter()
    for ply in range(cfg.horizon_white_moves * 2):
        if _waypoint_success(trial):
            return {"success": True, "endpoint": "waypoint_reached", "plies": ply, "branches": dict(branches)}
        if trial.is_stalemate():
            return {"success": False, "endpoint": "stalemate", "plies": ply, "branches": dict(branches)}
        if _rook_lost(trial):
            return {"success": False, "endpoint": "rook_lost", "plies": ply, "branches": dict(branches)}
        if not fence_established_geometry(trial):
            return {"success": False, "endpoint": "fence_broken", "plies": ply, "branches": dict(branches)}
        if trial.turn == chess.WHITE:
            move = chooser(trial, counts, row_id)
            if move is None:
                return {"success": False, "endpoint": "no_move", "plies": ply, "branches": dict(branches)}
            if move not in trial.legal_moves:
                return {"success": False, "endpoint": "illegal", "plies": ply, "branches": dict(branches)}
            key = _after_move_repetition_key(trial, move)
            if int(counts.get(key, 0)) >= 2:
                return {"success": False, "endpoint": "third_repetition", "plies": ply, "branches": dict(branches)}
            branches["white_move"] += 1
            trial.push(move)
            counts[trial._transposition_key()] += 1
        else:
            reply = _black_reply(trial, rng)
            if reply is None:
                return {
                    "success": trial.is_check(),
                    "endpoint": "no_black_reply_check" if trial.is_check() else "stalemate",
                    "plies": ply,
                    "branches": dict(branches),
                }
            trial.push(reply)
            counts[trial._transposition_key()] += 1
    return {
        "success": _waypoint_success(trial),
        "endpoint": "waypoint_reached" if _waypoint_success(trial) else "horizon",
        "plies": cfg.horizon_white_moves * 2,
        "branches": dict(branches),
    }


def _load_weight_table(path: Path) -> dict[str, float]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return {
        str(item["terminal_key"]): float(item["local_weight"])
        for item in payload["weights"]
        if not learner_visible_key_firewall_leaks([str(item["terminal_key"])])
    }


def _choose_weighted_move(
    board: chess.Board,
    counts: Mapping[Any, int],
    weights: Mapping[str, float],
) -> chess.Move | None:
    legal = _legal_without_third_repetition(board, counts)
    if not legal:
        legal = tuple(sorted(board.legal_moves, key=lambda item: item.uci()))
    rows = [
        (
            sum(weights.get(key, 0.0) * scale for key, scale in _sealed_action_key_scales(board, move)),
            move.uci(),
            move,
        )
        for move in legal
    ]
    rows.sort(reverse=True)
    return rows[0][-1] if rows else None


def _choose_fallback_move(board: chess.Board, counts: Mapping[Any, int], *, scorer) -> chess.Move | None:
    legal = tuple(sorted(board.legal_moves, key=lambda item: item.uci()))
    ordered = scorer.order_moves(board, legal)
    allowed = tuple(move for move in ordered if int(counts.get(_after_move_repetition_key(board, move), 0)) < 2)
    if allowed:
        ordered = allowed
    return ordered[0] if ordered else None


def _choose_random_move(board: chess.Board, counts: Mapping[Any, int], *, seed: int) -> chess.Move | None:
    rng = random.Random(seed)
    legal = list(_legal_without_third_repetition(board, counts))
    if not legal:
        legal = sorted(board.legal_moves, key=lambda item: item.uci())
    return None if not legal else legal[rng.randrange(len(legal))]


def _legal_without_third_repetition(board: chess.Board, counts: Mapping[Any, int]) -> tuple[chess.Move, ...]:
    return tuple(
        move
        for move in sorted(board.legal_moves, key=lambda item: item.uci())
        if int(counts.get(_after_move_repetition_key(board, move), 0)) < 2
    )


def _sealed_action_keys(board: chess.Board, move: chess.Move) -> tuple[str, ...]:
    keys = tuple(key for key, _scale in _sealed_action_key_scales(board, move))
    return keys


def _sealed_action_key_scales(board: chess.Board, move: chess.Move) -> tuple[tuple[str, float], ...]:
    cache_key = (board.fen(), move.uci())
    cached = _ACTION_KEY_SCALE_CACHE.get(cache_key)
    if cached is not None:
        return cached
    pairs = tuple((key, float(scale)) for key, scale in terminal_action_feature_keys(board, move))
    keys = tuple(key for key, _scale in pairs)
    validate_learner_visible_keys(keys, builder="approach_discovery_probe._sealed_action_keys")
    _ACTION_KEY_SCALE_CACHE[cache_key] = pairs
    return pairs


def _as_move(value: Any) -> chess.Move | None:
    if value is None:
        return None
    if isinstance(value, chess.Move):
        return value
    return chess.Move.from_uci(str(value))


def _black_reply(board: chess.Board, rng: random.Random) -> chess.Move | None:
    legal = sorted(board.legal_moves, key=lambda item: item.uci())
    return None if not legal else legal[rng.randrange(len(legal))]


def _rook_lost(board: chess.Board) -> bool:
    return not bool(board.pieces(chess.ROOK, chess.WHITE))


def _waypoint_success(board: chess.Board) -> bool:
    return bool(_king_support_waypoint_geometry(board) and fence_established_geometry(board))


def _move_int(move: chess.Move) -> int:
    return move.from_square * 64 + move.to_square


def _stable_seed(text: str) -> int:
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    return int(digest[:16], 16)


def _wilson(success: int, total: int) -> list[float]:
    if total <= 0:
        return [0.0, 0.0]
    z = 1.959963984540054
    p = success / total
    denom = 1.0 + z * z / total
    center = (p + z * z / (2 * total)) / denom
    margin = z * math.sqrt(p * (1.0 - p) / total + z * z / (4 * total * total)) / denom
    return [center - margin, center + margin]


def _evidence_summary(evidence: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    endpoints = Counter(str(item["endpoint"]) for item in evidence)
    positive = sum(1 for item in evidence if item["success"])
    total = len(evidence)
    active_keys = {key for item in evidence for key in item["keys"]}
    return {
        "action_rows": total,
        "positive_action_rows": positive,
        "negative_action_rows": total - positive,
        "positive_rate": positive / max(1, total),
        "unique_key_count": len(active_keys),
        "leaked_key_count": sum(1 for key in active_keys if learner_visible_key_firewall_leaks([key])),
        "label_endpoint_counts": dict(sorted(endpoints.items())),
    }


def _summary_tables(seed_results: Mapping[str, Any], references: Mapping[str, Any]) -> dict[str, Any]:
    eval_table = []
    for name in ("hand_approach_ceiling", "fallback", "random"):
        item = references[name]
        eval_table.append(_table_row("reference", name, item))
    for seed, item in references["sealed_flat_learned"].items():
        eval_table.append(_table_row(seed, "sealed_flat_learned", item))
    for seed, item in references["sealed_flat_weight_replay"].items():
        eval_table.append(_table_row(seed, "sealed_flat_weight_replay", item))
    for seed, result in seed_results.items():
        for name, item in result["evaluations"].items():
            eval_table.append(_table_row(seed, name, item))
    structure_table = [
        {
            "seed": seed,
            "node_count": result["structure"]["node_count"],
            "edge_count": result["structure"]["edge_count"],
            "atom_terminal_count": result["structure"]["atom_terminal_count"],
            "quorum_script_count": result["structure"]["quorum_script_count"],
            "candidate_quorum_script_count": result["structure"].get("candidate_quorum_script_count", result["structure"]["quorum_script_count"]),
            "leak_count": result["structure"]["leak_count"],
            "causal_ablation_drop": result["decision"]["causal_ablation_drop"],
            "quorum_ablation_drop": result["decision"]["quorum_ablation_drop"],
            "spawned_load_bearing_quorums": result["decision"].get("spawned_load_bearing_quorums", 0),
            "spawned_inert_quorums": result["decision"].get("spawned_inert_quorums", 0),
            "spawned_harmful_quorums": result["decision"].get("spawned_harmful_quorums", 0),
            "promoted_load_bearing_quorums": result["decision"].get("promoted_load_bearing_quorums", 0),
            "promoted_inert_quorums": result["decision"].get("promoted_inert_quorums", 0),
            "promoted_harmful_quorums": result["decision"].get("promoted_harmful_quorums", 0),
            "promoted_affordance_count": result["decision"].get("promoted_affordance_count", 0),
            "promoted_veto_count": result["decision"].get("promoted_veto_count", 0),
        }
        for seed, result in seed_results.items()
    ]
    return {
        "wins_nonwins_repetitions_violations": eval_table,
        "discovered_node_edge_counts": structure_table,
    }


def _table_row(seed: str, policy: str, item: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "seed": seed,
        "policy": policy,
        "wins": item["wins"],
        "nonwins": item["nonwins"],
        "win_rate": item["win_rate"],
        "repetitions": item["repetition_count"],
        "violations": item["violation_count"],
        "mean_plies_to_success": item["mean_plies_to_success"],
        "median_plies_to_success": item["median_plies_to_success"],
        "failure_clusters": item["failure_clusters"],
    }


def _overall_decision(seed_results: Mapping[str, Any], references: Mapping[str, Any]) -> dict[str, Any]:
    discovered_wins = [result["evaluations"]["discovered_structure"]["wins"] for result in seed_results.values()]
    ablated_wins = [result["evaluations"]["discovered_structure_ablated_all"]["wins"] for result in seed_results.values()]
    flat_wins = [item["wins"] for item in references["sealed_flat_learned"].values()]
    flat_replay_wins = [item["wins"] for item in references["sealed_flat_weight_replay"].values()]
    total = max(1, next(iter(seed_results.values()))["evaluations"]["discovered_structure"]["row_count"]) if seed_results else 1
    seed_rates = [wins / total for wins in discovered_wins]
    seed_spread = (max(seed_rates) - min(seed_rates)) if seed_rates else 0.0
    no_seed_beats_fallback = not any(wins > references["fallback"]["wins"] for wins in discovered_wins)
    seed_spread_too_wide = seed_spread > 0.15
    return {
        "all_seeds_leak_free": all(result["structure"]["leak_count"] == 0 for result in seed_results.values()),
        "all_seeds_beat_random": all(result["decision"]["beats_random"] for result in seed_results.values()),
        "all_seeds_beat_fallback": all(result["decision"]["beats_fallback"] for result in seed_results.values()),
        "all_seeds_causal": all(result["decision"]["causal_ablation_drop"] > 0 for result in seed_results.values()),
        "any_seed_competitive_with_flat_baseline": any(
            result["decision"]["competitive_with_flat_baseline"] for result in seed_results.values()
        ),
        "discovered_wins": discovered_wins,
        "ablated_wins": ablated_wins,
        "sealed_flat_wins": flat_wins,
        "sealed_flat_weight_replay_wins": flat_replay_wins,
        "hand_ceiling_wins": references["hand_approach_ceiling"]["wins"],
        "fallback_wins": references["fallback"]["wins"],
        "random_wins": references["random"]["wins"],
        "seed_success_rates": seed_rates,
        "seed_spread": seed_spread,
        "stop_rules": {
            "no_seed_beats_fallback": no_seed_beats_fallback,
            "seed_spread_gt_0_15": seed_spread_too_wide,
            "stop_required": no_seed_beats_fallback or seed_spread_too_wide,
            "action": "report_and_stop" if no_seed_beats_fallback else "report_no_tuning" if seed_spread_too_wide else "continue",
        },
    }


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
