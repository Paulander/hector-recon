"""Predeclared 2x2 birth selection/scheduling pilot; no retry or extension."""
import argparse
from dataclasses import asdict
import json
import os
from pathlib import Path
import resource
import signal
import time

import run_owner_nomination_fivefold as prior
from run_owner_nomination import (ROOT, ROWS, SEEDS, BooleanEnvironment, Feedback,
    OwnershipLimits, OwnerDevelopmentConfig, encoded, digest, write_once, json_once,
    save_actor, load_actor, evaluate, structure, verify_conversion)
from recon_lite_hector.learning.owner_birth_search import BirthSearchConfig, BirthSearchOwnerDevelopment

SOURCE = ROOT/'snapshots/autogrowth/owner-nomination-fivefold-20260914'
PROTOCOL = ROOT/'docs/autogrowth/OWNER_BIRTH_SEARCH.md'
ROLES = ('random-current', 'residual-current', 'random-extra', 'residual-extra')
COUNTS = {'training': 10240, 'evaluation': 2560, 'verification_actions': 2560,
          'blocks': 160, 'checkpoints': 168}


def source_hashes():
    result = prior.source_hashes()
    for path in (Path(__file__).resolve(), PROTOCOL):
        result[path.relative_to(ROOT).as_posix()] = digest(path.read_bytes())
    return result


def train_block(actor, order, directory, previous):
    start = actor.completed
    directory.mkdir()
    (directory/'submitted').mkdir(); (directory/'credited').mkdir()
    json_once(directory/'intent.json', {'start':start, 'stop':start+len(order),
        'order':list(order), 'previous':previous, 'evaluate':True})
    records = []
    for row in order:
        event = actor.completed
        env = BooleanEnvironment(ROWS[row])
        action = actor.act(env, event_id=event, learn=True)
        reward = env.outcome()
        _, _, prediction, active = actor.pending[-1]
        weights = [actor.conditions[cid].weight for cid in active]
        pending = actor.candidate_pending
        record = {'event':event, 'row':row, 'action':action, 'reward':reward,
            'prediction':prediction, 'active':active, 'denominator':len(active),
            'owner':pending[2], 'candidate_values':pending[4],
            'birth_candidate_values':actor.birth_search_pending[4],
            'weights_before':[float(w) for w in weights]}
        json_once(directory/'submitted'/f'{event:06d}.json', record)
        actor.observe(Feedback(event, action, reward))
        record['weights_after'] = [float(w) for w in weights]
        data = encoded(record)
        write_once(directory/'credited'/f'{event:06d}.json', data)
        records.append(data)
    write_once(directory/'training.jsonl', b''.join(records))
    checkpoint = save_actor(actor, directory/'checkpoint.pkl.gz')
    restored = load_actor(directory/'checkpoint.pkl.gz')
    restored.validate_ownership()
    result = evaluate(restored)
    json_once(directory/'evaluation.json', result)
    json_once(directory/'complete.json', {'start':start, 'stop':restored.completed,
        'files':{p.relative_to(directory).as_posix():digest(p.read_bytes())
            for p in sorted(directory.rglob('*')) if p.is_file()}})
    prior.verify_block(directory, order, start, previous)
    return restored, checkpoint, result


def verify_run(out):
    for name, expected in json.loads((out/'source.json').read_text()).items():
        assert digest((ROOT/name).read_bytes()) == digest((out/'source-snapshot'/name).read_bytes()) == expected
    counts = dict.fromkeys(COUNTS, 0)
    for seed in SEEDS:
        directory = out/f'seed-{seed}'
        _, order = prior.schedule(seed)
        assert json.loads((directory/'schedule.json').read_text()) == order
        expected = json.loads((directory/'source-checkpoint.json').read_text())['sha256']
        assert digest((directory/'source.pkl.gz').read_bytes()) == expected
        for role in ROLES:
            role_dir = directory/role
            actor = load_actor(role_dir/'start.pkl.gz')
            assert actor.completed == 640 and actor.birth_search_pending is None
            previous = digest((role_dir/'start.pkl.gz').read_bytes())
            counts['checkpoints'] += 1
            # Independently reconstruct all local birth residual statistics from
            # immutable actual records; parent histories remain available.
            evidence = {}
            for offset in range(0, 1280, 64):
                block = role_dir/f'block-{640+offset:06d}'
                actor = prior.verify_block(block, order[offset:offset+64], 640+offset, previous)
                previous = digest((block/'checkpoint.pkl.gz').read_bytes())
                for line in (block/'training.jsonl').read_text().splitlines():
                    row = json.loads(line)
                    owner = row['owner']
                    if owner not in evidence:
                        evidence[owner] = [[0,0,0.0,0.0] for _ in actor.birth_definitions]
                    for values, active in zip(evidence[owner], row['birth_candidate_values']):
                        values[int(active)] += 1
                        values[2+int(active)] += row['reward']-row['prediction']
                for owner, observed in evidence.items():
                    assert [[e.n0,e.n1,e.sum0,e.sum1] for e in actor.birth_evidence[owner]] == observed
                assert evaluate(actor) == json.loads((block/'evaluation.json').read_text())
                counts['training'] += 64; counts['evaluation'] += 16
                counts['verification_actions'] += 16; counts['blocks'] += 1
                counts['checkpoints'] += 1
    assert counts == COUNTS, counts
    return counts


def run(output):
    out = Path(output); out.mkdir(parents=True, exist_ok=False)
    os.sched_setaffinity(0, {min(os.sched_getaffinity(0))})
    resource.setrlimit(resource.RLIMIT_AS, (2*1024**3, 2*1024**3))
    resource.setrlimit(resource.RLIMIT_FSIZE, (64*1024**2, 64*1024**2))
    resource.setrlimit(resource.RLIMIT_CPU, (3600, 3605))
    def expired(_signal, _frame): raise TimeoutError('fixed 3600-second worker limit reached')
    signal.signal(signal.SIGALRM, expired); signal.alarm(3600)
    started = time.monotonic()
    report = {'status':'running', 'seeds':SEEDS, 'roles':ROLES, 'planned':COUNTS,
              'source_payloads':2, 'arms':[]}
    try:
        json_once(out/'unchanged-original-learner.json', prior.verify_unchanged_learner())
        hashes = source_hashes(); json_once(out/'source.json', hashes)
        for name in hashes:
            path=out/'source-snapshot'/name; path.parent.mkdir(parents=True, exist_ok=True)
            write_once(path, (ROOT/name).read_bytes())
        json_once(out/'intent.json', report)
        for seed in SEEDS:
            directory=out/f'seed-{seed}'; directory.mkdir()
            _, order = prior.schedule(seed); json_once(directory/'schedule.json', order)
            source_block=SOURCE/f'seed-{seed}/prefix/block-000576'
            expected=json.loads((source_block/'complete.json').read_text())['files']['checkpoint.pkl.gz']
            payload=(source_block/'checkpoint.pkl.gz').read_bytes(); assert digest(payload)==expected
            write_once(directory/'source.pkl.gz',payload)
            json_once(directory/'source-checkpoint.json',{'sha256':expected,
                'path':source_block.relative_to(ROOT).as_posix(),'completed':640})
            source=load_actor(directory/'source.pkl.gz')
            initial=json.loads((source_block/'evaluation.json').read_text())
            rng_states=[]; pool=None
            for role in ROLES:
                mode, schedule=role.split('-')
                actor=BirthSearchOwnerDevelopment.from_actor(source, state_coordinates=(0,1,2,3),
                    search_seed=seed, search=BirthSearchConfig(mode=mode,extra_after_split=schedule=='extra'),
                    development=OwnerDevelopmentConfig(),
                    limits=OwnershipLimits(max_parameters=64,max_definitions=256,max_physical_nodes=2048))
                verify_conversion(source,actor)
                if pool is None: pool=actor.birth_definitions
                assert actor.birth_definitions==pool
                role_dir=directory/role; role_dir.mkdir()
                previous=save_actor(actor,role_dir/'start.pkl.gz')
                arm={'seed':seed,'role':role,'initial':initial,'evaluations':[],
                    'structures':[], 'search':asdict(actor.birth_search_config),
                    'candidate_pool':actor.birth_definitions,'initial_structure':structure(actor)}
                report['arms'].append(arm)
                for offset in range(0,1280,64):
                    block=role_dir/f'block-{640+offset:06d}'
                    actor,previous,result=train_block(actor,order[offset:offset+64],block,previous)
                    arm['evaluations'].append(result); arm['structures'].append(structure(actor))
                    print(json.dumps({'seed':seed,'role':role,'event':actor.completed,
                        'correct':result['correct'],'nodes':len(actor.graph.nodes),
                        'nominations':len(actor.birth_nominations),
                        'elapsed_seconds':round(time.monotonic()-started,2)}),flush=True)
                arm['birth_nominations']=actor.birth_nominations
                arm['development_history']=actor.development_history
                json_once(role_dir/'results.json',arm)
                rng_states.append(actor.exploration_rng.getstate())
            assert all(s==rng_states[0] for s in rng_states)
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


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',required=True)
    run(parser.parse_args().output)
