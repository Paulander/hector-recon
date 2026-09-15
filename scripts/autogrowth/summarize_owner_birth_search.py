"""Read-only row-level summary of the declared owner-birth comparison."""
import argparse
import json
from pathlib import Path


def solved(evaluation, context=None):
    return {r['row'] for r in evaluation['rows'] if r['reward'] > 0
            and (context is None or r['context'] == context)}


def summarize(path):
    root=Path(path)
    result=json.loads((root/'result.json').read_text())
    out={'status':result['status'],'elapsed_seconds':result['elapsed_seconds'],
         'max_rss_kib':result['max_rss_kib'],'verification':result.get('verification'),
         'arms':[], 'paired_effects':[]}
    for arm in result['arms']:
        evaluations=[arm['initial'],*arm['evaluations']]
        if not arm['evaluations']: continue
        first,last=evaluations[0],evaluations[-1]
        boundary=next((e for e in evaluations if e['episode']==1280),None)
        b_reference=solved(boundary,1) if boundary else set()
        post=[e for e in evaluations if e['episode']>1280]
        changes=[]
        for before,after in zip(evaluations,evaluations[1:]):
            gains=sorted(solved(after)-solved(before)); losses=sorted(solved(before)-solved(after))
            if gains or losses: changes.append({'event':after['episode'],'gains':gains,'losses':losses})
        nominations=arm.get('birth_nominations',[])
        births=[n for n in nominations if n.get('birth') is not None]
        owner_counts={}
        credited={}
        directory=root/f"seed-{arm['seed']}"/arm['role']
        for block in sorted(directory.glob('block-*')):
            if not (block/'complete.json').exists(): continue
            for line in (block/'training.jsonl').read_text().splitlines():
                row=json.loads(line); owner_counts[row['owner']]=owner_counts.get(row['owner'],0)+1
                for cid in row['active']:credited[cid]=credited.get(cid,0)+1
        structure=dict(arm['structures'][-1])
        # The reused legacy recorder counts ordinary births in this one field.
        # Preserve that count under an explicit name and include extra births
        # using the complete nomination records in this study's summary.
        structure['ordinary_births_after_conversion']=structure.pop('births_after_conversion')
        structure['births_after_conversion']=len(births)
        summary={'seed':arm['seed'],'role':arm['role'],'initial':first['correct'],
            'final':last['correct'],'final_A_B':last['context_correct'],
            'final_gains_from_prefix':sorted(solved(last)-solved(first)),
            'final_losses_from_prefix':sorted(solved(first)-solved(last)),
            'prefix_A_solved':sorted(solved(first,0)),
            'prefix_A_worst_retained':min(len(solved(e,0)&solved(first,0)) for e in evaluations),
            'B_boundary_solved':sorted(b_reference),
            'B_final_retained':len(solved(last,1)&b_reference),
            'B_worst_post_boundary_retained':min((len(solved(e,1)&b_reference) for e in post),default=None),
            'row_changes':changes,'score_trajectory':[[e['episode'],e['correct']] for e in evaluations],
            'nominations':len(nominations),'accepted_births':len(births),
            'residual_selections':sum(n.get('selection')=='residual' for n in nominations),
            'random_selections':sum(n.get('selection')=='random' for n in nominations),
            'extra_birth_opportunities':sum('extra_birth' in e for e in arm.get('development_history',[])),
            'born_condition_credited_counts':{str(n['birth']):credited.get(n['birth'],0) for n in births},
            'direct_identity_zero_credit_births':sum(not credited.get(n['birth'],0) for n in births),
            'visited_owner_counts':owner_counts,'final_structure':structure}
        out['arms'].append(summary)
    indexed={(a['seed'],a['role']):a for a in out['arms']}
    for seed in result['seeds']:
        for schedule in ('current','extra'):
            left=indexed.get((seed,'random-'+schedule));right=indexed.get((seed,'residual-'+schedule))
            if left and right:out['paired_effects'].append({'seed':seed,'comparison':'residual minus random',
                'schedule':schedule,'final_score_difference':right['final']-left['final'],
                'birth_difference':right['accepted_births']-left['accepted_births']})
        for mode in ('random','residual'):
            left=indexed.get((seed,mode+'-current'));right=indexed.get((seed,mode+'-extra'))
            if left and right:out['paired_effects'].append({'seed':seed,'comparison':'extra minus current',
                'mode':mode,'final_score_difference':right['final']-left['final'],
                'birth_difference':right['accepted_births']-left['accepted_births']})
    return out


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('run');p.add_argument('--output',required=True)
    args=p.parse_args();out=Path(args.output)
    with out.open('x') as stream:json.dump(summarize(args.run),stream,indent=2,sort_keys=True);stream.write('\n')
