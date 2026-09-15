"""Offline endpoint capacity and owner partitions; no act/observe or policy repair."""
import argparse
from collections import Counter
from fractions import Fraction
import json
from pathlib import Path

from analyze_owner_fresh_failures import checkpoint, margin, spans
from attribute_recursive_retention import capacity
from audit_owner_nomination import value, target
from run_recursive_retention import ROWS, digest, json_once


def analyze(root):
    raw = json.loads((root/'result.json').read_text())
    assert raw['status'] == 'complete'
    out = {'status': 'complete', 'new_training_actions': 0,
           'new_evaluation_actions': 0, 'checkpoint_files_modified': False,
           'fitted_weights_installed': False, 'arms': []}
    for arm in raw['arms']:
        directory = root/f"seed-{arm['seed']}"/arm['role']
        evaluations = [arm['initial'], *arm['evaluations']]
        histories = {row: [] for row in range(16)}
        for evaluation in evaluations:
            actor = checkpoint(directory, evaluation['episode'])
            for record in evaluation['rows']:
                row = record['row']
                gap = margin(actor, row)
                assert record['action'] == ('act-b' if gap >= 0 else 'act-a')
                histories[row].append({'event': actor.completed,
                    'correct': record['reward'] > 0, 'margin_B_minus_A': gap})
        final = actor
        cap = capacity(final)
        if cap['joint_perfect_ranking_feasible']:
            witness = [Fraction(float(w)).limit_denominator(1000000)
                       for w in cap['offline_witness']]
            for row in range(16):
                sign = 1 if target(row) else -1
                gap = sum(w*sign*(int(value(final.expressions[cid], row, 1))-
                                  int(value(final.expressions[cid], row, 0)))
                          for w, cid in zip(witness, cap['identities']))
                assert gap >= 1-target(row)
        cap = {k: cap[k] for k in ('status', 'message', 'joint_perfect_ranking_feasible')}
        cap['exact_rational_feasibility_verified'] = cap['joint_perfect_ranking_feasible']
        owners = []
        for owner, leaf in final.leaves.items():
            rows = [r for r in range(16) if value(leaf.path, r, 0)]
            owners.append({'owner': owner, 'path': repr(leaf.path), 'rows': rows,
                'local_visits': final.owner_visits[owner],
                'failed_rows': [r for r in rows if not histories[r][-1]['correct']],
                'parameters': len(leaf.contributions)})
        assert sorted(r for owner in owners for r in owner['rows']) == list(range(16))
        out['arms'].append({'seed': arm['seed'], 'role': arm['role'],
            'capacity': cap, 'owners': owners,
            'live_condition_states': dict(Counter(str(c.state) for c in final.conditions.values())),
            'row_histories': [{'row': row, 'state': ROWS[row], 'correct_output': target(row),
                              'spans': spans(history), 'history': history}
                             for row, history in histories.items()]})
    out['analysis_source_sha256'] = digest(Path(__file__).read_bytes())
    return out


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('run', type=Path); p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    json_once(args.output, analyze(args.run))
