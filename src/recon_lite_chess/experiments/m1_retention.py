"""Offline retention attribution; never imports into the learner or coach.

Frozen choices are checked through the formal engine. Credit accounting uses
ordinary Python numbers and recorded actions/outcomes, never learner updates.
"""
import argparse
from collections import defaultdict
from dataclasses import asdict
import gzip
import json
import math
from pathlib import Path
import pickle
import time

from . import m1_failure_patterns as f

d, prior = f.d, f.prior
ACTORS = ((9, .25, 4096), (9, .25, 4608), (9, .25, 6144), (9, .5, 6144), (7, .25, 6144))
TARGETS = (6, 9, 15, 105)


def arm_record(reference, seed, rate):
    return next(r for r in reference['run']['results'] if (r['seed'], r['exploration']) == (seed, rate))


def restore(reference, private, seed, rate, event):
    manifest = reference['run']['manifest']
    if (reference['status'] != 'complete' or reference['run']['status'] != 'complete'
            or manifest['source'] != prior.sources()):
        raise ValueError('complete source-matched exploration reference required')
    record = arm_record(reference, seed, rate)
    prefix = f'seed-{seed}/exploration-{rate:.2f}/checkpoint-0-{event:06d}-'
    entries = [x for x in reference['private_checkpoint_index'] if x['path'].startswith(prefix)]
    milestone = record['milestones'].get(str(event))
    if milestone:
        entries = [x for x in entries if x['sha256'] == milestone['checkpoint_sha256']]
    if len(entries) != 1:
        raise ValueError('one exact indexed boundary required')
    entry = entries[0]; private = Path(private)
    path = (private/entry['path']).resolve()
    if not path.is_relative_to(private.resolve()) or prior.sha(path) != entry['sha256']:
        raise ValueError('checkpoint path/transport differs')
    with gzip.open(path, 'rb') as stream:
        payload = pickle.load(stream)
    state = payload['state']; actor = state['organism']
    if (payload['source'] != manifest['source'] or payload['manifest_digest'] != prior.digest(manifest)
            or state['seed'] != seed or state['role_index'] != 0 or state['next_event'] != event
            or actor.completed != event or actor.pending or actor.hold_topology
            or actor.trial_condition is not None or asdict(actor.config) != record['config']):
        raise ValueError('checkpoint state/configuration differs')
    expected = (record['initial'] if event == manifest['start_event'] else
                {k:v for k,v in milestone['result'].items() if k != 'evaluation'} if milestone else None)
    if expected is not None and prior.snapshot(actor) != expected:
        raise ValueError('checkpoint learned state differs')
    evaluation = (record['inherited_evaluation'] if event == manifest['start_event'] else
                  milestone['result']['evaluation'] if milestone else None)
    return actor, evaluation, entry['sha256']


def numerical_trace(actor, row):
    matrix = [tuple(d.gate_value(c,v) for c in actor.conditions.values()) for v in row['vectors']]
    scores = [math.fsum([float(actor.bias), *(float(c.weight)*x for c,x in zip(actor.conditions.values(),v))])
              for v in matrix]
    chosen = max(range(len(scores)), key=lambda i:(scores[i],f'option:{i}'))
    return {'matrix':matrix,'scores':scores,'chosen':chosen}


def inspect(actor, data, *, deadline, counts):
    reports, traces = {}, {}
    for split, rows in data.items():
        observed = []
        def observer(i,row,matrix,scores,chosen):
            observed.append({'matrix':matrix,'scores':scores,'chosen':chosen})
        reports[split] = d.inspect_actor(actor, rows, deadline=deadline, counts=counts, row_observer=observer)
        traces[split] = observed
        if not reports[split]['strict_gate_ranking']['strict_all_winners_rankable']:
            reports[split]['tie_aware_ranking'] = f.checked_certificate(rows,[x['matrix'] for x in observed],deadline=deadline)
        reports[split]['failures'] = [{'row':i,'orbit':r['orbit'],'geometry':r['geometry'],
            'chosen_effect':r['after'][t['chosen']],
            'win_minus_chosen_support':t['scores'][r['wins'].index(1)]-t['scores'][t['chosen']]}
            for i,(r,t,won) in enumerate(zip(rows,observed,reports[split]['outcomes'])) if not won]
    rows = data['train']+data['validation']
    matrices = [x['matrix'] for x in traces['train']+traces['validation']]
    joint = d.ranking_feasibility(rows, matrices, deadline=deadline)
    if not joint['strict_all_winners_rankable']:
        joint['tie_aware_ranking'] = f.checked_certificate(rows,matrices,deadline=deadline)
    return reports, joint


def definition(c):
    return c.operator, c.atoms, c.born


def credit_accounting(boundaries, actions, training_rows, targets, *, deadline):
    """Reconstruct numerical increments without invoking act/observe/birth/prune.

    Recorded request counts determine retirement times; no counterfactual reward
    or alternative choice affects this arithmetic. Every boundary must verify.
    """
    events = sorted(boundaries); start, end = events[0], events[-1]
    initial, final = boundaries[start], boundaries[end]
    before = {event:prior.actor_digest(a) for event,a in boundaries.items()}
    catalog = {c.identity:c for c in (*final.retired_conditions.values(),*final.conditions.values())}
    deaths = {c.identity:c.born+c.stats.relevance_stats.request_exposures for c in final.retired_conditions.values()}
    for a in boundaries.values():
        for cid,c in a.conditions.items():
            if cid not in catalog or definition(c) != definition(catalog[cid]):
                raise ValueError('condition history lacks a persistent definition')
    if [a['event'] for a in actions] != list(range(start,end)):
        raise ValueError('complete chronological actual-action log required')
    weights = {cid:[c.weight.fast,c.weight.slow] for cid,c in initial.conditions.items()}
    bias = [initial.bias.fast,initial.bias.slow]
    groups = defaultdict(lambda:{'events':0,'reward_sum':0.,'selected_active_sum':0,
        'prediction_sum':0.,'delta_sum':0.,'target_margin_credit_sum':0.})
    by_condition = defaultdict(float)
    removal = 0.; max_error = 0.; checked = []; crossings = []
    target = targets[0]
    win = target['wins'].index(1)
    loss = numerical_trace(final,target)['chosen']
    if target['wins'][loss]:
        raise ValueError('credit attribution requires a final failed target')
    contrasts = {cid:d.gate_value(c,target['vectors'][win])-d.gate_value(c,target['vectors'][loss]) for cid,c in catalog.items()}
    def margin():
        return math.fsum((w[0]+w[1])*contrasts[cid] for cid,w in weights.items())
    initial_margin = margin(); previous_margin = initial_margin
    cfg = initial.config
    for item in actions:
        d.expired(deadline)
        event = item['event']; row = training_rows[item['pool_index']]
        if (item['real_moves'] != 1 or item['action'] not in row['bindings']
                or item['reward'] not in (-1,1)):
            raise ValueError('invalid submitted-action record')
        # Use the logged actual reward, not laboratory grades in row['wins'].
        vector = row['vectors'][row['bindings'].index(item['action'])]
        active = [cid for cid in weights if d.gate_value(catalog[cid],vector)]
        prediction = math.fsum([bias[0]+bias[1],*(sum(weights[cid]) for cid in active)])
        delta = cfg.learning_rate*(item['reward']-prediction)/(1+len(active))
        bias[0] += delta
        for cid in active:
            weights[cid][0] += delta
            by_condition[cid] += delta*contrasts[cid]
        credit = delta*sum(contrasts[cid] for cid in active)
        g = row['geometry']; family = f"{g['edge_orientation']}:{g['king_file_distance']},{g['king_rank_distance']}"
        interval = next(bound for bound in events if bound>event)
        key = (interval,family,int(item['reward']))
        group = groups[key]; group['events'] += 1; group['reward_sum'] += item['reward']
        group['selected_active_sum'] += len(active); group['prediction_sum'] += prediction
        group['delta_sum'] += delta; group['target_margin_credit_sum'] += credit
        completed = event+1
        if completed % cfg.consolidate_every == 0:
            transfer = cfg.consolidation_rate*bias[0]
            bias[0] -= transfer; bias[1] += transfer
        for cid in list(weights):
            if deaths.get(cid) == completed:
                removal -= sum(weights[cid])*contrasts[cid]
                del weights[cid]
        for cid,c in catalog.items():
            if c.born == completed:
                weights[cid] = [0.,0.]
        now = margin()
        if (previous_margin>0) != (now>0):
            crossings.append({'after_event':event,'completed':completed,'pool_index':item['pool_index'],
                'reward':item['reward'],'family':family,'margin_before':previous_margin,'margin_after':now})
        previous_margin = now
        if completed in boundaries:
            a = boundaries[completed]
            if set(weights) != set(a.conditions):
                raise RuntimeError('reconstructed condition lifetimes differ at saved boundary')
            errors = [abs(bias[0]-a.bias.fast),abs(bias[1]-a.bias.slow)]
            errors += [abs(weights[cid][i]-value) for cid,c in a.conditions.items()
                       for i,value in enumerate((c.weight.fast,c.weight.slow))]
            error = max(errors); max_error = max(max_error,error)
            if error>1e-8:
                raise RuntimeError('numerical credit does not reproduce saved weights')
            checked.append({'event':completed,'max_weight_error':error,'target_margin':now})
    final_margin = margin(); total_credit = math.fsum(by_condition.values())
    if not math.isclose(final_margin-initial_margin,total_credit+removal,abs_tol=1e-8):
        raise RuntimeError('credit plus removals does not account for target margin change')
    if before != {event:prior.actor_digest(a) for event,a in boundaries.items()}:
        raise RuntimeError('credit accounting mutated an actor')
    return {'verified_boundaries':checked,'max_weight_error':max_error,'actors_unchanged':True,
        'training_moves':0,'learner_updates_called':0,'target_orbit':target['orbit'],
        'initial_margin_on_final_pair':initial_margin,'final_margin_on_final_pair':final_margin,
        'actual_credit_margin_change':total_credit,'removal_margin_change':removal,
        'margin_sign_crossings':crossings,
        'credit_groups':[{'through_boundary':k[0],'family':k[1],'reward':k[2],**v} for k,v in sorted(groups.items())],
        'condition_credit':[{'id':cid,'operator':catalog[cid].operator,'atoms':catalog[cid].atoms,
            'born':catalog[cid].born,'retired_at':deaths.get(cid),'target_contrast':contrasts[cid],
            'target_margin_credit_sum':value} for cid,value in sorted(by_condition.items(),key=lambda x:abs(x[1]),reverse=True)]}


def run(args):
    if args.wall_seconds<=0:raise ValueError('positive diagnostic budget required')
    ref = prior.read(args.reference); source = ref['run']['manifest']
    if ref['status']!='complete' or source['source']!=prior.sources():
        raise ValueError('complete source-matched reference required')
    splits,hashes = {},{}
    for name in ('train','validation'):
        splits[name],hashes[name] = prior.load_split(args.pool,name)
        if hashes[name]!=source[name+'_sha256']:raise ValueError('original pools required')
    events = list(range(source['start_event'],source['end_event']+1,source['block']))
    manifest = {'schema':'m1_retention.v1','source':prior.sources(),'diagnostic_sha256':prior.sha(__file__),
        'representation_sha256':prior.sha(d.__file__),'pattern_sha256':prior.sha(f.__file__),
        'certificate_sha256':prior.sha(f.ranking.__file__),'scipy':d.scipy.__version__,
        'reference_sha256':prior.sha(args.reference),'actors':ACTORS,'targets':TARGETS,
        'timeline_events':events,'pool_hashes':hashes,'wall_seconds':args.wall_seconds,
        'laboratory_transitions':sum(f.chess.Board(fen).legal_moves.count() for rows in splits.values() for fen in rows),
        'actor_evaluation_moves':len(ACTORS)*sum(map(len,splits.values())),
        'training_moves':0,'learner_updates_called':0,'final_test_opened':False,
        'limits':['All diagnosis is offline and never supplied to learning.',
            'Joint train/development feasibility is existence, not learned performance or generalization.',
            'Credit accounting conditions on actual logged actions and observed rewards; it is not a no-change counterfactual.',
            'Numerical attribution must match every saved boundary; no inferred credit claim if it fails.']}
    args.output.mkdir(parents=True,exist_ok=False)
    prior.atomic_json(args.output/'manifest.json',manifest)
    started=time.monotonic(); deadline=started+args.wall_seconds
    counts={'laboratory_transitions':0,'actor_actions_started':0,'actor_evaluation_moves':0}
    results=[]
    try:
        data={name:f.laboratory_rows(rows,deadline=deadline,counts=counts) for name,rows in splits.items()}
        print(json.dumps({'laboratory_complete':counts['laboratory_transitions']}),flush=True)
        for seed,rate,event in ACTORS:
            a,expected,sha=restore(ref,args.private,seed,rate,event)
            before=prior.actor_digest(a)
            reports,joint=inspect(a,data,deadline=deadline,counts=counts)
            if any(reports['validation'][k]!=expected[k] for k in ('mates','outcomes','action_digest')):
                raise RuntimeError('historical behavior differs')
            if prior.actor_digest(a)!=before:raise RuntimeError('diagnosis changed actor')
            result={'seed':seed,'exploration':rate,'event':event,'checkpoint_sha256':sha,
                'historical_behavior_matches':True,'learned_state_unchanged':True,'reports':reports,'joint_ranking':joint}
            results.append(result)
            prior.atomic_json(args.output/f'seed-{seed}-{rate:.2f}-{event}.json',result)
            print(json.dumps({'seed':seed,'rate':rate,'event':event,'mates':reports['validation']['mates'],
                'joint_strict_rankable':joint['strict_all_winners_rankable']}),flush=True)
        timelines=[]
        for rate in (.25,.5):
            boundaries={event:restore(ref,args.private,9,rate,event)[0] for event in events}
            final=boundaries[events[-1]]
            target_rows=[data['validation'][i] for i in TARGETS]
            timeline=[]
            for event,a in boundaries.items():
                trace=[]
                for i,row in zip(TARGETS,target_rows):
                    t=numerical_trace(a,row); stop=numerical_trace(final,row)
                    trace.append({'row':i,'orbit':row['orbit'],'won':row['wins'][t['chosen']],
                        'win_minus_chosen_support':t['scores'][row['wins'].index(1)]-t['scores'][t['chosen']],
                        'accounting_to_final':f.margin_change(a,final,row,t,stop)})
                timeline.append({'event':event,'targets':trace})
            log=args.private/f'seed-9/exploration-{rate:.2f}/training-actions.jsonl'
            record=arm_record(ref,9,rate)
            if prior.sha(log)!=record['transcript_sha256']:raise ValueError('actual-action log hash differs')
            actions=[json.loads(line) for line in log.read_text().splitlines()]
            if [x['pool_index'] for x in actions]!=source['plans']['9'][events[0]:events[-1]]:
                raise ValueError('logged exercise schedule differs')
            credit=credit_accounting(boundaries,actions,data['train'],target_rows,deadline=deadline)
            item={'seed':9,'exploration':rate,'timeline':timeline,'credit':credit}
            timelines.append(item);prior.atomic_json(args.output/f'timeline-9-{rate:.2f}.json',item)
        d.expired(deadline)
        if (counts['laboratory_transitions']!=manifest['laboratory_transitions']
                or counts['actor_actions_started']!=counts['actor_evaluation_moves']
                or counts['actor_evaluation_moves']!=manifest['actor_evaluation_moves']):
            raise RuntimeError('diagnostic execution counts differ')
        result={'status':'complete','manifest':manifest,'actual_counts':counts,
            'wall_seconds':time.monotonic()-started,'results':results,'timelines':timelines}
        prior.atomic_json(args.output/'summary.json',result);return result
    except BaseException as error:
        prior.atomic_json(args.output/'failure.json',{'status':'incomplete','error':str(error),
            'completed_counts':counts,'possible_unreturned_actor_moves':counts['actor_actions_started']-counts['actor_evaluation_moves']})
        raise


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('pool','reference','private','output'):p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--wall-seconds',type=int,default=2400)
    print(json.dumps({'status':run(p.parse_args())['status']}))


if __name__=='__main__':main()
