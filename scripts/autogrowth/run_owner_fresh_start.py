"""Fixed fresh-from-zero comparison; immutable journals and no retry path."""
import argparse
import copy
from dataclasses import asdict, replace
import json
import os
from pathlib import Path
import pickle
import resource
import signal
import time

import run_owner_birth_search as recording
from run_owner_nomination import (ROOT, BooleanEnvironment, DevelopmentConfig,
    OwnershipLimits, OwnerDevelopmentConfig, digest, write_once, json_once,
    save_actor, load_actor, evaluate, structure)
from recon_lite_hector.learning.fresh_owner import FreshOwnerDevelopment
from recon_lite_hector.learning.owner_birth_search import BirthSearchConfig

SEEDS = (12, 13, 14)
ROLES = ('random-current', 'residual-current')
PROTOCOL = ROOT/'docs/autogrowth/OWNER_FRESH_START.md'
COUNTS = {'training':11520, 'evaluation':2976, 'verification_actions':2976,
          'blocks':180, 'checkpoints':186}


def schedule(seed):
    prefix, continuation = recording.prior.schedule(seed)
    return prefix + continuation


def create_actor(seed, role):
    if role not in ROLES:
        raise ValueError('unknown declared fresh-start arm')
    return FreshOwnerDevelopment.create(schema=BooleanEnvironment.schema,
        state_coordinates=(0,1,2,3), seed=seed,
        config=DevelopmentConfig(max_conditions=8),
        search=BirthSearchConfig(mode=role.split('-')[0]),
        development=OwnerDevelopmentConfig(),
        limits=OwnershipLimits(max_parameters=64,max_definitions=256,max_physical_nodes=2048))


def verify_initial(actor):
    assert actor.completed == actor.converted_at == 0 and actor.last_event == -1
    assert len(actor.leaves) == len(actor.conditions) == actor.slots == 1
    assert actor.graph.nodes['option:0'].meta['actuator_identity'] == 'unbound'
    assert float(actor.bias) == 0
    bias = actor.conditions[actor.leaves[0].bias_id]
    assert bias.weight.fast == bias.weight.slow == 0 and bias.born == 0
    assert actor.owner_visits == {0:0} and actor.owner_evidence == {0:{}}
    assert not actor.development_history and not actor.birth_nominations
    assert all(e.n0 == e.n1 == e.sum0 == e.sum1 == 0 for e in actor.birth_evidence[0])
    assert not actor.pending and actor.owner_pending is actor.candidate_pending is None
    assert actor.birth_search_pending is None
    actor.validate_ownership()


def verify_initial_pair(actors):
    normalized = []
    for actor in actors:
        verify_initial(actor)
        clone = copy.deepcopy(actor)
        clone.birth_search_config = replace(clone.birth_search_config, mode='random')
        normalized.append(clone)
    for actor in normalized[1:]:
        verify_same_state(actor, normalized[0])


def verify_same_state(left, right):
    # Pickle bytes can change string/reference sharing after restoration even
    # when every value and graph edge is identical. Compare complete state.
    assert type(left) is type(right) and vars(left).keys() == vars(right).keys()
    rngs = ('rng','proposal_rng','exploration_rng','birth_selection_rng')
    for name in vars(left).keys()-{'graph',*rngs}:
        assert getattr(left,name) == getattr(right,name), name
    for name in rngs:
        assert getattr(left,name).getstate() == getattr(right,name).getstate(), name
    assert vars(left.graph) == vars(right.graph)


def source_hashes():
    result = recording.source_hashes()
    for path in (Path(__file__).resolve(), PROTOCOL):
        result[path.relative_to(ROOT).as_posix()] = digest(path.read_bytes())
    return result


def verify_birth_evidence(actor, records, evidence):
    for row in records:
        owner = row['owner']
        flags = row['birth_candidate_values']
        assert len(flags) == len(actor.birth_definitions) and all(type(f) is bool for f in flags)
        values = evidence.setdefault(owner, [[0,0,0.0,0.0] for _ in flags])
        for item, active in zip(values, flags):
            item[int(active)] += 1
            item[2+int(active)] += row['reward']-row['prediction']
    for owner, observations in actor.birth_evidence.items():
        expected = evidence.get(owner, [[0,0,0.0,0.0] for _ in observations])
        assert [[e.n0,e.n1,e.sum0,e.sum1] for e in observations] == expected
    assert set(evidence) <= actor.birth_evidence.keys()


def verify_run(out):
    for name, expected in json.loads((out/'source.json').read_text()).items():
        assert digest((ROOT/name).read_bytes()) == digest((out/'source-snapshot'/name).read_bytes()) == expected
    counts = dict.fromkeys(COUNTS, 0)
    for seed in SEEDS:
        directory = out/f'seed-{seed}'
        order = schedule(seed)
        assert json.loads((directory/'schedule.json').read_text()) == order
        starts = [load_actor(directory/role/'start.pkl.gz') for role in ROLES]
        verify_initial_pair(starts)
        final_rngs = []
        for role, actor in zip(ROLES, starts):
            verify_same_state(actor,create_actor(seed,role))
            role_dir = directory/role
            initial = json.loads((role_dir/'initial-evaluation.json').read_text())
            assert evaluate(actor) == initial
            counts['evaluation'] += 16; counts['verification_actions'] += 16
            counts['checkpoints'] += 1
            previous = digest((role_dir/'start.pkl.gz').read_bytes())
            evidence = {}
            for offset in range(0, len(order), 64):
                block = role_dir/f'block-{offset:06d}'
                actor = recording.prior.verify_block(block,order[offset:offset+64],offset,previous)
                previous = digest((block/'checkpoint.pkl.gz').read_bytes())
                records = [json.loads(line) for line in (block/'training.jsonl').read_text().splitlines()]
                verify_birth_evidence(actor, records, evidence)
                assert evaluate(actor) == json.loads((block/'evaluation.json').read_text())
                counts['training'] += 64; counts['evaluation'] += 16
                counts['verification_actions'] += 16; counts['blocks'] += 1
                counts['checkpoints'] += 1
            final_rngs.append(actor.exploration_rng.getstate())
        assert all(state == final_rngs[0] for state in final_rngs)
    assert counts == COUNTS, counts
    return counts


def run(output):
    out = Path(output); out.mkdir(parents=True,exist_ok=False)
    os.sched_setaffinity(0,{min(os.sched_getaffinity(0))})
    resource.setrlimit(resource.RLIMIT_AS,(2*1024**3,2*1024**3))
    resource.setrlimit(resource.RLIMIT_FSIZE,(64*1024**2,64*1024**2))
    resource.setrlimit(resource.RLIMIT_CPU,(3600,3605))
    def expired(_signal,_frame): raise TimeoutError('fixed 3600-second worker limit reached')
    signal.signal(signal.SIGALRM,expired); signal.alarm(3600)
    started = time.monotonic()
    report = {'status':'running','seeds':SEEDS,'roles':ROLES,'planned':COUNTS,
              'source_payloads':0,'initialization':'zero-training owner','arms':[]}
    try:
        hashes = source_hashes(); json_once(out/'source.json',hashes)
        for name in hashes:
            path = out/'source-snapshot'/name; path.parent.mkdir(parents=True,exist_ok=True)
            write_once(path,(ROOT/name).read_bytes())
        json_once(out/'intent.json',report)
        for seed in SEEDS:
            directory = out/f'seed-{seed}'; directory.mkdir()
            order = schedule(seed); json_once(directory/'schedule.json',order)
            actors = [create_actor(seed,role) for role in ROLES]
            verify_initial_pair(actors)
            final_rngs = []
            for role, actor in zip(ROLES,actors):
                role_dir = directory/role; role_dir.mkdir()
                previous = save_actor(actor,role_dir/'start.pkl.gz')
                initial = evaluate(actor); json_once(role_dir/'initial-evaluation.json',initial)
                arm = {'seed':seed,'role':role,'initial':initial,'evaluations':[],
                    'structures':[],'search':asdict(actor.birth_search_config),
                    'candidate_pool':actor.birth_definitions,'initial_structure':structure(actor)}
                report['arms'].append(arm)
                for offset in range(0,len(order),64):
                    block = role_dir/f'block-{offset:06d}'
                    actor,previous,result = recording.train_block(actor,order[offset:offset+64],block,previous)
                    arm['evaluations'].append(result); arm['structures'].append(structure(actor))
                    print(json.dumps({'seed':seed,'role':role,'event':actor.completed,
                        'correct':result['correct'],'nodes':len(actor.graph.nodes),
                        'nominations':len(actor.birth_nominations),
                        'elapsed_seconds':round(time.monotonic()-started,2)}),flush=True)
                arm['birth_nominations'] = actor.birth_nominations
                arm['development_history'] = actor.development_history
                json_once(role_dir/'results.json',arm)
                final_rngs.append(actor.exploration_rng.getstate())
            assert all(state == final_rngs[0] for state in final_rngs)
        report['verification'] = verify_run(out)
        report['status'] = 'complete'
    except BaseException as error:
        report.update(status='incomplete',error=f'{type(error).__name__}: {error}')
        raise
    finally:
        signal.alarm(0)
        report['elapsed_seconds'] = time.monotonic()-started
        report['max_rss_kib'] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        json_once(out/'result.json',report)
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',required=True)
    run(parser.parse_args().output)
