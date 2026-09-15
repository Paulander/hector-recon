"""First fixed comparison combining owner splits with actual-use trial acceptance."""
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
import run_owner_fresh_start as fresh
from run_owner_nomination import (ROOT, BooleanEnvironment, DevelopmentConfig,
    OwnershipLimits, OwnerDevelopmentConfig, digest, write_once, json_once,
    save_actor, load_actor, evaluate, structure, ROWS, Feedback, encoded)
from recon_lite_hector.learning.fresh_owner import FreshOwnerDevelopment
from recon_lite_hector.learning.owner_trial import TrialOwnerDevelopment
from recon_lite_hector.learning.trial_usefulness import UseOutcome
from recon_lite_hector.learning.owner_birth_search import BirthSearchConfig

SEEDS = (18, 19, 20)
ROLES = ('current', 'trial')
PROTOCOL = ROOT/'docs/autogrowth/OWNER_SPLIT_TRIAL.md'
COUNTS = {'training':11520, 'evaluation':2976, 'verification_actions':2976,
          'blocks':180, 'checkpoints':186}


schedule = fresh.schedule
verify_initial = fresh.verify_initial
def verify_same_state(left, right):
    if isinstance(left, TrialOwnerDevelopment):
        assert left.split_use_rng.getstate() == right.split_use_rng.getstate()
        left, right = copy.deepcopy(left), copy.deepcopy(right)
        del left.split_use_rng, right.split_use_rng
    fresh.verify_same_state(left, right)

verify_birth_evidence = fresh.verify_birth_evidence


def create_actor(seed, role):
    if role not in ROLES:
        raise ValueError('unknown declared owner-trial arm')
    cls = FreshOwnerDevelopment if role == 'current' else TrialOwnerDevelopment
    return cls.create(schema=BooleanEnvironment.schema,
        state_coordinates=(0,1,2,3), seed=seed,
        config=DevelopmentConfig(max_conditions=8),
        search=BirthSearchConfig(mode='residual'),
        development=OwnerDevelopmentConfig(),
        limits=OwnershipLimits(max_leaves=4,
            max_parameters=64,max_definitions=256,max_physical_nodes=2048))


def verify_initial_pair(actors):
    left, right = actors
    verify_initial(left); verify_initial(right)
    for name in ('config','development_config','birth_search_config','ownership_limits',
                 'birth_definitions','owner_candidates','conditions','leaves'):
        assert getattr(left,name) == getattr(right,name), name
    for name in ('rng','proposal_rng','exploration_rng','birth_selection_rng'):
        assert getattr(left,name).getstate() == getattr(right,name).getstate(), name
    assert vars(left.graph) == vars(right.graph)


def structure(actor):
    value = recording.structure(actor)
    trials = getattr(actor,'split_trials',{})
    value.update(stored_scorers=len(actor.leaves), committed_owners=len(actor.leaves)-2*len(trials),
        reserved_owners=actor._leaf_budget_count(), pending_trials=len(trials),
        accepted_trials=len(actor.ownership_history),
        resolved_trials=len(getattr(actor,'split_trial_history',())))
    return value


def verify_trials(actor, records, evidence):
    for row in records:
        assignment = row['split_use_assignment']
        if assignment is None: continue
        event, action, parent, owner, enabled, born = assignment
        assert (event,action,owner) == (row['event'],row['action'],row['owner'])
        assert row['split_assignments'][str(parent)] == enabled
        evidence.setdefault((parent,born),[]).append((UseOutcome(event,action,enabled,enabled,row['reward']),owner))
    if not isinstance(actor,TrialOwnerDevelopment):
        assert not evidence
        return
    trials = [*actor.split_trial_history,*actor.split_trials.values()]
    for trial in trials:
        seen = evidence.get((trial.parent,trial.born),[])
        assert trial.outcomes == [r for r,_ in seen]
        assert trial.child_exposures == {c:sum(owner==c for _,owner in seen) for c in trial.children}
        assert all(r.enabled == (owner in trial.children) for r,owner in seen)
        assert len(trial.outcomes) <= actor.owner_trial_config.window
    assert set(evidence) <= {(t.parent,t.born) for t in trials}
    assert actor.split_use_pending is None



def source_hashes():
    result = fresh.source_hashes()
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
            'weights_before':[float(w) for w in weights],
            'split_use_assignment':getattr(actor,'split_use_pending',None),
            'split_assignments':dict(getattr(actor,'split_enabled',{})),
            'stored_nodes':len(actor.graph.nodes), 'stored_parameters':len(actor.conditions),
            'stored_scorers':len(actor.leaves)}
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
    recording.prior.verify_block(directory, order, start, previous)
    return restored, checkpoint, result


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
            expected_limits = actor.ownership_limits
            role_dir = directory/role
            initial = json.loads((role_dir/'initial-evaluation.json').read_text())
            assert evaluate(actor) == initial
            counts['evaluation'] += 16; counts['verification_actions'] += 16
            counts['checkpoints'] += 1
            previous = digest((role_dir/'start.pkl.gz').read_bytes())
            evidence = {}; trial_evidence = {}
            for offset in range(0, len(order), 64):
                block = role_dir/f'block-{offset:06d}'
                actor = recording.prior.verify_block(block,order[offset:offset+64],offset,previous)
                assert actor.ownership_limits == expected_limits
                previous = digest((block/'checkpoint.pkl.gz').read_bytes())
                records = [json.loads(line) for line in (block/'training.jsonl').read_text().splitlines()]
                verify_birth_evidence(actor, records, evidence)
                verify_trials(actor, records, trial_evidence)
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
                    'limits':asdict(actor.ownership_limits),
                    'candidate_pool':actor.birth_definitions,'initial_structure':structure(actor)}
                report['arms'].append(arm)
                arm_started = time.monotonic()
                for offset in range(0,len(order),64):
                    block = role_dir/f'block-{offset:06d}'
                    actor,previous,result = train_block(actor,order[offset:offset+64],block,previous)
                    arm['evaluations'].append(result); arm['structures'].append(structure(actor))
                    print(json.dumps({'seed':seed,'role':role,'event':actor.completed,
                        'correct':result['correct'],'nodes':len(actor.graph.nodes),'owners':len(actor.leaves),
                        'nominations':len(actor.birth_nominations),
                        'elapsed_seconds':round(time.monotonic()-started,2)}),flush=True)
                arm['training_wall_seconds'] = time.monotonic()-arm_started
                arm['trial_history'] = [dict(parent=t.parent,children=t.children,route=t.route,born=t.born,
                    state=t.state.name,resolution=t.resolution,summary=actor.trial_summary(t))
                    for t in [*actor.split_trial_history,*actor.split_trials.values()]] if isinstance(actor,TrialOwnerDevelopment) else []
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
