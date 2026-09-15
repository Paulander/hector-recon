"""Bounded offline inspection of saved conditions and corner feature symmetry."""
import os
for key in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS'):
    os.environ[key] = '1'
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT/'src'), str(ROOT/'libs/recon-lite/src')]
from collections import defaultdict
import json
import math
import time
import chess
from recon_lite_chess.experiments import m1_retention as r


def run():
    deadline = time.monotonic()+180
    reference = r.prior.read(ROOT/'reports/autogrowth/development/M1_EXPLORATION_20260908.json')
    previous = r.prior.read(ROOT/'reports/autogrowth/development/M1_RETENTION_20260908.json')
    private = ROOT/'snapshots/autogrowth/m1-exploration-seeds479'
    pool = ROOT/'reports/autogrowth/runs/m1-coach-smoke-pool'
    counts = {'laboratory_transitions': 0}
    data = {name:r.f.laboratory_rows(r.prior.load_split(pool,name)[0], deadline=deadline, counts=counts)
            for name in ('train','validation')}
    target = data['validation'][6]
    all_rows = data['train']+data['validation']
    swap = (0,1,3,2,5,4,7,6,9,8,11,10,13,12,15,14)
    transforms = [((),False), ((chess.flip_horizontal,),False), ((chess.flip_vertical,),False),
        ((chess.flip_horizontal,chess.flip_vertical),False), ((chess.flip_diagonal,),True),
        ((chess.flip_diagonal,chess.flip_horizontal),True), ((chess.flip_diagonal,chess.flip_vertical),True),
        ((chess.flip_diagonal,chess.flip_horizontal,chess.flip_vertical),True)]
    transformed = 0
    for row in all_rows:
        r.d.expired(deadline)
        for fns, swapped in transforms:
            board = chess.Board(row['fen'])
            for fn in fns: board.apply_transform(fn)
            bindings,vectors = r.d.terminal_vectors(r.d.ChessFeaturePort(board))
            by_move = dict(zip(bindings,vectors))
            def square(s):
                bb = chess.BB_SQUARES[s]
                for fn in fns: bb=fn(bb)
                return chess.msb(bb)
            for move,vector in zip(row['bindings'],row['vectors']):
                m=chess.Move.from_uci(move); mapped=chess.Move(square(m.from_square),square(m.to_square)).uci()
                expected=tuple(vector[i] for i in swap) if swapped else tuple(vector)
                assert tuple(by_move[mapped])==expected
                transformed += 1
    raw = defaultdict(set)
    for row in all_rows:
        for v,win in zip(row['vectors'],row['wins']): raw[tuple(v)].add(win)
    actors=[]
    for event in (4096,4352,4480,6144):
        actor,_,sha=r.restore(reference,private,9,.25,event)
        before=r.prior.actor_digest(actor)
        rows=[]
        final_actor,_,_=r.restore(reference,private,9,.25,6144)
        final_choice=r.numerical_trace(final_actor,target)['chosen']
        win=target['wins'].index(1)
        rotated=chess.Board(target['fen']).transform(chess.flip_diagonal)
        opposite=r.f.laboratory_rows([rotated.fen()],deadline=deadline,counts=counts)[0]
        for label,example in [('target',target),('transposed',opposite)]:
            trace=r.numerical_trace(actor,example)
            winning=example['wins'].index(1)
            other=final_choice if label=='target' else next(i for i,v in enumerate(example['vectors'])
                if tuple(v)==tuple(target['vectors'][final_choice][j] for j in swap))
            conditions=[]
            for c in actor.conditions.values():
                wg=r.d.gate_value(c,example['vectors'][winning]); lg=r.d.gate_value(c,example['vectors'][other])
                conditions.append({'id':c.identity,'operator':c.operator,'atoms':c.atoms,'born':c.born,
                    'weight':float(c.weight),'win_gate':wg,'other_gate':lg,'contribution':float(c.weight)*(wg-lg)})
            rows.append({'label':label,'fen':example['fen'],'win':example['bindings'][winning],
                'other':example['bindings'][other],'chosen':example['bindings'][trace['chosen']],
                'won':example['wins'][trace['chosen']], 'win_vector':example['vectors'][winning],
                'other_vector':example['vectors'][other],
                'margin':trace['scores'][winning]-trace['scores'][other],
                'conditions':conditions})
        masks=defaultdict(list)
        outcomes={name:[] for name in data}
        for name,examples in data.items():
            for i,example in enumerate(examples):
                trace=r.numerical_trace(actor,example);outcomes[name].append(example['wins'][trace['chosen']])
                for j,(mask,grade) in enumerate(zip(trace['matrix'],example['wins'])):
                    masks[tuple(mask)].append((name,i,example['bindings'][j],grade))
        conflicts=[v for v in masks.values() if len({x[3] for x in v})>1]
        if event in (4096,6144):
            expected=next(a for a in previous['run']['results'] if a['seed']==9 and a['exploration']==.25 and a['event']==event)
            assert all(outcomes[name]==expected['reports'][name]['outcomes'] for name in data)
        mirror_keys={(c.operator,tuple(sorted((swap[i],v) for i,v in c.atoms))) for c in actor.conditions.values()}
        mirror_count=sum((c.operator,c.atoms) in mirror_keys for c in actor.conditions.values())
        assert before==r.prior.actor_digest(actor)
        actors.append({'event':event,'sha256':sha,'live_conditions':len(actor.conditions),'pruned':actor.pruned,
            'conditions_with_transposed_definition_present':mirror_count,'examples':rows,
            'train_mates':sum(outcomes['train']),'development_mates':sum(outcomes['validation']),
            'mixed_reward_gate_patterns':len(conflicts),'mixed_reward_gate_example':conflicts[:2]})
    # Reconstruct just the block enclosing the first observed crossing. Do not
    # call act/observe or change the saved organism. Verify at its next boundary.
    start,_,_=r.restore(reference,private,9,.25,4352)
    stop,_,_=r.restore(reference,private,9,.25,4480)
    catalog={c.identity:c for c in (*stop.retired_conditions.values(),*stop.conditions.values())}
    deaths={c.identity:c.born+c.stats.relevance_stats.request_exposures for c in stop.retired_conditions.values()}
    w={i:float(c.weight) for i,c in start.conditions.items()};bias=float(start.bias)
    actions=[json.loads(line) for line in (private/'seed-9/exploration-0.25/training-actions.jsonl').read_text().splitlines()]
    win=target['wins'].index(1);loss=r.numerical_trace(final_actor,target)['chosen']
    contrast={i:r.d.gate_value(c,target['vectors'][win])-r.d.gate_value(c,target['vectors'][loss]) for i,c in catalog.items()}
    crossing=None
    for item in actions:
        if not 4352<=item['event']<4480:continue
        row=data['train'][item['pool_index']]; v=row['vectors'][row['bindings'].index(item['action'])]
        active=[i for i in w if r.d.gate_value(catalog[i],v)]
        prediction=math.fsum([bias,*(w[i] for i in active)])
        delta=start.config.learning_rate*(item['reward']-prediction)/(1+len(active))
        margin_before=math.fsum(w[i]*contrast[i] for i in w)
        detail=[{'id':i,'weight_before':w[i],'target_contrast':contrast[i],
                 'margin_delta':delta*contrast[i],'atoms':catalog[i].atoms,'operator':catalog[i].operator} for i in active]
        bias+=delta
        for i in active:w[i]+=delta
        completed=item['event']+1
        removed=[i for i in w if deaths.get(i)==completed]
        for i in removed:del w[i]
        born=[i for i,c in catalog.items() if c.born==completed]
        for i in born:w[i]=0.
        after=math.fsum(w[i]*contrast[i] for i in w)
        if item['event']==4378:
            crossing={'event':item['event'],'training_row':item['pool_index'],'fen':row['fen'],
                'action':item['action'],'reward':item['reward'],'feature_vector':v,'prediction':prediction,
                'active_count':len(active),'delta':delta,'margin_before':margin_before,'margin_after':after,
                'removed':removed,'born':born,'conditions':detail}
    assert set(w)==set(stop.conditions)
    error=max([abs(bias-float(stop.bias)),*(abs(w[i]-float(c.weight)) for i,c in stop.conditions.items())])
    assert error<1e-10 and crossing['margin_before']>0>crossing['margin_after']
    result={'schema':'m1_corner_mechanism.v1','source_commit':'6b464f0bf924befe08097ae288c41746211ce2b3',
        'source_hashes':{str(p.relative_to(ROOT)):r.prior.sha(p) for p in [ROOT/'src/recon_lite_chess/coach/terminal.py',ROOT/'src/recon_lite_hector/learning/terminal_development.py']},
        'training_moves':0,'learner_update_calls':0,'laboratory_transitions':counts['laboratory_transitions'],
        'symmetry_action_vectors_checked':transformed,'raw_vectors':len(raw),
        'raw_vectors_with_conflicting_reward':sum(len(x)>1 for x in raw.values()),
        'actors':actors,'first_crossing':crossing,'block_weight_reconstruction_error':error,
        'feature_names':[c.name for c in r.d.ChessFeaturePort.schema],'seconds':time.monotonic()-(deadline-180)}
    output=ROOT/'reports/autogrowth/development/M1_CORNER_MECHANISM_20260909.json'
    r.prior.atomic_json(output,result)
    print(json.dumps({k:v for k,v in result.items() if k not in ('actors','first_crossing','feature_names','source_hashes')}))
    print(json.dumps({'actors':[{k:v for k,v in a.items() if k not in ('examples','mixed_reward_gate_example')} for a in actors], 'crossing':crossing}))

if __name__=='__main__': run()
