#!/usr/bin/env python3
"""Run the frozen graph-internal exact-evidence experiment with frozen admission."""

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
    CompositeCandidate,
    EpisodicCompositionConfig,
    EpisodicCompositionPolicy,
    ExperienceReservoirConfig,
    LifetimeDecisionRecord,
    LinkType,
    OnlineCompositionConfig,
)


DEFAULT_OUTPUT = Path(
    "reports/autogrowth/generic_core/"
    "graph_internal_exact_evidence_20260713.json"
)
CANDIDATE_SEEDS = tuple(range(20262301, 20262341))
ADMITTED_COUNT = 20
ADMISSION_OUTPUT = Path(
    "reports/autogrowth/generic_core/"
    "graph_internal_exact_evidence_admission_20260713.json"
)
DEMANDS = (2,)
ARMS = (
    "fixed_8_ranked",
    "rent_batch_4_ranked",
    "rent_batch_4_graph_activation_directed",
    "rent_batch_4_graph_exact_directed",
    "rent_batch_4_graph_exact_shuffled",
)
RENT_ARMS = ARMS[1:]
REQUEST_ARMS = ARMS[2:]
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
    "GENERIC_CORE_GRAPH_INTERNAL_EXACT_EVIDENCE_WORK_PACKAGE_20260713.md"
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
                "rent_batch_4_graph_activation_directed": (
                    "support_directed"
                ),
                "rent_batch_4_graph_exact_directed": (
                    "exact_support_directed"
                ),
                "rent_batch_4_graph_exact_shuffled": (
                    "exact_support_shuffled"
                ),
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
                    "ever_matured": False,
                    "ever_positive_rent": False,
                    "rent_evidence_support": 0,
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
                "ever_matured": any(
                    event.get("event") in {"promoted", "promoted_replacement"}
                    for event in review_events
                ),
                "ever_positive_rent": any(
                    event.get("event") == "review"
                    and event.get("rent") is not None
                    and float(event["rent"]) > 0.0
                    for event in review_events
                ),
                "activation_count": candidate.activation_count,
                "rent_evidence_support": candidate.rent_evidence_support,
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
    if policy.causal_rent_config is not None:
        policy.assert_rent_evidence_support_parity()
    return [
        {
            "action_id": action_id,
            "candidate_index": index,
            "members": candidate.members,
            "state": candidate.state,
            "activation_count": candidate.activation_count,
            "rent_evidence_support": candidate.rent_evidence_support,
            "confirmation_count": candidate.confirmation_count,
            "exploration_request_count": candidate.exploration_request_count,
            "exploration_probe_benefit_count": (
                candidate.exploration_probe_benefit_count
            ),
        }
        for action_id, channel in policy.channels.items()
        for index, candidate in enumerate(channel.learner.candidates)
    ]


def _request_topology_audit(
    policy: EpisodicCompositionPolicy,
) -> dict[str, object]:
    failures = []
    signatures = {}
    for action_id, channel in policy.channels.items():
        trial_indices = {
            index
            for index, candidate in enumerate(channel.learner.candidates)
            if candidate.state == "trial"
        }
        deficit_indices = set(channel.evidence_deficit_node_ids)
        request_indices = set(channel.evidence_request_node_ids)
        if trial_indices != deficit_indices or trial_indices != request_indices:
            failures.append({
                "action_id": action_id,
                "failure": "trial_request_identity_mismatch",
                "trial_indices": sorted(trial_indices),
                "deficit_indices": sorted(deficit_indices),
                "request_indices": sorted(request_indices),
            })
        for index in sorted(trial_indices & request_indices & deficit_indices):
            candidate = channel.learner.candidates[index]
            request_id = channel.evidence_request_node_ids[index]
            terminal_id = channel.evidence_deficit_node_ids[index]
            request = channel.graph.nodes.get(request_id)
            terminal = channel.graph.nodes.get(terminal_id)
            expected_children = {terminal_id, *candidate.members}
            actual_children = {
                child_id
                for child_id, _ in channel.graph.get_sub_children(request_id)
            }
            if any((
                request is None,
                terminal is None,
                request is not None and request.ntype.name != "SCRIPT",
                terminal is not None and terminal.ntype.name != "TERMINAL",
                actual_children != expected_children,
                channel.graph.parent_of(request_id) is not None,
                channel.graph.get_edge(
                    channel.ROOT_ID, request_id, LinkType.SUB
                ) is not None,
            )):
                failures.append({
                    "action_id": action_id,
                    "candidate_index": index,
                    "failure": "request_topology_firewall",
                    "request_id": request_id,
                    "terminal_id": terminal_id,
                    "expected_children": sorted(expected_children),
                    "actual_children": sorted(actual_children),
                })
        signatures[action_id] = channel.evidence_request_topology_signature()
    return {
        "pass": not failures,
        "failure_count": len(failures),
        "failures": failures,
        "signatures": signatures,
    }


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
    if policy.causal_rent_config is not None:
        policy.assert_rent_evidence_support_parity()
    request_topology = _request_topology_audit(policy)
    snapshot = policy.snapshot()
    channels = {
        action_id: channel.learner.snapshot()
        for action_id, channel in policy.channels.items()
    }
    return {
        "training_episode_count": training_episode_count,
        "terminal_count": policy.terminal_count,
        "terminal_return_sum": policy.terminal_return_sum,
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
        "request_topology": request_topology,
        "main_rng_state_sha256": _hash_json(policy._rng.getstate()),
        "support_rng_state_sha256": _hash_json(
            policy._support_exploration_rng.getstate()
        ),
        "reservoir_rng_state_sha256": (
            _hash_json(policy.experience_reservoir._rng.getstate())
            if policy.experience_reservoir is not None
            else None
        ),
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
        "rent_batch_4_graph_activation_directed": "support_directed",
        "rent_batch_4_graph_exact_directed": "exact_support_directed",
        "rent_batch_4_graph_exact_shuffled": "exact_support_shuffled",
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
            config["max_uncertain_reviews"] == 2,
            snapshot["maximum_global_live_candidate_count"] <= 36,
            snapshot["global_mature_count"] <= 32,
            snapshot["global_live_count"]
            - snapshot["global_mature_count"] <= 4,
            snapshot["final_terminal_return_sum"]
            == arms[arm]["terminal_return_sum"],
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
        and all(
            not forbidden.intersection(request)
            for request in event["requesters"]
        )
        for arm in REQUEST_ARMS
        for event in arms[arm]["exploration"]["events"]
    )

    experience_budget_matched = len({
        (
            arms[arm]["terminal_count"],
            arms[arm]["credited_decision_count"],
            arms[arm]["experience_reservoir"]["seen_count"],
            arms[arm]["experience_reservoir"]["rng_call_count"],
        )
        for arm in ARMS
    }) == 1
    main_rng_matched = len({
        arms[arm]["main_rng_state_sha256"] for arm in ARMS
    }) == 1
    reservoir_rng_matched = len({
        arms[arm]["reservoir_rng_state_sha256"] for arm in ARMS
    }) == 1

    request_explorations = [arms[arm]["exploration"] for arm in REQUEST_ARMS]
    first_exploration = request_explorations[0]
    exploration_timing_matched = all(
        exploration["decision_count"] == first_exploration["decision_count"]
        and exploration["event_count"] == first_exploration["event_count"]
        and exploration["event_decision_indices"]
        == first_exploration["event_decision_indices"]
        and exploration["support_rng_call_count"]
        == first_exploration["support_rng_call_count"]
        and exploration["support_rng_call_count"]
        == exploration["rent_enabled_event_count"]
        and exploration["rent_enabled_event_decision_indices"]
        == first_exploration["rent_enabled_event_decision_indices"]
        for exploration in request_explorations
    )
    support_rng_matched = len({
        arms[arm]["support_rng_state_sha256"] for arm in REQUEST_ARMS
    }) == 1

    probe_accounting_balanced = True
    measurement_firewall_ok = True
    expected_source = {
        "rent_batch_4_graph_activation_directed": "activation",
        "rent_batch_4_graph_exact_directed": "exact_reservoir",
        "rent_batch_4_graph_exact_shuffled": "exact_reservoir",
    }
    for arm in REQUEST_ARMS:
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
            exploration["zero_request_opportunity_count"]
            + exploration["one_request_opportunity_count"]
            + exploration["multi_request_opportunity_count"] == len(events),
            exploration["unequal_strength_opportunity_count"]
            == sum(event["unequal_request_strengths"] for event in events),
            exploration["allocator_could_differ_count"]
            == sum(event["allocators_could_differ"] for event in events),
            candidate_probe_total == sum(
                len(event["beneficiary_candidate_ids"]) for event in events
            ),
        ))
        measurement_firewall_ok = measurement_firewall_ok and all(
            all(
                request["measurement_source"] == expected_source[arm]
                for request in event["requesters"]
            )
            and (
                event["fallback"]
                or event.get("selected_request_graph_node") is not None
            )
            for event in events
        )

    request_topology_ok = all(
        arms[arm]["request_topology"]["pass"] for arm in ARMS
    )
    result = {
        "clone_parity": cell["clone_parity"],
        "shared_unchanged": all(
            arms[arm]["shared_state_unchanged"] for arm in ARMS
        ),
        "experience_budget_matched": experience_budget_matched,
        "main_rng_matched": main_rng_matched,
        "reservoir_rng_matched": reservoir_rng_matched,
        "support_rng_matched": support_rng_matched,
        "exploration_timing_matched": exploration_timing_matched,
        "probe_accounting_balanced": probe_accounting_balanced,
        "measurement_firewall_ok": measurement_firewall_ok,
        "request_topology_ok": request_topology_ok,
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
    activation = summaries["2"][
        "rent_batch_4_graph_activation_directed"
    ]
    exact = summaries["2"]["rent_batch_4_graph_exact_directed"]
    shuffled = summaries["2"]["rent_batch_4_graph_exact_shuffled"]

    def target_rows(cell: dict[str, object], arm: str) -> list[dict[str, object]]:
        return cell["arms"][arm]["target_candidate_diagnostics"]

    activation_min_support = [
        min(
            row["max_review_support"]
            for row in target_rows(
                cell, "rent_batch_4_graph_activation_directed"
            )
        )
        for cell in cells
    ]
    exact_min_support = [
        min(
            row["max_review_support"]
            for row in target_rows(
                cell, "rent_batch_4_graph_exact_directed"
            )
        )
        for cell in cells
    ]
    shuffled_min_support = [
        min(
            row["max_review_support"]
            for row in target_rows(
                cell, "rent_batch_4_graph_exact_shuffled"
            )
        )
        for cell in cells
    ]
    exact_over_activation_support = [
        exact_value - activation_value
        for exact_value, activation_value in zip(
            exact_min_support, activation_min_support
        )
    ]
    exact_over_shuffled_support = [
        exact_value - shuffled_value
        for exact_value, shuffled_value in zip(
            exact_min_support, shuffled_min_support
        )
    ]
    exact_all_mature_and_positive_count = sum(
        all(
            row["ever_matured"] and row["ever_positive_rent"]
            for row in target_rows(
                cell, "rent_batch_4_graph_exact_directed"
            )
        )
        for cell in cells
    )
    exact_unsupported_deaths = sum(
        row["unsupported_death"]
        for cell in cells
        for row in target_rows(
            cell, "rent_batch_4_graph_exact_directed"
        )
    )
    exact_vs_fixed = [
        _minimum_score(cell, "rent_batch_4_graph_exact_directed")
        - _minimum_score(cell, "fixed_8_ranked")
        for cell in cells
    ]
    exact_vs_shuffled_behavior = [
        _minimum_score(cell, "rent_batch_4_graph_exact_directed")
        - _minimum_score(cell, "rent_batch_4_graph_exact_shuffled")
        for cell in cells
    ]

    exact_explorations = [
        cell["arms"][arm]["exploration"]
        for cell in cells
        for arm in (
            "rent_batch_4_graph_exact_directed",
            "rent_batch_4_graph_exact_shuffled",
        )
    ]
    priority_total = sum(
        exploration["zero_request_opportunity_count"]
        + exploration["one_request_opportunity_count"]
        + exploration["multi_request_opportunity_count"]
        for exploration in exact_explorations
    )
    priority_multi = sum(
        exploration["multi_request_opportunity_count"]
        for exploration in exact_explorations
    )
    priority_unequal = sum(
        exploration["unequal_strength_opportunity_count"]
        for exploration in exact_explorations
    )
    priority_could_differ = sum(
        exploration["allocator_could_differ_count"]
        for exploration in exact_explorations
    )
    priority_multi_fraction = (
        priority_multi / priority_total if priority_total else 0.0
    )
    priority_unequal_fraction = (
        priority_unequal / priority_total if priority_total else 0.0
    )
    priority_identified = all((
        priority_multi_fraction >= 0.20,
        priority_unequal_fraction >= 0.10,
        priority_could_differ >= 100,
    ))

    measurement_integrity = all(
        cell["invariants"]["pass"]
        and all(
            cell["arms"][arm]["causal_rent"][
                "safety_ceiling_bind_count"
            ] == 0
            for arm in RENT_ARMS
        )
        for cell in cells
    )
    evidence_acquisition = all((
        sum(value >= 32 for value in exact_min_support) >= 16,
        exact_unsupported_deaths <= 4,
        sum(value > 0 for value in exact_over_activation_support) >= 14,
        statistics.median(exact_over_activation_support) >= 12,
    ))
    maturation = exact_all_mature_and_positive_count >= 16
    behavior = all((
        exact["median_old_joint_success"] >= 0.85,
        exact["median_new_joint_success"] >= 0.85,
        exact["both_at_least_0_85_task_count"] >= 16,
        statistics.median(exact_vs_fixed) >= -0.05,
    ))
    stability = all((
        fixed["median_old_joint_success"] >= 0.85,
        fixed["median_new_joint_success"] >= 0.85,
        fixed["both_at_least_0_85_task_count"] >= 16,
    ))
    priority_effect = None
    priority_status = "not_identified"
    if priority_identified:
        priority_effect = all((
            sum(value > 0 for value in exact_over_shuffled_support) >= 14,
            statistics.median(exact_over_shuffled_support) >= 12,
            sum(value > 0 for value in exact_vs_shuffled_behavior) >= 14,
            statistics.median(exact_vs_shuffled_behavior) >= 0.10,
        ))
        priority_status = "pass" if priority_effect else "fail"

    evidence_mechanism_support = all((
        measurement_integrity,
        evidence_acquisition,
        maturation,
    ))
    transfer_authorized = all((
        evidence_mechanism_support,
        behavior,
        stability,
        priority_identified,
        priority_effect is True,
    ))
    gate_rows = {
        "measurement_integrity": measurement_integrity,
        "evidence_acquisition": evidence_acquisition,
        "maturation": maturation,
        "priority_exposure_identified": priority_identified,
        "priority_effect": priority_effect,
        "behavior": behavior,
        "stability": stability,
    }
    return {
        "gate_rows": gate_rows,
        "evidence_mechanism_support": evidence_mechanism_support,
        "development_support": evidence_mechanism_support,
        "transfer_authorized": transfer_authorized,
        "priority_status": priority_status,
        "exact_all_four_supported_task_count": sum(
            value >= 32 for value in exact_min_support
        ),
        "exact_all_four_mature_positive_task_count": (
            exact_all_mature_and_positive_count
        ),
        "exact_target_unsupported_death_count": exact_unsupported_deaths,
        "exact_over_activation_support_task_count": sum(
            value > 0 for value in exact_over_activation_support
        ),
        "median_exact_min_support_advantage_over_activation": (
            statistics.median(exact_over_activation_support)
        ),
        "exact_over_shuffled_support_task_count": sum(
            value > 0 for value in exact_over_shuffled_support
        ),
        "median_exact_min_support_advantage_over_shuffled": (
            statistics.median(exact_over_shuffled_support)
        ),
        "median_exact_difference_vs_fixed": statistics.median(
            exact_vs_fixed
        ),
        "exact_over_shuffled_behavior_task_count": sum(
            value > 0 for value in exact_vs_shuffled_behavior
        ),
        "median_exact_behavior_advantage_over_shuffled": (
            statistics.median(exact_vs_shuffled_behavior)
        ),
        "priority_exposure": {
            "total_opportunities": priority_total,
            "multi_request_opportunities": priority_multi,
            "multi_request_fraction": priority_multi_fraction,
            "unequal_strength_opportunities": priority_unequal,
            "unequal_strength_fraction": priority_unequal_fraction,
            "allocator_could_differ_count": priority_could_differ,
        },
        "activation_summary": activation,
        "exact_summary": exact,
        "shuffled_summary": shuffled,
    }


def _passes_admission(
    development: dict[str, object],
    quiescence: dict[str, object],
) -> bool:
    return all((
        development["joint_success"] >= 0.85,
        quiescence["post_trial_count"] == 0,
        quiescence["behavior_unchanged"],
    ))


def _priority_canary() -> dict[str, object]:
    """Deterministically prove that priority is observable, not beneficial."""
    directed = EpisodicCompositionPolicy(
        ("action_a", "action_b"),
        random_seed=73,
        config=EpisodicCompositionConfig(exploration_rate=1.0),
        composition_config=OnlineCompositionConfig(
            max_candidates=8,
            max_total_proposals=64,
            residual_update_mode="shared_frozen",
        ),
        reservoir_config=ExperienceReservoirConfig(capacity=64),
    )
    specs = (
        ("action_a", ("anonymous_x", "anonymous_y")),
        ("action_b", ("anonymous_x", "anonymous_z")),
    )
    for action_id, members in specs:
        channel = directed.channels[action_id]
        channel.learner.candidates.append(CompositeCandidate(
            members=members,
            born_observation=0,
            proposal_score=1.0,
            support_at_proposal=2,
            state="trial",
        ))
        channel.sync_external_lifecycle()
    assert directed.experience_reservoir is not None
    for action_id, atoms, count in (
        ("action_a", ("anonymous_x", "anonymous_y"), 2),
        ("action_b", ("anonymous_x", "anonymous_z"), 10),
    ):
        for _ in range(count):
            sequence = directed.experience_reservoir.seen_count
            directed.experience_reservoir.add(LifetimeDecisionRecord(
                sequence=sequence,
                action_id=action_id,
                active_atom_ids=atoms,
                legal_action_ids=("action_a", "action_b"),
                decision_scores=(("action_a", 0.0), ("action_b", 0.0)),
                target=0.0,
                discount=0.97,
                elapsed_steps=0,
            ))
    directed.enable_causal_rent(CausalRentConfig(
        temporary_challenger_allowance=2,
        exploration_request_mode="exact_support_directed",
    ))
    shuffled = deepcopy(directed)
    shuffled.causal_rent_config = replace(
        shuffled.causal_rent_config,
        exploration_request_mode="exact_support_shuffled",
    )
    atoms = ("anonymous_x", "anonymous_y", "anonymous_z")
    directed_actions = tuple(directed.choose(atoms) for _ in range(100))
    shuffled_actions = tuple(shuffled.choose(atoms) for _ in range(100))
    timing_parity = all((
        directed.exploration_event_decision_indices
        == shuffled.exploration_event_decision_indices,
        directed.exploration_event_count == shuffled.exploration_event_count,
        directed.support_exploration_rng_call_count
        == shuffled.support_exploration_rng_call_count,
        directed.rng_call_count == shuffled.rng_call_count,
        _hash_json(directed._rng.getstate())
        == _hash_json(shuffled._rng.getstate()),
        _hash_json(directed._support_exploration_rng.getstate())
        == _hash_json(shuffled._support_exploration_rng.getstate()),
    ))
    opportunity_count = len(directed.support_exploration_events)
    multi_fraction = (
        directed.support_multi_request_opportunity_count / opportunity_count
    )
    unequal_fraction = (
        directed.support_unequal_strength_opportunity_count / opportunity_count
    )
    divergence_count = sum(
        left != right
        for left, right in zip(directed_actions, shuffled_actions)
    )
    passed = all((
        multi_fraction >= 0.40,
        unequal_fraction >= 0.30,
        divergence_count / opportunity_count >= 0.20,
        directed.support_allocator_could_differ_count == opportunity_count,
        timing_parity,
    ))
    return {
        "schema_version": "recon_anonymous_priority_canary.v1",
        "instrumentation_only": True,
        "opportunity_count": opportunity_count,
        "multi_request_count": directed.support_multi_request_opportunity_count,
        "multi_request_fraction": multi_fraction,
        "unequal_strength_count": (
            directed.support_unequal_strength_opportunity_count
        ),
        "unequal_strength_fraction": unequal_fraction,
        "allocator_could_differ_count": (
            directed.support_allocator_could_differ_count
        ),
        "selected_action_divergence_count": divergence_count,
        "selected_action_divergence_fraction": (
            divergence_count / opportunity_count
        ),
        "event_and_rng_budget_parity": timing_parity,
        "directed_action_sha256": _hash_json(directed_actions),
        "shuffled_action_sha256": _hash_json(shuffled_actions),
        "pass": passed,
    }


def _head_file_matches(repo_root: Path, path: Path) -> bool:
    relative = path.resolve().relative_to(repo_root).as_posix()
    result = subprocess.run(
        ("git", "show", f"HEAD:{relative}"),
        cwd=repo_root,
        check=False,
        capture_output=True,
        timeout=30,
    )
    return result.returncode == 0 and result.stdout == path.read_bytes()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--admission-output", type=Path, default=ADMISSION_OUTPUT
    )
    parser.add_argument(
        "--seed-start", type=int, default=CANDIDATE_SEEDS[0]
    )
    parser.add_argument(
        "--seed-count", type=int, default=len(CANDIDATE_SEEDS)
    )
    parser.add_argument(
        "--admission-count", type=int, default=ADMITTED_COUNT
    )
    parser.add_argument("--train-per-phase", type=int, default=TRAIN_PER_PHASE)
    parser.add_argument("--development-count", type=int, default=DEVELOPMENT_COUNT)
    parser.add_argument("--evaluation-count", type=int, default=EVALUATION_COUNT)
    parser.add_argument(
        "--pause-after-admission",
        action="store_true",
        help="pause for the mandatory manifest commit before phase 1",
    )
    parser.add_argument(
        "--smoke",
        action="store_true",
        help="allow a bounded retired-seed protocol check",
    )
    args = parser.parse_args()
    seeds = tuple(range(args.seed_start, args.seed_start + args.seed_count))
    if not 1 <= args.admission_count <= len(seeds):
        raise ValueError("admission count must fit inside candidate seeds")
    if args.smoke:
        if any(seed in CANDIDATE_SEEDS for seed in seeds):
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
        if seeds != CANDIDATE_SEEDS:
            raise ValueError("fresh runner uses only the frozen candidate range")
        if args.admission_count != ADMITTED_COUNT:
            raise ValueError("fresh runner admits exactly twenty checkpoints")
        if not args.pause_after_admission:
            raise ValueError("canonical fresh run requires admission pause")

    partial = args.output.with_suffix(".partial.json")
    repo_root = Path(__file__).resolve().parents[2]
    implementation_commit = _git_commit(repo_root)
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
    priority_canary = _priority_canary()
    if not priority_canary["pass"]:
        raise RuntimeError("anonymous priority canary failed before admission")

    task_rows = []
    admission_attempts = []
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
        for experience_row in task["train_regime_0"]:
            _train_episode(policy, task, experience_row, 0)
        quiescence = _quiesce_checkpoint(policy, task)
        development = _evaluate(
            policy,
            task,
            task["development_evaluation_regime_0"],
            0,
        )
        state = complete_state(policy)
        checkpoint_hash = _hash_json(state)
        admitted = _passes_admission(development, quiescence)
        attempt_row = {
            "attempt_index": index,
            "seed": seed,
            "admitted": admitted,
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
        }
        admission_attempts.append(attempt_row)
        if admitted:
            phase0_work.append((task, policy, checkpoint_hash))
            task_row = deepcopy(attempt_row)
            task_row["demands"] = {}
            task_rows.append(task_row)
        _write_json(partial, {
            "status": "admission_in_progress",
            "attempts": admission_attempts,
            "admitted_seed_count": len(task_rows),
        })
        print(
            f"completed admission candidate {index}/{len(seeds)}; "
            f"admitted {len(task_rows)}/{args.admission_count}",
            flush=True,
        )
        if len(task_rows) == args.admission_count:
            break

    admission_pass = len(task_rows) == args.admission_count
    admission_payload = {
        "schema_version": (
            "recon_graph_internal_exact_evidence_admission_manifest.v1"
        ),
        "status": "complete" if admission_pass else "admission_failed",
        "track": "generic_core_development",
        "implementation_commit": implementation_commit,
        "frozen_contract": str(CONTRACT),
        "candidate_seed_range": [seeds[0], seeds[-1]],
        "candidate_seed_count": len(seeds),
        "admission_target": args.admission_count,
        "attempted_seed_count": len(admission_attempts),
        "admitted_seeds": [row["seed"] for row in task_rows],
        "rejected_seeds": [
            row["seed"] for row in admission_attempts
            if not row["admitted"]
        ],
        "attempts": admission_attempts,
        "attempts_sha256": _hash_json(admission_attempts),
        "admission_rule": {
            "minimum_joint_success": 0.85,
            "required_post_trial_count": 0,
            "require_quiescence_behavior_unchanged": True,
            "order": "ascending_seed_first_twenty",
        },
        "smoke_mode": args.smoke,
        "policy_config": asdict(policy_config),
        "phase0_composition_config": asdict(phase0_config),
        "reservoir_config": asdict(reservoir_config),
        "priority_canary": priority_canary,
        "rng_stream_offsets": {
            "main": 0,
            "channel_first": 1,
            "reservoir": 20_000_003,
            "topology": 30_000_007,
            "support": 40_000_009,
        },
        "contract_sha256": _file_hash(repo_root / CONTRACT),
        "architecture_decision_sha256": _file_hash(
            repo_root / "docs/autogrowth/"
            "INTERNAL_PROPRIOCEPTION_ARCHITECTURE_DECISION_20260713.md"
        ),
        "graph_implementation_sha256": _file_hash(
            repo_root / "libs/recon-lite/src/recon_lite/graph.py"
        ),
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
    _write_json(args.admission_output, admission_payload)
    admission_manifest_sha256 = _file_hash(args.admission_output)
    if not admission_pass:
        payload = {
            "schema_version": (
                "recon_graph_internal_exact_evidence_raw.v1"
            ),
            "status": "admission_failed",
            "implementation_commit": implementation_commit,
            "admission_manifest": str(args.admission_output),
            "admission_manifest_sha256": admission_manifest_sha256,
            "development_support": False,
        }
        _write_json(args.output, payload)
        partial.unlink(missing_ok=True)
        print(args.output)
        return 0

    admission_freeze_commit = "smoke-not-required"
    if not args.smoke:
        print(
            f"ADMISSION_FREEZE_READY {args.admission_output} "
            f"sha256={admission_manifest_sha256}",
            flush=True,
        )
        input(
            "Commit and push the admission manifest, then press Enter "
            "to begin phase 1: "
        )
        if _file_hash(args.admission_output) != admission_manifest_sha256:
            raise RuntimeError("admission manifest changed during freeze pause")
        if not _head_file_matches(repo_root, args.admission_output):
            raise RuntimeError("HEAD does not contain the exact admission manifest")
        admission_freeze_commit = _git_commit(repo_root)
        print(
            f"ADMISSION_FREEZE_VERIFIED {admission_freeze_commit}",
            flush=True,
        )

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
                    "admission_freeze_commit": admission_freeze_commit,
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
                "admission_freeze_commit": admission_freeze_commit,
            })
            print(
                f"completed admitted seed {task_index + 1}/"
                f"{len(phase0_work)} demand {demand}",
                flush=True,
            )

    summaries = _summaries(task_rows)
    gates = _gates(task_rows, summaries)
    payload = {
        "schema_version": (
            "recon_graph_internal_exact_evidence_raw.v1"
        ),
        "status": "complete",
        "track": "generic_core_development",
        "confirmation_claimed": False,
        "krk_claimed": False,
        "implementation_commit": implementation_commit,
        "source_commit": _git_commit(repo_root),
        "admission_freeze_commit": admission_freeze_commit,
        "admission_manifest": str(args.admission_output),
        "admission_manifest_sha256": admission_manifest_sha256,
        "admission_attempts": admission_attempts,
        "frozen_contract": str(CONTRACT),
        "candidate_seed_range": [seeds[0], seeds[-1]],
        "attempted_seed_count": len(admission_attempts),
        "admitted_seeds": [row["seed"] for row in task_rows],
        "smoke_mode": args.smoke,
        "policy_config": asdict(policy_config),
        "phase0_composition_config": asdict(phase0_config),
        "reservoir_config": asdict(reservoir_config),
        "priority_canary": priority_canary,
        "rng_stream_offsets": {
            "main": 0,
            "channel_first": 1,
            "reservoir": 20_000_003,
            "topology": 30_000_007,
            "support": 40_000_009,
        },
        "task_rows": task_rows,
        "task_rows_sha256": _hash_json(task_rows),
        "summaries": summaries,
        "gates": gates,
        "development_support": gates["development_support"],
        "contract_sha256": _file_hash(repo_root / CONTRACT),
        "architecture_decision_sha256": _file_hash(
            repo_root / "docs/autogrowth/"
            "INTERNAL_PROPRIOCEPTION_ARCHITECTURE_DECISION_20260713.md"
        ),
        "graph_implementation_sha256": _file_hash(
            repo_root / "libs/recon-lite/src/recon_lite/graph.py"
        ),
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
