"""Retention diagnosis is numerical accounting, not another training channel."""
import copy
from dataclasses import asdict
import inspect
from pathlib import Path
import time

import chess
import pytest

from recon_lite_chess.experiments import m1_retention as e
from recon_lite_chess.experiments.m1_exploration import train_logged
from recon_lite_hector.learning.terminal_development import DevelopmentConfig
from recon_lite_hector.learning.residual_shadow import ShadowConfig

FENS=('7k/5K2/8/8/8/8/8/R7 w - - 0 1','k7/2K5/8/8/8/8/8/7R w - - 0 1')


def history(tmp_path,rate=.25):
    cfg=DevelopmentConfig(max_conditions=6,births_per_episode=1,grace_episodes=4,
        consolidate_every=4,prune_weight=100,exploration=rate)
    spec={'actor_config':asdict(cfg),'shadow_config':asdict(ShadowConfig(candidates=4,discovery_episodes=2,min_support=1)),
          'after_episode':3,'recovery_after':4}
    a=e.prior.new_actor(9,'none',spec)
    e.prior.train(a,FENS,[0,1]*4,start_event=0,deadline=time.monotonic()+30)
    boundaries={8:copy.deepcopy(a)}
    path=tmp_path/'actions.jsonl'
    with path.open('x') as stream:
        for start in range(8,24,4):
            train_logged(a,FENS,[0,1,1,0],start_event=start,deadline=time.monotonic()+30,stream=stream)
            boundaries[start+4]=copy.deepcopy(a)
    import json
    actions=[json.loads(line) for line in path.read_text().splitlines()]
    counts={'laboratory_transitions':0}
    data=e.f.laboratory_rows(FENS,deadline=time.monotonic()+30,counts=counts)
    # Synthetic attribution target only: do not alter any training outcome.
    target=copy.deepcopy(data[0]); chosen=e.numerical_trace(a,target)['chosen']
    target['wins']=[int(i==(chosen+1)%len(target['bindings'])) for i in range(len(target['bindings']))]
    return boundaries,actions,data,[target]


@pytest.mark.parametrize('rate',[.25,.5])
def test_credit_reconstructs_births_retirements_and_every_saved_weight_without_learning(tmp_path,monkeypatch,rate):
    boundaries,actions,data,targets=history(tmp_path,rate)
    assert boundaries[24].pruned>boundaries[8].pruned
    before={k:e.prior.actor_digest(a) for k,a in boundaries.items()}
    def forbidden(*args,**kwargs):raise AssertionError('numerical audit must not play or update a learner')
    monkeypatch.setattr(chess.Board,'push',forbidden)
    for a in boundaries.values():
        for name in ('act','observe','_birth','_prune'):monkeypatch.setattr(a,name,forbidden)
    result=e.credit_accounting(boundaries,actions,data,targets,deadline=time.monotonic()+30)
    assert result['learner_updates_called']==result['training_moves']==0
    assert result['actors_unchanged'] and result['max_weight_error']<1e-8
    assert [r['event'] for r in result['verified_boundaries']]==[12,16,20,24]
    assert sum(r['events'] for r in result['credit_groups'])==16
    assert result['final_margin_on_final_pair']-result['initial_margin_on_final_pair']==pytest.approx(
        result['actual_credit_margin_change']+result['removal_margin_change'])
    assert before=={k:e.prior.actor_digest(a) for k,a in boundaries.items()}
    # Alternative-action labels are unused in credit. Only logged rewards enter.
    corrupted=copy.deepcopy(data)
    for row in corrupted:row['wins']=[0]*len(row['wins'])
    assert result==e.credit_accounting(boundaries,actions,corrupted,targets,deadline=time.monotonic()+30)


def test_incomplete_or_corrupted_actual_credit_is_rejected(tmp_path):
    boundaries,actions,data,targets=history(tmp_path)
    with pytest.raises(ValueError,match='chronological'):
        e.credit_accounting(boundaries,actions[1:],data,targets,deadline=time.monotonic()+30)
    wrong=copy.deepcopy(actions);wrong[0]['reward']*=-1
    with pytest.raises(RuntimeError,match='saved weights'):
        e.credit_accounting(boundaries,wrong,data,targets,deadline=time.monotonic()+30)
    bad=copy.deepcopy(boundaries);bad[24].retired_conditions.clear()
    with pytest.raises(ValueError,match='persistent definition'):
        e.credit_accounting(bad,actions,data,targets,deadline=time.monotonic()+30)


def test_separate_split_feasibility_does_not_imply_joint_feasibility():
    rows=[{'wins':[1,0]},{'wins':[0,1]}]; matrices=[[(1,),(0,)],[(1,),(0,)]]
    deadline=time.monotonic()+30
    assert all(e.d.ranking_feasibility([row],[matrix],deadline=deadline)['strict_all_winners_rankable']
               for row,matrix in zip(rows,matrices))
    assert not e.d.ranking_feasibility(rows,matrices,deadline=deadline)['strict_all_winners_rankable']
    proof=e.f.checked_certificate(rows,matrices,deadline=deadline)
    assert proof['solver_independent_impossibility_witness']


def test_exploration_boundary_loader_rejects_bad_identity_and_preserves_source(tmp_path,monkeypatch):
    boundaries,_,_,_=history(tmp_path)
    manifest={'source':e.prior.sources(),'start_event':8,'end_event':24}
    private=tmp_path/'private';directory=private/'seed-9/exploration-0.25';directory.mkdir(parents=True)
    a=boundaries[8]
    pointer=e.prior.save_checkpoint(directory,{'seed':9,'role_index':0,'next_event':8,'organism':a},manifest)
    reference={'status':'complete','run':{'status':'complete','manifest':manifest,'results':[
        {'seed':9,'exploration':.25,'config':asdict(a.config),'initial':e.prior.snapshot(a),
         'inherited_evaluation':{'mates':0},'milestones':{}}]},'private_checkpoint_index':[
             {'path':str((directory/pointer['file']).relative_to(private)),'sha256':pointer['sha256']}]}
    before={str(p):p.read_bytes() for p in private.rglob('*') if p.is_file()}
    restored,_,sha=e.restore(reference,private,9,.25,8)
    assert sha==pointer['sha256'] and e.prior.snapshot(restored)==e.prior.snapshot(a)
    assert before=={str(p):p.read_bytes() for p in private.rglob('*') if p.is_file()}
    def forbidden(*args,**kwargs):raise AssertionError('must reject before unpickling')
    monkeypatch.setattr(e.pickle,'load',forbidden)
    reference['private_checkpoint_index'][0]['sha256']='bad'
    with pytest.raises(ValueError,match='transport'):e.restore(reference,private,9,.25,8)


def test_frozen_inspection_counts_moves_and_uses_terminal_readers_only(tmp_path,monkeypatch):
    boundaries,_,data,_=history(tmp_path)
    a=boundaries[24]
    pushes=[]; original=chess.Board.push; measure=e.d.ChessFeaturePort.measure
    def pushed(board,move):pushes.append(move);return original(board,move)
    def measured(port,coordinate,binding):
        assert inspect.currentframe().f_back.f_code is e.d._reader.__code__
        return measure(port,coordinate,binding)
    monkeypatch.setattr(chess.Board,'push',pushed)
    monkeypatch.setattr(e.d.ChessFeaturePort,'measure',measured)
    before=e.prior.actor_digest(a)
    counts={'actor_actions_started':0,'actor_evaluation_moves':0}
    report,joint=e.inspect(a,{'train':data,'validation':data},deadline=time.monotonic()+30,counts=counts)
    assert counts['actor_evaluation_moves']==counts['actor_actions_started']==len(pushes)==4
    assert before==e.prior.actor_digest(a)
    assert all(r['formal_support_and_choice_match'] for r in report.values())
    assert joint['fitted_weights_discarded']
