#!/usr/bin/env python3
"""Run the frozen generic-core support-directed exploration experiment."""

from __future__ import annotations

import argparse
from copy import deepcopy
from dataclasses import asdict, replace
import hashlib
import json
from pathlib import Path
import runpy
import statistics
import subprocess

from recon_lite import (
    CausalRentConfig,
    EpisodicCompositionConfig,
    EpisodicCompositionPolicy,
    ExperienceReservoirConfig,
    OnlineCompositionConfig,
)


DEFAULT_OUTPUT = Path(
    "reports/autogrowth/generic_core/"
    "support_directed_exploration_20260713.json"
)
SEEDS = tuple(range(20262101, 20262121))
DEMANDS = (2,)
ARMS = (
    "fixed_8_ranked",
    "rent_batch_4_ranked",
    "rent_batch_4_support_directed",
    "rent_batch_4_support_shuffled",
)
RENT_ARMS = ARMS[1:]
CHECKPOINTS = (512, 1024, 2048, 4096)
TRAIN_PER_PHASE = 4096
DEVELOPMENT_COUNT = 512
EVALUATION_COUNT = 512
KEY_DOOR_RUNNER = Path(__file__).with_name(
    "run_generic_core_multistate_key_door.py"
)
RESPONSIBILITY_RUNNER = Path(__file__).with_name(
    "run_generic_core_responsibility_allocation.py"
)
CONTRACT = Path(
    "docs/autogrowth/"
    "GENERIC_CORE_SUPPORT_DIRECTED_EXPLORATION_WORK_PACKAGE_20260713.md"
)


def _hash_json(value: object) -> str:
    encoded = json.dumps(
        value, sort_keys=True, separators=(",", ":")
    ).encode()
    return hashlib.sha256(encoded).hexdigest()


def _file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _git_commit(repo_root: Path) -> str:
    result = subprocess.run(
        ("git", "rev-parse", "HEAD"),
        cwd=repo_root,
        check=False,
        capture_output=True,
        text=True,
        timeout=10,
    )
    return result.stdout.strip() if result.returncode == 0 else "unavailable"


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _prepare_task(task: dict[str, object]) -> dict[str, object]:
    """Remove unused host solution fields and freeze matched row manifests."""
    prepared = deepcopy(task)
    row_names = (
        "train_regime_0",
        "train_regime_1",
        "evaluation_regime_0",
        "evaluation_regime_1",
        "development_evaluation_regime_0",
    )
    for name in row_names:
        rows = tuple(
            {
                key: value
                for key, value in row.items()
                if key != "correct_door_index"
            }
            for row in prepared[name]
        )
        prepared[name] = rows
        prepared[f"{name}_sha256"] = _hash_json(rows)
    prepared["m1_changed_cue_bit"] = int(prepared["seed"]) % 2
    return prepared


def _truncate_task(
    task: dict[str, object],
    *,
    train_count: int,
    development_count: int,
    evaluation_count: int,
) -> dict[str, object]:
    """Bound retired-data smoke work without changing fresh manifests."""
    truncated = deepcopy(task)
    counts = {
        "train_regime_0": train_count,
        "train_regime_1": train_count,
        "evaluation_regime_0": evaluation_count,
        "evaluation_regime_1": evaluation_count,
        "development_evaluation_regime_0": development_count,
    }
    for name, count in counts.items():
        rows = tuple(truncated[name][:count])
        truncated[name] = rows
        truncated[f"{name}_sha256"] = _hash_json(rows)
    return truncated


def _changed_cue_bits(task: dict[str, object], demand: int) -> frozenset[int]:
    if demand == 0:
        return frozenset()
    if demand == 1:
        return frozenset({int(task["m1_changed_cue_bit"])})
    if demand == 2:
        return frozenset({0, 1})
    raise ValueError("demand must be 0, 1 or 2")


def _correct_actions(
    task: dict[str, object],
    row: dict[str, object],
    demand: int,
) -> tuple[str, str]:
    key_action = next(
        action_id
        for action_id, index in task["key_index_by_action"].items()
        if index == row["correct_key_index"]
    )
    cue_bit = int(row["door_cue_bit"])
    door_index = int(bool(cue_bit) ^ bool(task["door_inverted"]))
    if cue_bit in _changed_cue_bits(task, demand):
        door_index ^= 1
    door_action = next(
        action_id
        for action_id, index in task["door_index_by_action"].items()
        if index == door_index
    )
    return key_action, door_action


def _door_observation(
    task: dict[str, object],
    row: dict[str, object],
    selected_key_action: str,
) -> tuple[str, ...]:
    key_index = task["key_index_by_action"][selected_key_action]
    atoms = [
        task["carried_ids"][key_index],
        task["door_cue_literals"][row["door_cue_bit"]],
        task["regime_ids"][row["regime"]],
    ]
    atoms.extend(
        task["door_nuisance_literals"][index][bit]
        for index, bit in enumerate(row["door_nuisance_bits"])
    )
    return tuple(sorted(atoms))


def _train_episode(
    policy: EpisodicCompositionPolicy,
    task: dict[str, object],
    row: dict[str, object],
    demand: int,
    *,
    capture_trace: bool = False,
) -> tuple[str, str, tuple[str, ...], dict[str, object] | None]:
    policy.begin_episode()
    key_action = policy.choose(
        row["key_active_terminal_ids"],
        legal_action_ids=task["key_action_ids"],
    )
    policy.real_step(clear_trace=False)
    door_atoms = _door_observation(task, row, key_action)
    door_action = policy.choose(
        door_atoms,
        legal_action_ids=task["door_action_ids"],
    )
    correct_key, correct_door = _correct_actions(task, row, demand)
    terminal_return = (
        1.0
        if key_action == correct_key and door_action == correct_door
        else -1.0
    )
    captured = None
    if capture_trace:
        captured = {
            "terminal_return": terminal_return,
            "decisions": [
                {
                    "action_id": decision.action_id,
                    "active_atom_ids": decision.active_atom_ids,
                    "legal_action_ids": decision.legal_action_ids,
                    "decision_scores": decision.decision_scores,
                    "elapsed_steps": decision.elapsed_steps,
                }
                for decision in policy.episode_trace
            ],
        }
    policy.observe_terminal(terminal_return)
    return key_action, door_action, door_atoms, captured


def _evaluate(
    policy: EpisodicCompositionPolicy,
    task: dict[str, object],
    rows: tuple[dict[str, object], ...],
    demand: int,
    *,
    include_mature_composites: bool = True,
    disabled_candidates_by_action: (
        dict[str, frozenset[int]] | None
    ) = None,
) -> dict[str, float | int | None]:
    if not rows:
        return {
            "count": 0,
            "key_accuracy": None,
            "door_accuracy": None,
            "joint_success": None,
        }
    key_correct = door_correct = joint_correct = 0
    for row in rows:
        key_action = policy.greedy_action(
            row["key_active_terminal_ids"],
            include_mature_composites=include_mature_composites,
            legal_action_ids=task["key_action_ids"],
            disabled_candidates_by_action=disabled_candidates_by_action,
        )
        door_action = policy.greedy_action(
            _door_observation(task, row, key_action),
            include_mature_composites=include_mature_composites,
            legal_action_ids=task["door_action_ids"],
            disabled_candidates_by_action=disabled_candidates_by_action,
        )
        correct_key, correct_door = _correct_actions(task, row, demand)
        key_ok = key_action == correct_key
        door_ok = door_action == correct_door
        key_correct += int(key_ok)
        door_correct += int(door_ok)
        joint_correct += int(key_ok and door_ok)
    count = len(rows)
    return {
        "count": count,
        "key_accuracy": key_correct / count,
        "door_accuracy": door_correct / count,
        "joint_success": joint_correct / count,
    }


def _behavior_digest(
    policy: EpisodicCompositionPolicy,
    task: dict[str, object],
    rows: tuple[dict[str, object], ...],
) -> str:
    values = []
    for row in rows:
        key_scores = {
            action_id: policy.channels[action_id].learner.predict(
                row["key_active_terminal_ids"]
            )
            for action_id in task["key_action_ids"]
        }
        key_action = max(
            task["key_action_ids"],
            key=lambda action_id: (key_scores[action_id], action_id),
        )
        door_atoms = _door_observation(task, row, key_action)
        door_scores = {
            action_id: policy.channels[action_id].learner.predict(door_atoms)
            for action_id in task["door_action_ids"]
        }
        values.append((key_scores, door_scores))
    return _hash_json(values)


def _quiesce_checkpoint(
    policy: EpisodicCompositionPolicy,
    task: dict[str, object],
) -> dict[str, object]:
    rows = task["development_evaluation_regime_0"]
    before_digest = _behavior_digest(policy, task, rows)
    pre_trials = 0
    for channel in policy.channels.values():
        learner = channel.learner
        for index, candidate in enumerate(learner.candidates):
            if candidate.state != "trial":
                continue
            pre_trials += 1
            learner.transition_candidate(index, "pruned")
        channel.sync_external_lifecycle()
    after_digest = _behavior_digest(policy, task, rows)
    return {
        "pre_trial_count": pre_trials,
        "post_trial_count": sum(
            candidate.state == "trial"
            for channel in policy.channels.values()
            for candidate in channel.learner.candidates
        ),
        "behavior_sha256_before": before_digest,
        "behavior_sha256_after": after_digest,
        "behavior_unchanged": before_digest == after_digest,
    }


def _shared_state(policy: EpisodicCompositionPolicy) -> dict[str, object]:
    return {
        action_id: {
            "bias": channel.learner.bias,
            "primitive_weights": dict(sorted(
                channel.learner.primitive_weights.items()
            )),
        }
        for action_id, channel in policy.channels.items()
    }


def _shared_hash(policy: EpisodicCompositionPolicy) -> str:
    return _hash_json(_shared_state(policy))


def _configure_arm(
    policy: EpisodicCompositionPolicy,
    arm: str,
) -> None:
    for channel in policy.channels.values():
        channel.learner.config = replace(
            channel.learner.config,
            residual_update_mode="shared_frozen",
            prediction_min=-1.0,
            prediction_max=1.0,
            max_candidates=8,
            max_total_proposals=64,
        )
        channel.learner.proposal_mode = "residual_ranked"
    if arm in RENT_ARMS:
        policy.enable_causal_rent(CausalRentConfig(
            temporary_challenger_allowance=4,
            proposal_mode="residual_ranked",
            exploration_request_mode={
                "rent_batch_4_ranked": "ordinary_random",
                "rent_batch_4_support_directed": "support_directed",
                "rent_batch_4_support_shuffled": "support_shuffled",
            }[arm],
        ))


def _cohort_rows(
    task: dict[str, object], demand: int
) -> dict[str, tuple[dict[str, object], ...]]:
    old = task["evaluation_regime_0"]
    new = task["evaluation_regime_1"]
    changed = _changed_cue_bits(task, demand)
    output = {
        "phase0_retention": old,
        "phase1_changed_cue": tuple(
            row for row in new if int(row["door_cue_bit"]) in changed
        ),
        "phase1_unchanged_cue": tuple(
            row for row in new if int(row["door_cue_bit"]) not in changed
        ),
    }
    for nuisance in ((0, 0), (0, 1), (1, 0), (1, 1)):
        output[f"phase1_nuisance_{nuisance[0]}{nuisance[1]}"] = tuple(
            row for row in new
            if tuple(row["door_nuisance_bits"]) == nuisance
        )
    return output


def _candidate_ablations(
    policy: EpisodicCompositionPolicy,
    task: dict[str, object],
    demand: int,
) -> list[dict[str, object]]:
    cohorts = _cohort_rows(task, demand)
    full = {
        name: _evaluate(policy, task, rows, demand if name != "phase0_retention" else 0)
        for name, rows in cohorts.items()
    }
    output = []
    for action_id, channel in policy.channels.items():
        for index, candidate in enumerate(channel.learner.candidates):
            if candidate.state != "mature":
                continue
            disabled = {action_id: frozenset({index})}
            effects = {}
            for name, rows in cohorts.items():
                ablated = _evaluate(
                    policy,
                    task,
                    rows,
                    demand if name != "phase0_retention" else 0,
                    disabled_candidates_by_action=disabled,
                )
                full_value = full[name]["joint_success"]
                ablated_value = ablated["joint_success"]
                effects[name] = {
                    "count": len(rows),
                    "full_joint_success": full_value,
                    "ablated_joint_success": ablated_value,
                    "joint_effect": (
                        full_value - ablated_value
                        if full_value is not None and ablated_value is not None
                        else None
                    ),
                }
            output.append({
                "action_id": action_id,
                "candidate_index": index,
                "members": candidate.members,
                "weight": candidate.shadow_weight,
                "last_rent": candidate.last_rent,
                "last_margin_utility": candidate.last_margin_utility,
                "effects": effects,
            })
    return output


def _target_candidate_diagnostics(
    policy: EpisodicCompositionPolicy,
    task: dict[str, object],
) -> list[dict[str, object]]:
    """Describe the four exact cue-by-regime-1 action candidates post hoc."""
    target_members = {
        tuple(sorted((task["door_cue_literals"][cue], task["regime_ids"][1])))
        for cue in (0, 1)
    }
    rows = []
    rent_snapshot = policy.snapshot()["causal_rent"]
    events = rent_snapshot["events"] if rent_snapshot is not None else []
    for action_id in task["door_action_ids"]:
        channel = policy.channels[action_id]
        for members in sorted(target_members):
            matches = [
                (index, candidate)
                for index, candidate in enumerate(channel.learner.candidates)
                if candidate.members == members
            ]
            if not matches:
                rows.append({
                    "action_id": action_id,
                    "members": members,
                    "found": False,
                    "max_review_support": 0,
                    "mature": False,
                    "unsupported_death": False,
                })
                continue
            index, candidate = matches[0]
            review_events = [
                event for event in events
                if event.get("action_id") == action_id
                and event.get("candidate_index") == index
            ]
            review_support = [
                int(event["support"])
                for event in review_events
                if event.get("event") == "review"
                and event.get("support") is not None
            ]
            stats = asdict(policy.candidate_rent_stats(action_id, index))
            rows.append({
                "action_id": action_id,
                "candidate_index": index,
                "members": members,
                "found": True,
                "state": candidate.state,
                "mature": candidate.state == "mature",
                "activation_count": candidate.activation_count,
                "confirmation_count": candidate.confirmation_count,
                "exploration_request_count": candidate.exploration_request_count,
                "exploration_probe_benefit_count": (
                    candidate.exploration_probe_benefit_count
                ),
                "proposal_terminal_count": next((
                    event["terminal_count"] for event in review_events
                    if event.get("event") == "proposed"
                ), None),
                "max_review_support": max(review_support, default=0),
                "unsupported_death": any(
                    event.get("event") == "unsupported_pruned"
                    for event in review_events
                ),
                "last_rent": candidate.last_rent,
                "last_margin_utility": candidate.last_margin_utility,
                "rent_diagnostics": stats,
            })
    return rows


def _candidate_checkpoint(
    policy: EpisodicCompositionPolicy,
) -> list[dict[str, object]]:
    return [
        {
            "action_id": action_id,
            "candidate_index": index,
            "members": candidate.members,
            "state": candidate.state,
            "activation_count": candidate.activation_count,
            "confirmation_count": candidate.confirmation_count,
            "exploration_request_count": candidate.exploration_request_count,
            "exploration_probe_benefit_count": (
                candidate.exploration_probe_benefit_count
            ),
        }
        for action_id, channel in policy.channels.items()
        for index, candidate in enumerate(channel.learner.candidates)
    ]


def _arm_result(
    policy: EpisodicCompositionPolicy,
    task: dict[str, object],
    demand: int,
    *,
    shared_before: str,
    trajectory: list[dict[str, object]],
    action_digest: str,
    observation_digest: str,
    training_episode_count: int,
) -> dict[str, object]:
    old_full = _evaluate(
        policy, task, task["evaluation_regime_0"], 0
    )
    new_full = _evaluate(
        policy, task, task["evaluation_regime_1"], demand
    )
    old_without = _evaluate(
        policy,
        task,
        task["evaluation_regime_0"],
        0,
        include_mature_composites=False,
    )
    new_without = _evaluate(
        policy,
        task,
        task["evaluation_regime_1"],
        demand,
        include_mature_composites=False,
    )
    shared_after = _shared_hash(policy)
    snapshot = policy.snapshot()
    channels = {
        action_id: channel.learner.snapshot()
        for action_id, channel in policy.channels.items()
    }
    return {
        "training_episode_count": training_episode_count,
        "terminal_count": policy.terminal_count,
        "credited_decision_count": policy.credited_decision_count,
        "selection_count": dict(policy.selection_count),
        "rng_call_count": policy.rng_call_count,
        "shared_state_sha256_before": shared_before,
        "shared_state_sha256_after": shared_after,
        "shared_state_unchanged": shared_before == shared_after,
        "phase1_action_sequence_sha256": action_digest,
        "phase1_action_conditioned_observation_sha256": observation_digest,
        "evaluation_trajectory": trajectory,
        "evaluations": {
            "regime_0": {
                "full_graph": old_full,
                "without_composites": old_without,
                "joint_ablation_drop": (
                    old_full["joint_success"]
                    - old_without["joint_success"]
                ),
            },
            "regime_1": {
                "full_graph": new_full,
                "without_composites": new_without,
                "joint_ablation_drop": (
                    new_full["joint_success"]
                    - new_without["joint_success"]
                ),
            },
        },
        "global_live_candidate_count": policy._global_live_count(),
        "global_mature_candidate_count": policy._mature_count(),
        "candidate_ablations": _candidate_ablations(policy, task, demand),
        "target_candidate_diagnostics": _target_candidate_diagnostics(
            policy, task
        ),
        "experience_reservoir": snapshot["experience_reservoir"],
        "causal_rent": snapshot["causal_rent"],
        "exploration": snapshot["exploration"],
        "channels": channels,
        "graph_prediction_mismatch_count": sum(
            channel.graph_prediction_mismatch_count
            for channel in policy.channels.values()
        ),
        "trial_root_edge_count": sum(
            channel.trial_root_edge_count
            for channel in policy.channels.values()
        ),
    }


def _minimum_score(cell: dict[str, object], arm: str) -> float:
    values = cell["arms"][arm]["evaluations"]
    return min(
        values["regime_0"]["full_graph"]["joint_success"],
        values["regime_1"]["full_graph"]["joint_success"],
    )


def _cell_invariants(cell: dict[str, object]) -> dict[str, object]:
    arms = cell["arms"]
    fixed_capacity_ok = all(
        channel["max_observed_live_candidate_count"] <= 8
        and channel["candidate_count"] <= 64
        for channel in arms["fixed_8_ranked"]["channels"].values()
    )
    expected_modes = {
        "rent_batch_4_ranked": "ordinary_random",
        "rent_batch_4_support_directed": "support_directed",
        "rent_batch_4_support_shuffled": "support_shuffled",
    }
    causal_bounds_ok = True
    modes = {}
    for arm in RENT_ARMS:
        snapshot = arms[arm]["causal_rent"]
        config = snapshot["config"]
        modes[arm] = config["exploration_request_mode"]
        causal_bounds_ok = causal_bounds_ok and all((
            config["temporary_challenger_allowance"] == 4,
            config["global_capacity"] == 32,
            config["proposal_interval_episodes"] == 128,
            config["review_interval_episodes"] == 512,
            config["min_eligible_support"] == 32,
            snapshot["maximum_global_live_candidate_count"] <= 36,
            snapshot["global_mature_count"] <= 32,
            snapshot["global_live_count"]
            - snapshot["global_mature_count"] <= 4,
        ))
    causal_bounds_ok = causal_bounds_ok and modes == expected_modes
    forbidden = {
        "role", "demand", "correctness", "correct_action", "cohort",
        "cue", "regime", "target",
    }
    allocation_record_clean = all(
        not forbidden.intersection(event)
        for arm in RENT_ARMS
        for event in arms[arm]["causal_rent"]["events"]
    ) and all(
        not forbidden.intersection(event)
        for arm in (
            "rent_batch_4_support_directed",
            "rent_batch_4_support_shuffled",
        )
        for event in arms[arm]["exploration"]["events"]
    )
    experience_budget = len({
        (
            arms[arm]["terminal_count"],
            arms[arm]["credited_decision_count"],
            arms[arm]["experience_reservoir"]["seen_count"],
        )
        for arm in ARMS
    }) == 1
    directed = arms["rent_batch_4_support_directed"]["exploration"]
    shuffled = arms["rent_batch_4_support_shuffled"]["exploration"]
    exploration_timing_matched = all((
        directed["decision_count"] == shuffled["decision_count"],
        directed["event_count"] == shuffled["event_count"],
        directed["event_decision_indices"]
        == shuffled["event_decision_indices"],
        directed["support_rng_call_count"]
        == shuffled["support_rng_call_count"],
        directed["support_rng_call_count"]
        == directed["rent_enabled_event_count"],
        shuffled["support_rng_call_count"]
        == shuffled["rent_enabled_event_count"],
        directed["rent_enabled_event_decision_indices"]
        == shuffled["rent_enabled_event_decision_indices"],
    ))
    probe_accounting_balanced = True
    for arm in (
        "rent_batch_4_support_directed",
        "rent_batch_4_support_shuffled",
    ):
        exploration = arms[arm]["exploration"]
        events = exploration["events"]
        candidate_probe_total = sum(
            candidate["exploration_probe_benefit_count"]
            for channel in arms[arm]["channels"].values()
            for candidate in channel["candidates"]
        )
        probe_accounting_balanced = probe_accounting_balanced and all((
            exploration["probe_action_count"]
            == sum(not event["fallback"] for event in events),
            exploration["request_opportunity_count"]
            == sum(event["active_request_count"] > 0 for event in events),
            exploration["fallback_count"]
            == sum(event["fallback"] for event in events),
            candidate_probe_total == sum(
                len(event["beneficiary_candidate_ids"]) for event in events
            ),
        ))
    result = {
        "clone_parity": cell["clone_parity"],
        "shared_unchanged": all(
            arms[arm]["shared_state_unchanged"] for arm in ARMS
        ),
        "experience_budget_matched": experience_budget,
        "exploration_timing_matched": exploration_timing_matched,
        "probe_accounting_balanced": probe_accounting_balanced,
        "fixed_capacity_ok": fixed_capacity_ok,
        "causal_bounds_ok": causal_bounds_ok,
        "allocation_records_role_blind": allocation_record_clean,
        "graph_update_parity": sum(
            arms[arm]["graph_prediction_mismatch_count"] for arm in ARMS
        ) == 0,
        "trial_root_isolation": sum(
            arms[arm]["trial_root_edge_count"] for arm in ARMS
        ) == 0,
    }
    result["pass"] = all(result.values())
    return result


def _summaries(task_rows: list[dict[str, object]]) -> dict[str, object]:
    summaries = {}
    for demand in DEMANDS:
        cells = [row["demands"][str(demand)] for row in task_rows]
        summaries[str(demand)] = {}
        for arm in ARMS:
            old = [
                cell["arms"][arm]["evaluations"]["regime_0"]
                ["full_graph"]["joint_success"]
                for cell in cells
            ]
            new = [
                cell["arms"][arm]["evaluations"]["regime_1"]
                ["full_graph"]["joint_success"]
                for cell in cells
            ]
            occupancy = [
                cell["arms"][arm]["global_mature_candidate_count"]
                for cell in cells
            ]
            summaries[str(demand)][arm] = {
                "median_old_joint_success": statistics.median(old),
                "median_new_joint_success": statistics.median(new),
                "both_at_least_0_85_task_count": sum(
                    min(old_value, new_value) >= 0.85
                    for old_value, new_value in zip(old, new)
                ),
                "median_mature_occupancy": statistics.median(occupancy),
            }
    return summaries


def _gates(
    task_rows: list[dict[str, object]], summaries: dict[str, object]
) -> dict[str, object]:
    cells = [row["demands"]["2"] for row in task_rows]
    fixed = summaries["2"]["fixed_8_ranked"]
    ordinary = summaries["2"]["rent_batch_4_ranked"]
    directed = summaries["2"]["rent_batch_4_support_directed"]

    def target_rows(cell: dict[str, object], arm: str) -> list[dict[str, object]]:
        return cell["arms"][arm]["target_candidate_diagnostics"]

    directed_min_support = [
        min(row["max_review_support"] for row in target_rows(cell, "rent_batch_4_support_directed"))
        for cell in cells
    ]
    shuffled_min_support = [
        min(row["max_review_support"] for row in target_rows(cell, "rent_batch_4_support_shuffled"))
        for cell in cells
    ]
    support_advantage = [
        direct - shuffled
        for direct, shuffled in zip(directed_min_support, shuffled_min_support)
    ]
    directed_all_mature_count = sum(
        all(row["mature"] for row in target_rows(cell, "rent_batch_4_support_directed"))
        for cell in cells
    )
    directed_unsupported_deaths = sum(
        row["unsupported_death"]
        for cell in cells
        for row in target_rows(cell, "rent_batch_4_support_directed")
    )
    directed_vs_fixed = [
        _minimum_score(cell, "rent_batch_4_support_directed")
        - _minimum_score(cell, "fixed_8_ranked")
        for cell in cells
    ]
    directed_vs_shuffled = [
        _minimum_score(cell, "rent_batch_4_support_directed")
        - _minimum_score(cell, "rent_batch_4_support_shuffled")
        for cell in cells
    ]
    ordinary_negative = (
        ordinary["median_old_joint_success"] < 0.85
        or ordinary["median_new_joint_success"] < 0.85
        or ordinary["both_at_least_0_85_task_count"] < 16
    )
    matched_exploration = all(
        cell["invariants"]["exploration_timing_matched"]
        and cell["invariants"]["experience_budget_matched"]
        for cell in cells
    )
    safety_and_identity = all(
        cell["invariants"]["pass"]
        and all(
            cell["arms"][arm]["causal_rent"]["safety_ceiling_bind_count"] == 0
            for arm in RENT_ARMS
        )
        for cell in cells
    )
    gate_rows = {
        "fixed_reference": all((
            fixed["median_old_joint_success"] >= 0.85,
            fixed["median_new_joint_success"] >= 0.85,
            fixed["both_at_least_0_85_task_count"] >= 16,
        )),
        "negative_replication": ordinary_negative,
        "evidence_manipulation": all((
            sum(value >= 32 for value in directed_min_support) >= 16,
            sum(value > 0 for value in support_advantage) >= 14,
            statistics.median(support_advantage) >= 12,
        )),
        "unsupported_death": all((
            directed_all_mature_count >= 16,
            directed_unsupported_deaths <= 4,
        )),
        "behavior": all((
            directed["median_old_joint_success"] >= 0.85,
            directed["median_new_joint_success"] >= 0.85,
            directed["both_at_least_0_85_task_count"] >= 16,
        )),
        "fixed_noninferiority": (
            statistics.median(directed_vs_fixed) >= -0.05
        ),
        "responsibility_selectivity": all((
            sum(value > 0 for value in directed_vs_shuffled) >= 14,
            statistics.median(directed_vs_shuffled) >= 0.10,
        )),
        "matched_exploration": matched_exploration,
        "safety_and_identity": safety_and_identity,
    }
    return {
        "gate_rows": gate_rows,
        "development_support": all(gate_rows.values()),
        "directed_all_four_supported_task_count": sum(
            value >= 32 for value in directed_min_support
        ),
        "directed_all_four_mature_task_count": directed_all_mature_count,
        "directed_target_unsupported_death_count": directed_unsupported_deaths,
        "directed_over_shuffled_support_task_count": sum(
            value > 0 for value in support_advantage
        ),
        "median_directed_min_support_advantage": statistics.median(
            support_advantage
        ),
        "median_directed_difference_vs_fixed": statistics.median(
            directed_vs_fixed
        ),
        "directed_over_shuffled_behavior_task_count": sum(
            value > 0 for value in directed_vs_shuffled
        ),
        "median_directed_behavior_advantage_over_shuffled": (
            statistics.median(directed_vs_shuffled)
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--seed-start", type=int, default=SEEDS[0])
    parser.add_argument("--seed-count", type=int, default=len(SEEDS))
    parser.add_argument("--train-per-phase", type=int, default=TRAIN_PER_PHASE)
    parser.add_argument("--development-count", type=int, default=DEVELOPMENT_COUNT)
    parser.add_argument("--evaluation-count", type=int, default=EVALUATION_COUNT)
    parser.add_argument(
        "--smoke",
        action="store_true",
        help="allow a bounded retired-seed protocol check",
    )
    args = parser.parse_args()
    seeds = tuple(range(args.seed_start, args.seed_start + args.seed_count))
    if args.smoke:
        if any(seed in SEEDS for seed in seeds):
            raise ValueError("smoke mode may not touch frozen fresh seeds")
        if not 1 <= args.train_per_phase <= TRAIN_PER_PHASE:
            raise ValueError("invalid smoke training budget")
        if not 1 <= args.development_count <= DEVELOPMENT_COUNT:
            raise ValueError("invalid smoke development budget")
        if not 1 <= args.evaluation_count <= EVALUATION_COUNT:
            raise ValueError("invalid smoke evaluation budget")
    else:
        if args.train_per_phase != TRAIN_PER_PHASE:
            raise ValueError("fresh runner uses the frozen 4,096 episode budget")
        if args.development_count != DEVELOPMENT_COUNT:
            raise ValueError("fresh runner uses the frozen 512-row development pool")
        if args.evaluation_count != EVALUATION_COUNT:
            raise ValueError("fresh runner uses the frozen 512-row evaluation pool")
        if seeds != SEEDS:
            raise ValueError("fresh runner uses only the frozen seed range")

    partial = args.output.with_suffix(".partial.json")
    repo_root = Path(__file__).resolve().parents[2]
    key_door = runpy.run_path(str(KEY_DOOR_RUNNER))
    responsibility = runpy.run_path(str(RESPONSIBILITY_RUNNER))
    make_task = key_door["_make_task"]
    complete_state = responsibility["_complete_policy_state"]
    policy_config = EpisodicCompositionConfig(
        exploration_rate=0.15,
        discount=0.97,
    )
    phase0_config = OnlineCompositionConfig(max_total_proposals=64)
    reservoir_config = ExperienceReservoirConfig(capacity=2048)

    task_rows = []
    phase0_work = []
    for index, seed in enumerate(seeds, start=1):
        task = _prepare_task(make_task(
            seed,
            development_evaluation_count=args.development_count,
        ))
        if args.smoke:
            task = _truncate_task(
                task,
                train_count=args.train_per_phase,
                development_count=args.development_count,
                evaluation_count=args.evaluation_count,
            )
        policy = EpisodicCompositionPolicy(
            task["all_action_ids"],
            random_seed=seed + 11_000_000,
            config=policy_config,
            composition_config=phase0_config,
            reservoir_config=reservoir_config,
        )
        for row in task["train_regime_0"]:
            _train_episode(policy, task, row, 0)
        quiescence = _quiesce_checkpoint(policy, task)
        development = _evaluate(
            policy,
            task,
            task["development_evaluation_regime_0"],
            0,
        )
        state = complete_state(policy)
        checkpoint_hash = _hash_json(state)
        phase0_work.append((task, policy, checkpoint_hash))
        task_rows.append({
            "seed": seed,
            "phase0_checkpoint_sha256": checkpoint_hash,
            "phase0_development": development,
            "phase0_quiescence": quiescence,
            "task_manifests": {
                name: task[f"{name}_sha256"]
                for name in (
                    "train_regime_0",
                    "train_regime_1",
                    "evaluation_regime_0",
                    "evaluation_regime_1",
                    "development_evaluation_regime_0",
                )
            },
            "m1_changed_cue_bit": task["m1_changed_cue_bit"],
            "demands": {},
        })
        _write_json(partial, {
            "status": "phase0_in_progress",
            "task_rows": task_rows,
        })
        print(f"completed phase0 task {index}/{len(seeds)}", flush=True)

    phase0_pass = all(
        row["phase0_development"]["joint_success"] >= 0.85
        and row["phase0_quiescence"]["post_trial_count"] == 0
        and row["phase0_quiescence"]["behavior_unchanged"]
        for row in task_rows
    )
    if not phase0_pass:
        payload = {
            "schema_version": "recon_support_directed_exploration_raw.v1",
            "status": "phase0_failed",
            "source_commit": _git_commit(repo_root),
            "task_rows": task_rows,
            "development_support": False,
        }
        _write_json(args.output, payload)
        partial.unlink(missing_ok=True)
        print(args.output)
        return 0

    for task_index, (task, phase0_policy, checkpoint_hash) in enumerate(
        phase0_work
    ):
        row_output = task_rows[task_index]
        for demand in DEMANDS:
            clones = {arm: deepcopy(phase0_policy) for arm in ARMS}
            clone_hashes = {
                arm: _hash_json(complete_state(policy))
                for arm, policy in clones.items()
            }
            clone_parity = all(
                value == checkpoint_hash for value in clone_hashes.values()
            )
            arm_rows = {}
            for arm in ARMS:
                policy = clones[arm]
                _configure_arm(policy, arm)
                shared_before = _shared_hash(policy)
                action_digest = hashlib.sha256()
                observation_digest = hashlib.sha256()
                trajectory = []
                active_checkpoints = tuple(sorted(set(
                    checkpoint
                    for checkpoint in (*CHECKPOINTS, args.train_per_phase)
                    if checkpoint <= args.train_per_phase
                )))
                for episode, experience_row in enumerate(
                    task["train_regime_1"], start=1
                ):
                    key_action, door_action, door_atoms, _ = _train_episode(
                        policy, task, experience_row, demand
                    )
                    action_digest.update(
                        f"{key_action}|{door_action}\n".encode()
                    )
                    observation_digest.update(
                        ("|".join(door_atoms) + "\n").encode()
                    )
                    if episode in active_checkpoints:
                        trajectory.append({
                            "phase1_episode": episode,
                            "old_development": _evaluate(
                                policy, task,
                                task["development_evaluation_regime_0"], 0,
                            ),
                            "new_development": _evaluate(
                                policy, task,
                                task["evaluation_regime_1"], demand,
                            ),
                            "candidates": _candidate_checkpoint(policy),
                        })
                arm_rows[arm] = _arm_result(
                    policy, task, demand,
                    shared_before=shared_before,
                    trajectory=trajectory,
                    action_digest=action_digest.hexdigest(),
                    observation_digest=observation_digest.hexdigest(),
                    training_episode_count=args.train_per_phase,
                )
                _write_json(partial, {
                    "status": "arm_checkpoint",
                    "completed_seed": task["seed"],
                    "completed_demand": demand,
                    "completed_arm": arm,
                    "clone_hashes": clone_hashes,
                    "completed_arm_rows": arm_rows,
                    "task_rows": task_rows,
                })

            cell = {
                "demand": demand,
                "changed_cue_bits": sorted(_changed_cue_bits(task, demand)),
                "clone_hashes": clone_hashes,
                "clone_parity": clone_parity,
                "arms": arm_rows,
            }
            cell["invariants"] = _cell_invariants(cell)
            row_output["demands"][str(demand)] = cell
            _write_json(partial, {
                "status": "phase1_in_progress",
                "completed_seed": task["seed"],
                "completed_demand": demand,
                "task_rows": task_rows,
            })
            print(
                f"completed seed {task_index + 1}/{len(seeds)} demand {demand}",
                flush=True,
            )

    summaries = _summaries(task_rows)
    gates = _gates(task_rows, summaries)
    payload = {
        "schema_version": "recon_support_directed_exploration_raw.v1",
        "status": "complete",
        "track": "generic_core_development",
        "confirmation_claimed": False,
        "krk_claimed": False,
        "source_commit": _git_commit(repo_root),
        "frozen_contract": str(CONTRACT),
        "frozen_seed_range": [seeds[0], seeds[-1]],
        "smoke_mode": args.smoke,
        "policy_config": asdict(policy_config),
        "phase0_composition_config": asdict(phase0_config),
        "reservoir_config": asdict(reservoir_config),
        "task_rows": task_rows,
        "task_rows_sha256": _hash_json(task_rows),
        "summaries": summaries,
        "gates": gates,
        "development_support": gates["development_support"],
        "contract_sha256": _file_hash(repo_root / CONTRACT),
        "causal_rent_implementation_sha256": _file_hash(
            repo_root / "libs/recon-lite/src/recon_lite/causal_rent.py"
        ),
        "online_composition_implementation_sha256": _file_hash(
            repo_root / "libs/recon-lite/src/recon_lite/online_composition.py"
        ),
        "episodic_implementation_sha256": _file_hash(
            repo_root / "libs/recon-lite/src/recon_lite/episodic_composition.py"
        ),
        "runner_sha256": _file_hash(Path(__file__)),
    }
    _write_json(args.output, payload)
    partial.unlink(missing_ok=True)
    print(args.output)
    print(json.dumps({
        "summaries": summaries,
        "gates": gates,
        "development_support": gates["development_support"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
