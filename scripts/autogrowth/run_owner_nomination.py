"""Fixed, bounded owner-nomination pilot with immutable journals; no retry path."""
import argparse
from dataclasses import asdict, replace
import json
import math
import os
from pathlib import Path
import random
import resource
import signal
import sys
import time

from run_recursive_retention import (
    BooleanEnvironment, ROWS, ROOT, RecursiveDevelopment, RecursiveConfig,
    DevelopmentConfig, Feedback, digest, encoded, write_once, json_once,
    save_actor, load_actor, evaluate,
)
from recon_lite_hector.learning.context_decision import OwnershipLimits
from recon_lite_hector.learning.owner_development import AdaptiveOwnerDevelopment, OwnerDevelopmentConfig

SEEDS = (10, 11)
ROLES = ("unsplit", "adaptive")


def schedule(seed):
    rng = random.Random(f"owner-nomination:{seed}")
    a = [i for i, row in enumerate(ROWS) if not row[2]]
    b = [i for i, row in enumerate(ROWS) if row[2]]
    prefix = a * 16
    rng.shuffle(prefix)
    continuation = []
    for block in range(4):
        unit = a + b * 7 if block < 2 else a * 7 + b
        rng.shuffle(unit)
        continuation.extend(unit)
    return prefix, continuation


def structure(actor):
    adaptive = isinstance(actor, AdaptiveOwnerDevelopment)
    return {
        "owners": len(actor.leaves) if adaptive else 1,
        "effective_parameters": len(actor.conditions) if adaptive else len(actor.conditions) + 1,
        "physical_nodes": len(actor.graph.nodes), "expression_definitions": len(actor.expression_ids),
        "depth": max((actor.expressions[cid].depth for cid in actor.conditions), default=0),
        "splits": len(actor.ownership_history) if adaptive else len(actor.splits),
        "pruned": actor.pruned,
        "births_after_conversion": sum(e['birth'] is not None for e in actor.development_history) if adaptive else 0,
        "owner_visits": dict(actor.owner_visits) if adaptive else {},
        "exploration_rng_digest": digest(repr(actor.exploration_rng.getstate()).encode()),
    }


def verify_conversion(source, actor):
    assert actor.completed == source.completed and len(actor.leaves) == 1
    leaf = actor.leaves[0]
    assert actor.conditions[leaf.bias_id].weight == source.bias
    for cid, condition in source.conditions.items():
        assert actor.conditions[cid] == condition
        assert actor.base_expressions[cid] == source.expressions[cid]
    assert set(leaf.contributions) == set(source.conditions) | {leaf.bias_id}
    actor.validate_ownership()


def verify_pair(left, right):
    assert left.development_config == replace(right.development_config, split_enabled=False)
    excluded = {'development_config', 'graph', 'rng', 'proposal_rng', 'exploration_rng'}
    assert vars(left).keys() == vars(right).keys()
    for name in vars(left).keys() - excluded:
        assert getattr(left, name) == getattr(right, name), name
    for name in ('rng', 'proposal_rng', 'exploration_rng'):
        assert getattr(left, name).getstate() == getattr(right, name).getstate()
    assert vars(left.graph) == vars(right.graph)


def train_block(actor, order, directory, previous, *, do_evaluate):
    start = actor.completed
    directory.mkdir()
    json_once(directory/'intent.json', {'start': start, 'stop': start+len(order),
              'order': list(order), 'previous': previous, 'evaluate': do_evaluate})
    records = []
    with (directory/'progress.jsonl').open('xb') as stream, (directory/'submissions.jsonl').open('xb') as submitted:
        for row in order:
            event = actor.completed
            env = BooleanEnvironment(ROWS[row])
            action = actor.act(env, event_id=event, learn=True)
            reward = env.outcome()
            _, _, prediction, active = actor.pending[-1]
            weights = [actor.conditions[cid].weight for cid in active]
            adaptive = isinstance(actor, AdaptiveOwnerDevelopment)
            pending = actor.candidate_pending if adaptive else None
            record = {'event': event, 'row': row, 'action': action, 'reward': reward,
                      'prediction': prediction, 'active': active,
                      'denominator': len(active) if adaptive else 1+len(active),
                      'owner': pending[2] if pending else None,
                      'candidate_values': pending[4] if pending else None,
                      'weights_before': [float(w) for w in weights]}
            submitted.write(encoded(record)); submitted.flush(); os.fsync(submitted.fileno())
            actor.observe(Feedback(event, action, reward))
            record['weights_after'] = [float(w) for w in weights]
            records.append(encoded(record))
            stream.write(records[-1]); stream.flush(); os.fsync(stream.fileno())
    write_once(directory/'training.jsonl', b''.join(records))
    checkpoint_hash = save_actor(actor, directory/'checkpoint.pkl.gz')
    restored = load_actor(directory/'checkpoint.pkl.gz')
    if isinstance(restored, AdaptiveOwnerDevelopment):
        restored.validate_ownership()
    result = evaluate(restored) if do_evaluate else None
    if result is not None:
        json_once(directory/'evaluation.json', result)
    json_once(directory/'complete.json', {'start':start, 'stop':restored.completed,
              'files':{p.name:digest(p.read_bytes()) for p in directory.iterdir() if p.is_file()}})
    verify_block(directory, order, start, previous)
    return restored, checkpoint_hash, result


def verify_block(directory, order, start, previous):
    manifest = json.loads((directory/'complete.json').read_text())
    for name, expected in manifest['files'].items():
        assert digest((directory/name).read_bytes()) == expected
    intent = json.loads((directory/'intent.json').read_text())
    assert intent == {'start': start, 'stop': start+len(order), 'order': list(order),
                      'previous': previous, 'evaluate': intent['evaluate']}
    assert manifest['start'] == start and manifest['stop'] == start+len(order)
    assert (directory/'training.jsonl').read_bytes() == (directory/'progress.jsonl').read_bytes()
    rows = [json.loads(line) for line in (directory/'training.jsonl').read_text().splitlines()]
    submissions = [json.loads(line) for line in (directory/'submissions.jsonl').read_text().splitlines()]
    assert len(rows) == len(order)
    assert submissions == [{k:v for k,v in record.items() if k!='weights_after'} for record in rows]
    for event, row, record in zip(range(start, start+len(order)), order, rows):
        assert (record['event'], record['row']) == (event, row)
        x,y,z,_ = ROWS[row]
        assert record['action'] in ('act-a','act-b')
        assert record['reward'] == (1 if (record['action']=='act-b') == (y if z else x) else -1)
        expected_n = len(record['active']) + int(record['owner'] is None)
        assert record['denominator'] == expected_n and expected_n > 0
        assert len(record['weights_before']) == len(record['weights_after']) == len(record['active'])
        delta = .3*(record['reward']-record['prediction'])/expected_n
        assert all(math.isclose(after-before, delta, abs_tol=2e-12)
                   for before,after in zip(record['weights_before'],record['weights_after']))
    actor = load_actor(directory/'checkpoint.pkl.gz')
    assert actor.completed == start+len(order)
    if isinstance(actor, AdaptiveOwnerDevelopment):
        actor.validate_ownership()
        assert actor.candidate_pending is None and actor.owner_pending is None
    return actor


def sources():
    paths={Path(__file__).resolve(), ROOT/'docs/autogrowth/OWNER_NOMINATION_PILOT.md',
           ROOT/'scripts/autogrowth/guard_recursive_budget.py'}
    paths.update(Path(m.__file__).resolve() for m in tuple(sys.modules.values())
                 if getattr(m,'__file__',None) and Path(m.__file__).resolve().is_relative_to(ROOT)
                 and Path(m.__file__).suffix=='.py')
    return {p.relative_to(ROOT).as_posix():digest(p.read_bytes()) for p in sorted(paths)}


def verify_run(out):
    source=json.loads((out/'source.json').read_text())
    for name, expected in source.items():
        assert digest((ROOT/name).read_bytes()) == digest((out/'source-snapshot'/name).read_bytes()) == expected
    counts={'training':0,'evaluation':0,'verification_actions':0,'blocks':0,'checkpoints':0}
    for seed in SEEDS:
        prefix, continuation=schedule(seed)
        directory=out/f'seed-{seed}'
        assert json.loads((directory/'schedule.json').read_text())=={'prefix':prefix,'continuation':continuation}
        for role in ('prefix',*ROLES):
            role_dir=directory/role
            start=load_actor(role_dir/'start.pkl.gz')
            previous=digest((role_dir/'start.pkl.gz').read_bytes())
            counts['checkpoints']+=1
            order=prefix if role=='prefix' else continuation
            start_event=start.completed
            for offset in range(0,len(order),64):
                block=role_dir/f'block-{start_event+offset:06d}'
                actor=verify_block(block,order[offset:offset+64],start_event+offset,previous)
                previous=digest((block/'checkpoint.pkl.gz').read_bytes())
                counts['training']+=64; counts['blocks']+=1; counts['checkpoints']+=1
                path=block/'evaluation.json'
                if path.exists():
                    assert evaluate(actor)==json.loads(path.read_text())
                    counts['evaluation']+=16; counts['verification_actions']+=16
    assert counts=={'training':1280,'evaluation':288,'verification_actions':288,'blocks':20,'checkpoints':26}
    return counts


def run(output):
    out=Path(output); out.mkdir(parents=True,exist_ok=False)
    os.sched_setaffinity(0,{min(os.sched_getaffinity(0))})
    resource.setrlimit(resource.RLIMIT_AS,(2*1024**3,2*1024**3))
    resource.setrlimit(resource.RLIMIT_FSIZE,(64*1024**2,64*1024**2))
    resource.setrlimit(resource.RLIMIT_CPU,(540,545))
    def expired(_signal,_frame):
        raise TimeoutError('fixed 540-second pilot limit reached')
    signal.signal(signal.SIGALRM,expired); signal.alarm(540)
    started=time.monotonic()
    report={'status':'running','seeds':SEEDS,'roles':ROLES,'arms':[],
            'planned_training':1280,'planned_evaluation':288,'planned_verification_actions':288}
    source=sources(); json_once(out/'source.json',source)
    for name in source:
        path=out/'source-snapshot'/name; path.parent.mkdir(parents=True,exist_ok=True)
        write_once(path,(ROOT/name).read_bytes())
    json_once(out/'intent.json',report)
    try:
        for seed in SEEDS:
            directory=out/f'seed-{seed}'; directory.mkdir()
            prefix,continuation=schedule(seed)
            json_once(directory/'schedule.json',{'prefix':prefix,'continuation':continuation})
            source_actor=RecursiveDevelopment(seed=seed,config=DevelopmentConfig(max_conditions=8),
                            recursive_config=RecursiveConfig(role='flat',prefix=128))
            prefix_dir=directory/'prefix'; prefix_dir.mkdir()
            previous=save_actor(source_actor,prefix_dir/'start.pkl.gz')
            for offset in (0,64):
                source_actor,previous,initial=train_block(source_actor,prefix[offset:offset+64],
                    prefix_dir/f'block-{offset:06d}',previous,do_evaluate=offset==64)
            actors={role:AdaptiveOwnerDevelopment.from_actor(source_actor,state_coordinates=(0,1,2,3),
                    limits=OwnershipLimits(max_parameters=64,max_definitions=256,max_physical_nodes=2048),
                    development=OwnerDevelopmentConfig(split_enabled=role=='adaptive')) for role in ROLES}
            for actor in actors.values(): verify_conversion(source_actor,actor)
            verify_pair(actors['unsplit'],actors['adaptive'])
            pair=[]
            for role,actor in actors.items():
                role_dir=directory/role; role_dir.mkdir()
                previous=save_actor(actor,role_dir/'start.pkl.gz')
                arm={'seed':seed,'role':role,'initial':initial,'evaluations':[],
                     'structures':[],'limits':asdict(actor.ownership_limits),
                     'development_config':asdict(actor.development_config)}
                report['arms'].append(arm)
                for offset in range(0,256,64):
                    actor,previous,result=train_block(actor,continuation[offset:offset+64],
                        role_dir/f'block-{128+offset:06d}',previous,do_evaluate=True)
                    arm['evaluations'].append(result); arm['structures'].append(structure(actor))
                    print(json.dumps({'seed':seed,'role':role,'event':actor.completed,
                          'correct':result['correct'],'owners':len(actor.leaves),
                          'elapsed_seconds':round(time.monotonic()-started,2)}),flush=True)
                arm['development_history']=actor.development_history
                json_once(role_dir/'results.json',arm)
                pair.append(structure(actor)['exploration_rng_digest'])
            assert len(set(pair))==1
        report['verification']=verify_run(out)
        report['status']='complete'
    except BaseException as error:
        report.update(status='incomplete',error=f'{type(error).__name__}: {error}')
        raise
    finally:
        signal.alarm(0)
        report['elapsed_seconds']=time.monotonic()-started
        report['max_rss_kib']=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        json_once(out/'result.json',report)
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',required=True)
    run(parser.parse_args().output)
