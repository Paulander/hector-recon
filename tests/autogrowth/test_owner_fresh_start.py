"""Fresh initialization and real terminal/feedback/checkpoint boundaries."""
import copy
import json
import pickle

import pytest

import run_owner_fresh_start as runner
from recon_lite_hector.learning.fresh_owner import FreshOwnerDevelopment


def step(actor, row):
    event = actor.completed
    port = runner.BooleanEnvironment(runner.recording.ROWS[row])
    action = actor.act(port,event_id=event,learn=True)
    reward = port.outcome()
    actor.observe(runner.recording.Feedback(event,action,reward))
    return action, reward


def test_empty_pair_has_no_learned_state_and_frozen_evaluation_cannot_initialize_it():
    actors = [runner.create_actor(99,role) for role in runner.ROLES]
    runner.verify_initial_pair(actors)
    for actor in actors:
        before = pickle.dumps(actor,protocol=5)
        runner.verify_same_state(pickle.loads(before),actor)
        assert runner.evaluate(actor)['correct'] == 8
        assert pickle.dumps(actor,protocol=5) == before
        assert actor.slots == 1
        assert actor.graph.nodes['option:0'].meta['actuator_identity'] == 'unbound'


@pytest.mark.parametrize('schema',[(),('not a coordinate',), (1,)])
def test_constructor_rejects_undeclared_schema(schema):
    with pytest.raises(ValueError,match='typed terminal schema'):
        FreshOwnerDevelopment.create(schema=schema,state_coordinates=(0,))


def test_first_actions_use_formal_terminals_and_exploration_stream_from_zero():
    actor = runner.create_actor(99,runner.ROLES[0])
    expected = copy.deepcopy(actor.exploration_rng)
    dormant = actor.rng.getstate()
    for event in range(12):
        if expected.random() < actor.config.exploration:
            expected.randrange(2)
        step(actor,event)
        assert actor.exploration_rng.getstate() == expected.getstate()
        assert actor.rng.getstate() == dormant
    assert actor.completed == actor.owner_visits[0] == 12
    assert all(e.n0+e.n1 == 12 for e in actor.birth_evidence[0])
    assert actor.slots == 2
    with pytest.raises(ValueError,match='increase'):
        actor.act(runner.BooleanEnvironment(runner.recording.ROWS[0]),event_id=0,learn=True)


def test_first_development_checkpoint_replay_evidence_and_tamper_detection(tmp_path):
    actor = runner.create_actor(99,runner.ROLES[1])
    previous = runner.save_actor(actor,tmp_path/'start.pkl.gz')
    order = list(range(16))*4
    actor,_,result = runner.recording.train_block(actor,order,tmp_path/'block',previous)
    assert actor.completed == 64 and actor.development_history[0]['episode'] == 64
    records = [json.loads(s) for s in (tmp_path/'block/training.jsonl').read_text().splitlines()]
    runner.verify_birth_evidence(actor,records,{})
    assert runner.evaluate(actor) == result
    restored = runner.load_actor(tmp_path/'block/checkpoint.pkl.gz')
    for row in (5,14,1,8):
        assert step(actor,row) == step(restored,row)
        assert actor.conditions == restored.conditions
        assert actor.birth_evidence == restored.birth_evidence
    damaged = copy.deepcopy(records)
    damaged[0]['birth_candidate_values'][0] = not damaged[0]['birth_candidate_values'][0]
    checkpoint = runner.load_actor(tmp_path/'block/checkpoint.pkl.gz')
    with pytest.raises(AssertionError): runner.verify_birth_evidence(checkpoint,damaged,{})
    target = tmp_path/'block/credited/000000.json'
    target.write_bytes(target.read_bytes()+b' ')
    with pytest.raises(AssertionError):
        runner.recording.prior.verify_block(tmp_path/'block',order,0,previous)
