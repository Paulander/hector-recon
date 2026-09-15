"""Read-only committed-policy retention and full provisional-storage costs."""
import argparse
import json
from pathlib import Path

from summarize_owner_fresh_start import summarize as fresh_summary


def summarize(path):
    root = Path(path)
    result = json.loads((root/'result.json').read_text())
    out = fresh_summary(root)
    for summary,arm in zip(out['arms'],result['arms']):
        directory = root/f"seed-{arm['seed']}"/arm['role']
        rows = [json.loads(line) for block in sorted(directory.glob('block-*'))
                for line in (block/'training.jsonl').read_text().splitlines()]
        summary['trial_history'] = arm['trial_history']
        summary['trial_counts'] = {state:sum(t['state']==state for t in arm['trial_history'])
                                   for state in ('TRIAL','MATURE','PRUNED')}
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
        summary['maximum_correct'] = max(e['correct'] for e in evaluations)
        summary['sustained_perfect_from'] = next((e['episode'] for i,e in enumerate(evaluations)
            if all(later['correct']==16 for later in evaluations[i:])),None)
        summary['row_histories'] = [{'row':i,'first_correct':next((e['episode'] for e in evaluations
            if e['rows'][i]['reward']>0),None),
            'correct_at':[e['episode'] for e in evaluations if e['rows'][i]['reward']>0],
            'final_correct':evaluations[-1]['rows'][i]['reward']>0} for i in range(16)]
    for pair in out['paired_effects']:
        pair['comparison'] = 'combined provisional trial rule minus current'
    return out


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('run'); parser.add_argument('--output',required=True)
    args = parser.parse_args()
    with Path(args.output).open('x') as stream:
        json.dump(summarize(args.run),stream,indent=2,sort_keys=True)
        stream.write('\n')
