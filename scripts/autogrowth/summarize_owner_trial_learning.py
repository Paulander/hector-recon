"""Read-only fresh-start results; retention references real phase boundaries."""
import argparse
import json
import itertools
from pathlib import Path

from summarize_owner_birth_search import solved


def retention(evaluations, event, context):
    boundary = next(e for e in evaluations if e['episode'] == event)
    reference = solved(boundary,context)
    later = [e for e in evaluations if e['episode'] > event]
    final = evaluations[-1]
    return {'boundary':event,'context':context,'boundary_correct_rows':sorted(reference),
        'final_retained_rows':sorted(reference & solved(final,context)),
        'final_lost_rows':sorted(reference - solved(final,context)),
        'worst_measured_retained':min(len(reference & solved(e,context)) for e in later)}


def base_summary(path):
    root = Path(path)
    result = json.loads((root/'result.json').read_text())
    if result['status'] != 'complete':
        raise ValueError('complete verification is required for the final comparison')
    out = {k:result[k] for k in ('status','seeds','roles','verification','elapsed_seconds','max_rss_kib')}
    out['arms'] = []
    for arm in result['arms']:
        evaluations = [arm['initial'],*arm['evaluations']]
        first, last = evaluations[0],evaluations[-1]
        history = arm['development_history']
        splits = [e for e in history if e['split'] is not None]
        nominations = arm['birth_nominations']
        births = [n for n in nominations if n.get('birth') is not None]
        changes = []
        for before,after in zip(evaluations,evaluations[1:]):
            gains,losses = solved(after)-solved(before),solved(before)-solved(after)
            if gains or losses:
                changes.append({'event':after['episode'],'gains':sorted(gains),'losses':sorted(losses)})
        trained = [{'start':s,'stop':s+640,'actions':0,'correct':0} for s in (0,640,1280)]
        owner_counts,credited = {},{}
        for block in sorted((root/f"seed-{arm['seed']}"/arm['role']).glob('block-*')):
            for line in (block/'training.jsonl').read_text().splitlines():
                row = json.loads(line)
                phase = trained[row['event']//640]
                phase['actions'] += 1; phase['correct'] += row['reward'] > 0
                owner_counts[row['owner']] = owner_counts.get(row['owner'],0)+1
                for cid in row['active']: credited[cid] = credited.get(cid,0)+1
        assert all(p['actions'] == 640 for p in trained)
        final_structure = dict(arm['structures'][-1])
        assert final_structure.pop('births_after_conversion') == len(births)
        final_structure['births_from_zero'] = len(births)
        outcomes = {}
        for n in nominations:
            outcomes[n['outcome']] = outcomes.get(n['outcome'],0)+1
        out['arms'].append({'seed':arm['seed'],'role':arm['role'],
            'initial':first['correct'],'final':last['correct'],'final_A_B':last['context_correct'],
            'phase_boundaries':{str(e['episode']):{'correct':e['correct'],'A_B':e['context_correct']}
                                for e in evaluations if e['episode'] in (640,1280,1920)},
            'first_perfect_event':next((e['episode'] for e in evaluations if e['correct']==16),None),
            'A_retention':retention(evaluations,640,0),'B_retention':retention(evaluations,1280,1),
            'score_trajectory':[[e['episode'],e['correct'],e['context_correct']] for e in evaluations],
            'row_changes':changes,'training_by_phase':trained,
            'split_events':[{'episode':e['episode'],'owner':e['owner'],'split':e['split']} for e in splits],
            'first_scoring_birth':births[0]['episode'] if births else None,
            'nominations':len(nominations),'accepted_births':len(births),'nomination_outcomes':outcomes,
            'residual_selections':sum(n.get('selection')=='residual' for n in nominations),
            'random_selections':sum(n.get('selection')=='random' for n in nominations),
            'direct_identity_zero_credit_births':sum(not credited.get(n['birth'],0) for n in births),
            'visited_owner_counts':owner_counts,'final_structure':final_structure,
            'peak_nodes':max(s['physical_nodes'] for s in arm['structures']),
            'peak_parameters':max(s['effective_parameters'] for s in arm['structures'])})
    indexed = {(a['seed'],a['role']):a for a in out['arms']}
    out['paired_effects'] = []
    for seed in result['seeds']:
        for control,treatment in (('current','trial'),('current','learning-trial'),('trial','learning-trial')):
            left,right = (indexed[(seed,role)] for role in (control,treatment))
            out['paired_effects'].append({'seed':seed,'comparison':f'{treatment} minus {control}',
                'final_score_difference':right['final']-left['final'],
                'node_difference':right['final_structure']['physical_nodes']-left['final_structure']['physical_nodes'],
                'parameter_difference':right['final_structure']['effective_parameters']-left['final_structure']['effective_parameters']})
    return out


def summarize(path):
    root = Path(path)
    result = json.loads((root/'result.json').read_text())
    out = base_summary(root)
    for summary,arm in zip(out['arms'],result['arms']):
        directory = root/f"seed-{arm['seed']}"/arm['role']
        rows = [json.loads(line) for block in sorted(directory.glob('block-*'))
                for line in (block/'training.jsonl').read_text().splitlines()]
        summary['trial_history'] = arm['trial_history']
        summary['trial_counts'] = {state:sum(t['state']==state for t in arm['trial_history'])
                                   for state in ('TRIAL','PROBATION','MATURE','PRUNED')}
        # The immutable runner's generic field counts all committed splits,
        # including current-arm automatic ones. Normalize that label here.
        summary['final_structure']['committed_splits'] = summary['final_structure']['splits']
        summary['final_structure']['accepted_trials'] = summary['trial_counts']['MATURE']
        summary['trial_assigned_actions'] = sum(r['split_use_assignment'] is not None for r in rows)
        summary['trial_child_actions'] = sum(bool(r['split_use_assignment'] and r['split_use_assignment'][4]) for r in rows)
        summary['training_wall_seconds_including_recording_and_scheduled_eval'] = arm['training_wall_seconds']
        summary['storage_cost'] = {
            'peak_nodes':max([r['stored_nodes'] for r in rows]+[arm['structures'][-1]['physical_nodes']]),
            'peak_parameters':max([r['stored_parameters'] for r in rows]+[arm['structures'][-1]['effective_parameters']]),
            'peak_stored_scorers':max([r['stored_scorers'] for r in rows]+[arm['structures'][-1]['stored_scorers']]),
            'node_action_sum':sum(r['stored_nodes'] for r in rows),
            'parameter_action_sum':sum(r['stored_parameters'] for r in rows),
            'note':'Stored allocation at each real training action; not executed FLOPs.'}
        evaluations = [arm['initial'],*arm['evaluations']]
        states = list(itertools.product((False,True),repeat=4))
        summary['final_single_input_matches'] = [name for i,name in enumerate(('x','y'))
            if all((r['action']=='act-b') == states[r['row']][i] for r in evaluations[-1]['rows'])]
        summary['maximum_correct'] = max(e['correct'] for e in evaluations)
        summary['sustained_perfect_from'] = next((e['episode'] for i,e in enumerate(evaluations)
            if all(later['correct']==16 for later in evaluations[i:])),None)
        summary['row_histories'] = [{'row':i,'first_correct':next((e['episode'] for e in evaluations
            if e['rows'][i]['reward']>0),None),
            'correct_at':[e['episode'] for e in evaluations if e['rows'][i]['reward']>0],
            'final_correct':evaluations[-1]['rows'][i]['reward']>0} for i in range(16)]
    return out


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('run'); parser.add_argument('--output',required=True)
    args = parser.parse_args()
    with Path(args.output).open('x') as stream:
        json.dump(summarize(args.run),stream,indent=2,sort_keys=True)
        stream.write('\n')
