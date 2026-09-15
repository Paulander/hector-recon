"""Audit interrupted evidence without executing an environment or changing actors."""
import argparse
from collections import Counter
from dataclasses import asdict
import json
import math
from pathlib import Path
import random

import run_owner_trial_learning as run
from audit_owner_trial_learning import truth
from analyze_owner_split_trial import committed_ids, capacity, value
from summarize_owner_fresh_start import retention


def audit(path):
    root=Path(path)
    assert not (root/'result.json').exists(), 'Use the complete-run audit if a runner result exists.'
    inventory={p.relative_to(root).as_posix():run.digest(p.read_bytes())
               for p in sorted(root.rglob('*')) if p.is_file()}
    sources=json.loads((root/'source.json').read_text())
    for name,expected in sources.items():
        assert run.digest((run.ROOT/name).read_bytes())==run.digest((root/'source-snapshot'/name).read_bytes())==expected
    out={'status':'incomplete','surviving_evidence_audit':'verified','new_environment_actions':0,
         'source_files':len(sources),'sealed_training_actions':0,'unsealed_submitted_actions':0,
         'unsealed_credited_actions':0,'scheduled_evaluation_actions_recorded':0,
         'frozen_reproduction_actions_completed':0,'arithmetic_choices_verified':0,
         'sealed_blocks':0,'checkpoints':0,'arms':[],'missing_arms':[]}
    def check_record(r,order):
        assert r['row']==order[r['event']]
        x,y,z,_=run.ROWS[r['row']]
        assert r['reward']==(1 if (r['action']=='act-b')==(y if z else x) else -1)
        assert r['action'] in ('act-a','act-b')
        n=len(r['active']);assert r['denominator']==n>0
        assert len(r['weights_before'])==len(r['weights_after'])==n
        delta=.3*(r['reward']-r['prediction'])/n
        assert all(math.isclose(after-before,delta,abs_tol=2e-12)
                   for before,after in zip(r['weights_before'],r['weights_after']))
    def arithmetic(actor,e):
        ids=committed_ids(actor)
        for r in e['rows']:
            gap=sum(float(actor.conditions[cid].weight)*(int(value(actor.expressions[cid],r['row'],1))-
                int(value(actor.expressions[cid],r['row'],0))) for cid in ids)
            assert r['action']==('act-b' if gap>=0 else 'act-a')
            x,y,z,_=run.ROWS[r['row']]
            assert r['reward']==(1 if (r['action']=='act-b')==(y if z else x) else -1)
            out['arithmetic_choices_verified']+=1
    for seed in run.SEEDS:
        directory=root/f'seed-{seed}'
        if not directory.exists():
            out['missing_arms'].extend([{'seed':seed,'role':role} for role in run.ROLES]);continue
        order=json.loads((directory/'schedule.json').read_text());assert order==run.schedule(seed)
        starts=[run.load_actor(directory/role/'start.pkl.gz') for role in run.ROLES]
        run.verify_initial_pair(starts)
        for role,actor in zip(run.ROLES,starts):
            role_dir=directory/role
            run.verify_same_state(actor,run.create_actor(seed,role))
            previous=run.digest((role_dir/'start.pkl.gz').read_bytes())
            evaluations=[json.loads((role_dir/'initial-evaluation.json').read_text())]
            arithmetic(actor,evaluations[-1]);out['checkpoints']+=1
            rng=random.Random(f'owner-split-use:{seed}');births={};trials={};records=[];partial=[]
            for block in sorted(role_dir.glob('block-*')):
                offset=int(block.name.removeprefix('block-'))
                if (block/'complete.json').exists():
                    assert offset==actor.completed
                    actor=run.recording.prior.verify_block(block,order[offset:offset+64],offset,previous)
                    previous=run.digest((block/'checkpoint.pkl.gz').read_bytes())
                    rows=[json.loads(s) for s in (block/'training.jsonl').read_text().splitlines()]
                    run.verify_birth_evidence(actor,rows,births);run.verify_trials(actor,rows,trials)
                    evaluations.append(json.loads((block/'evaluation.json').read_text()))
                    arithmetic(actor,evaluations[-1])
                    out['sealed_blocks']+=1;out['checkpoints']+=1;out['sealed_training_actions']+=len(rows)
                else:
                    assert offset==actor.completed
                    intent=json.loads((block/'intent.json').read_text())
                    assert intent=={'start':offset,'stop':offset+64,'order':order[offset:offset+64],
                                    'previous':previous,'evaluate':True}
                    submitted=sorted((block/'submitted').glob('*.json'))
                    credited=sorted((block/'credited').glob('*.json'))
                    rows=[]
                    for index,p in enumerate(credited):
                        r=json.loads(p.read_text());assert r['event']==offset+index
                        assert json.loads((block/'submitted'/p.name).read_text())=={k:v for k,v in r.items() if k!='weights_after'}
                        check_record(r,order);rows.append(r)
                    assert len(submitted)==len(credited)==39
                    assert not (block/'checkpoint.pkl.gz').exists() and not (block/'evaluation.json').exists()
                    out['unsealed_submitted_actions']+=len(submitted);out['unsealed_credited_actions']+=len(credited)
                    partial=rows
                for r in rows:
                    values=(*run.ROWS[r['row']],r['action']=='act-b')
                    assert r['candidate_values']==[truth(e,values) for e in actor.owner_candidates]
                    assert r['birth_candidate_values']==[truth(e,values) for e in actor.birth_expressions]
                    flags=r['split_assignments']
                    assert flags=={str(k):rng.random()<.5 for k in sorted(map(int,flags))}
                if (block/'complete.json').exists() and role!='current':
                    assert actor.split_use_rng.getstate()==rng.getstate()
                records.extend(rows)
            out['scheduled_evaluation_actions_recorded']+=16*len(evaluations)
            sealed=records[:-len(partial)] if partial else records
            residuals = {}
            for r in sealed:
                evidence=residuals.setdefault(r['owner'],[[0,0,0.,0.] for _ in actor.owner_candidates])
                for e,flag in zip(evidence,r['candidate_values']):
                    e[int(flag)]+=1;e[2+int(flag)]+=r['reward']-r['prediction']
            for owner,observed in actor.owner_evidence.items():
                for index,e in observed.items():
                    assert [e.n0,e.n1,e.sum0,e.sum1]==residuals[owner][index]
            counts=Counter(r['owner'] for r in sealed)
            assert all(counts[o]==n for o,n in actor.owner_visits.items())
            all_trials=[*getattr(actor,'split_trial_history',()),*getattr(actor,'split_trials',{}).values()]
            if role=='learning-trial':
                assert set(actor.assessment_clocks)=={(t.parent,t.born) for t in all_trials}
            history=[dict(parent=t.parent,children=t.children,route=t.route,born=t.born,state=t.state.name,
                summary=actor.trial_summary(t),resolution=t.resolution,
                clock=asdict(actor.assessment_clocks[(t.parent,t.born)]) if role=='learning-trial' else None) for t in all_trials]
            final=evaluations[-1]
            out['arms'].append({'seed':seed,'role':role,'checkpoint_episode':actor.completed,
                'recorded_training_actions':len(records),'uncheckpointed_credits':len(partial),
                'score':final['correct'],'A_B':final['context_correct'],
                'first_perfect_episode':next((e['episode'] for e in evaluations if e['correct']==16),None),
                'maximum_correct':max(e['correct'] for e in evaluations),
                'sustained_perfect_from':next((e['episode'] for i,e in enumerate(evaluations)
                    if all(later['correct']==16 for later in evaluations[i:])),None),
                'score_trajectory':[[e['episode'],e['correct']] for e in evaluations],
                'A_retention':retention(evaluations,640,0),'B_retention':retention(evaluations,1280,1),
                'structure':run.structure(actor),'trial_history':history,
                'birth_events':[n['episode'] for n in actor.birth_nominations if n.get('birth') is not None],
                'final_failed_rows':[r['row'] for r in final['rows'] if r['reward']<0],
                'saved_checkpoint_capacity':capacity(actor),
                'storage_cost_through_recorded_actions':{'peak_nodes':max(r['stored_nodes'] for r in records),
                    'peak_parameters':max(r['stored_parameters'] for r in records),
                    'peak_stored_scorers':max(r['stored_scorers'] for r in records)},
                'all_probe_flags_assignment_rng_owner_counts_and_sealed_histories_verified':True})
    assert out['sealed_training_actions']==5376
    assert out['unsealed_credited_actions']==39
    assert out['scheduled_evaluation_actions_recorded']==out['arithmetic_choices_verified']==1392
    assert out['sealed_blocks']==84 and out['checkpoints']==87
    def prefix(role):
        return [json.loads(line) for b in sorted((root/'seed-21'/role).glob('block-*'))[:5]
                for line in (b/'training.jsonl').read_text().splitlines()]
    assert prefix('trial')==prefix('learning-trial')
    assert len(prefix('trial'))==320
    out['matched_trial_first_320_actual_records_identical']=True
    out['matched_checkpoint_1536_scores']={a['role']:next(score for event,score in a['score_trajectory']
                                                      if event==1536) for a in out['arms']}
    out['audit_source_sha256']=run.digest(Path(__file__).read_bytes())
    out['recorded_training_actions']=out['sealed_training_actions']+out['unsealed_submitted_actions']
    out['unrecorded_inflight_action_cannot_be_excluded']=True
    out['raw_inventory_sha256']=run.digest(run.encoded(inventory))
    assert inventory=={p.relative_to(root).as_posix():run.digest(p.read_bytes())
                      for p in sorted(root.rglob('*')) if p.is_file()}
    out['raw_evidence_unchanged_during_audit']=True
    return out


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('run');p.add_argument('--output',required=True)
    args=p.parse_args()
    run.write_once(Path(args.output),run.encoded(audit(args.run)))
