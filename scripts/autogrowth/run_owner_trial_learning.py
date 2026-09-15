"""Fixed three-arm comparison of learning before prospective split assessment."""
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
import run_owner_split_trial as previous_trial
from run_owner_nomination import (ROOT, BooleanEnvironment, DevelopmentConfig,
    OwnershipLimits, OwnerDevelopmentConfig, digest, write_once, json_once,
    save_actor, load_actor, evaluate, structure, ROWS, Feedback, encoded)
from recon_lite_hector.learning.fresh_owner import FreshOwnerDevelopment
from recon_lite_hector.learning.owner_trial import TrialOwnerDevelopment
from recon_lite_hector.learning.owner_trial_learning import LearningTrialOwnerDevelopment
from recon_lite_hector.learning.trial_usefulness import UseOutcome
from recon_lite_hector.learning.owner_birth_search import BirthSearchConfig

SEEDS = (21, 22, 23)
ROLES = ('current', 'trial', 'learning-trial')
PROTOCOL = ROOT/'docs/autogrowth/OWNER_TRIAL_LEARNING.md'
COUNTS = {'training':17280, 'evaluation':4464, 'verification_actions':4464,
          'blocks':270, 'checkpoints':279}


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
    cls = {'current':FreshOwnerDevelopment,'trial':TrialOwnerDevelopment,
           'learning-trial':LearningTrialOwnerDevelopment}[role]
    return cls.create(schema=BooleanEnvironment.schema,
        state_coordinates=(0,1,2,3), seed=seed,
        config=DevelopmentConfig(max_conditions=8),
        search=BirthSearchConfig(mode='residual'),
        development=OwnerDevelopmentConfig(),
        limits=OwnershipLimits(max_leaves=4,
            max_parameters=64,max_definitions=256,max_physical_nodes=2048))


def verify_initial_pair(actors):
    for right in actors[1:]: previous_trial.verify_initial_pair((actors[0],right))


def structure(actor):
    value = recording.structure(actor)
    trials = getattr(actor,'split_trials',{})
    value.update(stored_scorers=len(actor.leaves), committed_owners=len(actor.leaves)-2*len(trials),
        reserved_owners=actor._leaf_budget_count(), pending_trials=len(trials),
        committed_splits=len(actor.ownership_history),
        accepted_trials=sum(t.state.name=='MATURE' for t in getattr(actor,'split_trial_history',())),
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
        assert len(trial.outcomes) <= actor.owner_trial_config.window*(6 if isinstance(actor,LearningTrialOwnerDevelopment) else 1)
        if isinstance(actor,LearningTrialOwnerDevelopment): verify_assessment(actor,trial,seen)
    assert set(evidence) <= {(t.parent,t.born) for t in trials}
    assert actor.split_use_pending is None



def verify_assessment(actor, trial, seen):
    """Reconstruct readiness and every review from immutable real assignments."""
    from collections import Counter
    clock = actor.assessment_clocks[(trial.parent,trial.born)]
    counts = Counter(); start = None; learning = {}; started_at = None
    for index,(outcome,owner) in enumerate(seen,1):
        counts[owner] += 1
        if start is None and all(counts[o]>=actor.development_config.develop_every
                                  for o in (trial.parent,*trial.children)):
            start,started_at = index,outcome.event_id+1
            learning = {o:counts[o] for o in (trial.parent,*trial.children)}
    assert (clock.start,clock.started_at,clock.learning_counts)==(start,started_at,learning)
    cfg = actor.owner_trial_config
    reviews = []
    def expected_summary(end):
        local = seen[start:end] if start is not None else []
        groups = [[r.reward for r,_ in local if r.enabled==flag] for flag in (False,True)]
        arm_counts = list(map(len,groups))
        gain = sum(groups[1])/len(groups[1])-sum(groups[0])/len(groups[0]) if all(groups) else None
        child_counts = {c:sum(o==c for _,o in local) for c in trial.children}
        supported = min(arm_counts)>=cfg.min_arm and min(child_counts.values())>=cfg.min_child
        accepted = len(local) in (cfg.window,2*cfg.window) and supported and gain>=cfg.min_reward_gain
        return dict(assigned=end,assessment_assigned=len(local),assessment_start=start,
            assessment_started_at=started_at,learning_counts=learning,arm_counts=arm_counts,
            child_exposures={c:sum(o==c for _,o in seen[:end]) for c in trial.children},
            assessment_child_exposures=child_counts,mean_reward_gain=gain,
            supported=supported,accepted=accepted)
    if start is not None:
        for age in (cfg.window,2*cfg.window):
            end = start+age
            if end>len(seen): break
            summary = expected_summary(end)
            reviews.append(dict(summary,episode=seen[end-1][0].event_id+1))
            if summary['accepted']:
                assert end==len(seen)
                break
    assert len(clock.reviews)==len(reviews)
    for index,(actual,expected) in enumerate(zip(clock.reviews,reviews)):
        assert all(actual[k]==v for k,v in expected.items())
        assert actual['reviews_completed']==index
    final = expected_summary(len(seen))
    assert all(actor.trial_summary(trial)[k]==v for k,v in final.items())
    resolved = bool(reviews and (reviews[-1]['accepted'] or len(reviews)==2)) or len(seen)==6*cfg.window
    if resolved:
        assert trial.resolution is not None
        assert all(trial.resolution[k]==v for k,v in final.items())
        assert trial.resolution['episode']==seen[-1][0].event_id+1
        assert trial.state.name==('MATURE' if final['accepted'] else 'PRUNED')
    else:
        assert trial.resolution is None
        assert trial.state.name==('TRIAL' if start is None else 'PROBATION')


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
                    state=t.state.name,resolution=t.resolution,summary=actor.trial_summary(t),
                    assessment_clock=asdict(actor.assessment_clocks[(t.parent,t.born)]) if isinstance(actor,LearningTrialOwnerDevelopment) else None)
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
