"""Read-only failure history, capacity and actual-credit attribution.

No act/observe calls, new play, growth or installation of fitted parameters.
Offline task labels are used only to audit the completed saved experiment.
"""
import argparse
from collections import defaultdict
from fractions import Fraction
import json
import math
from pathlib import Path

from audit_owner_nomination import value, target
from attribute_recursive_retention import capacity
from run_recursive_retention import ROWS, digest, json_once, load_actor


def margin(actor, row):
    return sum(float(c.weight)*(int(value(actor.expressions[cid],row,1))-
                                int(value(actor.expressions[cid],row,0)))
               for cid,c in actor.conditions.items())


def checkpoint(directory, event):
    path = directory/'start.pkl.gz' if event == 0 else directory/f'block-{event-64:06d}'/'checkpoint.pkl.gz'
    return load_actor(path)


def spans(history):
    result = []
    for item in history:
        if result and result[-1]['correct'] == item['correct']:
            result[-1]['last'] = item['event']
        else:
            result.append({'first':item['event'],'last':item['event'],'correct':item['correct']})
    return result


def attribute(directory, row, start, stop):
    before,after = checkpoint(directory,start),checkpoint(directory,stop)
    assert not [e for e in after.ownership_history if start < e['episode'] <= stop]
    assert not [e for e in after.retirement_history if start < e['episode'] <= stop]
    sign = 1 if target(row) else -1
    differences = {cid:sign*(int(value(ex,row,1))-int(value(ex,row,0)))
                   for cid,ex in after.expressions.items()}
    by_row = defaultdict(float)
    for offset in range(start,stop,64):
        for line in (directory/f'block-{offset:06d}'/'training.jsonl').read_text().splitlines():
            record = json.loads(line)
            change = sum(differences[cid]*(b-a) for cid,a,b in zip(
                record['active'],record['weights_before'],record['weights_after']))
            by_row[record['row']] += change
    old,new = sign*margin(before,row),sign*margin(after,row)
    assert math.isclose(sum(by_row.values()),new-old,abs_tol=1e-10)
    return {'row':row,'start':start,'stop':stop,'correct_margin_before':old,
        'correct_margin_after':new,'change_by_training_row':dict(by_row),
        'change_from_A':sum(v for r,v in by_row.items() if not ROWS[r][2]),
        'change_from_B':sum(v for r,v in by_row.items() if ROWS[r][2]),
        'attribution_matches_observed_weight_change':True}


def analyze(root):
    raw = json.loads((root/'result.json').read_text())
    assert raw['status'] == 'complete'
    out = {'status':'complete','method':__doc__,'new_training_actions':0,
           'new_evaluation_actions':0,'checkpoint_files_modified':False,'arms':[]}
    for arm in raw['arms']:
        directory = root/f"seed-{arm['seed']}"/arm['role']
        evaluations = [arm['initial'],*arm['evaluations']]
        actors = {e['episode']:checkpoint(directory,e['episode']) for e in evaluations}
        final = actors[1920]
        identities = list(final.conditions)
        vectors = {r:tuple(int(value(final.expressions[c],r,1))-
                           int(value(final.expressions[c],r,0)) for c in identities)
                   for r in range(16)}
        for e in evaluations:
            for row in e['rows']:
                assert row['action'] == ('act-b' if margin(actors[e['episode']],row['row']) >= 0 else 'act-a')
        wrong = [r['row'] for r in evaluations[-1]['rows'] if r['reward'] < 0]
        details = []
        for row in wrong:
            history = [{'event':e['episode'],
                        'correct':next(r for r in e['rows'] if r['row']==row)['reward'] > 0,
                        'margin_B_minus_A':margin(actors[e['episode']],row)} for e in evaluations]
            owner = next(o for o,l in final.leaves.items() if value(l.path,row,0))
            aliases = [r for r in range(16) if r != row and vectors[r] == vectors[row]]
            details.append({'row':row,'state':ROWS[row],'correct_output':target(row),
                'history':history,'correctness_spans':spans(history),
                'owner':owner,'owner_path':repr(final.leaves[owner].path),
                'final_margin_B_minus_A':margin(final,row),
                'opposite_target_exact_aliases':[r for r in aliases if target(r) != target(row)]})
        cap = capacity(final)
        if cap['joint_perfect_ranking_feasible']:
            witness = [Fraction(float(w)).limit_denominator(1000000) for w in cap['offline_witness']]
            for row in range(16):
                sign = 1 if target(row) else -1
                actual = sum(w*sign*d for w,d in zip(witness,vectors[row]))
                assert actual >= 1-target(row)
        # A feasibility witness is used by the offline checker only. No fitted
        # weights are assigned to an actor or exported as a replacement policy.
        cap = {k:cap[k] for k in ('status','message','joint_perfect_ranking_feasible')}
        cap['exact_rational_feasibility_verified'] = cap['joint_perfect_ranking_feasible']
        solved = lambda e: {r['row'] for r in e['rows'] if r['reward'] > 0}
        final_set = solved(evaluations[-1])
        stable_start = 1920
        for e in reversed(evaluations[:-1]):
            if solved(e) != final_set: break
            stable_start = e['episode']
        out['arms'].append({'seed':arm['seed'],'role':arm['role'],
            'final_score':evaluations[-1]['correct'],
            'best_score':max(e['correct'] for e in evaluations),
            'best_score_events':[e['episode'] for e in evaluations
                                 if e['correct'] == max(x['correct'] for x in evaluations)],
            'same_final_correct_set_since':stable_start,
            'final_wrong_rows':wrong,'final_failures':details,'final_capacity':cap})
    out['loss_attributions'] = [dict(seed=seed,role='residual-current',**attribute(
        root/f'seed-{seed}'/'residual-current',row,start,stop))
        for seed,row,start,stop in ((12,10,960,1024),(12,11,1728,1792),(13,7,896,960))]
    out['analysis_source_sha256'] = digest(Path(__file__).read_bytes())
    return out


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('run',type=Path);p.add_argument('--output',type=Path,required=True)
    args = p.parse_args();json_once(args.output,analyze(args.run))
