"""Explicit checkpoint recovery; learner and original recorder remain unchanged."""
import argparse
from dataclasses import asdict
import fcntl
import json
import os
from pathlib import Path
import resource
import shutil
import signal
import time

import run_owner_trial_learning as run

SOURCE=run.ROOT/'snapshots/autogrowth/owner-trial-learning-20260915'
PROTOCOL=run.ROOT/'docs/autogrowth/OWNER_TRIAL_LEARNING_RETRY.md'
NEW_COUNTS={'training':11904,'evaluation':3072,'verification_actions':4464}
MAX_WORKER_SECONDS=3600


def read(path): return json.loads(path.read_text())
def save(path,value): run.json_once(path,value)


def check_sources(out):
    for name,expected in read(out/'source.json').items():
        assert run.digest((run.ROOT/name).read_bytes())==run.digest((out/'source-snapshot'/name).read_bytes())==expected,name


def init(out):
    assert not out.exists(), 'Initialization is once only; inspect status of an existing retry.'
    assert read(SOURCE/'interruption.json')['recorded_training_actions']==5415
    original=read(SOURCE/'source.json')
    for name,expected in original.items():
        assert run.digest((run.ROOT/name).read_bytes())==run.digest((SOURCE/'source-snapshot'/name).read_bytes())==expected
    out.mkdir(parents=True)
    (out/'retry-control/units').mkdir(parents=True)
    (out/'verification').mkdir()
    hashes=dict(original)
    for p in (Path(__file__).resolve(),PROTOCOL):hashes[p.relative_to(run.ROOT).as_posix()]=run.digest(p.read_bytes())
    save(out/'source.json',hashes)
    for name in hashes:
        p=out/'source-snapshot'/name;p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(run.ROOT/name,p)
    provenance={}
    def copy(p):
        relative=p.relative_to(SOURCE);target=out/relative
        target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,target)
        expected=run.digest(p.read_bytes());assert run.digest(target.read_bytes())==expected
        provenance[str(relative)]=expected
    copy(SOURCE/'seed-21/schedule.json')
    blocks=0
    for role in run.ROLES:
        source=SOURCE/'seed-21'/role
        for name in ('start.pkl.gz','initial-evaluation.json'):copy(source/name)
        previous=run.digest((source/'start.pkl.gz').read_bytes())
        order=run.schedule(21)
        for b in sorted(source.glob('block-*')):
            if not (b/'complete.json').exists():continue
            offset=int(b.name.removeprefix('block-'))
            run.recording.prior.verify_block(b,order[offset:offset+64],offset,previous)
            for p in sorted(b.rglob('*')):
                if p.is_file():copy(p)
            previous=run.digest((b/'checkpoint.pkl.gz').read_bytes());blocks+=1
    assert blocks==84
    save(out/'reused.json',{'source':str(SOURCE),'files':provenance,'blocks':84,'checkpoints':87,
         'training':5376,'evaluation':1392,'original_uncheckpointed_credits':39})
    save(out/'intent.json',{'status':'initialized','seeds':run.SEEDS,'roles':run.ROLES,
        'planned':run.COUNTS,'new_execution':NEW_COUNTS,'known_repeated_training':39,
        'original_unrecorded_inflight_execution_unknown':True})
    status(out,write=True)
    return {'initialized':True,'reused_blocks':84,'new_execution':NEW_COUNTS}


def receipts(out):
    return [read(p) for p in sorted((out/'retry-control/units').glob('*.result.json'))]


def status(out,write=False):
    rs=receipts(out);units=out/'retry-control/units'
    pending=[p.name for p in sorted(units.glob('*.intent.json'))
             if not p.with_name(p.name.replace('.intent.json','.result.json')).exists()]
    rows=[]
    for seed in run.SEEDS:
        for role in run.ROLES:
            d=out/f'seed-{seed}'/role
            blocks=sorted(b for b in d.glob('block-*') if (b/'complete.json').exists())
            rows.append({'seed':seed,'role':role,'initialized':(d/'initial-evaluation.json').exists(),
                         'sealed_actions':len(blocks)*64,'verified':(d/'verification.json').exists()})
    actual={k:sum(r.get('new_execution',{}).get(k,0) for r in rs) for k in NEW_COUNTS}
    result={'status':'complete' if (out/'result.json').exists() else 'incomplete_unit' if pending or any(r['status']!='complete' for r in rs) else 'ready',
        'arms':rows,'new_execution_sealed_receipts':actual,'pending_units':pending,
        'worker_wall_seconds':sum(r['wall_seconds'] for r in rs),'failed_units':[r['unit'] for r in rs if r['status']!='complete']}
    if write:
        p=out/'retry-control/status.json';tmp=p.with_suffix('.tmp');tmp.write_bytes(run.encoded(result));os.replace(tmp,p)
    return result


def unit(out,name,limit,fn):
    before=status(out)
    assert not before['pending_units'] and not before['failed_units'], 'Unfinished unit requires evidence accounting before further play.'
    assert before['worker_wall_seconds']+limit<=MAX_WORKER_SECONDS,'Cumulative fixed worker budget reached.'
    directory=out/'retry-control/units';started=time.monotonic()
    save(directory/f'{name}.intent.json',{'unit':name,'pid':os.getpid(),
        'process_start_ticks':Path('/proc/self/stat').read_text().split()[21],
        'started_at_unix':time.time(),'allocated_seconds':limit})
    counts=dict.fromkeys(NEW_COUNTS,0);result={'unit':name,'status':'incomplete','new_execution':counts}
    try:
        payload=fn(counts)
        result.update(status='complete',payload=payload)
        return result
    except BaseException as e:
        result['error']=f'{type(e).__name__}: {e}';raise
    finally:
        result.update(wall_seconds=time.monotonic()-started,max_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
        save(directory/f'{name}.result.json',result);status(out,write=True)


def tail_match(source_block,new_block):
    paths=sorted((source_block/'credited').glob('*.json'))
    assert len(paths)==39
    for p in paths:
        assert read(p)==read(new_block/'credited'/p.name),f'Real reexecution diverged at {p.name}'
        assert read(source_block/'submitted'/p.name)==read(new_block/'submitted'/p.name)
    return {'identical_real_reexecutions':len(paths),'source_tail':str(source_block),
        'source_credit_hashes':{p.name:run.digest(p.read_bytes()) for p in paths}}


def train_unit(actor,order,block,previous,source_tail=None):
    restored,checkpoint,evaluation=run.train_block(actor,order,block,previous)
    comparison=tail_match(source_tail,block) if source_tail is not None else None
    return restored,checkpoint,evaluation,comparison


def step(out):
    check_sources(out)
    for seed in run.SEEDS:
        for role in run.ROLES:
            d=out/f'seed-{seed}'/role
            if not (d/'initial-evaluation.json').exists():
                def start(counts):
                    d.mkdir(parents=True,exist_ok=True)
                    schedule_path=d.parent/'schedule.json'
                    if schedule_path.exists():assert read(schedule_path)==run.schedule(seed)
                    else:save(schedule_path,run.schedule(seed))
                    actors=[run.create_actor(seed,r) for r in run.ROLES];run.verify_initial_pair(actors)
                    a=actors[run.ROLES.index(role)];run.save_actor(a,d/'start.pkl.gz')
                    evaluation=run.evaluate(a);counts['evaluation']+=16;save(d/'initial-evaluation.json',evaluation)
                    return {'seed':seed,'role':role,'event':0,'correct':evaluation['correct']}
                return unit(out,f'{seed}-{role}-start',90,start)
            blocks=sorted(b for b in d.glob('block-*') if (b/'complete.json').exists())
            offset=64*len(blocks)
            if offset>=1920:continue
            target=d/f'block-{offset:06d}'
            assert not target.exists(),'Unsealed block already exists; preserve and account for it.'
            p=d/'start.pkl.gz' if offset==0 else d/f'block-{offset-64:06d}/checkpoint.pkl.gz'
            def train(counts):
                a=run.load_actor(p);assert a.completed==offset
                tail=SOURCE/'seed-21/learning-trial/block-001536' if (seed,role,offset)==(21,'learning-trial',1536) else None
                a,_,evaluation,comparison=train_unit(a,run.schedule(seed)[offset:offset+64],target,run.digest(p.read_bytes()),tail)
                counts['training']+=64;counts['evaluation']+=16
                if comparison:save(out/'retry-control/tail-comparison.json',comparison)
                return {'seed':seed,'role':role,'event':a.completed,'correct':evaluation['correct'],
                        'nodes':len(a.graph.nodes),'parameters':len(a.conditions)}
            return unit(out,f'{seed}-{role}-{offset:06d}',90,train)
    return {'training_complete':True,'next':'verify'}


def verify_arm(out,seed,role,counts):
    d=out/f'seed-{seed}'/role;vd=out/'verification'/f'{seed}-{role}';vd.mkdir(exist_ok=True)
    order=run.schedule(seed);assert read(d.parent/'schedule.json')==order
    actor=run.load_actor(d/'start.pkl.gz');run.verify_same_state(actor,run.create_actor(seed,role))
    previous=run.digest((d/'start.pkl.gz').read_bytes());births={};trials={}
    tally=dict.fromkeys(run.COUNTS,0)
    def verify_eval(actor,path):
        expected=read(path);actual=run.evaluate(actor);counts['verification_actions']+=16
        assert actual==expected
        save(vd/f'{actor.completed:06d}.json',{'checkpoint_episode':actor.completed,
             'evaluation_sha256':run.digest(path.read_bytes()),'actual':actual,'environment_actions':16})
        tally['evaluation']+=16;tally['verification_actions']+=16;tally['checkpoints']+=1
    verify_eval(actor,d/'initial-evaluation.json')
    limits=actor.ownership_limits
    for offset in range(0,1920,64):
        b=d/f'block-{offset:06d}'
        actor=run.recording.prior.verify_block(b,order[offset:offset+64],offset,previous)
        assert actor.ownership_limits==limits
        previous=run.digest((b/'checkpoint.pkl.gz').read_bytes())
        records=[json.loads(s) for s in (b/'training.jsonl').read_text().splitlines()]
        run.verify_birth_evidence(actor,records,births);run.verify_trials(actor,records,trials)
        verify_eval(actor,b/'evaluation.json');tally['training']+=64;tally['blocks']+=1
    save(d/'verification.json',tally)
    return {'seed':seed,'role':role,'counts':tally}


def verify(out):
    check_sources(out)
    assert all(a['sealed_actions']==1920 for a in status(out)['arms'])
    for seed in run.SEEDS:
        for role in run.ROLES:
            if not (out/f'seed-{seed}'/role/'verification.json').exists():
                return unit(out,f'{seed}-{role}-verify',180,lambda counts:verify_arm(out,seed,role,counts))
    return {'verification_complete':True,'next':'finalize'}


def assemble_arm(out,seed,role):
    d=out/f'seed-{seed}'/role;start=run.load_actor(d/'start.pkl.gz')
    actors=[run.load_actor(d/f'block-{i:06d}/checkpoint.pkl.gz') for i in range(0,1920,64)]
    a=actors[-1]
    rs=[r for r in receipts(out) if r.get('payload',{}).get('seed')==seed and r.get('payload',{}).get('role')==role and r['new_execution']['training']]
    seconds=sum(r['wall_seconds'] for r in rs)
    original=read(SOURCE/f'seed-{seed}'/role/'results.json') if seed==21 and role!='learning-trial' else None
    return {'seed':seed,'role':role,'initial':read(d/'initial-evaluation.json'),
        'evaluations':[read(d/f'block-{i:06d}/evaluation.json') for i in range(0,1920,64)],
        'structures':[run.structure(x) for x in actors],'search':asdict(a.birth_search_config),
        'limits':asdict(a.ownership_limits),'candidate_pool':a.birth_definitions,'initial_structure':run.structure(start),
        'training_wall_seconds':original['training_wall_seconds'] if original else None if seed==21 else seconds,
        'new_training_worker_seconds':seconds,'timing_scope':'Reused full control time; revised21 prefix time unavailable; fresh arms sum worker time.',
        'trial_history':[dict(parent=t.parent,children=t.children,route=t.route,born=t.born,state=t.state.name,
            resolution=t.resolution,summary=a.trial_summary(t),assessment_clock=asdict(a.assessment_clocks[(t.parent,t.born)]) if isinstance(a,run.LearningTrialOwnerDevelopment) else None)
            for t in [*a.split_trial_history,*a.split_trials.values()]] if isinstance(a,run.TrialOwnerDevelopment) else [],
        'birth_nominations':a.birth_nominations,'development_history':a.development_history}


def finalize(out):
    check_sources(out);state=status(out)
    assert not state['pending_units'] and not state['failed_units']
    assert all(a['verified'] for a in state['arms'])
    assert state['new_execution_sealed_receipts']==NEW_COUNTS
    assert read(out/'retry-control/tail-comparison.json')['identical_real_reexecutions']==39
    for name,expected in read(out/'reused.json')['files'].items():
        assert run.digest((out/name).read_bytes())==run.digest((SOURCE/name).read_bytes())==expected
    tally=dict.fromkeys(run.COUNTS,0);arms=[]
    for seed in run.SEEDS:
        actors=[run.load_actor(out/f'seed-{seed}'/r/'block-001856/checkpoint.pkl.gz') for r in run.ROLES]
        assert all(a.exploration_rng.getstate()==actors[0].exploration_rng.getstate() for a in actors)
        for role in run.ROLES:
            for k,v in read(out/f'seed-{seed}'/role/'verification.json').items():tally[k]+=v
            arm=assemble_arm(out,seed,role);save(out/f'seed-{seed}'/role/'results.json',arm);arms.append(arm)
    assert tally==run.COUNTS
    result={'status':'complete','seeds':run.SEEDS,'roles':run.ROLES,'planned':run.COUNTS,'verification':tally,
        'arms':arms,'elapsed_seconds':state['worker_wall_seconds'],'elapsed_seconds_scope':'Sum of retry unit wall time only; excludes reused work and orchestration pauses.',
        'max_rss_kib':max(r['max_rss_kib'] for r in receipts(out)),
        'recovery':{'new_execution':NEW_COUNTS,'reused_training':5376,'reused_evaluation':1392,
            'known_repeated_training':39,'recorded_physical_actions_both_attempts':26247,
            'original_unrecorded_inflight_execution_unknown':True,'original_status':'incomplete'}}
    save(out/'result.json',result);status(out,write=True)
    return {k:v for k,v in result.items() if k!='arms'}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('command',choices=('init','step','verify','finalize','status'));p.add_argument('--output',required=True);args=p.parse_args()
    out=Path(args.output)
    os.sched_setaffinity(0,{min(os.sched_getaffinity(0))})
    limit=180 if args.command in ('init','verify','finalize') else 90
    resource.setrlimit(resource.RLIMIT_AS,(2*1024**3,2*1024**3));resource.setrlimit(resource.RLIMIT_FSIZE,(64*1024**2,64*1024**2));resource.setrlimit(resource.RLIMIT_CPU,(limit,limit+1))
    def expired(*_):raise TimeoutError('Bounded recovery worker deadline reached')
    signal.signal(signal.SIGALRM,expired);signal.alarm(limit)
    if args.command=='init':result=init(out)
    elif args.command=='status':result=status(out)
    else:
        with (out/'retry-control/lock').open('a') as lock:
            fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
            result=globals()[args.command](out)
    print(json.dumps(result,default=str),flush=True)


if __name__=='__main__':main()
