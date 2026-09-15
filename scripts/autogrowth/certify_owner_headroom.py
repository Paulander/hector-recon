"""Exact offline contradiction certificates for reported endpoint infeasibility."""
import argparse
from fractions import Fraction
import json
from pathlib import Path

import numpy as np
from scipy.optimize import linprog
from attribute_recursive_retention import difference, target
from analyze_owner_fresh_failures import checkpoint
from run_recursive_retention import digest, json_once


def certify(root, analysis):
    out = {'new_training_actions': 0, 'new_evaluation_actions': 0,
           'fitted_weights_installed': False, 'certificates': []}
    for arm in analysis['arms']:
        if arm['capacity']['joint_perfect_ranking_feasible']:
            continue
        actor = checkpoint(root/f"seed-{arm['seed']}"/arm['role'], 1920)
        ids = list(actor.conditions)
        matrix = [[difference(actor.expressions[cid], row) for cid in ids]
                  for row in range(16)]
        threshold = [1-target(row) for row in range(16)]
        fit = linprog(-np.array(threshold),
            A_eq=np.vstack((np.array(matrix).T, np.ones(16))),
            b_eq=np.array([0]*len(ids)+[1]), bounds=[(0, None)]*16,
            method='highs', options={'time_limit': 10})
        assert fit.success
        factors = [Fraction(float(x)).limit_denominator(1000000) for x in fit.x]
        assert all(x >= 0 for x in factors) and sum(factors) == 1
        assert all(sum(factors[r]*matrix[r][c] for r in range(16)) == 0
                   for c in range(len(ids)))
        contradiction = sum(factors[r]*threshold[r] for r in range(16))
        assert contradiction > 0
        out['certificates'].append({'seed': arm['seed'], 'role': arm['role'],
            'condition_ids': ids, 'matrix': matrix, 'threshold': threshold,
            'nonnegative_row_factors': [str(x) for x in factors],
            'weighted_required_margin': str(contradiction),
            'exact_rational_verification': True})
    out['source_sha256'] = digest(Path(__file__).read_bytes())
    return out


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('run', type=Path); p.add_argument('--analysis', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    json_once(args.output, certify(args.run, json.loads(args.analysis.read_text())))
