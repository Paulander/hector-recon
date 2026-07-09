"""Clean engine-native planted-composition certification.

The learner sees anonymous binary atoms and scalar final action success only.
The planted XOR rule is used solely by the task evaluator and oracle arm.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from hashlib import sha256
from itertools import combinations, product
import json
import math
from pathlib import Path
import random
from typing import Any, Iterable, Mapping, Sequence

from recon_lite import FormalReConEngine, Graph, Node, NodeState, NodeType

from recon_lite_chess.autogrowth.measurement_integrity import (
    assert_complete_arm_record,
    assert_noop_parity,
    holm_adjusted_pvalues,
    paired_binary_outcomes,
    validate_split_ids,
)
from recon_lite_hector.nodes import StemCellState, StemCellTerminal


@dataclass(frozen=True)
class BenchmarkConfig:
    output_dir: str = "reports/planted_composition_certification"
    dataset_salt: str = "certification-v1-frozen"
    seeds: tuple[int, ...] = (11, 23, 37, 41, 53)
    train_groups: int = 8
    validation_groups: int = 4
    final_test_groups: int = 8
    discovery_top_k: int = 8
    tick_budget: int = 12
    primary_alpha: float = 0.05


@dataclass(frozen=True)
class BenchmarkRow:
    row_id: int
    split: str
    group_id: str
    atoms: Mapping[str, bool]
    correct_action: str


@dataclass(frozen=True)
class NativeEvaluation:
    confirmed: bool
    predicate_evaluated_ids: tuple[str, ...]
    trace_digest: str
    root_state: str


@dataclass(frozen=True)
class Prediction:
    action: str
    active_ids: tuple[str, ...]
    predicate_evaluated_ids: tuple[str, ...]
    trace_digest: str


@dataclass(frozen=True)
class CandidateSpec:
    operator: str
    members: tuple[str, str]
    k: int | None = None

    @property
    def candidate_id(self) -> str:
        payload = json.dumps(asdict(self), sort_keys=True, separators=(",", ":"))
        return f"candidate_{sha256(payload.encode()).hexdigest()[:12]}"


class NativeBooleanComposite:
    """A materialized SCRIPT with real atom/literal TERMINAL children."""

    def __init__(
        self,
        cell_id: str,
        literals: Sequence[tuple[str, bool]],
        *,
        operator: str,
        k: int | None = None,
        tick_budget: int = 12,
    ) -> None:
        self.cell_id = str(cell_id)
        self.literals = tuple((str(atom_id), bool(value)) for atom_id, value in literals)
        self.operator = str(operator)
        self.k = k
        self.tick_budget = int(tick_budget)
        self.graph = Graph()
        meta: dict[str, Any] = {"confirm_policy": self.operator, "origin": "planted_composition"}
        if self.operator == "k_of_n":
            meta["confirm_k"] = int(k if k is not None else 1)
        self.graph.add_node(Node(self.cell_id, NodeType.SCRIPT, meta=meta))
        self.terminal_ids: list[str] = []
        for index, (atom_id, expected) in enumerate(self.literals):
            terminal_id = f"{self.cell_id}:literal:{index}"
            self.terminal_ids.append(terminal_id)

            def predicate(_node: Node, env: Mapping[str, Any], *, key: str = atom_id, value: bool = expected) -> tuple[bool, bool]:
                return True, bool(env["atoms"].get(key, False)) is value

            self.graph.add_node(
                Node(
                    terminal_id,
                    NodeType.TERMINAL,
                    predicate=predicate,
                    meta={"atom_id": atom_id, "expected_value": expected, "origin": "planted_composition"},
                )
            )
            self.graph.add_hierarchy_pair(self.cell_id, terminal_id)

    def evaluate(self, atoms: Mapping[str, bool]) -> NativeEvaluation:
        for node in self.graph.nodes.values():
            node.state = NodeState.INACTIVE
            node.tick_entered = 0
            node.activation.value = 0.0
            node.activation.target = 0.0
        engine = FormalReConEngine(self.graph, record_trace=True)
        engine.request(self.cell_id)
        engine.run(
            max_ticks=self.tick_budget,
            env={"atoms": dict(atoms)},
            until=lambda formal: formal.g.nodes[self.cell_id].state in {NodeState.CONFIRMED, NodeState.FAILED},
        )
        root_state = self.graph.nodes[self.cell_id].state
        evaluated = tuple(
            terminal_id
            for terminal_id in self.terminal_ids
            if self.graph.nodes[terminal_id].state != NodeState.INACTIVE
        )
        trace_payload = {
            "cell_id": self.cell_id,
            "root_state": root_state.name,
            "terminal_states": {terminal_id: self.graph.nodes[terminal_id].state.name for terminal_id in self.terminal_ids},
            "messages": [message for frame in engine.trace for message in frame.get("messages", ())],
        }
        return NativeEvaluation(
            confirmed=root_state == NodeState.CONFIRMED,
            predicate_evaluated_ids=evaluated,
            trace_digest=_hash_json(trace_payload),
            root_state=root_state.name,
        )


class AtomOnlyPolicy:
    def __init__(self, weights: Mapping[str, int]) -> None:
        self.weights = dict(weights)
        self.name = "atom_only"

    def predict(self, row: BenchmarkRow) -> Prediction:
        score = sum(int(weight) * (1 if row.atoms[atom_id] else -1) for atom_id, weight in self.weights.items())
        action = "A" if score > 0 else "B"
        payload = {"policy": self.name, "score": score, "action": action, "atoms": row.atoms}
        return Prediction(action, (), tuple(sorted(self.weights)), _hash_json(payload))


class CompositePolicy:
    def __init__(self, composite: NativeBooleanComposite, *, name: str, fallback: AtomOnlyPolicy | None = None) -> None:
        self.composite = composite
        self.name = name
        self.fallback = fallback

    def predict(self, row: BenchmarkRow) -> Prediction:
        result = self.composite.evaluate(row.atoms)
        action = "A" if result.confirmed else "B"
        return Prediction(
            action,
            (self.composite.cell_id,) if result.confirmed else (),
            result.predicate_evaluated_ids,
            result.trace_digest,
        )


@dataclass(frozen=True)
class RegionCell:
    composite: NativeBooleanComposite
    action: str
    resource: int


class RegionPolicy:
    def __init__(
        self,
        name: str,
        cells: Sequence[RegionCell],
        *,
        fallback: AtomOnlyPolicy,
        training_firing_rate: float,
    ) -> None:
        self.name = str(name)
        self.cells = tuple(cells)
        self.fallback = fallback
        self.training_firing_rate = float(training_firing_rate)
        self.population_size = len(self.cells)

    def predict(self, row: BenchmarkRow) -> Prediction:
        fired: list[RegionCell] = []
        evaluated_ids: list[str] = []
        digests: list[str] = []
        for cell in self.cells:
            result = cell.composite.evaluate(row.atoms)
            evaluated_ids.extend(result.predicate_evaluated_ids)
            digests.append(result.trace_digest)
            if result.confirmed:
                fired.append(cell)
        if not fired:
            fallback = self.fallback.predict(row)
            return Prediction(
                fallback.action,
                (),
                tuple(sorted(set(evaluated_ids))),
                _hash_json({"cell_digests": digests, "fallback": fallback.trace_digest}),
            )
        fired.sort(key=lambda cell: (cell.resource, cell.composite.cell_id), reverse=True)
        selected = fired[0]
        return Prediction(
            selected.action,
            tuple(sorted(cell.composite.cell_id for cell in fired)),
            tuple(sorted(set(evaluated_ids))),
            _hash_json({"cell_digests": digests, "selected": selected.composite.cell_id}),
        )


def build_dataset(config: BenchmarkConfig) -> dict[str, Any]:
    total_groups = config.train_groups + config.validation_groups + config.final_test_groups
    salt_tag = sha256(config.dataset_salt.encode()).hexdigest()[:8]
    signal_ids = ("atom_000", "atom_001")
    nuisance_ids = tuple(f"atom_{salt_tag}_{index + 2:03d}" for index in range(total_groups))
    atom_ids = signal_ids + nuisance_ids
    split_specs = (
        ("train", config.train_groups, 0, 10_000),
        ("validation", config.validation_groups, config.train_groups, 20_000),
        (
            "final_test",
            config.final_test_groups,
            config.train_groups + config.validation_groups,
            30_000,
        ),
    )
    dataset: dict[str, Any] = {"atom_ids": atom_ids, "signal_ids": signal_ids}
    for split, group_count, nuisance_offset, row_base in split_specs:
        rows: list[BenchmarkRow] = []
        for local_group in range(group_count):
            nuisance_index = nuisance_offset + local_group
            group_id = f"{salt_tag}_{split}_group_{local_group:02d}"
            for pattern, (left, right) in enumerate(product((False, True), repeat=2)):
                atoms = {atom_id: False for atom_id in atom_ids}
                atoms[signal_ids[0]] = left
                atoms[signal_ids[1]] = right
                atoms[nuisance_ids[nuisance_index]] = True
                rows.append(
                    BenchmarkRow(
                        row_id=row_base + local_group * 4 + pattern,
                        split=split,
                        group_id=group_id,
                        atoms=atoms,
                        correct_action="A" if left ^ right else "B",
                    )
                )
        dataset[split] = tuple(rows)
    validate_split_ids(
        (row.row_id for row in dataset["train"]),
        (row.row_id for row in dataset["validation"]),
        (row.row_id for row in dataset["final_test"]),
    )
    groups = {
        split: {row.group_id for row in dataset[split]}
        for split in ("train", "validation", "final_test")
    }
    if not (
        groups["train"].isdisjoint(groups["validation"])
        and groups["train"].isdisjoint(groups["final_test"])
        and groups["validation"].isdisjoint(groups["final_test"])
    ):
        raise ValueError("group identities must be disjoint across splits")
    dataset["manifest"] = {
        split: _source_manifest(dataset[split]) for split in ("train", "validation", "final_test")
    }
    dataset["manifest"]["group_ids"] = {split: sorted(value) for split, value in groups.items()}
    dataset["manifest"]["group_disjoint"] = True
    return dataset


def fit_atom_only_policy(rows: Sequence[BenchmarkRow], atom_ids: Sequence[str]) -> AtomOnlyPolicy:
    weights = {}
    for atom_id in atom_ids:
        weights[atom_id] = sum(
            (1 if row.atoms[atom_id] else -1) * (1 if _final_reward(row, "A") else -1)
            for row in rows
        )
    return AtomOnlyPolicy(weights)


def build_point_policy(
    rows: Sequence[BenchmarkRow],
    atom_ids: Sequence[str],
    *,
    fallback: AtomOnlyPolicy,
    tick_budget: int = 12,
) -> RegionPolicy:
    votes: dict[tuple[tuple[str, bool], ...], Counter[str]] = defaultdict(Counter)
    for row in rows:
        literals = tuple((atom_id, bool(row.atoms[atom_id])) for atom_id in atom_ids)
        votes[literals][_action_from_scalar_outcome(row)] += 1
    cells = _cells_from_votes(votes, operator="k_of_n", k=len(atom_ids), prefix="point", tick_budget=tick_budget)
    return RegionPolicy(
        "exact_point_cells",
        cells,
        fallback=fallback,
        training_firing_rate=_mean_cell_firing(cells, rows),
    )


def build_frequency_widened_policy(
    rows: Sequence[BenchmarkRow],
    atom_ids: Sequence[str],
    *,
    width: int,
    seed: int,
    fallback: AtomOnlyPolicy,
    tick_budget: int = 12,
) -> RegionPolicy:
    del seed  # deterministic tie order is part of the preregistered operator
    literal_frequency = {
        (atom_id, value): sum(row.atoms[atom_id] is value for row in rows) / len(rows)
        for atom_id in atom_ids
        for value in (False, True)
    }
    votes: dict[tuple[tuple[str, bool], ...], Counter[str]] = defaultdict(Counter)
    for row in rows:
        literals = [(atom_id, bool(row.atoms[atom_id])) for atom_id in atom_ids]
        literals.sort(key=lambda literal: (abs(literal_frequency[literal] - 0.5), literal[0], literal[1]))
        key = tuple(sorted(literals[: int(width)]))
        votes[key][_action_from_scalar_outcome(row)] += 1
    cells = _cells_from_votes(votes, operator="k_of_n", k=int(width), prefix=f"region{width}", tick_budget=tick_budget)
    return RegionPolicy(
        "signature_coarsened_cells" if int(width) == 1 else "content_blind_k_of_n_widening",
        cells,
        fallback=fallback,
        training_firing_rate=_mean_cell_firing(cells, rows),
    )


def build_matched_random_policy(
    rows: Sequence[BenchmarkRow],
    atom_ids: Sequence[str],
    widened: RegionPolicy,
    *,
    seed: int,
    fallback: AtomOnlyPolicy,
    tick_budget: int = 12,
) -> RegionPolicy:
    positive_frequency = {
        atom_id: sum(row.atoms[atom_id] for row in rows) / len(rows) for atom_id in atom_ids
    }
    target_rate = widened.training_firing_rate
    # Rare positive literals can be randomly paired with OR to match each 2-of-2
    # widened cell's training firing rate, without inspecting names or outcomes.
    rare = [atom_id for atom_id in atom_ids if math.isclose(2.0 * positive_frequency[atom_id], target_rate)]
    rng = random.Random(int(seed) + 9_001)
    rng.shuffle(rare)
    needed = 2 * widened.population_size
    if len(rare) < needed:
        raise ValueError("insufficient frequency-matched literals for random merge control")
    actions = [cell.action for cell in widened.cells]
    rng.shuffle(actions)
    cells: list[RegionCell] = []
    for index in range(widened.population_size):
        literals = ((rare[2 * index], True), (rare[2 * index + 1], True))
        composite = NativeBooleanComposite(
            f"random_merge_{seed}_{index}", literals, operator="k_of_n", k=1, tick_budget=tick_budget
        )
        cells.append(RegionCell(composite, actions[index], 1))
    policy = RegionPolicy(
        "matched_random_merges",
        cells,
        fallback=fallback,
        training_firing_rate=_mean_cell_firing(cells, rows),
    )
    if policy.population_size != widened.population_size or not math.isclose(
        policy.training_firing_rate, widened.training_firing_rate
    ):
        raise AssertionError("random merge control is not population/firing-rate matched on train")
    return policy


def enumerate_candidate_specs(atom_ids: Sequence[str]) -> tuple[CandidateSpec, ...]:
    return tuple(
        CandidateSpec(operator, tuple(pair), 1 if operator == "k_of_n" else None)
        for pair in combinations(sorted(map(str, atom_ids)), 2)
        for operator in ("and", "k_of_n", "xor")
    )


def discover_composite(
    train_rows: Sequence[BenchmarkRow],
    validation_rows: Sequence[BenchmarkRow],
    atom_ids: Sequence[str],
    *,
    seed: int,
    top_k: int = 8,
    tick_budget: int = 12,
) -> dict[str, Any]:
    scored: list[tuple[float, str, CandidateSpec, CompositePolicy, StemCellTerminal]] = []
    for spec in enumerate_candidate_specs(atom_ids):
        composite = _composite_from_spec(spec, tick_budget=tick_budget)
        policy = CompositePolicy(composite, name=f"discovered:{spec.candidate_id}")
        predictions = [policy.predict(row).action for row in train_rows]
        successes = [int(_final_reward(row, action)) for row, action in zip(train_rows, predictions, strict=True)]
        cell = StemCellTerminal(spec.candidate_id)
        cell.state = StemCellState.TRIAL
        cell.is_composition = True
        cell.children = list(spec.members)
        for success in successes:
            cell.update_xp(1.0 if success else -1.0)
        accuracy = sum(successes) / len(successes)
        tie = _stable_unit_interval(seed, spec.candidate_id)
        scored.append((accuracy, f"{tie:.16f}", spec, policy, cell))
    scored.sort(key=lambda item: (item[0], item[1], item[2].candidate_id), reverse=True)
    finalists = scored[: max(1, int(top_k))]
    validated: list[tuple[float, float, CandidateSpec, CompositePolicy, StemCellTerminal]] = []
    for training_accuracy, _tie, spec, policy, cell in finalists:
        validation_accuracy = sum(
            int(_final_reward(row, policy.predict(row).action)) for row in validation_rows
        ) / len(validation_rows)
        validated.append((validation_accuracy, training_accuracy, spec, policy, cell))
    validated.sort(key=lambda item: (item[0], item[1], item[2].candidate_id), reverse=True)
    validation_accuracy, training_accuracy, selected_spec, selected_policy, selected_cell = validated[0]
    selected_cell.state = StemCellState.MATURE if validation_accuracy == 1.0 else StemCellState.PROBATION
    truth_table_equivalent = validation_accuracy == 1.0 and {
        tuple(row.atoms[member] for member in selected_spec.members)
        for row in validation_rows
    } == set(product((False, True), repeat=2))
    return {
        "candidate_count": len(scored),
        "top_k_validated": len(finalists),
        "selected_spec": asdict(selected_spec),
        "selected_candidate_id": selected_spec.candidate_id,
        "selected_training_accuracy": training_accuracy,
        "selected_validation_accuracy": validation_accuracy,
        "selected_cell_state": selected_cell.state.name,
        "selected_cell_xp": int(selected_cell.xp),
        "truth_table_equivalent": truth_table_equivalent,
        "candidate_generation_used_target_rule": False,
        "credit_signal": "scalar final action success only",
        "_policy": selected_policy,
    }


def evaluate_policy(
    policy: Any,
    rows: Sequence[BenchmarkRow],
    *,
    arm: str,
    seed: int,
    tick_budget: int = 12,
) -> dict[str, Any]:
    success_by_row: dict[str, bool] = {}
    endpoint_by_row: dict[str, str] = {}
    digest_by_row: dict[str, str] = {}
    active_by_row: dict[str, list[str]] = {}
    evaluated_by_row: dict[str, list[str]] = {}
    action_by_row: dict[str, list[str]] = {}
    row_records: list[dict[str, Any]] = []
    for row in rows:
        prediction = policy.predict(row)
        success = bool(_final_reward(row, prediction.action))
        key = str(row.row_id)
        success_by_row[key] = success
        endpoint_by_row[key] = "correct_action" if success else "incorrect_action"
        digest_by_row[key] = prediction.trace_digest
        active_by_row[key] = list(prediction.active_ids)
        evaluated_by_row[key] = list(prediction.predicate_evaluated_ids)
        action_by_row[key] = [prediction.action]
        row_records.append(
            {
                "seed": int(seed),
                "arm": str(arm),
                "row_id": int(row.row_id),
                "split": row.split,
                "group_id": row.group_id,
                "selected_action": prediction.action,
                "success": success,
                "endpoint": endpoint_by_row[key],
                "trace_digest": prediction.trace_digest,
                "active_composite_ids": list(prediction.active_ids),
                "predicate_evaluated_ids": list(prediction.predicate_evaluated_ids),
            }
        )
    manifest = _source_manifest(rows)
    runner_config = {
        "black_reply_policy": "not_applicable_single_step_task",
        "seed": int(seed),
        "seed_schedule": "fixed seed; frozen manifest order",
        "judge_version": "planted_composition_scalar_final_action_success.v1",
        "fence_check_timing": "not_applicable",
        "tick_budget": int(tick_budget),
        "tie_break": "resource then stable cell id; atom-only ties choose B",
        "deterministic_row_order": list(manifest["row_ids"]),
    }
    runner_config_sha256 = _hash_json(runner_config)
    for row_record in row_records:
        row_record["runner_config_sha256"] = runner_config_sha256
        row_record["source_manifest_sha256"] = manifest["sha256"]
    wins = sum(success_by_row.values())
    result = {
        "policy": str(arm),
        "wins": wins,
        "nonwins": len(rows) - wins,
        "row_count": len(rows),
        "win_rate": wins / max(1, len(rows)),
        "success_by_row": success_by_row,
        "endpoint_by_row": endpoint_by_row,
        "trace_digest_by_row": digest_by_row,
        "active_composite_ids_by_row": active_by_row,
        "predicate_evaluated_ids_by_row": evaluated_by_row,
        "action_by_row": action_by_row,
        "runner_config": runner_config,
        "source_manifest": manifest,
        "predicate_evaluated_coverage": sum(bool(value) for value in evaluated_by_row.values()) / max(1, len(rows)),
        "valid_predicate_evaluated_coverage": sum(
            bool(active_by_row[row_id]) and bool(evaluated_by_row[row_id]) for row_id in success_by_row
        ) / max(1, len(rows)),
        "row_records": row_records,
    }
    assert_complete_arm_record(result)
    return result


def run_planted_composition_certification(*, config: BenchmarkConfig | None = None) -> dict[str, Any]:
    cfg = config or BenchmarkConfig()
    if len(cfg.seeds) < 5:
        raise ValueError("certification requires at least five preregistered seeds")
    output_dir = Path(cfg.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    dataset = build_dataset(cfg)
    (output_dir / "split_manifest.json").write_text(
        json.dumps(dataset["manifest"], indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    engine_semantic_pass = _engine_semantic_check(cfg.tick_budget)
    validation_rows: list[dict[str, Any]] = []
    frozen_by_seed: dict[int, dict[str, Any]] = {}
    for seed in cfg.seeds:
        atom = fit_atom_only_policy(dataset["train"], dataset["atom_ids"])
        discovery = discover_composite(
            dataset["train"],
            dataset["validation"],
            dataset["atom_ids"],
            seed=int(seed),
            top_k=cfg.discovery_top_k,
            tick_budget=cfg.tick_budget,
        )
        point = build_point_policy(dataset["train"], dataset["atom_ids"], fallback=atom, tick_budget=cfg.tick_budget)
        coarse = build_frequency_widened_policy(
            dataset["train"], dataset["atom_ids"], width=1, seed=int(seed), fallback=atom, tick_budget=cfg.tick_budget
        )
        widened = build_frequency_widened_policy(
            dataset["train"], dataset["atom_ids"], width=2, seed=int(seed), fallback=atom, tick_budget=cfg.tick_budget
        )
        matched = build_matched_random_policy(
            dataset["train"], dataset["atom_ids"], widened, seed=int(seed), fallback=atom, tick_budget=cfg.tick_budget
        )
        oracle_spec = CandidateSpec("xor", tuple(dataset["signal_ids"]))
        oracle = CompositePolicy(_composite_from_spec(oracle_spec, tick_budget=cfg.tick_budget), name="planted_oracle")
        policies = {
            "atom_only": atom,
            "exact_point_cells": point,
            "signature_coarsened_cells": coarse,
            "content_blind_k_of_n_widening": widened,
            "matched_random_merges": matched,
            "discovered_composite": discovery["_policy"],
            "planted_oracle": oracle,
        }
        evaluations = {
            arm: evaluate_policy(policy, dataset["validation"], arm=f"validation:{arm}", seed=int(seed), tick_budget=cfg.tick_budget)
            for arm, policy in policies.items()
        }
        validation_rows.append(
            {
                "seed": int(seed),
                "arms": {arm: _compact_eval(value) for arm, value in evaluations.items()},
                "discovery": _public_discovery(discovery),
                "random_population_matched": matched.population_size == widened.population_size,
                "random_train_firing_rate_matched": math.isclose(matched.training_firing_rate, widened.training_firing_rate),
            }
        )
        frozen_by_seed[int(seed)] = {
            "policies": policies,
            "discovery": discovery,
            "population": {
                "point": point.population_size,
                "coarse": coarse.population_size,
                "widened": widened.population_size,
                "random": matched.population_size,
            },
        }
    validation_pass = bool(
        engine_semantic_pass
        and all(row["arms"]["atom_only"]["win_rate"] == 0.5 for row in validation_rows)
        and all(row["arms"]["planted_oracle"]["win_rate"] == 1.0 for row in validation_rows)
        and all(row["arms"]["discovered_composite"]["win_rate"] == 1.0 for row in validation_rows)
        and all(row["arms"]["content_blind_k_of_n_widening"]["win_rate"] == 1.0 for row in validation_rows)
        and all(
            row["arms"]["content_blind_k_of_n_widening"]["win_rate"]
            > row["arms"]["matched_random_merges"]["win_rate"]
            for row in validation_rows
        )
    )
    frozen_payload = {
        "config": asdict(cfg),
        "split_manifest": dataset["manifest"],
        "selected_candidates": {
            str(seed): _public_discovery(payload["discovery"]) for seed, payload in frozen_by_seed.items()
        },
        "operator": {
            "candidate_operators": ["and", "k_of_n(k=1)", "xor"],
            "signature_coarsening_width": 1,
            "widening_width": 2,
            "random_control": "population and train firing-rate matched by frequency-stratified random merges",
        },
    }
    freeze_hash = _hash_json(frozen_payload)
    if not validation_pass:
        summary = {
            "schema_version": "planted_composition_certification.v1",
            "engine_semantic_pass": engine_semantic_pass,
            "measurement_pass": False,
            "discovery_pass": False,
            "widening_pass": False,
            "causal_ablation_pass": False,
            "validation": {"passed": False, "per_seed": validation_rows},
            "final_test": {"touched": False, "touch_count": 0},
            "freeze_hash": freeze_hash,
            "stop_reason": "validation_gate_failed",
        }
        (output_dir / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return summary

    # Final-test access is deliberately centralized below and occurs once after freeze.
    final_touch_count = 1
    per_seed: list[dict[str, Any]] = []
    all_row_records: list[dict[str, Any]] = []
    aggregate: dict[str, list[bool]] = defaultdict(list)
    noop_table: list[dict[str, Any]] = []
    ablation_table: list[dict[str, Any]] = []
    final_ids_before = tuple(row.row_id for row in dataset["final_test"])
    for seed in cfg.seeds:
        payload = frozen_by_seed[int(seed)]
        policies = payload["policies"]
        evaluations = {
            arm: evaluate_policy(policy, dataset["final_test"], arm=f"final:{arm}", seed=int(seed), tick_budget=cfg.tick_budget)
            for arm, policy in policies.items()
        }
        noop_eval = evaluate_policy(
            policies["content_blind_k_of_n_widening"],
            dataset["final_test"],
            arm="final:widening_noop",
            seed=int(seed),
            tick_budget=cfg.tick_budget,
        )
        noop = assert_noop_parity(evaluations["content_blind_k_of_n_widening"], noop_eval)
        target_ablation = evaluate_policy(
            policies["atom_only"],
            dataset["final_test"],
            arm="final:widening_target_ablated",
            seed=int(seed),
            tick_budget=cfg.tick_budget,
        )
        evaluations["widening_noop"] = noop_eval
        evaluations["widening_target_ablated"] = target_ablation
        if tuple(row.row_id for row in dataset["final_test"]) != final_ids_before:
            raise AssertionError("final test manifest mutated during evaluation")
        for arm, evaluation in evaluations.items():
            aggregate[arm].extend(bool(value) for value in evaluation["success_by_row"].values())
            all_row_records.extend(evaluation["row_records"])
        noop_table.append(
            {
                "seed": int(seed),
                "full_wins": evaluations["content_blind_k_of_n_widening"]["wins"],
                "noop_wins": noop_eval["wins"],
                "paired_delta": noop["paired"]["difference"],
                "passed": noop["passed"],
            }
        )
        ablation_pair = paired_binary_outcomes(
            list(evaluations["content_blind_k_of_n_widening"]["success_by_row"].values()),
            list(target_ablation["success_by_row"].values()),
        )
        ablation_table.append(
            {
                "seed": int(seed),
                "full_wins": evaluations["content_blind_k_of_n_widening"]["wins"],
                "target_ablated_wins": target_ablation["wins"],
                "paired": ablation_pair,
            }
        )
        per_seed.append(
            {
                "seed": int(seed),
                "discovery": _public_discovery(payload["discovery"]),
                "truth_table_equivalent": bool(payload["discovery"]["truth_table_equivalent"]),
                "arms": {arm: _compact_eval(value) for arm, value in evaluations.items()},
                "population": payload["population"],
                "runner_config": evaluations["atom_only"]["runner_config"],
                "source_manifest": evaluations["atom_only"]["source_manifest"],
            }
        )

    comparisons = _primary_comparisons(aggregate, alpha=cfg.primary_alpha)
    measurement_pass = bool(all(row["passed"] for row in noop_table))
    discovery_pass = bool(
        sum(row["truth_table_equivalent"] for row in per_seed) >= 4
        and comparisons["discovery_vs_atom_only"]["holm_rejected"]
        and comparisons["discovery_vs_atom_only"]["simultaneous_ci_low"] > 0.0
    )
    widening_pass = bool(
        comparisons["widening_vs_points"]["holm_rejected"]
        and comparisons["widening_vs_random"]["holm_rejected"]
        and comparisons["widening_vs_points"]["simultaneous_ci_low"] > 0.0
        and comparisons["widening_vs_random"]["simultaneous_ci_low"] > 0.0
        and all(
            row["arms"]["content_blind_k_of_n_widening"]["valid_predicate_evaluated_coverage"]
            > row["arms"]["exact_point_cells"]["valid_predicate_evaluated_coverage"]
            and row["arms"]["content_blind_k_of_n_widening"]["valid_predicate_evaluated_coverage"]
            > row["arms"]["matched_random_merges"]["valid_predicate_evaluated_coverage"]
            for row in per_seed
        )
    )
    causal_ablation_pass = bool(
        all(row["full_wins"] > row["target_ablated_wins"] for row in ablation_table)
        and comparisons["widening_vs_target_ablation"]["holm_rejected"]
    )
    stop_reason = None
    if not measurement_pass:
        stop_reason = "measurement_certification_failed"
    elif not discovery_pass:
        stop_reason = "discovery_failed_across_preregistered_seeds"
    elif not widening_pass:
        stop_reason = "widening_failed_against_points_or_matched_random"
    rows_path = output_dir / "rows.jsonl"
    rows_path.write_text(
        "".join(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n" for row in all_row_records),
        encoding="utf-8",
    )
    summary = {
        "schema_version": "planted_composition_certification.v1",
        "config": asdict(cfg),
        "architecture": {
            "engine": "FormalReConEngine",
            "atoms": "materialized TERMINAL nodes",
            "composites": "materialized SCRIPT nodes with SUB/SUR pairs",
            "credit": "scalar final action success only",
            "candidate_generation": "blind enumeration of generic binary operators",
            "hand_recognizers_or_hidden_oracles_in_learner": False,
        },
        "engine_semantic_pass": engine_semantic_pass,
        "measurement_pass": measurement_pass,
        "discovery_pass": discovery_pass,
        "widening_pass": widening_pass,
        "causal_ablation_pass": causal_ablation_pass,
        "validation": {"passed": validation_pass, "per_seed": validation_rows},
        "final_test": {
            "touched": True,
            "touch_count": final_touch_count,
            "touched_after_freeze": True,
            "manifest_sha256": dataset["manifest"]["final_test"]["sha256"],
            "row_count_per_seed": len(dataset["final_test"]),
        },
        "freeze_hash": freeze_hash,
        "multiplicity": {
            "primary_family": list(comparisons),
            "p_value_method": "one-sided exact binomial sign test over discordant pairs",
            "correction": "Holm step-down at family alpha",
            "simultaneous_ci": "paired Wilson sign intervals at Bonferroni confidence 1-alpha/m",
        },
        "primary_comparisons": comparisons,
        "noop_table": noop_table,
        "target_ablation_table": ablation_table,
        "per_seed": per_seed,
        "artifacts": {
            "row_jsonl": str(rows_path),
            "split_manifest": str(output_dir / "split_manifest.json"),
        },
        "stop_reason": stop_reason,
    }
    (output_dir / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return summary


def _composite_from_spec(spec: CandidateSpec, *, tick_budget: int) -> NativeBooleanComposite:
    return NativeBooleanComposite(
        spec.candidate_id,
        tuple((member, True) for member in spec.members),
        operator=spec.operator,
        k=spec.k,
        tick_budget=tick_budget,
    )


def _cells_from_votes(
    votes: Mapping[tuple[tuple[str, bool], ...], Counter[str]],
    *,
    operator: str,
    k: int,
    prefix: str,
    tick_budget: int,
) -> list[RegionCell]:
    cells: list[RegionCell] = []
    for literals, action_votes in sorted(votes.items()):
        action = max(("A", "B"), key=lambda candidate: (action_votes[candidate], candidate == "B"))
        digest = _hash_json(literals)[:12]
        composite = NativeBooleanComposite(
            f"{prefix}_{digest}", literals, operator=operator, k=k, tick_budget=tick_budget
        )
        cells.append(RegionCell(composite, action, int(action_votes[action])))
    return cells


def _mean_cell_firing(cells: Sequence[RegionCell], rows: Sequence[BenchmarkRow]) -> float:
    if not cells or not rows:
        return 0.0
    firings = sum(cell.composite.evaluate(row.atoms).confirmed for cell in cells for row in rows)
    return firings / (len(cells) * len(rows))


def _action_from_scalar_outcome(row: BenchmarkRow) -> str:
    rewards = {action: int(_final_reward(row, action)) for action in ("A", "B")}
    return max(("A", "B"), key=lambda action: (rewards[action], action == "B"))


def _final_reward(row: BenchmarkRow, action: str) -> bool:
    return str(action) == row.correct_action


def _source_manifest(rows: Sequence[BenchmarkRow]) -> dict[str, Any]:
    payload = [
        {
            "row_id": row.row_id,
            "split": row.split,
            "group_id": row.group_id,
            "atoms": dict(sorted(row.atoms.items())),
        }
        for row in rows
    ]
    return {
        "split": rows[0].split if rows else "empty",
        "sha256": _hash_json(payload),
        "row_ids": [row.row_id for row in rows],
        "group_ids": sorted({row.group_id for row in rows}),
    }


def _compact_eval(evaluation: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "wins": int(evaluation["wins"]),
        "row_count": int(evaluation["row_count"]),
        "win_rate": float(evaluation["win_rate"]),
        "predicate_evaluated_coverage": float(evaluation["predicate_evaluated_coverage"]),
        "valid_predicate_evaluated_coverage": float(evaluation["valid_predicate_evaluated_coverage"]),
        "source_sha256": evaluation["source_manifest"]["sha256"],
    }


def _public_discovery(discovery: Mapping[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in discovery.items() if not key.startswith("_")}


def _engine_semantic_check(tick_budget: int) -> bool:
    truth = tuple(product((False, True), repeat=2))
    and_cell = NativeBooleanComposite("semantic_and", (("p", True), ("q", True)), operator="and", tick_budget=tick_budget)
    xor_cell = NativeBooleanComposite("semantic_xor", (("p", True), ("q", True)), operator="xor", tick_budget=tick_budget)
    quorum = NativeBooleanComposite(
        "semantic_quorum", (("p", True), ("q", True), ("r", True)), operator="k_of_n", k=2, tick_budget=tick_budget
    )
    return bool(
        [and_cell.evaluate({"p": p, "q": q}).confirmed for p, q in truth] == [False, False, False, True]
        and [xor_cell.evaluate({"p": p, "q": q}).confirmed for p, q in truth] == [False, True, True, False]
        and quorum.evaluate({"p": True, "q": False, "r": True}).confirmed
        and not quorum.evaluate({"p": True, "q": False, "r": False}).confirmed
    )


def _primary_comparisons(aggregate: Mapping[str, Sequence[bool]], *, alpha: float) -> dict[str, Any]:
    pairs = (
        ("discovery_vs_atom_only", "discovered_composite", "atom_only"),
        ("widening_vs_points", "content_blind_k_of_n_widening", "exact_point_cells"),
        ("widening_vs_random", "content_blind_k_of_n_widening", "matched_random_merges"),
        ("widening_vs_target_ablation", "content_blind_k_of_n_widening", "widening_target_ablated"),
    )
    confidence = 1.0 - float(alpha) / len(pairs)
    rows: list[dict[str, Any]] = []
    for name, left_key, right_key in pairs:
        left = list(map(bool, aggregate[left_key]))
        right = list(map(bool, aggregate[right_key]))
        paired = paired_binary_outcomes(left, right, confidence=confidence)
        raw_p = _exact_binomial_upper_tail(paired["favorable"], paired["discordant_count"])
        rows.append(
            {
                "name": name,
                "left": left_key,
                "right": right_key,
                "raw_p": raw_p,
                "favorable": paired["favorable"],
                "unfavorable": paired["unfavorable"],
                "discordant_count": paired["discordant_count"],
                "difference": paired["difference"],
                "simultaneous_confidence": confidence,
                "simultaneous_ci_low": paired["ci_low"],
                "simultaneous_ci_high": paired["ci_high"],
            }
        )
    holm = holm_adjusted_pvalues([row["raw_p"] for row in rows], alpha=float(alpha))
    result: dict[str, Any] = {}
    for row, adjusted in zip(rows, holm, strict=True):
        row["holm_adjusted_p"] = adjusted["adjusted_p"]
        row["holm_threshold"] = adjusted["holm_threshold"]
        row["holm_rejected"] = adjusted["rejected"]
        result[row.pop("name")] = row
    return result


def _exact_binomial_upper_tail(favorable: int, discordants: int) -> float:
    if discordants <= 0 or favorable <= 0:
        return 1.0
    return sum(math.comb(discordants, i) for i in range(favorable, discordants + 1)) / (2**discordants)


def _stable_unit_interval(seed: int, value: str) -> float:
    digest = sha256(f"{int(seed)}:{value}".encode()).hexdigest()
    return int(digest[:16], 16) / float(16**16 - 1)


def _hash_json(value: Any) -> str:
    return sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode()).hexdigest()


def main() -> None:
    summary = run_planted_composition_certification()
    print(
        json.dumps(
            {
                "engine_semantic_pass": summary["engine_semantic_pass"],
                "measurement_pass": summary["measurement_pass"],
                "discovery_pass": summary["discovery_pass"],
                "widening_pass": summary["widening_pass"],
                "causal_ablation_pass": summary["causal_ablation_pass"],
                "stop_reason": summary["stop_reason"],
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
