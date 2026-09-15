"""One-setting isolation and actual recursive development, outside study seeds."""
import copy
from dataclasses import replace
import json

import pytest

import run_owner_headroom as runner
from test_owner_fresh_start import step


def test_only_owner_limit_differs_and_control_is_existing_residual_actor():
    actors = [runner.create_actor(98, role) for role in runner.ROLES]
    runner.verify_initial_pair(actors)
    assert [a.ownership_limits.max_leaves for a in actors] == [4, 8]
    runner.verify_same_state(actors[0], runner.fresh.create_actor(98, 'residual-current'))
    assert all(a.birth_search_config.mode == 'residual' for a in actors)
    with pytest.raises(ValueError, match='unknown'):
        runner.create_actor(98, 'owners-16')


def test_actual_early_learning_matches_then_children_can_exceed_four_owners():
    left, right = [runner.create_actor(98, role) for role in runner.ROLES]
    # Fixture schedule covers all raw states, not a study score or seed search.
    for event in range(512):
        outcomes = [step(actor, event % 16) for actor in (left, right)]
        if event < 192:
            assert outcomes[0] == outcomes[1]
            normalized = copy.deepcopy(right)
            normalized.ownership_limits = replace(normalized.ownership_limits, max_leaves=4)
            runner.verify_same_state(left, normalized)
    assert len(left.leaves) == 4
    assert 4 < len(right.leaves) <= 8
    assert any(e['owner'] != 0 and e['split'] for e in right.development_history)
    for actor in (left, right):
        actor.validate_ownership()
        assert actor.completed == 512
    assert left.exploration_rng.getstate() == right.exploration_rng.getstate()


def test_eight_owner_checkpoint_keeps_limit_evidence_and_frozen_evaluation(tmp_path):
    actor = runner.create_actor(98, 'owners-8')
    previous = runner.save_actor(actor, tmp_path/'start.pkl.gz')
    actor, _, result = runner.recording.train_block(
        actor, list(range(16))*4, tmp_path/'block', previous)
    restored = runner.load_actor(tmp_path/'block/checkpoint.pkl.gz')
    runner.verify_same_state(actor, restored)
    assert restored.ownership_limits.max_leaves == 8
    records = [json.loads(s) for s in (tmp_path/'block/training.jsonl').read_text().splitlines()]
    runner.verify_birth_evidence(restored, records, {})
    assert runner.evaluate(restored) == result
    runner.verify_same_state(actor, restored)
