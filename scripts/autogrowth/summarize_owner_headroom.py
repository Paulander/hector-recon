"""Read-only owner headroom results; never imports a training entrypoint to run it."""
import argparse
import json
from pathlib import Path

from summarize_owner_fresh_start import summarize as summarize_fresh


def summarize(path):
    root = Path(path)
    result = json.loads((root/'result.json').read_text())
    out = summarize_fresh(root)
    assert result['roles'] == ['owners-4', 'owners-8']
    raw = {(a['seed'], a['role']): a for a in result['arms']}
    for effect in out['paired_effects']:
        effect['comparison'] = 'eight minus four owners'
    for arm in out['arms']:
        source = raw[(arm['seed'], arm['role'])]
        trajectory = [source['initial'], *source['evaluations']]
        arm['limits'] = source['limits']
        arm['maximum_measured_correct'] = max(e['correct'] for e in trajectory)
        arm['sustained_measured_perfection_from'] = next((
            e['episode'] for i, e in enumerate(trajectory)
            if all(later['correct'] == 16 for later in trajectory[i:])), None)
        arm['final_failed_rows'] = [r['row'] for r in trajectory[-1]['rows'] if r['reward'] < 0]
        # The structure recorder contains visits for ancestors and live owners.
        # Leaf identities come from splitting history, not exposure thresholds.
        live = {0}
        for event in arm['split_events']:
            live.remove(event['owner'])
            live.update(event['split']['children'])
        visits = arm['final_structure']['owner_visits']
        arm['final_live_owner_visits'] = {str(owner): visits[str(owner)] for owner in sorted(live)}
        arm['budget_rejections'] = [
            {'episode': e['episode'], 'owner': e['owner'], 'rejections': e['budget_rejections']}
            for e in source['development_history'] if e['budget_rejections']]
        arm['owner_count_trajectory'] = [[e['episode'], s['owners']]
            for e, s in zip(source['evaluations'], source['structures'])]
        arm['zero_credit_measure_limit'] = (
            'Direct condition identity only; inherited descendants are distinct identities. '
            'A zero count alone does not imply impossibility or causal uselessness.')
    return out


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('run'); p.add_argument('--output', required=True)
    args = p.parse_args()
    with Path(args.output).open('x') as stream:
        json.dump(summarize(args.run), stream, indent=2, sort_keys=True)
        stream.write('\n')
