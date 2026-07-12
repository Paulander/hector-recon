from __future__ import annotations

import pytest

from recon_lite import (
    CompositeCandidate,
    EpisodicCompositionConfig,
    EpisodicCompositionPolicy,
    GraphBackedCompositionChannel,
    LinkType,
    OnlineCompositionConfig,
)


def _fast_composition_config() -> OnlineCompositionConfig:
    return OnlineCompositionConfig(
        learning_rate=0.5,
        proposal_interval=2,
        min_pair_support=1,
        max_candidates=1,
        burn_in_activations=1,
        confirmation_activations=3,
        causal_margin=0.01,
        resource_cost=0.002,
        trial_max_age=20,
    )


def test_graph_score_is_the_prediction_updated_by_learning() -> None:
    channel = GraphBackedCompositionChannel(
        random_seed=3,
        composition_config=_fast_composition_config(),
    )
    before = channel.predict(("atom_a", "atom_b"))
    observed = channel.observe(("atom_a", "atom_b"), 1.0)

    assert observed == before
    assert channel.graph_prediction_mismatch_count == 0
    assert channel.predict(("atom_a", "atom_b")) == pytest.approx(
        channel.learner.predict(("atom_a", "atom_b"))
    )


def test_decision_trace_carries_pre_outcome_graph_responsibility() -> None:
    policy = EpisodicCompositionPolicy(
        ("left", "right"),
        random_seed=4,
        config=EpisodicCompositionConfig(exploration_rate=0.0),
        composition_config=OnlineCompositionConfig(proposal_interval=100),
    )
    selected = policy.choose(("a", "b"))
    trace = policy.episode_trace[0]

    assert set(trace.active_graph_nodes) == {"bias_terminal", "a", "b"}
    assert dict(trace.component_importance) == {
        "a": 0.0,
        "b": 0.0,
        "bias_terminal": 0.0,
    }
    assert dict(trace.raw_component_contributions) == {
        "a": 0.0,
        "b": 0.0,
        "bias_terminal": 0.0,
    }
    policy.observe_terminal(1.0)
    assert any(
        value > 0.0
        for value in policy.channels[
            selected
        ].learner.component_importance.values()
    )


def test_candidate_ablation_and_raw_score_decomposition() -> None:
    channel = GraphBackedCompositionChannel(
        random_seed=2,
        composition_config=OnlineCompositionConfig(proposal_interval=100),
    )
    channel.learner.bias = 0.1
    channel.learner.primitive_weights = {"a": 0.2, "b": 0.3}
    channel.learner.candidates.append(
        CompositeCandidate(
            members=("a", "b"),
            born_observation=0,
            proposal_score=1.0,
            support_at_proposal=16,
            state="mature",
            shadow_weight=0.4,
        )
    )
    channel._sync_topology()
    channel._sync_weights()

    assert channel.predict(("a", "b")) == pytest.approx(1.0)
    assert channel.predict(
        ("a", "b"), disabled_candidate_indices=frozenset({0})
    ) == pytest.approx(0.6)
    decomposition = channel.score_decomposition(("a", "b"))
    assert decomposition["raw_score"] == pytest.approx(1.0)
    assert decomposition["contributions"]["composite_0"] == pytest.approx(0.4)


def test_trial_script_cannot_reach_action_score_root() -> None:
    channel = GraphBackedCompositionChannel(
        random_seed=3,
        composition_config=_fast_composition_config(),
    )
    channel.observe(("atom_a", "atom_b"), 1.0)
    channel.observe(("atom_a", "atom_b"), 1.0)

    candidate = channel.learner.candidates[0]
    candidate_node = channel.candidate_node_ids[0]
    assert candidate.state == "trial"
    assert channel.graph.parent_of(candidate_node) is None
    assert (
        channel.graph.get_edge(channel.ROOT_ID, candidate_node, LinkType.SUB)
        is None
    )
    assert channel.trial_root_edge_count == 0


def test_mature_script_is_and_gated_and_linked_to_score_root() -> None:
    channel = GraphBackedCompositionChannel(
        random_seed=3,
        composition_config=_fast_composition_config(),
    )
    for _ in range(2):
        channel.observe(("atom_a", "atom_b"), 1.0)

    candidate = channel.learner.candidates[0]
    candidate.state = "mature"
    candidate.shadow_weight = 0.75
    channel._sync_topology()
    channel._sync_weights()
    candidate_node = channel.candidate_node_ids[0]
    assert candidate.state == "mature"
    assert channel.graph.parent_of(candidate_node) == channel.ROOT_ID
    assert channel.graph.nodes[candidate_node].meta["aggregation"] == "and"
    channel.predict(("atom_a",))
    assert channel.graph.nodes[candidate_node].activation.value == 0.0
    channel.predict(("atom_a", "atom_b"))
    assert channel.graph.nodes[candidate_node].activation.value == 1.0
    assert channel.graph_prediction_mismatch_count == 0


def test_terminal_credit_reaches_persistent_but_not_cleared_trace() -> None:
    config = EpisodicCompositionConfig(exploration_rate=0.0, discount=0.97)
    persistent = EpisodicCompositionPolicy(
        ("action_a", "action_b"), random_seed=5, config=config
    )
    cleared = EpisodicCompositionPolicy(
        ("action_a", "action_b"), random_seed=5, config=config
    )
    for policy, clear in ((persistent, False), (cleared, True)):
        policy.begin_episode()
        chosen = policy.choose(("atom_a", "atom_b"))
        for _ in range(4):
            policy.real_step(clear_trace=clear)
        credited = policy.observe_terminal(1.0)
        assert chosen in policy.action_ids
        assert credited == (0 if clear else 1)

    assert persistent.credited_decision_count == 1
    assert cleared.credited_decision_count == 0
    assert persistent.selection_update_mismatch_count == 0
    assert all(
        channel.graph_prediction_mismatch_count == 0
        for channel in persistent.channels.values()
    )
    assert all(
        channel.learner.observation_count == 0
        for channel in cleared.channels.values()
    )


def test_greedy_composite_ablation_does_not_mutate_policy() -> None:
    policy = EpisodicCompositionPolicy(
        ("action_a", "action_b"),
        random_seed=5,
        composition_config=_fast_composition_config(),
    )
    channel = policy.channels["action_b"]
    for _ in range(6):
        channel.observe(("atom_a", "atom_b"), 1.0)
    before = channel.learner.snapshot()

    assert policy.greedy_action(("atom_a", "atom_b")) in policy.action_ids
    assert policy.greedy_action(
        ("atom_a", "atom_b"), include_mature_composites=False
    ) in policy.action_ids
    assert channel.learner.snapshot() == before


def test_environment_legal_actions_are_the_only_scored_choices() -> None:
    policy = EpisodicCompositionPolicy(
        ("key_a", "key_b", "door_a", "door_b"),
        random_seed=5,
    )
    policy.channels["door_a"].learner.bias = 1.0
    policy.channels["door_a"]._sync_weights()

    chosen = policy.choose(
        ("anonymous_state",),
        legal_action_ids=("key_a", "key_b"),
    )
    assert chosen in {"key_a", "key_b"}
    assert policy.rng_call_count == 3
    assert policy.greedy_action(
        ("anonymous_state",),
        legal_action_ids=("door_a", "door_b"),
    ) in {"door_a", "door_b"}


def test_two_decision_episode_credits_both_retained_traces() -> None:
    persistent = EpisodicCompositionPolicy(
        ("key_a", "key_b", "door_a", "door_b"),
        random_seed=7,
    )
    reset = EpisodicCompositionPolicy(
        ("key_a", "key_b", "door_a", "door_b"),
        random_seed=7,
    )
    for policy, clear in ((persistent, False), (reset, True)):
        policy.begin_episode()
        policy.choose(("key_context",), legal_action_ids=("key_a", "key_b"))
        policy.real_step(clear_trace=clear)
        policy.choose(
            ("carried_key", "door_context"),
            legal_action_ids=("door_a", "door_b"),
        )
        credited = policy.observe_terminal(1.0)
        assert credited == (1 if clear else 2)

    assert persistent.terminal_trace_lengths == [2]
    assert reset.terminal_trace_lengths == [1]
    assert persistent.rng_call_count == reset.rng_call_count == 6
    assert persistent.selection_update_mismatch_count == 0
    assert reset.selection_update_mismatch_count == 0
