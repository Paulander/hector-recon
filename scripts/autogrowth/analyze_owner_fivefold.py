"""Offline row retention, exposure and ranking capacity; no training mutations."""
import argparse
from collections import Counter
import json
import os
from pathlib import Path
import resource
import signal
import time

from run_recursive_retention import ROWS, load_actor, json_once, digest
from run_owner_nomination import structure
from audit_owner_nomination import discrimination
from attribute_recursive_retention import capacity, value


def solved(evaluation):
    return {row['row'] for row in evaluation['rows'] if row['reward'] > 0}


def analyze(directory):
    report = json.loads((directory/'result.json').read_text())
    assert report['status'] == 'complete'
    result = {'run_status': report['status'], 'verification': report['verification'],
              'elapsed_seconds': report['elapsed_seconds'], 'max_rss_kib': report['max_rss_kib'],
              'prefix_evaluations': report['prefix_evaluations'], 'arms': [],
              'method': 'saved policies, actual journals and offline mathematical capacity; no new environment actions or weight installation'}
    for source in report['arms']:
        path = directory/f"seed-{source['seed']}"/source['role']
        initial_actor = load_actor(path/'start.pkl.gz')
        final = load_actor(path/'block-001856/checkpoint.pkl.gz')
        baseline = solved(source['initial'])
        previous = baseline
        ever = set(baseline)
        lost_events = []
        milestones = []
        for evaluation, shape in zip(source['evaluations'], source['structures']):
            current = solved(evaluation)
            losses = previous-current
            lost_events.extend({'episode': evaluation['episode'], 'row': row} for row in sorted(losses))
            milestones.append({'episode': evaluation['episode'], 'score': evaluation['correct'],
                'context_correct': evaluation['context_correct'], 'gains': sorted(current-previous),
                'losses': sorted(losses), 'lost_since_prefix': sorted(baseline-current),
                'gained_since_prefix': sorted(current-baseline), 'solved_rows': sorted(current),
                'structure': shape})
            ever |= current
            previous = current
        records = [json.loads(line) for file in sorted(path.glob('block-*/training.jsonl'))
                   for line in file.read_text().splitlines()]
        assert len(records) == 1280
        owner_exposure = Counter(record['owner'] for record in records)
        feedback_counts = Counter((record['owner'], record['action'], record['reward']) for record in records)
        checkpoints = {'initial': initial_actor,
                       'end_mostly_b': load_actor(path/'block-001216/checkpoint.pkl.gz'),
                       'final': final}
        representational = {name: {'discrimination': discrimination(actor), 'capacity': capacity(actor)}
                            for name, actor in checkpoints.items()}
        # Validate all published endpoint choices against the actual frozen score definition.
        for row in source['evaluations'][-1]['rows']:
            margin = sum(float(condition.weight)*(int(value(final.expressions[cid],row['row'],1))-
                                                   int(value(final.expressions[cid],row['row'],0)))
                         for cid, condition in final.conditions.items())
            assert row['action'] == ('act-b' if margin >= 0 else 'act-a')
        development = final.development_history
        leaves = []
        for owner, leaf in final.leaves.items():
            assert owner_exposure[owner] == final.owner_visits[owner] - (640 if owner==0 else 0)
            local_rows = [row for row in range(16) if value(leaf.path, row, 0)]
            assert all(value(leaf.path,row,0)==value(leaf.path,row,1) for row in range(16))
            sensitive = [cid for cid in leaf.contributions if any(
                value(final.expressions[cid],row,0)!=value(final.expressions[cid],row,1) for row in local_rows)]
            leaves.append({'owner': owner, 'born': leaf.born, 'path': repr(leaf.path),
                'observed_visits_after_conversion_or_birth': owner_exposure[owner],
                'development_opportunities': sum(event['owner']==owner for event in development),
                'rows': local_rows, 'parameters': len(leaf.contributions), 'action_sensitive_parameters': sensitive})
        births = []
        all_conditions = dict(final.conditions)
        all_conditions.update((event['condition'].identity,event['condition']) for event in final.retirement_history)
        for history in final.ownership_history:
            all_conditions.update((condition.identity,condition) for condition in history['conditions'])
        for event in development:
            cid = event['birth']
            if cid is None:
                continue
            condition = all_conditions[cid]
            effective = final.expressions[cid]
            births.append({'episode': event['episode'], 'owner': event['owner'], 'id': cid,
                'expression': repr(final.base_expressions[cid]), 'survives': cid in final.conditions,
                'action_sensitive_base': any(value(final.base_expressions[cid],row,0)!=value(final.base_expressions[cid],row,1) for row in range(16)),
                'reachable_rows_in_owned_context': [row for row in range(16) if any(value(effective,row,action) for action in (0,1))],
                'action_distinguishing_rows_in_owned_context': [row for row in range(16) if value(effective,row,0)!=value(effective,row,1)],
                'later_actual_credited_visits': sum(record['event']>=event['episode'] and cid in record['active'] for record in records),
                'final_or_retirement_weight': float(condition.weight)})
        b_boundary = solved(source['evaluations'][9])
        a_rows = {row for row in range(16) if not ROWS[row][2]}
        b_rows = set(range(16))-a_rows
        result['arms'].append({'seed': source['seed'], 'role': source['role'],
            'initial_score': source['initial']['correct'], 'initial_structure': structure(initial_actor),
            'final_score': source['evaluations'][-1]['correct'], 'final_structure': structure(final),
            'worst_score': min(m['score'] for m in milestones), 'best_score': max(m['score'] for m in milestones),
            'row_loss_events': lost_events, 'ever_solved_but_not_final': sorted(ever-previous),
            'original_a_losses_at_b_boundary': sorted((baseline & a_rows)-b_boundary),
            'b_gains_at_b_boundary': sorted((b_boundary-baseline)&b_rows),
            'b_boundary_successes_lost_by_final': sorted((b_boundary & b_rows)-previous),
            'milestones': milestones, 'representational': representational,
            'owner_visits': dict(owner_exposure), 'leaves': leaves, 'births': births,
            'development_history': development, 'retirement_history': final.retirement_history,
            'feedback_counts': [{'owner': owner, 'action': action, 'reward': reward, 'count': count}
                                for (owner,action,reward),count in sorted(feedback_counts.items())]})
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    os.sched_setaffinity(0,{min(os.sched_getaffinity(0))})
    resource.setrlimit(resource.RLIMIT_AS,(2*1024**3,2*1024**3))
    signal.alarm(110)
    started = time.monotonic()
    result = analyze(args.input)
    result['analysis_seconds'] = time.monotonic()-started
    result['analysis_source_sha256'] = digest(Path(__file__).read_bytes())
    json_once(args.output,result)
    print(json.dumps([{k:v for k,v in arm.items() if k in ('seed','role','initial_score','final_score','best_score','worst_score','leaves')}
                      for arm in result['arms']]))
