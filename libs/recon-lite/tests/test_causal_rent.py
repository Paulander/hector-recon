from __future__ import annotations

from dataclasses import fields

import pytest

from recon_lite import (
    CausalRentConfig,
    CompositeCandidate,
    EpisodicCompositionConfig,
    EpisodicCompositionPolicy,
    ExperienceReservoirConfig,
    LifetimeDecisionRecord,
    LifetimeDecisionReservoir,
    OnlineCompositionConfig,
)
from recon_lite.online_composition import PairEvidence


def _record(sequence: int, *, target: float) -> LifetimeDecisionRecord:
    return LifetimeDecisionRecord(
        sequence=sequence,
        action_id="action_a",
        active_atom_ids=("atom_x", "atom_y"),
        legal_action_ids=("action_a", "action_b"),
        decision_scores=(("action_a", 0.0), ("action_b", 0.0)),
        target=target,
        discount=0.97,
        elapsed_steps=0,
    )


def _policy(*, candidate_state: str, weight: float) -> EpisodicCompositionPolicy:
    policy = EpisodicCompositionPolicy(
        ("action_a", "action_b"),
        random_seed=41,
        composition_config=OnlineCompositionConfig(
            proposal_interval=128,
            max_candidates=8,
            max_total_proposals=64,
            residual_update_mode="shared_frozen",
        ),
        reservoir_config=ExperienceReservoirConfig(capacity=64),
    )
    channel = policy.channels["action_a"]
    channel.learner.candidates.append(CompositeCandidate(
        members=("atom_x", "atom_y"),
        born_observation=0,
        proposal_score=1.0,
        support_at_proposal=16,
        state=candidate_state,
        shadow_weight=weight,
    ))
    channel.sync_external_lifecycle()
    return policy


def test_lifetime_reservoir_is_bounded_content_blind_algorithm_r() -> None:
    reservoir = LifetimeDecisionReservoir(capacity=4, random_seed=9)
    for sequence in range(10):
        reservoir.add(_record(sequence, target=1.0))

    assert reservoir.seen_count == 10
    assert len(reservoir.records) == 4
    assert reservoir.rng_call_count == 6
    assert reservoir.snapshot()["retained_count"] == 4
    assert set(field.name for field in fields(LifetimeDecisionRecord)) == {
        "sequence",
        "action_id",
        "active_atom_ids",
        "legal_action_ids",
        "decision_scores",
        "target",
        "discount",
        "elapsed_steps",
    }


def test_positive_action_margin_rent_promotes_shadow_candidate() -> None:
    policy = _policy(candidate_state="trial", weight=0.5)
    assert policy.experience_reservoir is not None
    for sequence in range(8):
        policy.experience_reservoir.add(_record(sequence, target=1.0))
    policy.enable_causal_rent(CausalRentConfig(
        global_capacity=1,
        min_eligible_support=8,
    ))

    stats = policy.candidate_rent_stats("action_a", 0)
    assert stats.predictive_benefit == pytest.approx(0.75)
    assert stats.rent == pytest.approx(0.748)
    assert stats.margin_utility == pytest.approx(0.5)
    assert stats.mean_margin_with == pytest.approx(0.5)
    assert stats.mean_margin_without == pytest.approx(0.0)
    assert stats.margin_sign_flip_rate == pytest.approx(1.0)

    policy.review_causal_rent()
    candidate = policy.channels["action_a"].learner.candidates[0]
    assert candidate.state == "mature"
    assert policy.channels["action_a"].graph.parent_of("composite_0") == (
        policy.channels["action_a"].ROOT_ID
    )


def test_negative_mature_candidate_dies_after_two_review_blocks() -> None:
    policy = _policy(candidate_state="mature", weight=0.5)
    assert policy.experience_reservoir is not None
    for sequence in range(8):
        policy.experience_reservoir.add(_record(sequence, target=-1.0))
    policy.enable_causal_rent(CausalRentConfig(
        global_capacity=1,
        min_eligible_support=8,
        consecutive_negative_reviews=2,
    ))

    policy.review_causal_rent()
    candidate = policy.channels["action_a"].learner.candidates[0]
    assert candidate.state == "mature"
    assert candidate.negative_review_streak == 1

    policy.review_causal_rent()
    assert candidate.state == "pruned"
    assert "composite_0" not in policy.channels["action_a"].graph.nodes
    assert any(
        event["event"] == "retired"
        for event in policy.causal_rent_events
    )


def test_global_capacity_allows_only_one_temporary_challenger() -> None:
    policy = _policy(candidate_state="mature", weight=0.25)
    for action_id, channel in policy.channels.items():
        learner = channel.learner
        learner.observation_count = 16
        learner.global_residual_sum = 8.0
        learner.pair_evidence[("new_x", "new_y")] = PairEvidence(
            support=16,
            residual_sum=12.0 if action_id == "action_b" else 10.0,
        )
    policy.enable_causal_rent(CausalRentConfig(
        global_capacity=1,
        temporary_challenger_allowance=1,
        min_eligible_support=8,
    ))

    policy._causal_rent_proposal_opportunity()
    assert policy._global_live_count() == 2
    assert len(policy._trial_candidates()) == 1
    assert policy.maximum_global_live_candidate_count == 2
    assert policy.causal_rent_safety_ceiling_bind_count == 0

    policy._causal_rent_proposal_opportunity()
    assert policy._global_live_count() == 2
    assert policy.causal_rent_challenger_block_count == 1


def test_global_capacity_allows_a_bounded_temporary_challenger_batch() -> None:
    policy = _policy(candidate_state="mature", weight=0.25)
    for action_offset, channel in enumerate(policy.channels.values()):
        learner = channel.learner
        learner.observation_count = 64
        learner.global_residual_sum = 32.0
        for pair_index in range(4):
            pair = (
                f"batch_{action_offset}_{pair_index}_x",
                f"batch_{action_offset}_{pair_index}_y",
            )
            learner.pair_evidence[pair] = PairEvidence(
                support=16,
                residual_sum=20.0 + pair_index + action_offset,
            )
    policy.enable_causal_rent(CausalRentConfig(
        global_capacity=1,
        temporary_challenger_allowance=4,
        min_eligible_support=8,
    ))

    for _ in range(4):
        policy._causal_rent_proposal_opportunity()

    assert policy._global_live_count() == 5
    assert len(policy._trial_candidates()) == 4
    assert policy.maximum_global_live_candidate_count == 5
    assert policy.causal_rent_safety_ceiling_bind_count == 0

    policy._causal_rent_proposal_opportunity()
    assert policy._global_live_count() == 5
    assert policy.causal_rent_challenger_block_count == 1


def test_challenger_batch_is_adjudicated_by_descending_frozen_rent() -> None:
    policy = _policy(candidate_state="trial", weight=0.2)
    channel = policy.channels["action_a"]
    channel.learner.candidates.append(CompositeCandidate(
        members=("atom_x", "atom_y"),
        born_observation=1,
        proposal_score=0.5,
        support_at_proposal=16,
        state="trial",
        shadow_weight=0.5,
    ))
    channel.sync_external_lifecycle()
    assert policy.experience_reservoir is not None
    for sequence in range(8):
        policy.experience_reservoir.add(_record(sequence, target=1.0))
    policy.enable_causal_rent(CausalRentConfig(
        global_capacity=2,
        temporary_challenger_allowance=2,
        min_eligible_support=8,
    ))

    policy.review_causal_rent()

    promotions = [
        event["candidate_index"]
        for event in policy.causal_rent_events
        if event["event"] == "promoted"
    ]
    assert promotions == [1, 0]
    assert all(
        candidate.state == "mature"
        for candidate in channel.learner.candidates
    )


def _support_request_policy(
    mode: str,
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
        reservoir_config=ExperienceReservoirConfig(capacity=64),
    )
    for action_id, activation_count in (
        ("action_a", 2),
        ("action_b", 20),
    ):
        channel = policy.channels[action_id]
        channel.learner.candidates.append(CompositeCandidate(
            members=("atom_x", "atom_y"),
            born_observation=0,
            proposal_score=1.0,
            support_at_proposal=16,
            state="trial",
            shadow_weight=0.0,
            activation_count=activation_count,
        ))
        channel.sync_external_lifecycle()
    policy.enable_causal_rent(CausalRentConfig(
        temporary_challenger_allowance=2,
        exploration_request_mode=mode,
    ))
    return policy


def test_support_directed_exploration_uses_largest_local_deficit() -> None:
    policy = _support_request_policy("support_directed")

    selected = policy.choose(("atom_x", "atom_y"))

    assert selected == "action_a"
    assert policy.exploration_event_count == 1
    assert policy.support_exploration_rng_call_count == 1
    assert policy.support_request_opportunity_count == 1
    assert policy.support_probe_action_count == 1
    event = policy.support_exploration_events[0]
    assert event["selected_requester"] == "action_a:composite_0"
    assert event["selected_request_support"] == 2
    assert event["selected_request_deficit"] == 30
    assert event["fallback"] is False
    action_a = policy.channels["action_a"].learner.candidates[0]
    action_b = policy.channels["action_b"].learner.candidates[0]
    assert action_a.exploration_request_count == 1
    assert action_b.exploration_request_count == 1
    assert action_a.exploration_probe_benefit_count == 1
    assert action_b.exploration_probe_benefit_count == 0
    assert policy.channels["action_a"].trial_root_edge_count == 0


def test_directed_and_shuffled_share_exploration_timing_and_rng_budget() -> None:
    directed = _support_request_policy("support_directed")
    shuffled = _support_request_policy("support_shuffled")

    directed_actions = [
        directed.choose(("atom_x", "atom_y"))
        for _ in range(12)
    ]
    shuffled_actions = [
        shuffled.choose(("atom_x", "atom_y"))
        for _ in range(12)
    ]

    assert directed.exploration_event_decision_indices == (
        shuffled.exploration_event_decision_indices
    )
    assert directed.exploration_event_count == 12
    assert shuffled.exploration_event_count == 12
    assert directed.support_exploration_rng_call_count == 12
    assert shuffled.support_exploration_rng_call_count == 12
    directed_exploration = directed.snapshot()["exploration"]
    shuffled_exploration = shuffled.snapshot()["exploration"]
    assert directed_exploration["rent_enabled_event_count"] == 12
    assert shuffled_exploration["rent_enabled_event_count"] == 12
    assert directed_exploration["rent_enabled_event_decision_indices"] == (
        shuffled_exploration["rent_enabled_event_decision_indices"]
    )
    assert all(
        "cumulative_terminal_return" in event
        for event in directed.support_exploration_events
    )
    assert set(directed_actions) == {"action_a"}
    assert set(shuffled_actions) == {"action_a", "action_b"}


def test_support_requests_cannot_influence_exploitative_choice() -> None:
    policy = _support_request_policy("support_directed")

    selected = policy.choose(("atom_x", "atom_y"), explore=False)

    assert selected in {"action_a", "action_b"}
    assert policy.exploration_event_count == 0
    assert policy.support_exploration_rng_call_count == 0
    assert policy.support_request_opportunity_count == 0
    assert policy.support_probe_action_count == 0
    assert policy.support_exploration_events == []


def test_policy_records_decision_scores_without_laboratory_labels() -> None:
    policy = EpisodicCompositionPolicy(
        ("left", "right"),
        random_seed=12,
        reservoir_config=ExperienceReservoirConfig(capacity=8),
    )
    policy.begin_episode()
    policy.choose(("anonymous_0", "anonymous_1"))
    policy.observe_terminal(1.0)

    assert policy.experience_reservoir is not None
    record = policy.experience_reservoir.records[0]
    assert record.legal_action_ids == ("left", "right")
    assert set(dict(record.decision_scores)) == {"left", "right"}
    serialized_names = {field.name for field in fields(record)}
    assert not serialized_names & {
        "role", "demand", "regime", "correct_action", "phase", "cohort"
    }
