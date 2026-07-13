from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
import json

import pytest

from recon_lite import (
    CausalRentConfig,
    CompositeCandidate,
    EpisodicCompositionConfig,
    EpisodicCompositionPolicy,
    ExperienceReservoirConfig,
    LifetimeDecisionRecord,
    LifetimeDecisionReservoir,
    LinkType,
    OnlineCompositionConfig,
    record_supports_candidate,
)


def _record(
    sequence: int,
    *,
    action_id: str = "action_a",
    atoms: tuple[str, ...] = ("atom_x", "atom_y"),
    target: float = 1.0,
) -> LifetimeDecisionRecord:
    return LifetimeDecisionRecord(
        sequence=sequence,
        action_id=action_id,
        active_atom_ids=atoms,
        legal_action_ids=("action_a", "action_b"),
        decision_scores=(("action_a", 0.0), ("action_b", 0.0)),
        target=target,
        discount=0.97,
        elapsed_steps=0,
    )


def _policy_with_trials(
    mode: str,
    *,
    candidate_specs: tuple[
        tuple[str, tuple[str, str], int], ...
    ] = (
        ("action_a", ("atom_x", "atom_y"), 2),
        ("action_b", ("atom_x", "atom_z"), 20),
    ),
    min_support: int = 32,
    reservoir_capacity: int = 64,
) -> EpisodicCompositionPolicy:
    policy = EpisodicCompositionPolicy(
        ("action_a", "action_b"),
        random_seed=73,
        config=EpisodicCompositionConfig(exploration_rate=1.0),
        composition_config=OnlineCompositionConfig(
            max_candidates=8,
            max_total_proposals=64,
            residual_update_mode="shared_frozen",
        ),
        reservoir_config=ExperienceReservoirConfig(
            capacity=reservoir_capacity
        ),
    )
    for action_id, members, activation_count in candidate_specs:
        channel = policy.channels[action_id]
        channel.learner.candidates.append(CompositeCandidate(
            members=members,
            born_observation=0,
            proposal_score=1.0,
            support_at_proposal=16,
            state="trial",
            shadow_weight=0.0,
            activation_count=activation_count,
        ))
        channel.sync_external_lifecycle()
    policy.enable_causal_rent(CausalRentConfig(
        temporary_challenger_allowance=len(candidate_specs),
        min_eligible_support=min_support,
        exploration_request_mode=mode,
    ))
    return policy


def _add_retained_record(
    policy: EpisodicCompositionPolicy,
    *,
    action_id: str,
    atoms: tuple[str, ...],
) -> None:
    assert policy.experience_reservoir is not None
    mutation = policy.experience_reservoir.add(_record(
        policy.experience_reservoir.seen_count,
        action_id=action_id,
        atoms=atoms,
    ))
    policy._apply_reservoir_mutation(mutation)


def test_algorithm_r_mutations_are_unambiguous_and_byte_stable() -> None:
    rejected = LifetimeDecisionReservoir(capacity=1, random_seed=0)
    appended = rejected.add(_record(0))
    rejected_before = rejected.snapshot()
    rejection = rejected.add(_record(1))

    assert appended.retained is True
    assert appended.inserted_record == appended.attempted_record
    assert appended.evicted_record is None
    assert appended.retained_index == 0
    assert rejection.retained is False
    assert rejection.inserted_record is None
    assert rejection.evicted_record is None
    assert rejection.retained_index is None
    assert rejected.records == [appended.attempted_record]
    assert rejected.rng_call_count == rejected_before["rng_call_count"] + 1

    replaced = LifetimeDecisionReservoir(capacity=1, random_seed=1)
    first = replaced.add(_record(0))
    replacement = replaced.add(_record(1))
    assert replacement.retained is True
    assert replacement.inserted_record == replacement.attempted_record
    assert replacement.evicted_record == first.inserted_record
    assert replacement.retained_index == 0
    assert replaced.records == [replacement.inserted_record]
    assert replaced.replacement_count == 1
    assert replaced.rng_call_count == 1

    parity = LifetimeDecisionReservoir(capacity=4, random_seed=9)
    for sequence in range(10):
        parity.add(_record(sequence))
    assert [record.sequence for record in parity.records] == [0, 1, 9, 4]
    assert parity.snapshot() == {
        "schema_version": "recon_lifetime_decision_reservoir.v1",
        "capacity": 4,
        "seen_count": 10,
        "retained_count": 4,
        "replacement_count": 4,
        "rng_call_count": 6,
        "records_sha256": (
            "f72f137e9c2fbd299b4ee11c96d90274"
            "cf200fe9431a33f8c13bba9836e67ce2"
        ),
    }


def test_candidate_birth_scans_prebirth_records_and_updates_incrementally() -> None:
    policy = EpisodicCompositionPolicy(
        ("action_a", "action_b"),
        random_seed=19,
        reservoir_config=ExperienceReservoirConfig(capacity=8),
    )
    assert policy.experience_reservoir is not None
    for sequence in range(3):
        policy.experience_reservoir.add(_record(sequence))
    channel = policy.channels["action_a"]
    channel.learner.candidates.append(CompositeCandidate(
        members=("atom_x", "atom_y"),
        born_observation=0,
        proposal_score=1.0,
        support_at_proposal=3,
        state="trial",
    ))
    channel.sync_external_lifecycle()
    policy.enable_causal_rent(CausalRentConfig(
        temporary_challenger_allowance=1,
        min_eligible_support=4,
        exploration_request_mode="exact_support_directed",
    ))

    candidate = channel.learner.candidates[0]
    assert candidate.rent_evidence_support == 3
    _add_retained_record(
        policy, action_id="action_a", atoms=("atom_x", "atom_y")
    )
    assert candidate.rent_evidence_support == 4
    policy.assert_rent_evidence_support_parity()
    assert policy.candidate_rent_stats("action_a", 0).support == 4


def test_eviction_reactivates_exact_trial_deficit() -> None:
    policy = _policy_with_trials(
        "exact_support_directed",
        candidate_specs=(("action_a", ("atom_x", "atom_y"), 99),),
        min_support=1,
        reservoir_capacity=1,
    )
    candidate = policy.channels["action_a"].learner.candidates[0]
    _add_retained_record(
        policy, action_id="action_a", atoms=("atom_x", "atom_y")
    )
    assert candidate.rent_evidence_support == 1
    first = policy.choose(("atom_x", "atom_y"))
    assert policy.support_exploration_events[-1]["fallback"] is True

    assert policy.experience_reservoir is not None
    while candidate.rent_evidence_support:
        mutation = policy.experience_reservoir.add(_record(
            policy.experience_reservoir.seen_count,
            action_id="action_b",
            atoms=("unrelated_x", "unrelated_y"),
        ))
        policy._apply_reservoir_mutation(mutation)
    policy.assert_rent_evidence_support_parity()
    second = policy.choose(("atom_x", "atom_y"))

    assert first in policy.action_ids
    assert second == "action_a"
    event = policy.support_exploration_events[-1]
    assert event["fallback"] is False
    assert event["selected_request_support"] == 0
    assert event["selected_request_deficit"] == 1


def test_request_topology_is_trial_only_and_pruning_leaves_no_stale_nodes() -> None:
    policy = _policy_with_trials(
        "exact_support_directed",
        candidate_specs=(
            ("action_a", ("atom_x", "atom_y"), 0),
            ("action_b", ("atom_x", "atom_z"), 0),
        ),
    )
    action_a = policy.channels["action_a"]
    action_b = policy.channels["action_b"]
    policy._transition_candidate("action_b", 0, "mature", "test_mature")

    assert set(action_a.evidence_request_node_ids) == {0}
    assert action_b.evidence_request_node_ids == {}
    emissions = action_a.emit_evidence_requests(
        ("atom_x", "atom_y", "atom_z"),
        action_id="action_a",
        measurement_source="exact_reservoir",
        min_eligible_support=32,
    )
    assert len(emissions) == 1

    request_id = action_a.evidence_request_node_ids[0]
    terminal_id = action_a.evidence_deficit_node_ids[0]
    policy._transition_candidate("action_a", 0, "pruned", "test_pruned")
    assert action_a.evidence_request_node_ids == {}
    assert action_a.evidence_deficit_node_ids == {}
    assert request_id not in action_a.graph.nodes
    assert terminal_id not in action_a.graph.nodes
    assert all(
        edge.src not in {request_id, terminal_id}
        and edge.dst not in {request_id, terminal_id}
        for edge in action_a.graph.edges
    )


def test_proxy_and_exact_share_request_topology_and_root_isolation() -> None:
    proxy = _policy_with_trials("support_directed")
    exact = _policy_with_trials("exact_support_directed")
    atoms = ("atom_x", "atom_y", "atom_z")

    proxy_signatures = {
        action_id: channel.evidence_request_topology_signature()
        for action_id, channel in proxy.channels.items()
    }
    exact_signatures = {
        action_id: channel.evidence_request_topology_signature()
        for action_id, channel in exact.channels.items()
    }
    assert proxy_signatures == exact_signatures

    before_scores = {
        action_id: channel.predict(atoms)
        for action_id, channel in exact.channels.items()
    }
    exact.choose(atoms)
    after_scores = {
        action_id: channel.predict(atoms)
        for action_id, channel in exact.channels.items()
    }
    assert after_scores == before_scores
    for channel in exact.channels.values():
        for request_id in channel.evidence_request_node_ids.values():
            assert channel.graph.parent_of(request_id) is None
            assert channel.graph.get_edge(
                channel.ROOT_ID, request_id, LinkType.SUB
            ) is None
    assert proxy.support_exploration_events == []
    proxy.choose(atoms)
    assert {
        row["measurement_source"]
        for row in proxy.support_exploration_events[-1]["requesters"]
    } == {"activation"}
    assert {
        row["measurement_source"]
        for row in exact.support_exploration_events[-1]["requesters"]
    } == {"exact_reservoir"}


def test_terminal_ablation_uses_predrawn_ordinary_random_action() -> None:
    policy = _policy_with_trials("exact_support_directed")
    policy.evidence_request_terminals_enabled = False
    selected = policy.choose(("atom_x", "atom_y", "atom_z"))
    event = policy.support_exploration_events[-1]

    assert event["fallback"] is True
    assert selected == event["ordinary_random_action_id"]
    assert policy.support_exploration_rng_call_count == 1
    assert policy.support_zero_request_opportunity_count == 1


def test_deepcopy_preserves_counters_graph_identity_and_rng_state() -> None:
    policy = _policy_with_trials("exact_support_shuffled")
    _add_retained_record(
        policy, action_id="action_a", atoms=("atom_x", "atom_y")
    )
    policy.assert_rent_evidence_support_parity()
    cloned = deepcopy(policy)

    assert cloned.snapshot() == policy.snapshot()
    atoms = ("atom_x", "atom_y", "atom_z")
    assert cloned.choose(atoms) == policy.choose(atoms)
    assert cloned.support_exploration_events == policy.support_exploration_events
    assert cloned.support_exploration_rng_call_count == (
        policy.support_exploration_rng_call_count
    )
    assert {
        action: channel.evidence_request_topology_signature()
        for action, channel in cloned.channels.items()
    } == {
        action: channel.evidence_request_topology_signature()
        for action, channel in policy.channels.items()
    }


def test_graph_activation_proxy_preserves_retired_event_projection() -> None:
    policy = _policy_with_trials(
        "support_directed",
        candidate_specs=(
            ("action_a", ("atom_x", "atom_y"), 2),
            ("action_b", ("atom_x", "atom_y"), 20),
        ),
    )
    selected = policy.choose(("atom_x", "atom_y"))
    event = policy.support_exploration_events[0]
    legacy_fields = {
        key: event[key]
        for key in (
            "decision_index",
            "terminal_count",
            "mode",
            "cumulative_terminal_return",
            "active_request_count",
            "selected_requester",
            "selected_request_support",
            "selected_request_deficit",
            "selected_action_id",
            "ordinary_random_action_id",
            "beneficiary_candidate_ids",
            "fallback",
        )
    }

    assert selected == "action_a"
    assert json.dumps(
        legacy_fields, sort_keys=True, separators=(",", ":")
    ) == (
        '{"active_request_count":2,"beneficiary_candidate_ids":'
        '["action_a:composite_0"],"cumulative_terminal_return":0.0,'
        '"decision_index":1,"fallback":false,"mode":"support_directed",'
        '"ordinary_random_action_id":"action_b","selected_action_id":'
        '"action_a","selected_request_deficit":30,"selected_request_support":'
        '2,"selected_requester":"action_a:composite_0","terminal_count":0}'
    )


def test_final_terminal_return_is_persisted_in_causal_rent_summary() -> None:
    policy = _policy_with_trials("exact_support_directed")
    policy.begin_episode()
    policy.choose(("atom_x", "atom_y", "atom_z"))
    policy.observe_terminal(0.75)
    snapshot = policy.snapshot()

    assert snapshot["terminal_return_sum"] == pytest.approx(0.75)
    assert snapshot["causal_rent"]["final_terminal_return_sum"] == pytest.approx(
        0.75
    )


def test_planted_multi_request_priority_is_identifiable_with_rng_parity() -> None:
    directed = _policy_with_trials(
        "exact_support_directed",
        candidate_specs=(
            ("action_a", ("atom_x", "atom_y"), 0),
            ("action_b", ("atom_x", "atom_z"), 0),
        ),
    )
    for _ in range(2):
        _add_retained_record(
            directed, action_id="action_a", atoms=("atom_x", "atom_y")
        )
    for _ in range(10):
        _add_retained_record(
            directed, action_id="action_b", atoms=("atom_x", "atom_z")
        )
    shuffled = deepcopy(directed)
    shuffled.causal_rent_config = replace(
        shuffled.causal_rent_config,
        exploration_request_mode="exact_support_shuffled",
    )
    atoms = ("atom_x", "atom_y", "atom_z")
    directed_actions = [directed.choose(atoms) for _ in range(100)]
    shuffled_actions = [shuffled.choose(atoms) for _ in range(100)]

    for policy in (directed, shuffled):
        assert policy.support_multi_request_opportunity_count == 100
        assert policy.support_unequal_strength_opportunity_count == 100
        assert policy.support_allocator_could_differ_count == 100
        assert policy.support_exploration_rng_call_count == 100
        assert policy.exploration_event_count == 100
    assert set(directed_actions) == {"action_a"}
    assert set(shuffled_actions) == {"action_a", "action_b"}
    assert directed_actions != shuffled_actions
    assert directed.rng_call_count == shuffled.rng_call_count == 300


def test_support_predicate_is_shared_and_content_blind() -> None:
    record = _record(0)
    assert record_supports_candidate(
        record, "action_a", ("atom_x", "atom_y")
    )
    assert not record_supports_candidate(
        record, "action_b", ("atom_x", "atom_y")
    )
    assert not record_supports_candidate(
        replace(record, legal_action_ids=("action_a",)),
        "action_a",
        ("atom_x", "atom_y"),
    )


def test_incremental_full_scan_equality_after_every_reservoir_mutation() -> None:
    policy = _policy_with_trials(
        "exact_support_directed",
        candidate_specs=(("action_a", ("atom_x", "atom_y"), 0),),
        reservoir_capacity=1,
    )
    candidate = policy.channels["action_a"].learner.candidates[0]
    assert policy.experience_reservoir is not None

    append = policy.experience_reservoir.add(_record(
        0, action_id="action_a", atoms=("atom_x", "atom_y")
    ))
    policy._apply_reservoir_mutation(append)
    policy.assert_rent_evidence_support_parity()
    assert candidate.rent_evidence_support == 1

    saw_rejection = False
    saw_replacement = False
    for _ in range(100):
        mutation = policy.experience_reservoir.add(_record(
            policy.experience_reservoir.seen_count,
            action_id="action_b",
            atoms=("unrelated_x", "unrelated_y"),
        ))
        saw_rejection = saw_rejection or not mutation.retained
        saw_replacement = saw_replacement or mutation.evicted_record is not None
        policy._apply_reservoir_mutation(mutation)
        policy.assert_rent_evidence_support_parity()
        if saw_rejection and saw_replacement:
            break

    assert saw_rejection is True
    assert saw_replacement is True
    assert candidate.rent_evidence_support == 0


def test_causal_proposal_initializes_support_from_prebirth_reservoir() -> None:
    from recon_lite.online_composition import PairEvidence

    policy = EpisodicCompositionPolicy(
        ("action_a", "action_b"),
        random_seed=101,
        reservoir_config=ExperienceReservoirConfig(capacity=16),
    )
    assert policy.experience_reservoir is not None
    for sequence in range(6):
        policy.experience_reservoir.add(_record(sequence))
    learner = policy.channels["action_a"].learner
    learner.observation_count = 16
    learner.global_residual_sum = 4.0
    learner.pair_evidence[("atom_x", "atom_y")] = PairEvidence(
        support=16,
        residual_sum=12.0,
    )
    policy.enable_causal_rent(CausalRentConfig(
        temporary_challenger_allowance=1,
        min_eligible_support=8,
        exploration_request_mode="exact_support_directed",
    ))

    policy._causal_rent_proposal_opportunity()

    assert len(learner.candidates) == 1
    assert learner.candidates[0].rent_evidence_support == 6
    policy.assert_rent_evidence_support_parity()
    assert set(policy.channels["action_a"].evidence_request_node_ids) == {0}


def test_clone_preserves_live_terminal_measurement_state() -> None:
    policy = _policy_with_trials("exact_support_directed")
    channel = policy.channels["action_a"]
    emissions = channel.emit_evidence_requests(
        ("atom_x", "atom_y"),
        action_id="action_a",
        measurement_source="exact_reservoir",
        min_eligible_support=32,
    )
    assert emissions
    terminal_id = str(emissions[0]["terminal_node_id"])
    request_id = str(emissions[0]["request_node_id"])
    cloned = deepcopy(policy)
    cloned_channel = cloned.channels["action_a"]

    assert cloned_channel.graph.nodes[terminal_id].meta == (
        channel.graph.nodes[terminal_id].meta
    )
    assert cloned_channel.graph.nodes[terminal_id].activation.value == (
        channel.graph.nodes[terminal_id].activation.value
    )
    assert cloned_channel.graph.nodes[request_id].activation.value == (
        channel.graph.nodes[request_id].activation.value
    )
    assert cloned_channel.evidence_request_topology_signature() == (
        channel.evidence_request_topology_signature()
    )


def test_phase0_evictions_do_not_update_uninitialized_rent_counter() -> None:
    policy = EpisodicCompositionPolicy(
        ("action_a", "action_b"),
        random_seed=3,
        reservoir_config=ExperienceReservoirConfig(capacity=1),
    )
    channel = policy.channels["action_a"]
    channel.learner.candidates.append(CompositeCandidate(
        members=("atom_x", "atom_y"),
        born_observation=0,
        proposal_score=1.0,
        support_at_proposal=1,
        state="trial",
    ))
    channel.sync_external_lifecycle()
    assert policy.experience_reservoir is not None
    for sequence in range(20):
        mutation = policy.experience_reservoir.add(_record(
            sequence,
            action_id="action_a" if sequence == 0 else "action_b",
            atoms=("atom_x", "atom_y") if sequence == 0 else ("u", "v"),
        ))
        policy._apply_reservoir_mutation(mutation)

    assert channel.learner.candidates[0].rent_evidence_support == 0
