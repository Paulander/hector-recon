from __future__ import annotations

from copy import deepcopy

import pytest

from recon_lite import (
    CausalRentConfig,
    CompositeCandidate,
    EpisodicCompositionPolicy,
    ExperienceReservoirConfig,
    LifetimeDecisionRecord,
    OnlineCompositionConfig,
)


def _policy(mode: str) -> EpisodicCompositionPolicy:
    policy = EpisodicCompositionPolicy(
        ("action_a", "action_b"),
        random_seed=2026,
        composition_config=OnlineCompositionConfig(
            max_candidates=8,
            max_total_proposals=64,
            residual_update_mode="shared_frozen",
        ),
        reservoir_config=ExperienceReservoirConfig(capacity=64),
    )
    channel = policy.channels["action_a"]
    channel.learner.candidates.append(CompositeCandidate(
        members=("atom_x", "atom_y"),
        born_observation=7,
        proposal_score=1.0,
        support_at_proposal=0,
        state="trial",
        shadow_weight=0.0,
    ))
    channel.sync_external_lifecycle()
    policy.enable_causal_rent(CausalRentConfig(
        temporary_challenger_allowance=1,
        min_eligible_support=32,
        exploration_request_mode="exact_support_directed",
        lifecycle_grace_mode=mode,
    ))
    return policy


def _candidate(policy: EpisodicCompositionPolicy) -> CompositeCandidate:
    return policy.channels["action_a"].learner.candidates[0]


def _activate_request(policy: EpisodicCompositionPolicy) -> None:
    _candidate(policy).exploration_request_count += 1


def _add_support(policy: EpisodicCompositionPolicy) -> None:
    assert policy.experience_reservoir is not None
    mutation = policy.experience_reservoir.add(LifetimeDecisionRecord(
        sequence=policy.experience_reservoir.seen_count,
        action_id="action_a",
        active_atom_ids=("atom_x", "atom_y"),
        legal_action_ids=("action_a", "action_b"),
        decision_scores=(("action_a", 0.0), ("action_b", 0.0)),
        target=1.0,
        discount=0.97,
        elapsed_steps=0,
    ))
    policy._apply_reservoir_mutation(mutation)


def test_fixed_and_conditioned_use_identical_graph_local_topology() -> None:
    fixed = _policy("fixed_six")
    conditioned = _policy("support_conditioned_six")

    fixed_signature = fixed.channels["action_a"].lifecycle_grace_topology_signature()
    conditioned_signature = conditioned.channels["action_a"].lifecycle_grace_topology_signature()

    assert fixed_signature == conditioned_signature
    assert len(fixed_signature["node_ids"]) == 5
    assert len(fixed_signature["edges"]) == 8
    assert all(
        fixed.channels["action_a"].ROOT_ID not in edge[:2]
        for edge in fixed_signature["edges"]
    )
    node_ids = set(fixed_signature["node_ids"])
    assert {
        fixed.channels["action_a"].graph.nodes[node_id].meta.get(
            "internal_terminal"
        )
        for node_id in node_ids
        if fixed.channels["action_a"].graph.nodes[node_id].meta.get(
            "internal_terminal"
        ) is not None
    } == {
        "EVIDENCE_DEFICIT",
        "EVIDENCE_PROGRESS",
        "REQUEST_ACTIVE",
        "GRACE_BUDGET_REMAINING",
    }


def test_conditioned_grace_emits_only_from_graph_conjunction() -> None:
    policy = _policy("support_conditioned_six")
    _activate_request(policy)

    policy.review_causal_rent()

    candidate = _candidate(policy)
    assert candidate.state == "trial"
    assert candidate.grace_extension_count == 1
    deferred = [
        event for event in policy.causal_rent_events
        if event["event"] == "unsupported_deferred"
    ]
    assert len(deferred) == 1
    audit = deferred[0]["grace_audit"]
    assert audit["emitted"] is True
    assert audit["request_activation"] > 0.0
    assert all(
        value > 0.0
        for value in audit["terminal_measurements"].values()
    )


def test_host_lifecycle_consumes_emission_without_reconstructing_decision(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    policy = _policy("support_conditioned_six")
    channel = policy.channels["action_a"]

    def planted_emission(*args: object, **kwargs: object):
        return ({"request_node_id": "planted", "request_activation": 1.0}, {
            "mode": "support_conditioned_six",
            "emitted": True,
            "non_emission_reason": None,
        })

    monkeypatch.setattr(channel, "emit_defer_pruning_request", planted_emission)
    policy.review_causal_rent()

    assert _candidate(policy).state == "trial"
    assert _candidate(policy).grace_extension_count == 1


def test_conditioned_progress_allows_one_stall_then_prunes() -> None:
    policy = _policy("support_conditioned_six")
    candidate = _candidate(policy)

    _activate_request(policy)
    policy.review_causal_rent()
    _add_support(policy)
    _activate_request(policy)
    policy.review_causal_rent()
    _activate_request(policy)
    policy.review_causal_rent()
    assert candidate.state == "trial"
    assert candidate.grace_extension_count == 3

    _activate_request(policy)
    policy.review_causal_rent()
    assert candidate.state == "pruned"
    assert any(
        event["event"] == "conditioned_grace_no_progress"
        for event in policy.causal_rent_events
    )


def test_conditioned_inactive_request_prunes_despite_initial_progress() -> None:
    policy = _policy("support_conditioned_six")

    policy.review_causal_rent()

    assert _candidate(policy).state == "pruned"
    assert any(
        event["event"] == "conditioned_grace_request_inactive"
        for event in policy.causal_rent_events
    )


def test_fixed_grace_defers_five_reviews_and_prunes_at_six() -> None:
    policy = _policy("fixed_six")
    candidate = _candidate(policy)

    for review in range(1, 7):
        policy.review_causal_rent()
        assert candidate.rent_review_count == review
        if review < 6:
            assert candidate.state == "trial"
        else:
            assert candidate.state == "pruned"

    assert candidate.grace_extension_count == 5
    assert any(
        event["event"] == "fixed_grace_budget_exhausted"
        for event in policy.causal_rent_events
    )


def test_two_review_default_and_explicit_control_have_state_rng_parity() -> None:
    default = _policy("two_review")
    explicit = deepcopy(default)

    for policy in (default, explicit):
        policy.review_causal_rent()
        policy.review_causal_rent()

    assert default.snapshot() == explicit.snapshot()
    assert _candidate(default).state == "pruned"
    assert default.support_exploration_rng_call_count == 0
    assert default.causal_rent_topology_rng_call_count == 0


def test_pruning_removes_grace_topology_without_stale_references() -> None:
    policy = _policy("support_conditioned_six")
    channel = policy.channels["action_a"]
    grace_nodes = set(channel.lifecycle_grace_topology_signature()["node_ids"])

    policy.review_causal_rent()

    assert _candidate(policy).state == "pruned"
    assert channel.grace_terminal_node_ids == {}
    assert channel.defer_pruning_request_node_ids == {}
    assert grace_nodes.isdisjoint(channel.graph.nodes)


def test_end_of_phase_trial_is_right_censored_not_pruned() -> None:
    policy = _policy("fixed_six")
    policy.review_causal_rent()

    policy.finalize_causal_rent_phase()

    candidate = _candidate(policy)
    assert candidate.state == "trial"
    assert candidate.rent_right_censored is True
    assert policy.causal_rent_right_censored_count == 1
    assert any(
        event["event"] == "right_censored"
        for event in policy.causal_rent_events
    )
    assert not any(
        event.get("pruning_reason") == "no_progress"
        for event in policy.causal_rent_events
    )
    snapshot = policy.snapshot()["causal_rent"]
    assert snapshot["phase_finalized"] is True
    assert snapshot["right_censored_count"] == 1


def test_deepcopy_preserves_grace_graph_counters_and_events() -> None:
    policy = _policy("support_conditioned_six")
    _activate_request(policy)
    policy.review_causal_rent()

    clone = deepcopy(policy)

    assert clone.snapshot() == policy.snapshot()
    assert clone.channels["action_a"].lifecycle_grace_topology_signature() == (
        policy.channels["action_a"].lifecycle_grace_topology_signature()
    )
    assert _candidate(clone).rent_review_support_high_waters == [0, 0]


def test_grace_requires_exact_directed_evidence_measurement() -> None:
    policy = EpisodicCompositionPolicy(
        ("action_a", "action_b"),
        random_seed=2026,
        reservoir_config=ExperienceReservoirConfig(capacity=64),
    )

    with pytest.raises(ValueError, match="exact directed"):
        policy.enable_causal_rent(CausalRentConfig(
            exploration_request_mode="ordinary_random",
            lifecycle_grace_mode="fixed_six",
        ))


def test_gain_then_one_stall_extends_but_second_stall_prunes() -> None:
    policy = _policy("support_conditioned_six")
    candidate = _candidate(policy)

    _add_support(policy)
    _activate_request(policy)
    policy.review_causal_rent()
    _activate_request(policy)
    policy.review_causal_rent()
    assert candidate.state == "trial"
    assert candidate.grace_extension_count == 2

    _activate_request(policy)
    policy.review_causal_rent()
    assert candidate.state == "pruned"
    assert any(
        event["event"] == "conditioned_grace_no_progress"
        for event in policy.causal_rent_events
    )


def test_support_threshold_routes_to_ordinary_rent_not_grace() -> None:
    fixed = _policy("fixed_six")
    two_review = _policy("two_review")
    for policy in (fixed, two_review):
        _candidate(policy).shadow_weight = 0.5
        for _ in range(32):
            _add_support(policy)
        policy.review_causal_rent()

    fixed_candidate = _candidate(fixed)
    two_candidate = _candidate(two_review)
    assert fixed_candidate.state == two_candidate.state == "mature"
    assert fixed_candidate.last_rent == pytest.approx(two_candidate.last_rent)
    assert fixed_candidate.grace_extension_count == 0
    fixed_review = next(
        event for event in fixed.causal_rent_events
        if event["event"] == "review"
    )
    assert fixed_review["grace_audit"]["emitted"] is False
    assert (
        fixed_review["grace_audit"]["non_emission_reason"]
        == "grace_not_needed"
    )


def test_eviction_cannot_reset_birth_age_budget_or_high_water() -> None:
    policy = _policy("support_conditioned_six")
    candidate = _candidate(policy)
    for _ in range(64):
        _add_support(policy)
    candidate.rent_review_count = 3
    candidate.rent_review_support_high_waters = [0, 16, 32, 64]
    birth = (
        candidate.rent_birth_terminal_count,
        candidate.rent_birth_review_count,
        candidate.rent_birth_support,
    )

    assert policy.experience_reservoir is not None
    while candidate.rent_evidence_support == 64:
        mutation = policy.experience_reservoir.add(LifetimeDecisionRecord(
            sequence=policy.experience_reservoir.seen_count,
            action_id="action_b",
            active_atom_ids=("other_x", "other_y"),
            legal_action_ids=("action_a", "action_b"),
            decision_scores=(("action_a", 0.0), ("action_b", 0.0)),
            target=0.0,
            discount=0.97,
            elapsed_steps=0,
        ))
        policy._apply_reservoir_mutation(mutation)

    policy.assert_rent_evidence_support_parity()
    assert candidate.rent_evidence_support < 64
    assert candidate.rent_evidence_support_high_water == 64
    assert candidate.rent_review_count == 3
    assert candidate.rent_review_support_high_waters == [0, 16, 32, 64]
    assert (
        candidate.rent_birth_terminal_count,
        candidate.rent_birth_review_count,
        candidate.rent_birth_support,
    ) == birth
