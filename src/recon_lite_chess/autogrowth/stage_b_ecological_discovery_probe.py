"""Phase 2.9e sealed ecological discovery probe for Stage B / chase."""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
import hashlib
from itertools import combinations
import json
import math
from pathlib import Path
import random
from typing import Any, Callable, Iterable, Mapping, Sequence

import chess

from .approach_discovery_probe import _after_move_repetition_key
from .features import (
    learner_visible_key_firewall_leaks,
    validate_learner_visible_keys,
)
from .quorum_basin import (
    _edge_mate_enter_mate2_audit,
    _edge_mate_fixed_seed_black_reply,
    _position_repetition_key,
    _white_rook_square,
    fence_established_geometry,
    load_canonical_mate2_first_scorer,
    load_chain_confidence_gate,
    run_krk_policy,
)
from .terminal_substrate import terminal_action_feature_keys


DEFAULT_OUTPUT_DIR = Path(
    "reports/autogrowth/clean_slate_krk/phase2_9e_ecological_discovery"
)
DEFAULT_STAGE_B_ROWS = Path(
    "reports/autogrowth/clean_slate_krk/phase2_9_overnight/stage_b_rows.json"
)
DEFAULT_STAGE_B_BASELINE_DIR = Path(
    "reports/autogrowth/clean_slate_krk/phase2_9a_action_firewall"
)

_ACTION_KEY_SCALE_CACHE: dict[tuple[str, str], tuple[tuple[str, float], ...]] = {}
_JudgeCache = tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]


@dataclass(frozen=True)
class StageBEcologicalDiscoveryConfig:
    output_dir: str = str(DEFAULT_OUTPUT_DIR)
    stage_b_rows_path: str = str(DEFAULT_STAGE_B_ROWS)
    stage_b_baseline_dir: str = str(DEFAULT_STAGE_B_BASELINE_DIR)
    seeds: tuple[int, ...] = (20272931, 20272932, 20272933)
    flat_baseline_seeds: tuple[int, ...] = (20272911, 20272912, 20272913)
    train_row_limit: int | None = None
    heldout_row_limit: int | None = None
    horizon_plies: int = 16
    max_samples: int = 16
    max_population: int = 48
    max_births_per_decision: int = 2
    max_guided_births: int = 48
    composite_width: int = 2
    max_child_pool: int = 16
    low_margin_threshold: float = 0.035
    conflict_abs_threshold: float = 0.05
    uncertainty_min_visits: int = 3
    uncertainty_low: float = 0.35
    uncertainty_high: float = 0.65
    novelty_seen_threshold: int = 1
    initial_nutrition: float = 0.34
    mature_nutrition: float = 1.10
    passive_decay: float = 0.010
    positive_credit: float = 0.16
    negative_debt: float = 0.18
    initial_weight: float = 0.050
    nutrition_weight_scale: float = 0.035
    max_advisory_weight: float = 0.180
    atom_score_scale: float = 1.0


def run_stage_b_ecological_discovery_probe(
    *,
    config: StageBEcologicalDiscoveryConfig | None = None,
) -> dict[str, Any]:
    cfg = config or StageBEcologicalDiscoveryConfig()
    output_dir = Path(cfg.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    _write_json(output_dir / "design_spec.json", _design_spec(cfg))

    rows = json.loads(Path(cfg.stage_b_rows_path).read_text(encoding="utf-8"))
    train_rows = list(rows["train"])
    heldout_rows = list(rows["heldout"])
    if cfg.train_row_limit is not None:
        train_rows = train_rows[: int(cfg.train_row_limit)]
    if cfg.heldout_row_limit is not None:
        heldout_rows = heldout_rows[: int(cfg.heldout_row_limit)]

    references = _reference_baselines(cfg, heldout_rows)
    seed_results: dict[str, Any] = {}
    for index, seed in enumerate(cfg.seeds):
        flat_seed = int(cfg.flat_baseline_seeds[index % len(cfg.flat_baseline_seeds)])
        atom_weights = _load_weight_table(
            Path(cfg.stage_b_baseline_dir)
            / f"stage_d_B_sealed_seed_{flat_seed}_weights.json"
        )
        arm1 = _run_arm(
            cfg,
            train_rows,
            heldout_rows,
            seed=seed,
            flat_seed=flat_seed,
            atom_weights=atom_weights,
            atom_eval_reference=references["sealed_flat_weight_replay"][str(flat_seed)],
            arm="arm1_unguided_ecological",
        )
        arm2 = _run_arm(
            cfg,
            train_rows,
            heldout_rows,
            seed=seed + 10_000,
            flat_seed=flat_seed,
            atom_weights=atom_weights,
            atom_eval_reference=references["sealed_flat_weight_replay"][str(flat_seed)],
            arm="arm2_guided_residual_control",
        )
        result = {
            "schema_version": "phase2_9e_stage_b_ecological_seed.v0",
            "seed": seed,
            "flat_baseline_seed": flat_seed,
            "arm1_unguided_ecological": arm1,
            "arm2_guided_residual_control": arm2,
            "paired_vs_yardsticks": {
                "arm1": _paired_yardstick_table(arm1["evaluations"]["survivor_trial"], references),
                "arm2": _paired_yardstick_table(arm2["evaluations"]["survivor_trial"], references),
            },
            "decision": _seed_decision(arm1, arm2),
        }
        _write_json(output_dir / f"seed_{seed}_result.json", result)
        seed_results[str(seed)] = result

    summary = {
        "schema_version": "phase2_9e_stage_b_ecological_discovery.v0",
        "config": asdict(cfg),
        "dataset": {
            "source_rows_path": str(cfg.stage_b_rows_path),
            "train_count": len(train_rows),
            "heldout_count": len(heldout_rows),
            "stage_labels_learner_visible": False,
            "exact_judge_birth_control": "forbidden_in_arm1_quarantined_to_arm2",
        },
        "reference_baselines": references,
        "seed_results": seed_results,
        "tables": _summary_tables(seed_results, references),
        "decision": _overall_decision(seed_results),
    }
    _write_json(output_dir / "summary.json", summary)
    return summary


def _design_spec(cfg: StageBEcologicalDiscoveryConfig) -> dict[str, Any]:
    return {
        "schema_version": "phase2_9e_design_spec.v0",
        "rung": "Stage B / true-middle chase stratum",
        "discovery_boundary": {
            "learner_visible": [
                "board state",
                "legal moves",
                "sealed terminal_action_feature_keys",
                "atom weights from sealed Stage B learner",
                "trial composite activations and local nutrition",
            ],
            "forbidden_for_arm1_birth": [
                "stage labels",
                "selector-owner ids",
                "hand chase features as causal features",
                "exact judge failures or success labels",
                "human-selected spawn sites",
                "global top-K promotion",
            ],
            "exact_judge_use": "after-the-fact rollout outcome and heldout ablation only",
        },
        "arms": {
            "arm1_unguided_ecological": (
                "Births use learner-internal triggers only: low margin, active atom "
                "conflict, novel percept signatures, repeated trace uncertainty, and "
                "yoked random births. Survival uses local credit/debt plus passive decay."
            ),
            "arm2_guided_residual_control": (
                "Quarantined expressivity probe. Births are aimed at atom-only failure "
                "rows and must not be counted as autogrowth evidence."
            ),
        },
        "stop_rules": [
            "Arm1 population collapse-to-zero after nonzero births",
            "Arm1 cap pressure on more than half of train decisions",
            "Arm1 load-bearing count remains zero across all seeds",
        ],
        "config": asdict(cfg),
    }


def _run_arm(
    cfg: StageBEcologicalDiscoveryConfig,
    train_rows: Sequence[Mapping[str, Any]],
    heldout_rows: Sequence[Mapping[str, Any]],
    *,
    seed: int,
    flat_seed: int,
    atom_weights: Mapping[str, float],
    atom_eval_reference: Mapping[str, Any],
    arm: str,
) -> dict[str, Any]:
    rng = random.Random(seed)
    population: dict[str, dict[str, Any]] = {}
    seen_signatures: Counter[str] = Counter()
    signature_outcomes: dict[str, Counter[str]] = defaultdict(Counter)
    trigger_counts: Counter[str] = Counter()
    birth_curve: list[dict[str, Any]] = []
    traces: list[dict[str, Any]] = []
    train_judge_cache = _new_judge_cache()
    guided_plan = (
        _guided_residual_birth_plan(cfg, train_rows, atom_weights, seed=seed)
        if arm == "arm2_guided_residual_control"
        else {}
    )

    for step, row in enumerate(train_rows):
        if arm == "arm2_guided_residual_control":
            _spawn_guided_for_row(
                cfg,
                population,
                row,
                guided_plan.get(int(row["row_id"]), ()),
                step=step,
                seed=seed,
                trigger_counts=trigger_counts,
            )

        selected = _rollout_policy(
            cfg,
            row,
            lambda board, counts, row_id, ply, rng: _choose_ecological_move(
                cfg,
                board,
                counts,
                atom_weights=atom_weights,
                population=population,
                seed=seed + int(row_id) * 37 + ply,
                disabled_composite_ids=set(),
                row_id=row_id,
                ply=ply,
                spawn_hook=(
                    None
                    if arm == "arm2_guided_residual_control"
                    else lambda ctx: _spawn_arm1_from_context(
                        cfg,
                        population,
                        ctx,
                        seen_signatures=seen_signatures,
                        signature_outcomes=signature_outcomes,
                        trigger_counts=trigger_counts,
                        rng=rng,
                    )
                ),
            ),
            seed=seed + step * 31,
            collect_composites=True,
            population=population,
            judge_cache=train_judge_cache,
        )
        alternative = _rollout_policy(
            cfg,
            row,
            lambda board, counts, row_id, ply, rng: _choose_atom_move(
                board,
                counts,
                atom_weights=atom_weights,
                seed=seed + 50_000 + int(row_id) * 37 + ply,
            ),
            seed=seed + 100_000 + step * 31,
            collect_composites=True,
            population=population,
            judge_cache=train_judge_cache,
        )
        _apply_contrastive_nutrition(
            cfg,
            population,
            selected=selected,
            alternative=alternative,
            step=step,
        )
        for signature in selected["percept_signatures"]:
            signature_outcomes[signature]["success" if selected["success"] else "failure"] += 1
        _cap_population(cfg, population, step=step)
        if step % 25 == 0 or step == len(train_rows) - 1:
            birth_curve.append(_population_snapshot(population, step=step))
        if len(traces) < cfg.max_samples:
            traces.append(
                {
                    "row_id": int(row["row_id"]),
                    "selected_endpoint": selected["endpoint"],
                    "selected_success": bool(selected["success"]),
                    "alternative_endpoint": alternative["endpoint"],
                    "alternative_success": bool(alternative["success"]),
                    "reward_delta": selected["reward"] - alternative["reward"],
                    "active_composite_count": len(selected["active_composite_ids"]),
                }
            )

    survivors = [dict(item) for item in population.values() if item["state"] in {"TRIAL", "MATURE"}]
    survivors.sort(key=lambda item: (-float(item["nutrition"]), item["composite_id"]))
    structure = _structure_summary(
        cfg,
        arm=arm,
        seed=seed,
        flat_seed=flat_seed,
        atom_weights=atom_weights,
        population=population,
        survivors=survivors,
        trigger_counts=trigger_counts,
        guided_plan=guided_plan,
    )
    health = _composite_ablation_health(
        cfg,
        heldout_rows,
        atom_weights=atom_weights,
        composites=survivors,
        seed=seed + 700,
        policy_name=f"{arm}_survivor_trial",
    )
    promoted = [
        dict(item, m4_state="MATURE", heldout_counterfactual_delta=int(record["ablation_delta"]))
        for item in survivors
        for record in health["records"]
        if record["composite_id"] == item["composite_id"] and int(record["ablation_delta"]) > 0
    ]
    pruned_harmful = [
        str(record["composite_id"])
        for record in health["records"]
        if int(record["ablation_delta"]) < 0
    ]
    survivor_eval = health["full_evaluation"]
    atom_eval = {**atom_eval_reference, "policy": f"{arm}_atom_only_replay"}
    if promoted:
        promoted_eval = _evaluate_policy(
            cfg,
            heldout_rows,
            lambda board, counts, row_id, ply, rng: _choose_ecological_move(
                cfg,
                board,
                counts,
                atom_weights=atom_weights,
                population={item["composite_id"]: item for item in promoted},
                seed=seed + int(row_id) * 41 + ply,
                disabled_composite_ids=set(),
                row_id=row_id,
                ply=ply,
            ),
            seed=seed + 900,
            policy_name=f"{arm}_promoted_positive_only",
        )
    else:
        promoted_eval = {**atom_eval, "policy": f"{arm}_promoted_positive_only"}
    enrichment = _survivor_failure_enrichment(
        cfg,
        heldout_rows,
        atom_weights=atom_weights,
        composites=survivors,
        atom_eval=atom_eval,
        seed=seed + 990,
    )
    collapse = bool(structure["birth_count"] > 0 and structure["survivor_count"] == 0)
    explosion = bool(structure["survivor_count"] > cfg.max_population * 2)
    return {
        "schema_version": "phase2_9e_arm_result.v0",
        "arm": arm,
        "seed": seed,
        "flat_baseline_seed": flat_seed,
        "autogrowth_evidence": arm == "arm1_unguided_ecological",
        "uses_oracle_birth": arm == "arm2_guided_residual_control",
        "structure": structure,
        "birth_death_curve": birth_curve,
        "train_trace_sample": traces,
        "post_hoc_ablation": health,
        "promotion": {
            "rule": "promote_positive_heldout_counterfactual_delta_only",
            "promoted_count": len(promoted),
            "pruned_negative_ablation_delta_count": len(pruned_harmful),
            "pruned_negative_ablation_delta_ids": pruned_harmful[: cfg.max_samples],
        },
        "evaluations": {
            "atom_only_replay": atom_eval,
            "survivor_trial": survivor_eval,
            "promoted_positive_only": promoted_eval,
        },
        "post_hoc_failure_enrichment": enrichment,
        "load_bearing_composite_dumps": _load_bearing_dumps(
            cfg,
            heldout_rows,
            atom_weights=atom_weights,
            composites=survivors,
            health=health,
            seed=seed + 1_050,
        ),
        "stop_rule": {
            "population_collapse_to_zero": collapse,
            "unbounded_explosion_cap_pressure": explosion,
        },
    }


def _spawn_arm1_from_context(
    cfg: StageBEcologicalDiscoveryConfig,
    population: dict[str, dict[str, Any]],
    ctx: Mapping[str, Any],
    *,
    seen_signatures: Counter[str],
    signature_outcomes: Mapping[str, Counter[str]],
    trigger_counts: Counter[str],
    rng: random.Random,
) -> None:
    triggers = _internal_triggers(cfg, ctx, seen_signatures, signature_outcomes)
    signature = str(ctx["percept_signature"])
    seen_signatures[signature] += 1
    if not triggers:
        return
    spawned = 0
    for trigger in triggers:
        if spawned >= cfg.max_births_per_decision:
            break
        if _spawn_composite(
            cfg,
            population,
            _candidate_child_pool(ctx, trigger=trigger),
            trigger=trigger,
            arm="arm1_unguided_ecological",
            birth_step=int(ctx["step"]),
            birth_row_id=int(ctx["row_id"]),
            rng=rng,
            oracle_targeted=False,
            source_signature=signature,
        ):
            trigger_counts[trigger] += 1
            spawned += 1
    for _ in range(spawned):
        random_option = rng.choice(list(ctx["options"]))
        if _spawn_composite(
            cfg,
            population,
            _generic_child_pool(random_option["active_keys"]),
            trigger="random_yoked_birth",
            arm="arm1_unguided_ecological",
            birth_step=int(ctx["step"]),
            birth_row_id=int(ctx["row_id"]),
            rng=rng,
            oracle_targeted=False,
            source_signature=signature,
        ):
            trigger_counts["random_yoked_birth"] += 1
    _cap_population(cfg, population, step=int(ctx["step"]))


def _internal_triggers(
    cfg: StageBEcologicalDiscoveryConfig,
    ctx: Mapping[str, Any],
    seen_signatures: Counter[str],
    signature_outcomes: Mapping[str, Counter[str]],
) -> list[str]:
    triggers: list[str] = []
    margin = float(ctx["margin"])
    top = ctx["top_option"]
    if margin <= cfg.low_margin_threshold:
        triggers.append("low_margin_action_ranking")
    if (
        abs(float(top["positive_score"])) >= cfg.conflict_abs_threshold
        and abs(float(top["negative_score"])) >= cfg.conflict_abs_threshold
    ):
        triggers.append("conflicting_active_atoms")
    signature = str(ctx["percept_signature"])
    if int(seen_signatures[signature]) <= cfg.novelty_seen_threshold:
        triggers.append("novel_percept_signature")
    outcomes = signature_outcomes.get(signature, Counter())
    visits = int(outcomes["success"] + outcomes["failure"])
    if visits >= cfg.uncertainty_min_visits:
        rate = outcomes["success"] / max(1, visits)
        if cfg.uncertainty_low <= rate <= cfg.uncertainty_high:
            triggers.append("repeated_local_trace_uncertainty")
    return triggers


def _spawn_guided_for_row(
    cfg: StageBEcologicalDiscoveryConfig,
    population: dict[str, dict[str, Any]],
    row: Mapping[str, Any],
    plans: Sequence[Mapping[str, Any]],
    *,
    step: int,
    seed: int,
    trigger_counts: Counter[str],
) -> None:
    if not plans:
        return
    rng = random.Random(seed + int(row["row_id"]) * 101)
    for plan in plans:
        if _spawn_composite(
            cfg,
            population,
            plan["active_keys"],
            trigger="oracle_atom_failure_residual",
            arm="arm2_guided_residual_control",
            birth_step=step,
            birth_row_id=int(row["row_id"]),
            rng=rng,
            oracle_targeted=True,
            source_signature=str(plan["source_signature"]),
            target_move=str(plan["target_move"]),
        ):
            trigger_counts["oracle_atom_failure_residual"] += 1
    _cap_population(cfg, population, step=step)


def _spawn_composite(
    cfg: StageBEcologicalDiscoveryConfig,
    population: dict[str, dict[str, Any]],
    child_pool: Iterable[str],
    *,
    trigger: str,
    arm: str,
    birth_step: int,
    birth_row_id: int,
    rng: random.Random,
    oracle_targeted: bool,
    source_signature: str,
    target_move: str | None = None,
) -> bool:
    pool = tuple(dict.fromkeys(key for key in child_pool if not learner_visible_key_firewall_leaks([key])))
    if len(pool) < cfg.composite_width:
        return False
    combos = list(combinations(pool[: cfg.max_child_pool], cfg.composite_width))
    if not combos:
        return False
    children = tuple(sorted(rng.choice(combos)))
    if all(child.startswith("before_terminal:") for child in children):
        return False
    composite_id = _composite_id(arm, children)
    if composite_id in population:
        return False
    population[composite_id] = {
        "composite_id": composite_id,
        "node_type": "SCRIPT",
        "confirm_policy": "k_of_n",
        "k": len(children),
        "n": len(children),
        "children": list(children),
        "arm": arm,
        "birth_trigger": trigger,
        "birth_step": birth_step,
        "birth_row_id": birth_row_id,
        "source_signature": source_signature,
        "target_move": target_move,
        "oracle_targeted_birth": oracle_targeted,
        "nutrition": cfg.initial_nutrition,
        "state": "TRIAL",
        "credit_events": 0,
        "debt_events": 0,
        "passive_decay_events": 0,
        "activation_count": 0,
        "weight": cfg.initial_weight,
    }
    return True


def _candidate_child_pool(ctx: Mapping[str, Any], *, trigger: str) -> tuple[str, ...]:
    top = ctx["top_option"]
    second = ctx["second_option"]
    if trigger == "low_margin_action_ranking" and second is not None:
        return _generic_child_pool(set(top["active_keys"]) ^ set(second["active_keys"]))
    if trigger == "conflicting_active_atoms":
        return _generic_child_pool(top["positive_keys"] + top["negative_keys"] + top["active_keys"])
    return _generic_child_pool(top["active_keys"])


def _generic_child_pool(keys: Iterable[str]) -> tuple[str, ...]:
    scored: list[tuple[int, str]] = []
    for key in set(map(str, keys)):
        if _is_exact_coordinate_context_key(key):
            continue
        if key.startswith("action_pattern:"):
            score = 4
        elif key.startswith("delta_terminal:"):
            score = 3
        elif key.startswith("after_terminal:"):
            score = 2
        else:
            score = 1
        if _is_generic_context_key(key):
            score += 2
        scored.append((score, key))
    scored.sort(key=lambda item: (-item[0], item[1]))
    return tuple(key for _score, key in scored)


def _choose_ecological_move(
    cfg: StageBEcologicalDiscoveryConfig,
    board: chess.Board,
    counts: Mapping[Any, int],
    *,
    atom_weights: Mapping[str, float],
    population: Mapping[str, Mapping[str, Any]],
    seed: int,
    disabled_composite_ids: set[str],
    row_id: int | None = None,
    ply: int | None = None,
    spawn_hook: Callable[[Mapping[str, Any]], None] | None = None,
) -> chess.Move | None:
    options = _score_options(
        board,
        counts,
        atom_weights=atom_weights,
        composites=population.values(),
        disabled_composite_ids=disabled_composite_ids,
    )
    if not options:
        return None
    if spawn_hook is not None:
        ctx = _decision_context(
            cfg,
            board,
            counts,
            options,
            seed=seed,
            row_id=row_id,
            ply=ply,
        )
        spawn_hook(ctx)
        options = _score_options(
            board,
            counts,
            atom_weights=atom_weights,
            composites=population.values(),
            disabled_composite_ids=disabled_composite_ids,
        )
    rng = random.Random(seed)
    rows = [(float(item["score"]), rng.random(), str(item["move"]), item["move"]) for item in options]
    rows.sort(reverse=True)
    return rows[0][-1]


def _choose_atom_move(
    board: chess.Board,
    counts: Mapping[Any, int],
    *,
    atom_weights: Mapping[str, float],
    seed: int,
) -> chess.Move | None:
    options = _score_options(
        board,
        counts,
        atom_weights=atom_weights,
        composites=(),
        disabled_composite_ids=set(),
    )
    if not options:
        return None
    rng = random.Random(seed)
    rows = [(float(item["atom_score"]), rng.random(), str(item["move"]), item["move"]) for item in options]
    rows.sort(reverse=True)
    return rows[0][-1]


def _score_options(
    board: chess.Board,
    counts: Mapping[Any, int],
    *,
    atom_weights: Mapping[str, float],
    composites: Iterable[Mapping[str, Any]],
    disabled_composite_ids: set[str],
) -> list[dict[str, Any]]:
    legal = _legal_without_third_repetition(board, counts)
    if not legal:
        legal = tuple(sorted(board.legal_moves, key=lambda item: item.uci()))
    live_composites = [
        item for item in composites
        if item.get("state", "TRIAL") in {"TRIAL", "MATURE"}
        and str(item["composite_id"]) not in disabled_composite_ids
    ]
    options: list[dict[str, Any]] = []
    for move in legal:
        active_scales = _sealed_action_key_scales(board, move)
        active = {key for key, _scale in active_scales}
        pos = sum(max(0.0, atom_weights.get(key, 0.0) * scale) for key, scale in active_scales)
        neg = sum(min(0.0, atom_weights.get(key, 0.0) * scale) for key, scale in active_scales)
        atom_score = pos + neg
        active_composites = []
        composite_score = 0.0
        for comp in live_composites:
            children = tuple(map(str, comp["children"]))
            if all(child in active for child in children):
                active_composites.append(str(comp["composite_id"]))
                composite_score += _composite_weight(comp)
        options.append(
            {
                "move": move,
                "active_keys": tuple(sorted(active)),
                "active_composite_ids": tuple(sorted(active_composites)),
                "atom_score": atom_score,
                "positive_score": pos,
                "negative_score": neg,
                "positive_keys": tuple(key for key, scale in active_scales if atom_weights.get(key, 0.0) * scale > 0),
                "negative_keys": tuple(key for key, scale in active_scales if atom_weights.get(key, 0.0) * scale < 0),
                "composite_score": composite_score,
                "score": atom_score + composite_score,
            }
        )
    return options


def _decision_context(
    cfg: StageBEcologicalDiscoveryConfig,
    board: chess.Board,
    counts: Mapping[Any, int],
    options: Sequence[Mapping[str, Any]],
    *,
    seed: int,
    row_id: int | None,
    ply: int | None,
) -> dict[str, Any]:
    del cfg
    ordered = sorted(options, key=lambda item: (float(item["atom_score"]), str(item["move"])), reverse=True)
    top = ordered[0]
    second = ordered[1] if len(ordered) > 1 else None
    margin = float(top["atom_score"]) - (float(second["atom_score"]) if second is not None else 0.0)
    return {
        "board_fen": board.fen(),
        "row_id": int(row_id) if row_id is not None else _stable_seed(board.fen()) % 10_000_000,
        "step": int(ply) if ply is not None else seed % 10_000_000,
        "counts": dict(counts),
        "options": tuple(options),
        "top_option": top,
        "second_option": second,
        "margin": margin,
        "percept_signature": _percept_signature(top["active_keys"]),
    }


def _rollout_policy(
    cfg: StageBEcologicalDiscoveryConfig,
    row: Mapping[str, Any],
    chooser: Callable[[chess.Board, Mapping[Any, int], int, int, random.Random], chess.Move | None],
    *,
    seed: int,
    policy_name: str | None = None,
    collect_composites: bool = False,
    population: Mapping[str, Mapping[str, Any]] | None = None,
    judge_cache: _JudgeCache | None = None,
) -> dict[str, Any]:
    scorer = load_canonical_mate2_first_scorer()
    gate = load_chain_confidence_gate()
    del gate
    mate2_cache, enter_cache = judge_cache if judge_cache is not None else _new_judge_cache()
    board = chess.Board(str(row["fen"]))
    rng = random.Random(seed)
    counts: Counter[Any] = Counter({_position_repetition_key(board): 1, board._transposition_key(): 1})
    white_steps: list[dict[str, str]] = []
    active_composite_ids: set[str] = set()
    percept_signatures: list[str] = []
    endpoint = "horizon"
    success = False
    for ply in range(cfg.horizon_plies):
        audit = _edge_mate_enter_mate2_audit(
            board,
            scorer=scorer,
            mate2_cache=mate2_cache,
            enter_cache=enter_cache,
        )
        if audit["confirmed"]:
            endpoint = "ungated_exact_mate3_or_better_confirmed"
            success = True
            break
        if board.turn != chess.WHITE or board.is_game_over(claim_draw=False):
            endpoint = "terminal"
            break
        move = chooser(board, counts, int(row["row_id"]), ply, rng)
        if move is None or move not in board.legal_moves:
            endpoint = "illegal"
            break
        if int(counts.get(_after_move_repetition_key(board, move), 0)) >= 2:
            endpoint = "third_repetition"
            break
        if collect_composites and population:
            active = set(_sealed_action_keys(board, move))
            percept_signatures.append(_percept_signature(active))
            for comp in population.values():
                if comp.get("state") not in {"TRIAL", "MATURE"}:
                    continue
                if all(str(child) in active for child in comp["children"]):
                    active_composite_ids.add(str(comp["composite_id"]))
        white_steps.append({"fen": board.fen(), "move": move.uci()})
        board.push(move)
        counts[_position_repetition_key(board)] += 1
        counts[board._transposition_key()] += 1
        if _white_rook_square(board) is None:
            endpoint = "rook_lost"
            break
        if board.is_stalemate():
            endpoint = "stalemate"
            break
        if board.is_checkmate():
            endpoint = "mate_delivered"
            success = True
            break
        reply = _edge_mate_fixed_seed_black_reply(board, rng)
        if reply is None:
            endpoint = "mate_delivered" if board.is_check() else "stalemate"
            success = board.is_check()
            break
        board.push(reply)
        counts[_position_repetition_key(board)] += 1
        counts[board._transposition_key()] += 1
        if _white_rook_square(board) is None:
            endpoint = "rook_lost"
            break
        if board.is_stalemate():
            endpoint = "stalemate"
            break
        if not fence_established_geometry(board):
            endpoint = "fence_broken"
            break
    reward = 6.0 if success else -6.0 if endpoint in {"fence_broken", "rook_lost", "stalemate", "illegal"} else -1.0
    return {
        "policy": policy_name,
        "row_id": int(row["row_id"]),
        "success": success,
        "endpoint": endpoint,
        "reward": reward,
        "plies": len(white_steps) * 2,
        "white_steps": white_steps,
        "active_composite_ids": sorted(active_composite_ids),
        "percept_signatures": percept_signatures,
    }


def _evaluate_policy(
    cfg: StageBEcologicalDiscoveryConfig,
    rows: Sequence[Mapping[str, Any]],
    chooser: Callable[[chess.Board, Mapping[Any, int], int, int, random.Random], chess.Move | None],
    *,
    seed: int,
    policy_name: str,
    judge_cache: _JudgeCache | None = None,
    collect_composites: bool = False,
    population: Mapping[str, Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    endpoints: Counter[str] = Counter()
    success_by_row: dict[str, bool] = {}
    samples: list[dict[str, Any]] = []
    plies_to_success: list[int] = []
    active_composite_ids: set[str] = set()
    active_judge_cache = judge_cache if judge_cache is not None else _new_judge_cache()
    for index, row in enumerate(rows):
        outcome = _rollout_policy(
            cfg,
            row,
            chooser,
            seed=seed + index * 31,
            policy_name=policy_name,
            judge_cache=active_judge_cache,
            collect_composites=collect_composites,
            population=population,
        )
        active_composite_ids.update(map(str, outcome.get("active_composite_ids", ())))
        success_by_row[str(row["row_id"])] = bool(outcome["success"])
        endpoints[str(outcome["endpoint"])] += 1
        if outcome["success"]:
            plies_to_success.append(int(outcome["plies"]))
        elif len(samples) < cfg.max_samples:
            samples.append(
                {
                    "fen": row["fen"],
                    "endpoint": outcome["endpoint"],
                    "white_steps": outcome["white_steps"],
                }
            )
    wins = sum(int(value) for value in success_by_row.values())
    total = len(rows)
    return {
        "policy": policy_name,
        "wins": wins,
        "nonwins": total - wins,
        "row_count": total,
        "win_rate": wins / max(1, total),
        "wilson_95": _wilson(wins, total),
        "endpoint_counts": dict(sorted(endpoints.items())),
        "success_by_row": success_by_row,
        "active_composite_ids": sorted(active_composite_ids),
        "mean_plies_to_success": None if not plies_to_success else sum(plies_to_success) / len(plies_to_success),
        "sample_nonwins": samples,
    }


def _apply_contrastive_nutrition(
    cfg: StageBEcologicalDiscoveryConfig,
    population: dict[str, dict[str, Any]],
    *,
    selected: Mapping[str, Any],
    alternative: Mapping[str, Any],
    step: int,
) -> None:
    selected_ids = set(map(str, selected["active_composite_ids"]))
    alternative_ids = set(map(str, alternative["active_composite_ids"]))
    reward_delta = float(selected["reward"]) - float(alternative["reward"])
    for comp in population.values():
        if comp["state"] not in {"TRIAL", "MATURE"}:
            continue
        comp["nutrition"] = float(comp["nutrition"]) - cfg.passive_decay
        comp["passive_decay_events"] = int(comp["passive_decay_events"]) + 1
        cid = str(comp["composite_id"])
        if cid in selected_ids:
            comp["activation_count"] = int(comp["activation_count"]) + 1
            if reward_delta > 0:
                comp["nutrition"] = float(comp["nutrition"]) + cfg.positive_credit
                comp["credit_events"] = int(comp["credit_events"]) + 1
            elif reward_delta < 0:
                comp["nutrition"] = float(comp["nutrition"]) - cfg.negative_debt
                comp["debt_events"] = int(comp["debt_events"]) + 1
        if cid in alternative_ids and reward_delta > 0:
            comp["nutrition"] = float(comp["nutrition"]) - cfg.negative_debt
            comp["debt_events"] = int(comp["debt_events"]) + 1
        if float(comp["nutrition"]) >= cfg.mature_nutrition:
            comp["state"] = "MATURE"
        if float(comp["nutrition"]) <= 0.0:
            comp["state"] = "PRUNED"
            comp["prune_reason"] = "nutrition_depleted"
            comp["pruned_step"] = step
        else:
            comp["weight"] = _composite_weight(comp, cfg=cfg)


def _cap_population(
    cfg: StageBEcologicalDiscoveryConfig,
    population: dict[str, dict[str, Any]],
    *,
    step: int,
) -> None:
    live_trial = [
        item for item in population.values()
        if item["state"] == "TRIAL"
    ]
    overflow = len(live_trial) - cfg.max_population
    if overflow <= 0:
        return
    live_trial.sort(key=lambda item: (float(item["nutrition"]), int(item["birth_step"]), item["composite_id"]))
    for item in live_trial[:overflow]:
        item["state"] = "PRUNED"
        item["prune_reason"] = "immature_population_cap"
        item["pruned_step"] = step


def _composite_ablation_health(
    cfg: StageBEcologicalDiscoveryConfig,
    rows: Sequence[Mapping[str, Any]],
    *,
    atom_weights: Mapping[str, float],
    composites: Sequence[Mapping[str, Any]],
    seed: int,
    policy_name: str,
) -> dict[str, Any]:
    population = {str(item["composite_id"]): dict(item) for item in composites}
    judge_cache = _new_judge_cache()
    full_eval = _evaluate_policy(
        cfg,
        rows,
        lambda board, counts, row_id, ply, rng: _choose_ecological_move(
            cfg,
            board,
            counts,
            atom_weights=atom_weights,
            population=population,
            seed=seed + int(row_id) * 47 + ply,
            disabled_composite_ids=set(),
            row_id=row_id,
            ply=ply,
        ),
        seed=seed,
        policy_name=policy_name,
        judge_cache=judge_cache,
        collect_composites=True,
        population=population,
    )
    active_on_full = set(map(str, full_eval.get("active_composite_ids", ())))
    records: list[dict[str, Any]] = []
    counts: Counter[str] = Counter()
    for comp in composites:
        cid = str(comp["composite_id"])
        if cid in active_on_full:
            ablated = _evaluate_policy(
                cfg,
                rows,
                lambda board, counts, row_id, ply, rng, cid=cid: _choose_ecological_move(
                    cfg,
                    board,
                    counts,
                    atom_weights=atom_weights,
                    population=population,
                    seed=seed + int(row_id) * 47 + ply,
                    disabled_composite_ids={cid},
                    row_id=row_id,
                    ply=ply,
                ),
                seed=seed,
                policy_name=f"{policy_name}_without_{cid}",
                judge_cache=judge_cache,
            )
            ablated_wins = int(ablated["wins"])
            delta = int(full_eval["wins"]) - ablated_wins
        else:
            ablated_wins = int(full_eval["wins"])
            delta = 0
        classification = "load_bearing" if delta > 0 else "inert" if delta == 0 else "harmful"
        counts[classification] += 1
        records.append(
            {
                "composite_id": cid,
                "classification": classification,
                "full_wins": int(full_eval["wins"]),
                "ablated_wins": ablated_wins,
                "ablation_delta": delta,
                "active_on_full_heldout": cid in active_on_full,
                "birth_trigger": comp.get("birth_trigger"),
                "state": comp.get("state"),
                "nutrition": float(comp.get("nutrition", 0.0)),
                "children": list(comp.get("children", ())),
            }
        )
    return {
        "policy": policy_name,
        "composite_count": len(composites),
        "full_wins": int(full_eval["wins"]),
        "full_evaluation": full_eval,
        "load_bearing_count": int(counts["load_bearing"]),
        "inert_count": int(counts["inert"]),
        "harmful_count": int(counts["harmful"]),
        "nontrivial_delta_count": int(counts["load_bearing"] + counts["harmful"]),
        "records": records,
    }


def _guided_residual_birth_plan(
    cfg: StageBEcologicalDiscoveryConfig,
    rows: Sequence[Mapping[str, Any]],
    atom_weights: Mapping[str, float],
    *,
    seed: int,
) -> dict[int, list[dict[str, Any]]]:
    plan: dict[int, list[dict[str, Any]]] = defaultdict(list)
    budget = cfg.max_guided_births
    judge_cache = _new_judge_cache()
    for index, row in enumerate(rows):
        if budget <= 0:
            break
        atom_outcome = _rollout_policy(
            cfg,
            row,
            lambda board, counts, row_id, ply, rng: _choose_atom_move(
                board,
                counts,
                atom_weights=atom_weights,
                seed=seed + int(row_id) * 53 + ply,
            ),
            seed=seed + index * 17,
            judge_cache=judge_cache,
        )
        if atom_outcome["success"]:
            continue
        board = chess.Board(str(row["fen"]))
        options = _score_options(
            board,
            Counter({_position_repetition_key(board): 1, board._transposition_key(): 1}),
            atom_weights=atom_weights,
            composites=(),
            disabled_composite_ids=set(),
        )
        candidates: list[tuple[int, float, str, Mapping[str, Any]]] = []
        for option in options:
            forced = _rollout_forced_first_move(
                cfg,
                row,
                chess.Move.from_uci(str(option["move"])),
                atom_weights=atom_weights,
                seed=seed + index * 19,
                judge_cache=judge_cache,
            )
            candidates.append((int(forced["success"]), float(option["atom_score"]), str(option["move"]), option))
        candidates.sort(reverse=True)
        if not candidates or candidates[0][0] <= 0:
            continue
        option = candidates[0][-1]
        plan[int(row["row_id"])].append(
            {
                "target_move": str(option["move"]),
                "active_keys": _generic_child_pool(option["active_keys"]),
                "source_signature": _percept_signature(option["active_keys"]),
            }
        )
        budget -= 1
    return plan


def _rollout_forced_first_move(
    cfg: StageBEcologicalDiscoveryConfig,
    row: Mapping[str, Any],
    first_move: chess.Move,
    *,
    atom_weights: Mapping[str, float],
    seed: int,
    judge_cache: _JudgeCache | None = None,
) -> dict[str, Any]:
    used = False

    def chooser(
        board: chess.Board,
        counts: Mapping[Any, int],
        row_id: int,
        ply: int,
        rng: random.Random,
    ) -> chess.Move | None:
        nonlocal used
        if not used:
            used = True
            return first_move if first_move in board.legal_moves else None
        del rng
        return _choose_atom_move(board, counts, atom_weights=atom_weights, seed=seed + row_id * 59 + ply)

    return _rollout_policy(cfg, row, chooser, seed=seed, judge_cache=judge_cache)


def _reference_baselines(
    cfg: StageBEcologicalDiscoveryConfig,
    heldout_rows: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    scorer = load_canonical_mate2_first_scorer()
    gate = load_chain_confidence_gate()
    baseline_dir = Path(cfg.stage_b_baseline_dir)
    references: dict[str, Any] = {
        "fallback": _evaluate_policy(
            cfg,
            heldout_rows,
            lambda board, counts, row_id, ply, rng: _choose_fallback_move(board, counts, scorer=scorer),
            seed=20272900,
            policy_name="fallback_floor",
        ),
        "random": _evaluate_policy(
            cfg,
            heldout_rows,
            lambda board, counts, row_id, ply, rng: _choose_random_move(board, counts, rng=rng),
            seed=20272901,
            policy_name="random_floor",
        ),
        "dispatcher": _evaluate_policy(
            cfg,
            heldout_rows,
            lambda board, counts, row_id, ply, rng: _choose_dispatcher_move(
                board,
                counts,
                scorer=scorer,
                gate=gate,
            ),
            seed=20272902,
            policy_name="dispatcher_with_approach",
        ),
        "sealed_flat_weight_replay": {},
        "official_stage_b_flat": {},
    }
    for seed in cfg.flat_baseline_seeds:
        artifact_path = baseline_dir / f"stage_b_sealed_seed_{seed}.json"
        references["official_stage_b_flat"][str(seed)] = _load_official_flat_artifact(
            artifact_path,
            seed=seed,
        )
        weights = _load_weight_table(
            baseline_dir / f"stage_d_B_sealed_seed_{seed}_weights.json"
        )
        references["sealed_flat_weight_replay"][str(seed)] = _evaluate_policy(
            cfg,
            heldout_rows,
            lambda board, counts, row_id, ply, rng, weights=weights: _choose_atom_move(
                board,
                counts,
                atom_weights=weights,
                seed=seed + int(row_id) * 61 + ply,
            ),
            seed=seed + 700,
            policy_name=f"sealed_flat_weight_replay_{seed}",
        )
    return references


def _choose_fallback_move(board: chess.Board, counts: Mapping[Any, int], *, scorer) -> chess.Move | None:
    legal = _legal_without_third_repetition(board, counts)
    if not legal:
        legal = tuple(sorted(board.legal_moves, key=lambda item: item.uci()))
    ordered = scorer.order_moves(board, legal)
    return ordered[0] if ordered else None


def _choose_random_move(
    board: chess.Board,
    counts: Mapping[Any, int],
    *,
    rng: random.Random,
) -> chess.Move | None:
    legal = list(_legal_without_third_repetition(board, counts))
    if not legal:
        legal = sorted(board.legal_moves, key=lambda item: item.uci())
    return None if not legal else legal[rng.randrange(len(legal))]


def _choose_dispatcher_move(
    board: chess.Board,
    counts: Mapping[Any, int],
    *,
    scorer,
    gate: Mapping[str, Any],
) -> chess.Move | None:
    result = run_krk_policy(
        board,
        gate=gate,
        scorer=scorer,
        record_trace=False,
        repetition_counts=counts,
        mate2_cache={},
        enter_cache={},
        enable_chase=True,
        enable_approach=True,
    )
    move = result.get("bound_move")
    if move is None:
        return _choose_fallback_move(board, counts, scorer=scorer)
    parsed = chess.Move.from_uci(str(move))
    return parsed if parsed in board.legal_moves else None


def _load_official_flat_artifact(path: Path, *, seed: int) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    heldout = payload["heldout_eval"]
    wins = int(heldout["success_count"])
    total = int(heldout["row_count"])
    return {
        "policy": f"official_stage_b_flat_{seed}",
        "artifact_path": str(path),
        "wins": wins,
        "nonwins": total - wins,
        "row_count": total,
        "win_rate": wins / max(1, total),
        "wilson_95": _wilson(wins, total),
        "endpoint_counts": dict(sorted(heldout["endpoint_counts"].items())),
        "success_by_row": {},
    }


def _load_weight_table(path: Path) -> dict[str, float]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    raw = {
        str(item["terminal_key"]): float(item["local_weight"])
        for item in payload["weights"]
        if not learner_visible_key_firewall_leaks([str(item["terminal_key"])])
    }
    max_abs = max((abs(value) for value in raw.values()), default=1.0)
    if max_abs <= 0.0:
        max_abs = 1.0
    return {key: value / max_abs for key, value in raw.items()}


def _new_judge_cache() -> _JudgeCache:
    return ({}, {})


def _structure_summary(
    cfg: StageBEcologicalDiscoveryConfig,
    *,
    arm: str,
    seed: int,
    flat_seed: int,
    atom_weights: Mapping[str, float],
    population: Mapping[str, Mapping[str, Any]],
    survivors: Sequence[Mapping[str, Any]],
    trigger_counts: Mapping[str, int],
    guided_plan: Mapping[int, Sequence[Mapping[str, Any]]],
) -> dict[str, Any]:
    all_children = sorted({child for comp in survivors for child in comp["children"]})
    counts = Counter(str(item["state"]) for item in population.values())
    return {
        "schema_version": "phase2_9e_structure_summary.v0",
        "arm": arm,
        "seed": seed,
        "flat_baseline_seed": flat_seed,
        "atom_terminal_count": len(atom_weights),
        "birth_count": len(population),
        "survivor_count": len(survivors),
        "mature_count": int(counts["MATURE"]),
        "trial_count": int(counts["TRIAL"]),
        "pruned_count": int(counts["PRUNED"]),
        "cap_pruned_count": sum(1 for item in population.values() if item.get("prune_reason") == "immature_population_cap"),
        "oracle_targeted_birth_count": sum(1 for item in population.values() if item.get("oracle_targeted_birth")),
        "trigger_distribution": dict(sorted(trigger_counts.items())),
        "error_set_targeted_birth_count": sum(len(items) for items in guided_plan.values()),
        "elsewhere_birth_count": len(population) - sum(1 for item in population.values() if item.get("oracle_targeted_birth")),
        "leak_count": sum(1 for key in all_children if learner_visible_key_firewall_leaks([key])),
        "node_count": 1 + len(all_children) + len(survivors),
        "edge_count": len(survivors) + sum(len(item["children"]) for item in survivors),
        "top_survivors": [
            {
                "composite_id": item["composite_id"],
                "state": item["state"],
                "birth_trigger": item["birth_trigger"],
                "nutrition": round(float(item["nutrition"]), 6),
                "weight": round(_composite_weight(item), 6),
                "activation_count": int(item.get("activation_count", 0)),
                "children": list(item["children"]),
            }
            for item in survivors[:16]
        ],
    }


def _population_snapshot(population: Mapping[str, Mapping[str, Any]], *, step: int) -> dict[str, Any]:
    counts = Counter(str(item["state"]) for item in population.values())
    return {
        "step": step,
        "births_total": len(population),
        "alive_total": int(counts["TRIAL"] + counts["MATURE"]),
        "trial": int(counts["TRIAL"]),
        "mature": int(counts["MATURE"]),
        "pruned": int(counts["PRUNED"]),
    }


def _survivor_failure_enrichment(
    cfg: StageBEcologicalDiscoveryConfig,
    heldout_rows: Sequence[Mapping[str, Any]],
    *,
    atom_weights: Mapping[str, float],
    composites: Sequence[Mapping[str, Any]],
    atom_eval: Mapping[str, Any],
    seed: int,
) -> dict[str, Any]:
    del cfg
    failure_rows = {int(row_id) for row_id, ok in atom_eval.get("success_by_row", {}).items() if not ok}
    success_rows = {int(row_id) for row_id, ok in atom_eval.get("success_by_row", {}).items() if ok}
    fire_failure = Counter()
    fire_success = Counter()
    by_id = {str(item["composite_id"]): item for item in composites}
    for row in heldout_rows:
        board = chess.Board(str(row["fen"]))
        move = _choose_atom_move(
            board,
            Counter({_position_repetition_key(board): 1, board._transposition_key(): 1}),
            atom_weights=atom_weights,
            seed=seed + int(row["row_id"]),
        )
        if move is None:
            continue
        active = set(_sealed_action_keys(board, move))
        for cid, comp in by_id.items():
            if all(str(child) in active for child in comp["children"]):
                if int(row["row_id"]) in failure_rows:
                    fire_failure[cid] += 1
                elif int(row["row_id"]) in success_rows:
                    fire_success[cid] += 1
    return {
        "atom_failure_row_count": len(failure_rows),
        "atom_success_row_count": len(success_rows),
        "survivor_count": len(composites),
        "survivors_firing_on_atom_failure_count": sum(1 for cid in by_id if fire_failure[cid] > 0),
        "survivors_firing_on_atom_success_count": sum(1 for cid in by_id if fire_success[cid] > 0),
        "top_enriched": [
            {
                "composite_id": cid,
                "failure_fires": int(fire_failure[cid]),
                "success_fires": int(fire_success[cid]),
            }
            for cid in sorted(by_id, key=lambda item: (fire_failure[item], -fire_success[item], item), reverse=True)[:8]
        ],
    }


def _load_bearing_dumps(
    cfg: StageBEcologicalDiscoveryConfig,
    heldout_rows: Sequence[Mapping[str, Any]],
    *,
    atom_weights: Mapping[str, float],
    composites: Sequence[Mapping[str, Any]],
    health: Mapping[str, Any],
    seed: int,
) -> list[dict[str, Any]]:
    del cfg, seed
    by_id = {str(item["composite_id"]): item for item in composites}
    load_bearing = [
        record for record in health["records"]
        if record["classification"] == "load_bearing"
    ]
    dumps: list[dict[str, Any]] = []
    for record in load_bearing:
        comp = by_id[str(record["composite_id"])]
        firing_cluster = []
        for row in heldout_rows:
            board = chess.Board(str(row["fen"]))
            options = _score_options(
                board,
                Counter({_position_repetition_key(board): 1, board._transposition_key(): 1}),
                atom_weights=atom_weights,
                composites=[comp],
                disabled_composite_ids=set(),
            )
            fires = [
                str(option["move"])
                for option in options
                if str(comp["composite_id"]) in option["active_composite_ids"]
            ]
            if fires:
                firing_cluster.append(
                    {
                        "row_id": int(row["row_id"]),
                        "fen": row["fen"],
                        "firing_moves": fires[:4],
                    }
                )
            if len(firing_cluster) >= 6:
                break
        dumps.append(
            {
                "composite_id": comp["composite_id"],
                "ablation_delta": int(record["ablation_delta"]),
                "birth_trigger": comp.get("birth_trigger"),
                "children": list(comp["children"]),
                "firing_cluster": firing_cluster,
            }
        )
    return dumps


def _paired_yardstick_table(discovered: Mapping[str, Any], references: Mapping[str, Any]) -> dict[str, Any]:
    flat_seed, flat = max(
        references["sealed_flat_weight_replay"].items(),
        key=lambda item: int(item[1]["wins"]),
    )
    return {
        "random_floor": _paired_outcomes(discovered, references["random"]),
        "fallback_floor": _paired_outcomes(discovered, references["fallback"]),
        "dispatcher": _paired_outcomes(discovered, references["dispatcher"]),
        f"clean_flat_weight_replay_{flat_seed}": _paired_outcomes(discovered, flat),
    }


def _paired_outcomes(left: Mapping[str, Any], right: Mapping[str, Any]) -> dict[str, Any]:
    left_rows = {str(key): bool(value) for key, value in left.get("success_by_row", {}).items()}
    right_rows = {str(key): bool(value) for key, value in right.get("success_by_row", {}).items()}
    common = sorted(set(left_rows) & set(right_rows), key=lambda item: int(item))
    counts = Counter()
    for row_id in common:
        pair = (left_rows[row_id], right_rows[row_id])
        if pair == (True, True):
            counts["win_win"] += 1
        elif pair == (True, False):
            counts["win_loss"] += 1
        elif pair == (False, True):
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


def _summary_tables(seed_results: Mapping[str, Any], references: Mapping[str, Any]) -> dict[str, Any]:
    rows = []
    for seed, result in seed_results.items():
        for arm_name in ("arm1_unguided_ecological", "arm2_guided_residual_control"):
            arm = result[arm_name]
            health = arm["post_hoc_ablation"]
            eval_row = arm["evaluations"]["survivor_trial"]
            rows.append(
                {
                    "seed": int(seed),
                    "arm": arm_name,
                    "wins": int(eval_row["wins"]),
                    "row_count": int(eval_row["row_count"]),
                    "win_rate": float(eval_row["win_rate"]),
                    "load_bearing": int(health["load_bearing_count"]),
                    "inert": int(health["inert_count"]),
                    "harmful": int(health["harmful_count"]),
                    "births": int(arm["structure"]["birth_count"]),
                    "survivors": int(arm["structure"]["survivor_count"]),
                    "mature": int(arm["structure"]["mature_count"]),
                    "pruned": int(arm["structure"]["pruned_count"]),
                }
            )
    yardsticks = {
        "random": _compact_eval(references["random"]),
        "fallback": _compact_eval(references["fallback"]),
        "dispatcher": _compact_eval(references["dispatcher"]),
        "flat_replays": {
            seed: _compact_eval(item)
            for seed, item in references["sealed_flat_weight_replay"].items()
        },
        "official_flat": {
            seed: _compact_eval(item)
            for seed, item in references["official_stage_b_flat"].items()
        },
    }
    return {"arm_seed_table": rows, "yardsticks": yardsticks}


def _seed_decision(arm1: Mapping[str, Any], arm2: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "arm1_load_bearing_gt_zero": int(arm1["post_hoc_ablation"]["load_bearing_count"]) > 0,
        "arm2_load_bearing_gt_zero": int(arm2["post_hoc_ablation"]["load_bearing_count"]) > 0,
        "arm1_population_collapse": bool(arm1["stop_rule"]["population_collapse_to_zero"]),
        "arm1_unbounded_explosion": bool(arm1["stop_rule"]["unbounded_explosion_cap_pressure"]),
    }


def _overall_decision(seed_results: Mapping[str, Any]) -> dict[str, Any]:
    arm1_load = [
        int(result["arm1_unguided_ecological"]["post_hoc_ablation"]["load_bearing_count"])
        for result in seed_results.values()
    ]
    arm2_load = [
        int(result["arm2_guided_residual_control"]["post_hoc_ablation"]["load_bearing_count"])
        for result in seed_results.values()
    ]
    arm1_wins = [
        int(result["arm1_unguided_ecological"]["evaluations"]["survivor_trial"]["wins"])
        for result in seed_results.values()
    ]
    collapse = any(
        bool(result["arm1_unguided_ecological"]["stop_rule"]["population_collapse_to_zero"])
        for result in seed_results.values()
    )
    explosion = any(
        bool(result["arm1_unguided_ecological"]["stop_rule"]["unbounded_explosion_cap_pressure"])
        for result in seed_results.values()
    )
    if any(count > 0 for count in arm1_load):
        interpretation = "arm1_discovery_positive_audit_survivors"
    elif any(count > 0 for count in arm2_load):
        interpretation = "substrate_can_express_useful_composite_ecology_too_weak"
    else:
        interpretation = "flat_substrate_did_not_host_load_bearing_composition_step5_required"
    return {
        "arm1_load_bearing_counts": arm1_load,
        "arm2_load_bearing_counts": arm2_load,
        "arm1_wins": arm1_wins,
        "arm1_seed_spread": 0 if not arm1_wins else max(arm1_wins) - min(arm1_wins),
        "population_collapse_stop": collapse,
        "unbounded_explosion_stop": explosion,
        "all_arm1_load_bearing_zero": all(count == 0 for count in arm1_load),
        "interpretation": interpretation,
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


def _legal_without_third_repetition(board: chess.Board, counts: Mapping[Any, int]) -> tuple[chess.Move, ...]:
    return tuple(
        move
        for move in sorted(board.legal_moves, key=lambda item: item.uci())
        if int(counts.get(_after_move_repetition_key(board, move), 0)) < 2
    )


def _sealed_action_keys(board: chess.Board, move: chess.Move) -> tuple[str, ...]:
    return tuple(key for key, _scale in _sealed_action_key_scales(board, move))


def _sealed_action_key_scales(board: chess.Board, move: chess.Move) -> tuple[tuple[str, float], ...]:
    cache_key = (board.fen(), move.uci())
    cached = _ACTION_KEY_SCALE_CACHE.get(cache_key)
    if cached is not None:
        return cached
    pairs = tuple((key, float(scale)) for key, scale in terminal_action_feature_keys(board, move))
    keys = tuple(key for key, _scale in pairs)
    validate_learner_visible_keys(keys, builder="stage_b_ecological_discovery_probe._sealed_action_keys")
    _ACTION_KEY_SCALE_CACHE[cache_key] = pairs
    return pairs


def _composite_weight(
    comp: Mapping[str, Any],
    *,
    cfg: StageBEcologicalDiscoveryConfig | None = None,
) -> float:
    if cfg is None:
        return float(comp.get("weight", 0.0))
    nutrition = max(0.0, float(comp.get("nutrition", 0.0)))
    return min(cfg.max_advisory_weight, cfg.initial_weight + nutrition * cfg.nutrition_weight_scale)


def _composite_id(arm: str, children: Sequence[str]) -> str:
    digest = hashlib.sha256((arm + "\n" + "\n".join(children)).encode("utf-8")).hexdigest()
    prefix = "eco" if arm == "arm1_unguided_ecological" else "guided"
    return f"stage_b_{prefix}_quorum_{digest[:12]}"


def _percept_signature(keys: Iterable[str]) -> str:
    before = [
        key for key in map(str, keys)
        if key.startswith("before_terminal:")
        and _is_generic_context_key(key)
        and not _is_exact_coordinate_context_key(key)
    ]
    if not before:
        before = [
            key for key in map(str, keys)
            if key.startswith("before_terminal:")
            and not _is_exact_coordinate_context_key(key)
        ]
    digest = hashlib.sha256("\n".join(sorted(set(before))[:16]).encode("utf-8")).hexdigest()
    return f"percept_{digest[:12]}"


def _is_generic_context_key(key: str) -> bool:
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
        "black_king",
        "white_king",
        "white_rook",
    )
    return any(fragment in key for fragment in fragments)


def _is_exact_coordinate_context_key(key: str) -> bool:
    name = key.split(":", 1)[-1].split("=", 1)[0]
    return name.endswith("_file") or name.endswith("_rank")


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


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
