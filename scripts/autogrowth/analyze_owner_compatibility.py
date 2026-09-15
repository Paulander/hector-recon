"""Read-only comparison of saved compatibility trajectories; no environment actions."""
import argparse
from collections import Counter
import json
from pathlib import Path
import signal

from run_owner_compatibility import SEEDS, ROLES, load_actor, json_once, digest
from run_recursive_retention import ROWS
from run_owner_nomination import structure
from analyze_owner_fivefold import solved
from attribute_recursive_retention import value


def records(path):
    return [json.loads(line) for block in sorted(path.glob('block-*/training.jsonl'))
            for line in block.read_text().splitlines()]


def analyze(directory):
    raw = json.loads((directory/'result.json').read_text())
    assert raw['status']=='complete'
    answer = {'status':'complete', 'verification':raw['verification'],
              'elapsed_seconds':raw['elapsed_seconds'], 'max_rss_kib':raw['max_rss_kib'],
              'historical_control_reproduction':raw['historical_control_reproduction'],
              'method':'Offline immutable expressions and actual journals only; no new actions or fitted weights',
              'arms':[], 'pairs':[]}
    saved = {}
    for arm in raw['arms']:
        seed, role = arm['seed'], arm['role']
        path = directory/f'seed-{seed}'/role
        final = load_actor(path/'block-001856/checkpoint.pkl.gz')
        log = records(path)
        assert len(log)==1280
        saved[seed,role]=(arm,final,log)
        initial = solved(arm['initial'])
        previous = initial
        losses, gains = [], []
        for evaluation in arm['evaluations']:
            current = solved(evaluation)
            losses.extend({'episode':evaluation['episode'], 'row':row} for row in sorted(previous-current))
            gains.extend({'episode':evaluation['episode'], 'row':row} for row in sorted(current-previous))
            previous = current
        births = []
        for proposal in final.birth_proposals:
            if proposal['proposal'] is None: continue
            reachable = [row for row in range(16) if any(
                value(proposal['path'],row,action) and value(proposal['proposal'],row,action)
                for action in (0,1))]
            if proposal['outcome']=='contradiction': assert not reachable
            if proposal['outcome']=='born':
                cid = proposal['birth']
                births.append({'episode':proposal['episode'], 'owner':proposal['owner'], 'id':cid,
                    'expression':repr(proposal['proposal']), 'path':repr(proposal['path']),
                    'reachable_rows':reachable, 'survives':cid in final.conditions,
                    'credited_visits':sum(cid in record['active'] for record in log),
                    'action_distinguishing_rows':[row for row in range(16) if value(proposal['path'],row,0)
                        and value(proposal['proposal'],row,0)!=value(proposal['proposal'],row,1)]})
        counts = Counter(p['outcome'] for p in final.birth_proposals)
        boundary = solved(arm['evaluations'][9])
        b_rows={row for row in range(16) if ROWS[row][2]}
        answer['arms'].append({'seed':seed, 'role':role, 'initial_score':arm['initial']['correct'],
            'boundary_score':arm['evaluations'][9]['correct'],
            'final_score':arm['evaluations'][-1]['correct'],
            'final_context_correct':arm['evaluations'][-1]['context_correct'],
            'final_structure':structure(final), 'final_solved_rows':sorted(previous),
            'row_losses':losses, 'row_gains':gains,
            'prefix_successes_lost_final':sorted(initial-previous),
            'boundary_b_successes_lost_final':sorted((boundary&b_rows)-previous),
            'proposal_outcomes':dict(counts),
            'proposal_draws':sum(p['proposal'] is not None for p in final.birth_proposals),
            'check_verdicts':dict(Counter(p['verdict']['status'] for p in final.birth_proposals if 'verdict' in p)),
            'cache_hits':sum(p.get('cached',False) for p in final.birth_proposals),
            'cached_rejections':len(final.rejection_cache),
            'check_seconds':sum(p.get('check_seconds',0) for p in final.birth_proposals),
            'check_assignments':sum(p.get('verdict',{}).get('assignments',0) for p in final.birth_proposals),
            'check_operations':sum(p.get('verdict',{}).get('operations',0) for p in final.birth_proposals),
            'dead_births':sum(not b['reachable_rows'] for b in births),
            'zero_credit_births':sum(b['credited_visits']==0 for b in births),
            'births':births, 'rejected_proposals':[p for p in final.birth_proposals if p['outcome']=='contradiction'],
            'block_seconds':arm['block_seconds'],
            'training_and_scheduled_evaluation_seconds':sum(arm['block_seconds']),
            'development_opportunities':len(final.development_history)})
    for seed in SEEDS:
        left, a, la = saved[seed,'control']
        right, b, lb = saved[seed,'compatible']
        fields = ('event','row','action','reward','prediction','owner','candidate_values',
                  'denominator','weights_before','weights_after')
        # Compare semantics when skipped births change storage IDs.
        same_credit = all(tuple(x[k] for k in fields)==tuple(y[k] for k in fields)
                         and [a.expressions[cid] for cid in x['active']]==[b.expressions[cid] for cid in y['active']]
                         for x,y in zip(la,lb))
        proposal_fields=('episode','owner','path','local_visit','proposal')
        signatures=lambda actor:[tuple(p[k] for k in proposal_fields) for p in actor.birth_proposals]
        answer['pairs'].append({'seed':seed, 'same_training_actions_rewards':all(
            (x['action'],x['reward'])==(y['action'],y['reward']) for x,y in zip(la,lb)),
            'same_prediction_active_expression_and_credit_trajectory':same_credit,
            'same_evaluations':left['evaluations']==right['evaluations'],
            'same_proposal_sequence':signatures(a)==signatures(b),
            'same_proposal_rng_end':a.proposal_rng.getstate()==b.proposal_rng.getstate(),
            'same_exploration_rng_end':a.exploration_rng.getstate()==b.exploration_rng.getstate(),
            'nodes_saved_final':len(a.graph.nodes)-len(b.graph.nodes),
            'parameters_saved_final':len(a.conditions)-len(b.conditions),
            'definitions_saved_final':len(a.expression_ids)-len(b.expression_ids)})
    return answer


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    signal.alarm(120)
    report=analyze(args.input)
    report['analysis_sha256']=digest(Path(__file__).read_bytes())
    json_once(args.output,report)
    print(json.dumps({'pairs':report['pairs'],'arms':[{k:v for k,v in a.items() if k in
        ('seed','role','final_score','final_structure','proposal_outcomes','dead_births','check_seconds')}
        for a in report['arms']]}))
