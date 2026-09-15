"""Recovery recorder fixtures only; original learner/source remain unchanged."""
import json
import pickle
import shutil

import pytest

import run_owner_trial_learning as run
import retry_owner_trial_learning as retry
from test_owner_fresh_start import step


@pytest.fixture(scope='module')
def recovered(tmp_path_factory):
    directory=tmp_path_factory.mktemp('actual-checkpoint-recovery')
    a=run.create_actor(98,'learning-trial')
    previous=run.save_actor(a,directory/'start.pkl.gz')
    a,previous,_=run.train_block(a,list(range(16))*4,directory/'prefix',previous)
    checkpoint=pickle.dumps(a,protocol=5)
    original,_,_=run.train_block(a,list(range(16))*4,directory/'original-full',previous)
    tail=directory/'preserved-tail'
    for name in ('submitted','credited'):
        (tail/name).mkdir(parents=True,exist_ok=True)
        for p in sorted((directory/'original-full'/name).glob('*.json'))[:39]:shutil.copyfile(p,tail/name/p.name)
    restored,_,evaluation,comparison=retry.train_unit(pickle.loads(checkpoint),list(range(16))*4,
        directory/'reexecuted',previous,tail)
    return directory,original,restored,evaluation,comparison


def test_checkpoint_reexecution_matches_all_39_real_records_and_full_actor(recovered):
    directory,original,restored,evaluation,comparison=recovered
    assert comparison['identical_real_reexecutions']==39
    run.verify_same_state(original,restored)
    assert json.loads((directory/'original-full/evaluation.json').read_text())==evaluation
    for row in (3,12,6,9):assert step(original,row)==step(restored,row)
    run.verify_same_state(original,restored)


def test_tail_divergence_is_detected_without_repairing_evidence(recovered,tmp_path):
    directory,_,_,_,_=recovered
    damaged=tmp_path/'damaged';shutil.copytree(directory/'preserved-tail',damaged)
    p=next((damaged/'credited').glob('*.json'));record=json.loads(p.read_text())
    record['prediction']+=.01;p.write_text(json.dumps(record))
    with pytest.raises(AssertionError,match='diverged'):
        retry.tail_match(damaged,directory/'reexecuted')
    assert json.loads(p.read_text())['prediction']==record['prediction']


def test_incomplete_unit_prevents_any_new_environment_work(tmp_path):
    units=tmp_path/'retry-control/units';units.mkdir(parents=True)
    (units/'lost.intent.json').write_text('{}')
    called=[]
    with pytest.raises(AssertionError,match='Unfinished unit'):
        retry.unit(tmp_path,'next',90,lambda counts:called.append(True))
    assert not called
    assert retry.status(tmp_path)['pending_units']==['lost.intent.json']
