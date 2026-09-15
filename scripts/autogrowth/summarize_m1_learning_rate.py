"""Post-run accounting and checkpoint verification; never calls act or observe."""
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'libs/recon-lite/src')]
from collections import defaultdict
import json
import zipfile
from recon_lite_chess.experiments import m1_learning_rate as e


def changes(before,after):
    return {'gains':[i for i,(a,b) in enumerate(zip(before,after)) if not a and b],
            'losses':[i for i,(a,b) in enumerate(zip(before,after)) if a and not b]}


def main():
    run=ROOT/'reports/autogrowth/runs/m1-learning-rate-seeds479-20260909'
    private=ROOT/'snapshots/autogrowth/m1-learning-rate-seeds479-20260909'
    result=e.prior.read(run/'summary.json');m=result['manifest']
    assert result['status']=='complete' and result['actual_training_moves']==m['training_moves']==12288
    assert result['actual_evaluation_moves']==m['evaluation_moves']==4608
    assert m['source']==e.prior.sources() and not m['final_test_opened']
    source=e.prior.read(ROOT/'reports/autogrowth/development/M1_LONG_PLAY_20260907.json')['run']
    historical=e.prior.read(ROOT/'reports/autogrowth/development/M1_EXPLORATION_20260908.json')['run']
    rows=[]
    for arm in result['results']:
        seed=arm['seed'];rate=arm['learning_rate']
        original,_=e.restore_source(source,ROOT/'snapshots/autogrowth/m1-long-play-seeds4-9',seed)
        assert e.prior.actor_digest(original)==arm['inherited_actor_digest']
        directory=private/f'seed-{seed}/learning_rate-{rate:.2f}'
        endpoint=e.prior.load_checkpoint(directory,m,seed)
        assert endpoint['next_event']==6144 and endpoint['organism'].config.learning_rate==rate
        assert endpoint['organism'].config.exploration==.25
        log=directory/'training-actions.jsonl';assert e.prior.sha(log)==arm['transcript_sha256']
        actions=[json.loads(line) for line in log.read_text().splitlines()]
        assert len(actions)==2048 and [a['event'] for a in actions]==list(range(4096,6144))
        assert [a['pool_index'] for a in actions]==m['plans'][str(seed)][4096:6144]
        assert all(a['real_moves']==1 and a['reward'] in (-1,1) for a in actions)
        initial=arm['inherited_evaluation']['outcomes'];before=initial;milestones=[]
        for event,item in sorted(arm['milestones'].items(),key=lambda x:int(x[0])):
            v=item['result']['evaluation'];assert v['learned_state_unchanged'] and item['checkpoint_reloaded']
            milestones.append({'event':int(event),'mates':v['mates'],
                'against_initial':changes(initial,v['outcomes']),'against_previous':changes(before,v['outcomes'])})
            before=v['outcomes']
        old=next(a for a in historical['results'] if a['seed']==seed and a['exploration']==.25)
        control_reproduced=None
        if rate==.3:
            assert arm['transcript_sha256']==old['transcript_sha256']
            assert all(arm['milestones'][event]['result']==old['milestones'][event]['result']
                for event in old['milestones'])
            control_reproduced=True
        rows.append({'seed':seed,'learning_rate':rate,'initial_mates':sum(initial),
            'milestones':milestones,'final_development_mates':sum(before),
            'final_train_mates':arm['final_train_evaluation']['evaluation']['mates'],
            'training_wins':sum(a['reward']>0 for a in actions),'historical_control_reproduced':control_reproduced,
            'final_outcomes':before,'wall_seconds':arm['wall_seconds']})
    pairs=[]
    for seed in m['seeds']:
        control=next(x for x in rows if x['seed']==seed and x['learning_rate']==.3)
        low=next(x for x in rows if x['seed']==seed and x['learning_rate']==.1)
        control_arm=next(x for x in result['results'] if x['seed']==seed and x['learning_rate']==.3)
        low_arm=next(x for x in result['results'] if x['seed']==seed and x['learning_rate']==.1)
        assert all(control_arm['milestones'][k]['result']['exploration_rng_digest']==
                   low_arm['milestones'][k]['result']['exploration_rng_digest'] for k in control_arm['milestones'])
        pairs.append({'seed':seed,'exploration_rng_matched_at_all_milestones':True,'development_difference_low_minus_control':low['final_development_mates']-control['final_development_mates'],
                      'paired_changes':changes(control['final_outcomes'],low['final_outcomes'])})
    index=[{'path':str(p.relative_to(private)),'sha256':e.prior.sha(p),'bytes':p.stat().st_size}
           for p in sorted(private.rglob('*')) if p.is_file()]
    report={'schema':'m1_learning_rate.public.v1','status':'complete','date':'2026-09-09',
            'distinct_required_tests_passed_before_play':226,'actor_comparison':rows,'paired_comparison':pairs,
            'private_checkpoint_index':index,'run':result,'post_run_actor_actions':0,'post_run_learner_updates':0}
    path=ROOT/'reports/autogrowth/development/M1_LEARNING_RATE_20260909.json'
    e.prior.atomic_json(path,report)
    archive=ROOT.parent/'HECTOR_M1_LEARNING_RATE_CHECKPOINTS_20260909.zip'
    with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=1) as z:
        for item in index:z.write(private/item['path'],'checkpoints/'+item['path'])
        for p in sorted(run.rglob('*.json')):z.write(p,'run/'+str(p.relative_to(run)))
        z.write(path,path.name)
        z.write(ROOT/'docs/autogrowth/M1_LEARNING_RATE.md','M1_LEARNING_RATE.md')
    print(json.dumps({'status':'complete','paired_comparison':pairs,'archive':str(archive)}))

if __name__=='__main__':main()
