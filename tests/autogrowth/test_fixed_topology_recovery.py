"""Planted fixtures isolate the experimental hold, never train chess actors."""
import copy
import pickle

import pytest

from recon_lite.graph import LinkType, NodeType
from recon_lite_chess.coach.interface import Feedback
from recon_lite_chess.experiments.fixed_topology_recovery import (
    RecoveryControl, control_digest, representation_digest, weight_digest,
)
from recon_lite_hector.learning.terminal_development import DevelopmentConfig, TerminalDevelopment
from test_terminal_development import BooleanPort, attach, learned_state


class Controlled(RecoveryControl, TerminalDevelopment):
    pass


def step(o, event, reward=-1, **port_args):
    action = o.act(BooleanPort(**port_args), event_id=event, learn=True)
    o.observe(Feedback(event, action, reward))
    return action


def test_boundary_outcome_preserves_normal_birth_and_pruning():
    config = DevelopmentConfig(max_conditions=8, grace_episodes=1,
                               consolidate_every=1, prune_weight=100)
    old = TerminalDevelopment(seed=2, config=config)
    new = Controlled(seed=2, config=config, recovery_after=2)
    new.hold_topology = True
    for event in range(2):
        assert step(old, event) == step(new, event)
        assert learned_state(old) == learned_state(new)
    assert new.pruned > 0 and new.next_condition > len(new.conditions)
    held, weights = representation_digest(new), weight_digest(new)
    step(new, 2)
    assert representation_digest(new) == held
    assert weight_digest(new) != weights


def test_fixed_definitions_allow_reward_to_change_edges_and_actual_choice():
    o = Controlled(config=DevelopmentConfig(exploration=0, max_conditions=1,
                   grace_episodes=1, consolidate_every=1), recovery_after=1)
    o.schema, o.completed, o.hold_topology = BooleanPort.schema, 1, True
    c = attach(o, ((2, False),), weight=0.01)
    before, weights = representation_digest(o), weight_digest(o)
    assert step(o, 1) == "left"
    assert representation_digest(o) == before and weight_digest(o) != weights
    assert c.stats.relevance_stats.activation_count > 0
    assert o.act(BooleanPort(), event_id=2, learn=False) == "right"
    assert o.bias.slow != 0  # Ordinary consolidation was not accidentally held.


def test_recovery_exploration_matches_despite_different_birth_histories():
    config = DevelopmentConfig(max_conditions=8, exploration=1,
                               grace_episodes=1, consolidate_every=1, prune_weight=100)
    normal = Controlled(seed=3, config=config, recovery_after=2)
    for event in range(2):
        step(normal, event)
    fixed = copy.deepcopy(normal)
    fixed.hold_topology = True
    before = representation_digest(fixed)
    for event in range(2, 12):
        assert step(normal, event) == step(fixed, event)
        assert normal.recovery_rng.getstate() == fixed.recovery_rng.getstate()
    assert normal.rng.getstate() != fixed.rng.getstate()
    assert representation_digest(fixed) == before
    assert representation_digest(normal) != before


def test_rng_restored_on_failure_and_evaluation_does_not_advance_it():
    o = Controlled(recovery_after=1)
    step(o, 0)
    structural_rng, control = o.rng, control_digest(o)
    with pytest.raises(ValueError, match="at least one"):
        o.act(BooleanPort(names=()), event_id=1, learn=True)
    assert o.rng is structural_rng and control_digest(o) == control
    o.act(BooleanPort(), event_id=0, learn=False)
    assert o.rng is structural_rng and control_digest(o) == control


def test_fixed_binding_replicas_share_weights_and_terminals_remain_leaves():
    o = Controlled(recovery_after=1)
    step(o, 0)
    o.hold_topology = True
    before = representation_digest(o)
    step(o, 1, names=("left", "right", "third", "fourth"))
    assert representation_digest(o) == before and o.slots == 4
    for c in o.conditions.values():
        for slot in range(4):
            assert o.graph.edge_by_key[(f"gate:{slot}:{c.identity}", f"option:{slot}", LinkType.SUR)].w is c.weight
    assert all(not o.graph.children(nid) for nid, n in o.graph.nodes.items() if n.ntype == NodeType.TERMINAL)
    o.graph.validate_formal_pairs()


def test_clone_and_checkpoint_keep_history_rng_and_feedback_guards():
    o = Controlled(recovery_after=1)
    step(o, 0)
    o.hold_topology = True
    restored = pickle.loads(pickle.dumps(o))
    for event in range(1, 5):
        assert step(o, event) == step(restored, event)
        assert learned_state(o) == learned_state(restored)
        assert control_digest(o) == control_digest(restored)
    action = o.act(BooleanPort(), event_id=5, learn=True)
    before = copy.deepcopy(learned_state(o))
    control = control_digest(o)
    with pytest.raises(ValueError, match="bind"):
        o.observe(Feedback(5, "wrong", 1))
    assert learned_state(o) == before and control_digest(o) == control
    with pytest.raises(RuntimeError, match="feedback"):
        pickle.dumps(o)
    o.observe(Feedback(5, action, -1))


def test_invalid_boundary_rejected():
    with pytest.raises(ValueError, match="boundary"):
        Controlled(recovery_after=0)
