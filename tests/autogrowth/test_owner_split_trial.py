"""Mechanical fixtures only; study seeds18/19/20 are not used here."""
import copy
from dataclasses import replace
import pickle

import pytest

import run_owner_fresh_start as old
from recon_lite_hector.learning.owner_trial import TrialOwnerDevelopment, OwnerTrialConfig
from recon_lite_hector.learning.fresh_owner import FreshOwnerDevelopment
from recon_lite_hector.learning.recursive_context import Expression
from recon_lite_hector.learning.terminal_development import Condition, PlasticWeight, StemCellState
from test_owner_fresh_start import step


def actor(*, growth=False, exploration=.25):
    return TrialOwnerDevelopment.create(schema=old.BooleanEnvironment.schema,
        state_coordinates=(0,1,2,3), seed=99,
        config=old.DevelopmentConfig(max_conditions=8, exploration=exploration),
        search=old.BirthSearchConfig(mode='residual'),
        development=old.OwnerDevelopmentConfig(develop_every=64 if growth else 10000),
        limits=old.OwnershipLimits(max_parameters=64,max_definitions=256,max_physical_nodes=2048))


def add_action_feature(a):
    # Planted only to isolate parameter separation, not a study learner feature.
    cid = a.next_condition; a.next_condition += 1
    a.conditions[cid] = Condition(cid, ((4,False),), 'and', a.completed, weight=PlasticWeight())
    a.base_expressions[cid] = Expression('read', atom=(4,False))
    a.birth_visits[cid] = a.owner_visits[0]
    a.owner_seen[0].add(a.base_expressions[cid])
    a.leaves[0] = replace(a.leaves[0],contributions=(*a.leaves[0].contributions,cid))
    a._rebuild(a.slots)


def test_clone_preserves_scores_and_history_but_credit_only_reaches_actual_owner():
    a = actor(); add_action_feature(a)
    for row in (0,12,0,12): step(a,row)
    parent = copy.deepcopy([a.conditions[c] for c in a.leaves[0].contributions])
    unsplit = copy.deepcopy(a)
    children = a.nominate_split(0,Expression('read',atom=(0,True)))
    assert a._leaf_budget_count() == 2 and len(a.leaves) == 3
    for child in children:
        assert a.owner_visits[child] == 0 and not a.owner_evidence[child]
        for oldc,cid in zip(parent,a.leaves[child].contributions):
            assert a.conditions[cid].weight == oldc.weight
            assert a.conditions[cid].stats.relevance_stats.request_exposures == 0
    assert a.split_trials[0].inherited == tuple(parent)
    for row in range(16):
        scores = []
        for candidate,enabled in ((unsplit,False),(a,False),(a,True)):
            probe = copy.deepcopy(candidate)
            probe._set_split_access({0:enabled})
            FreshOwnerDevelopment.act(probe,old.BooleanEnvironment(old.recording.ROWS[row]),
                                      event_id=-1,learn=False)
            scores.append([probe.graph.nodes[f'option:{slot}'].activation.value for slot in range(2)])
        assert scores[0] == scores[1] == scores[2]
    before = {cid:float(c.weight) for cid,c in a.conditions.items()}
    event = a.completed; port = old.BooleanEnvironment(old.recording.ROWS[12])
    action = a.act(port,event_id=event,learn=True)
    owner = a.owner_pending[2]; assignment = a.split_use_pending
    assert assignment[4] == (owner in children)
    with pytest.raises(RuntimeError,match='feedback'): pickle.dumps(a)
    with pytest.raises(ValueError,match='bind'): a.observe(old.recording.Feedback(event+1,action,1))
    assert a.split_use_pending == assignment
    a.observe(old.recording.Feedback(event,action,port.outcome()))
    changed = {cid for cid,c in a.conditions.items() if float(c.weight)!=before[cid]}
    assert changed and changed <= set(a.leaves[owner].contributions)
    assert len(a.split_trials[0].outcomes) == 1
    a.validate_ownership()


def test_bias_prediction_differences_do_not_earn_maturity_and_parent_keeps_learning():
    a = actor(exploration=0)
    children = a.nominate_split(0,Expression('read',atom=(3,True)))
    a.conditions[a.leaves[children[0]].bias_id].weight.fast = -.7
    a.conditions[a.leaves[children[1]].bias_id].weight.fast = .4
    # Bias adds the same score to both actions: identical greedy choices/outcomes
    # despite different predictions. The formal tie-break selects action-b.
    for i in range(255): step(a,i%2)
    assert a.split_trials[0].state == StemCellState.TRIAL
    parent_before = copy.deepcopy(a.conditions[a.leaves[0].bias_id])
    step(a,1)
    history = a.split_trial_history[0]
    assert history.state == StemCellState.PRUNED
    assert history.resolution['mean_reward_gain'] == 0
    assert set(a.leaves) == {0} and len(history.outcomes) == 256
    assert a.conditions[a.leaves[0].bias_id].weight.fast >= parent_before.weight.fast
    assert a.conditions[a.leaves[0].bias_id].stats.relevance_stats.request_exposures >= parent_before.stats.relevance_stats.request_exposures
    assert len(history.retired) == 2 and not a.ownership_history
    with pytest.raises(ValueError,match='already tried'):
        a.nominate_split(0,Expression('read',atom=(3,False)))


def test_real_conflicting_learning_can_accept_then_children_remain_plastic_and_splittable():
    a = actor(); add_action_feature(a)
    children = a.nominate_split(0,Expression('read',atom=(0,True)))
    for i in range(256): step(a,0 if i%2==0 else 12)
    history = a.split_trial_history[0]
    assert history.state == StemCellState.MATURE, history.resolution
    assert history.resolution['mean_reward_gain'] >= .1
    assert set(a.leaves) == set(children) and len(a.ownership_history) == 1
    before = {cid:float(c.weight) for cid,c in a.conditions.items()}
    step(a,12)
    assert any(float(c.weight)!=before[cid] for cid,c in a.conditions.items())
    grandchildren = a.nominate_split(children[0],Expression('read',atom=(3,True)))
    assert len(grandchildren) == 2


def test_pending_trial_does_not_block_births_and_restores_assignment_stream():
    a = actor(growth=True)
    for i in range(192): step(a,i%16)
    assert a.split_trials and any(e['birth'] is not None for e in a.development_history)
    assert a.development_history[0]['birth'] is not None
    assert a.development_history[0]['trial_nomination'] is not None
    b = pickle.loads(pickle.dumps(a,protocol=5))
    baseline = pickle.dumps(b,protocol=5)
    old.evaluate(b)
    assert pickle.dumps(b,protocol=5) == baseline
    for i in range(16):
        assert step(a,i) == step(b,i)
        assert a.conditions == b.conditions and a.split_trials == b.split_trials
        assert a.split_use_rng.getstate() == b.split_use_rng.getstate()
    assert a.owner_visits[0] > 64


def test_storage_budget_is_atomic_and_no_nested_competing_trial():
    a = actor()
    a.ownership_limits = replace(a.ownership_limits,max_parameters=2)
    before = pickle.dumps(a,protocol=5)
    with pytest.raises(ValueError,match='budget'):
        a.nominate_split(0,Expression('read',atom=(0,True)))
    assert pickle.dumps(a,protocol=5) == before
    a.ownership_limits = replace(a.ownership_limits,max_parameters=64)
    children = a.nominate_split(0,Expression('read',atom=(0,True)))
    with pytest.raises(ValueError,match='competing'):
        a.nominate_split(children[0],Expression('read',atom=(3,True)))
    with pytest.raises(ValueError): OwnerTrialConfig(window=255)


def test_runner_checkpoint_seals_trial_assignment_and_detects_evidence_tampering(tmp_path):
    import run_owner_split_trial as runner
    actors = [runner.create_actor(98,role) for role in runner.ROLES]
    runner.verify_initial_pair(actors)
    old.verify_same_state(actors[0],old.create_actor(98,'residual-current'))
    a = actors[1]
    previous = runner.save_actor(a,tmp_path/'start.pkl.gz')
    evidence,trial_evidence = {},{}
    for offset in (0,64):
        directory = tmp_path/f'block-{offset}'
        a,previous,result = runner.train_block(a,list(range(16))*4,directory,previous)
        restored = runner.load_actor(directory/'checkpoint.pkl.gz')
        runner.verify_same_state(a,restored)
        import json
        records = [json.loads(s) for s in (directory/'training.jsonl').read_text().splitlines()]
        runner.verify_birth_evidence(a,records,evidence)
        runner.verify_trials(a,records,trial_evidence)
        assert runner.evaluate(a) == result
    assert sum(len(v) for v in trial_evidence.values()) == 64
    damaged = copy.deepcopy(trial_evidence)
    key = next(iter(damaged)); damaged[key].pop()
    with pytest.raises(AssertionError): runner.verify_trials(a,[],damaged)
