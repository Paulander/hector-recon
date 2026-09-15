"""Offline committed-policy capacity and exact certificates; never training."""
import argparse
from fractions import Fraction
import json
from pathlib import Path

import numpy as np
from scipy.optimize import linprog

from attribute_recursive_retention import difference, value, target
from run_owner_split_trial import load_actor, digest


def committed_ids(actor):
    children = {c for trial in getattr(actor,'split_trials',{}).values() for c in trial.children}
    return [cid for owner,leaf in actor.leaves.items() if owner not in children
            for cid in leaf.contributions]


def capacity(actor):
    ids = committed_ids(actor)
    matrix = [[difference(actor.expressions[cid],row) for cid in ids] for row in range(16)]
    threshold = [1-target(row) for row in range(16)]
    fit = linprog(np.zeros(len(ids)),A_ub=-np.array(matrix),b_ub=-np.array(threshold),
        bounds=[(None,None)]*len(ids),method='highs',options={'time_limit':10})
    if fit.success:
        weights = [Fraction(float(x)).limit_denominator(1000000) for x in fit.x]
        margins = [sum(w*c for w,c in zip(weights,row)) for row in matrix]
        assert all(m>=t for m,t in zip(margins,threshold))
        certificate = {'type':'feasible rational ranking witness','weights':list(map(str,weights)),
                       'margins':list(map(str,margins))}
    else:
        assert fit.status == 2, fit.message
        dual = linprog(-np.array(threshold),A_eq=np.vstack((np.array(matrix).T,np.ones(16))),
            b_eq=np.array([0]*len(ids)+[1]),bounds=[(0,None)]*16,method='highs',
            options={'time_limit':10})
        assert dual.success
        weights = [Fraction(float(x)).limit_denominator(1000000) for x in dual.x]
        assert all(x>=0 for x in weights) and sum(weights)==1
        assert all(sum(weights[r]*matrix[r][c] for r in range(16))==0 for c in range(len(ids)))
        contradiction=sum(w*t for w,t in zip(weights,threshold)); assert contradiction>0
        certificate={'type':'infeasible exact nonnegative contradiction','row_factors':list(map(str,weights)),
                     'weighted_required_margin':str(contradiction)}
    return {'joint_16_capacity':bool(fit.success),'identities':ids,'matrix':matrix,
            'required_margins':threshold,'certificate':certificate,'installed':False}


def analyze(path):
    root=Path(path); raw=json.loads((root/'result.json').read_text())
    assert raw['status']=='complete'
    out={'status':'verified','new_environment_actions':0,'arithmetic_choices_verified':0,'arms':[]}
    for arm in raw['arms']:
        directory=root/f"seed-{arm['seed']}"/arm['role']
        evaluations=[arm['initial'],*arm['evaluations']]
        for e in evaluations:
            p=directory/'start.pkl.gz' if e['episode']==0 else directory/f"block-{e['episode']-64:06d}/checkpoint.pkl.gz"
            actor=load_actor(p); ids=committed_ids(actor)
            for row in e['rows']:
                gap=sum(float(actor.conditions[cid].weight)*(int(value(actor.expressions[cid],row['row'],1))-
                    int(value(actor.expressions[cid],row['row'],0))) for cid in ids)
                assert row['action']==('act-b' if gap>=0 else 'act-a')
                out['arithmetic_choices_verified']+=1
        out['arms'].append({'seed':arm['seed'],'role':arm['role'],'final_capacity':capacity(actor),
            'final_failed_rows':[r['row'] for r in evaluations[-1]['rows'] if r['reward']<0]})
    out['analysis_source_sha256']=digest(Path(__file__).read_bytes())
    return out


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('run'); parser.add_argument('--output',required=True)
    args=parser.parse_args()
    with Path(args.output).open('x') as stream:
        json.dump(analyze(args.run),stream,indent=2,sort_keys=True); stream.write('\n')
