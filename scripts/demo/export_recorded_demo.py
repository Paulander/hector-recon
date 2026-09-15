"""Read-only presentation export. No training, checkpoint writes or policy edits."""
import copy
import gzip
import hashlib
import json
from pathlib import Path
import pickle
import signal

import chess
from recon_lite.graph import LinkType
from recon_lite_hector.learning import terminal_development as td
from recon_lite_chess.coach.terminal import ChessFeaturePort
from recon_lite_chess.coach.pools import load_split
from recon_lite_chess.experiments.ordinary_m1 import actor_digest, sources

ROOT = Path(__file__).resolve().parents[2]
PRIVATE = Path('/workspace/scratch/63cf1a75c465/hector-recon/snapshots/autogrowth/m1-long-play-seeds4-9')
OUT = Path('/workspace/scratch/42ed9c9c2a4a/recon-demo')

def main():
    signal.signal(signal.SIGALRM, lambda *_: (_ for _ in ()).throw(TimeoutError('export budget')))
    signal.alarm(120)
    ref = json.loads((ROOT/'reports/autogrowth/development/M1_LONG_PLAY_20260907.json').read_text())
    assert ref['run']['manifest']['source'] == sources()
    record = next(r for r in ref['run']['results'] if r['seed'] == 7)
    snapshots = []
    for entry in ref['private_checkpoint_index']:
        if not entry['path'].startswith('seed-7/'):
            continue
        path = PRIVATE/entry['path']
        assert hashlib.sha256(path.read_bytes()).hexdigest() == entry['sha256']
        with gzip.open(path, 'rb') as f:
            payload = pickle.load(f)
        a = payload['state']['organism']
        assert a.completed == payload['state']['next_event'] and not a.pending
        assert payload['source'] == ref['run']['manifest']['source']
        snapshots.append((a.completed, a, entry))
    snapshots.sort(key=lambda x: x[0])
    final_sha = record['milestones']['4096']['checkpoint_sha256']
    actor = next(a for _, a, e in snapshots if e['sha256'] == final_sha)
    catalog = {c.identity: c for c in (*actor.retired_conditions.values(), *actor.conditions.values())}
    deaths = {c.identity: c.born+c.stats.relevance_stats.request_exposures for c in actor.retired_conditions.values()}
    definitions = []
    for cid,c in sorted(catalog.items()):
        death = deaths.get(cid, 1000000000)
        if death <= 1280:
            continue
        definitions.append(dict(id=cid, born=c.born, death=death, op=c.operator,
            atoms=[[i,int(v)] for i,v in c.atoms], weight=float(c.weight)))
    for event,a,_ in snapshots:
        assert {d['id'] for d in definitions if d['born']<=event<d['death']} == set(a.conditions)
    # Allocate stable display positions; reuse a visual seat only after retirement.
    seats = [-1]*64
    for d in sorted(definitions,key=lambda d:(d['born'],d['id'])):
        seat = next(i for i,t in enumerate(seats) if t<=max(1280,d['born']))
        d['seat']=seat; seats[seat]=d['death']
    milestones = [{'event':1280,'mates':record['inherited_evaluation']['mates']}]
    milestones += [{'event':int(k),'mates':v['result']['evaluation']['mates']} for k,v in record['milestones'].items()]
    # Choose a geometric illustration from the already-open development split.
    fens, pool_sha = load_split(Path('/workspace/scratch/63cf1a75c465/hector-recon/reports/autogrowth/runs/m1-coach-smoke-pool'),'validation')
    row,fen = next((i,f) for i,f in enumerate(fens) if
        chess.square_file(chess.Board(f).king(False)) in (0,7) and
        chess.square_rank(chess.Board(f).king(False)) in (0,7) and
        abs(chess.square_file(chess.Board(f).king(True))-chess.square_file(chess.Board(f).king(False))) == 2 and
        abs(chess.square_rank(chess.Board(f).king(True))-chess.square_rank(chess.Board(f).king(False))) == 1)
    baseline = copy.deepcopy(actor); before = actor_digest(baseline)
    board = chess.Board(fen)
    normal = baseline.act(ChessFeaturePort(board),event_id=0,learn=False)
    assert actor_digest(baseline)==before
    observed=[]
    original = td.FormalReConEngine
    class Recorder(original):
        def __init__(self,*args,**kwargs):
            kwargs['record_trace']=True
            super().__init__(*args,**kwargs)
            observed.append(self)
    traced = copy.deepcopy(actor)
    trace_before = actor_digest(traced)
    trace_board = chess.Board(fen)
    executions=[]
    class ObservedPort(ChessFeaturePort):
        def execute(self,binding):
            executions.append(dict(tick=observed[-1].tick,action=binding))
            return super().execute(binding)
    port = ObservedPort(trace_board)
    td.FormalReConEngine=Recorder
    try:
        chosen = traced.act(port,event_id=0,learn=False)
    finally:
        td.FormalReConEngine=original
    assert chosen==normal and trace_board.fen()==board.fen()
    assert actor_digest(traced)==trace_before
    assert len(observed)==1
    engine=observed[0]
    selected=traced.graph.nodes['action_choice'].meta['choice_selected_child']
    slot=int(selected.split(':')[1])
    bindings=ChessFeaturePort(chess.Board(fen)).bindings()
    visible={'action_choice','catalog_root','catalog','execute','actuator'}
    visible |= {f'option:{i}' for i in range(len(bindings))}
    visible |= {nid for nid in traced.graph.nodes if nid.startswith((f'gate:{slot}:',f'read:{slot}:',f'bias:{slot}',f'explore:{slot}'))}
    nodes=[]
    for nid in sorted(visible):
        n=traced.graph.nodes[nid]
        item=dict(id=nid,type=n.ntype.name if hasattr(n,'ntype') else n.kind.name,meta={})
        for key in ('atom','condition_id','confirm_policy','reading','emitted'):
            if key in n.meta: item['meta'][key]=n.meta[key]
        if nid.startswith('option:'): item['binding']=bindings[int(nid.split(':')[1])]
        nodes.append(item)
    frames=[]
    for frame in engine.trace:
        frames.append({**frame,'messages':[m for m in frame['messages'] if m['src'] in visible and m['dst'] in visible],
            **{k:{nid:v for nid,v in frame[k].items() if nid in visible} for k in ('states_before','states_after','activations')}})
    assert len(executions)==1 and executions[0]['action']==chosen
    execution_tick=executions[0]['tick']
    data=dict(schema='recon.presentation.v1',seed=7,start=1280,end=4096,
        definitions=definitions,coordinates=[dict(name=c.name,values=c.values) for c in actor.schema],
        milestones=milestones,verified_checkpoints=len(snapshots),
        checkpoint_counts=[dict(event=e,nodes=len(a.graph.nodes),conditions=len(a.conditions)) for e,a,_ in snapshots],
        trace=dict(fen=fen,after_fen=board.fen(),row=row,action=chosen,mate=board.is_checkmate(),
            selected=selected,slot=slot,nodes=nodes,frames=frames,execution_tick=execution_tick,
            edges=[dict(src=e.src,dst=e.dst,type=e.ltype.name) for e in traced.graph.edges if e.src in visible and e.dst in visible],
            conditions=[dict(id=c.identity,op=c.operator,atoms=c.atoms,weight=float(c.weight)) for c in actor.conditions.values()],
            pieces=[dict(square=chess.square_name(s),piece=p.symbol()) for s,p in chess.Board(fen).piece_map().items()]),
        provenance=dict(checkpoint_sha256=final_sha,pool_sha256=pool_sha,
            checkpoints=[e for _,_,e in snapshots],new_training_moves=0,frozen_demonstration_moves=2,
            trace_matches_uninstrumented=True,learned_state_unchanged=True,
            growth='Birth times and retirement exposure counts from saved conditions; live sets verified at every saved checkpoint.',
            view='Growth shares definitions across action bindings; execution shows all options and the selected option subtree. Other option subtrees are omitted.',
            timing='Recorded two-phase formal ticks; animated message travel is presentation timing, not extra runtime microticks.',
            limitation='Random condition proposal and supplied pruning/credit laws. Not autonomous graph-controlled development.'))
    OUT.mkdir(exist_ok=True)
    (OUT/'demo-data.json').write_text(json.dumps(data,separators=(',',':')))
    print(json.dumps(dict(definitions=len(definitions),checkpoints=len(snapshots),row=row,fen=fen,action=chosen,mate=board.is_checkmate(),ticks=len(frames),nodes=len(nodes),execution_tick=execution_tick)))

if __name__=='__main__': main()
