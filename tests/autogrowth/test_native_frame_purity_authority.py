from __future__ import annotations
from collections import defaultdict
import pickle
import chess
import pytest
from recon_lite import ChildResponse, FrameContext, FrameKind
from recon_lite_hector.nodes import StemCellState, StemCellTerminal
from recon_lite_chess.autogrowth.native_authority_handover import (
    ChildQuery, NativeHandoverGenome, NativeR0Organism,
)
from recon_lite_chess.autogrowth.native_authority_lab import (
    NativeAuthorityLabConfig, load_retired_r0_build,
)
from recon_lite_chess.autogrowth.native_child_availability import (
    FailClosedNativeHandoverGenome,
)
from recon_lite_chess.autogrowth.native_competence_envelope import (
    AvailabilityState, CompetenceContextCell, GraphNativeCompetenceEnvelope,
    NativeR0CompetenceOrganism,
)
import recon_lite_chess.autogrowth.native_competence_envelope_experiment as experiment

SYNTHETIC_PARENT="8/8/8/8/4K3/8/6R1/7k w - - 0 1"

@pytest.fixture(scope="module")
def build():
    return load_retired_r0_build(NativeAuthorityLabConfig())

def _frame(frame_id:str,fen:str)->FrameContext:
    return FrameContext(frame_id,FrameKind.VIRTUAL,values={"board":chess.Board(fen)})

def _query(available:bool,frame_id:str)->ChildQuery:
    return ChildQuery(
        ChildResponse(
            child_id="synthetic_grounded_child",confirmed=available,
            policy_response=True,available=available,
            expected_value=0.8 if available else 0.0,uncertainty=0.1,
            grounded=True,grounding_source="synthetic_real_outcomes",
        ),
        None,frame_id,0,(),
    )

def test_one_real_r0_query_preserves_every_persistent_component(build) -> None:
    organism=build.organism
    board=chess.Board(build.pools.r0_train[0])
    before=organism.persistent_state_audit()
    organism.emit_action(board)
    after=organism.persistent_state_audit()
    assert after==before
    assert after["topology_sha256"]==before["topology_sha256"]
    assert after["weights_sha256"]==before["weights_sha256"]
    assert after["credit_sha256"]==before["credit_sha256"]
    assert after["lifecycle_sha256"]==before["lifecycle_sha256"]
    assert after["exact_state_sha256"]==before["exact_state_sha256"]
    assert after["serialized_state_sha256"]==before["serialized_state_sha256"]

def test_repeated_and_permuted_frames_have_identical_actions_and_responses(build) -> None:
    organism=build.organism
    fens=tuple(build.pools.r0_train[:3])
    def evaluate(order):
        session=organism.dream_session()
        try:
            return {
                index:session.request(_frame(f"order:{index}",fens[index]))
                for index in order
            }
        finally:
            session.close()
    first=evaluate((0,1,2)); repeated=evaluate((0,1,2)); permuted=evaluate((2,0,1))
    for index in range(3):
        assert first[index].actuation==repeated[index].actuation==permuted[index].actuation
        assert first[index].response==repeated[index].response==permuted[index].response

def test_one_virtual_successor_cannot_contaminate_another(build) -> None:
    organism=build.organism
    fens=tuple(build.pools.r0_train[:2])
    session=organism.dream_session()
    try:
        first=session.request(_frame("a-first",fens[0]))
        session.request(_frame("b-middle",fens[1]))
        first_again=session.request(_frame("a-again",fens[0]))
    finally:
        session.close()
    assert first.actuation==first_again.actuation
    assert first.response==first_again.response

def test_serialized_competence_organism_passes_directly_to_query_child_slots(
    build,monkeypatch
) -> None:
    wrapper=NativeR0CompetenceOrganism(build.organism,GraphNativeCompetenceEnvelope())
    restored=NativeR0CompetenceOrganism.loads(wrapper.dumps())
    calls={"opened":0,"requested":0,"closed":0}
    class Session:
        def request(self,frame):
            calls["requested"]+=1
            return _query(False,frame.frame_id)
        def close(self):
            calls["closed"]+=1
    def open_session():
        calls["opened"]+=1
        return Session()
    monkeypatch.setattr(restored,"dream_session",open_session)
    slots,_frames=NativeHandoverGenome().query_child_slots(
        chess.Board(SYNTHETIC_PARENT),restored
    )
    assert slots
    assert calls["opened"]==1 and calls["requested"]>0 and calls["closed"]==1

def _synthetic_slots(board:chess.Board,available_action:str):
    slots={}; frames={}
    for action in sorted(board.legal_moves,key=lambda move:move.uci()):
        after=board.copy(stack=False); after.push(action); rows=[]
        for index,reply in enumerate(sorted(after.legal_moves,key=lambda move:move.uci())):
            successor=after.copy(stack=False); successor.push(reply)
            frame_id=f"{action.uci()}:{reply.uci()}"
            frames[(action.uci(),index)]=FrameContext(
                frame_id,FrameKind.VIRTUAL,values={"board":successor}
            )
            rows.append(_query(action.uci()==available_action,frame_id))
        slots[action.uci()]=tuple(rows)
    return slots,frames

def test_laboratory_injected_synthetic_slots_change_handover_upper_bound() -> None:
    board=chess.Board(SYNTHETIC_PARENT)
    empty_slots,frames=_synthetic_slots(board,"")
    fallback=FailClosedNativeHandoverGenome().decide_from_available_slots(
        board,empty_slots,frames
    ).actuation.move_uci
    by_replies=defaultdict(list)
    for action,rows in empty_slots.items():
        if rows: by_replies[len(rows)].append(action)
    pair=next(actions for actions in by_replies.values() if len(actions)>=2)
    target=next(action for action in pair if action!=fallback)
    shuffled_target=next(action for action in pair if action!=target)
    envelope=GraphNativeCompetenceEnvelope()
    stem=StemCellTerminal("synthetic_context")
    stem.state=StemCellState.MATURE
    cell=CompetenceContextCell(
        cell_id="synthetic_context",members=("synthetic:target",),
        born_round=0,born_request_ordinal=0,stem_cell=stem,
        polarity=AvailabilityState.AVAILABLE,
        support=4,successes=4,success_lower_bound=0.6,uncertainty=0.4,
    )
    envelope.cells[cell.cell_id]=cell; envelope.rebuild_graph()
    assert envelope.classify(
        ("synthetic:target",),policy_response=True
    ).state==AvailabilityState.AVAILABLE
    connected_slots,frames=_synthetic_slots(board,target)
    shuffled_slots,_=_synthetic_slots(board,shuffled_target)
    genome=FailClosedNativeHandoverGenome()
    connected=genome.decide_from_available_slots(board,connected_slots,frames)
    disconnected=genome.decide_from_available_slots(
        board,connected_slots,frames,disconnected=True
    )
    shuffled=genome.decide_from_available_slots(board,shuffled_slots,frames)
    assert connected.selection_mode=="exploit"
    assert connected.actuation.move_uci==target
    assert disconnected.actuation.move_uci!=target
    assert shuffled.actuation.move_uci!=target

def test_connected_wrapper_path_cannot_use_experiment_response_injection(
    build,monkeypatch
) -> None:
    wrapper=NativeR0CompetenceOrganism(build.organism,GraphNativeCompetenceEnvelope())
    class Session:
        def request(self,frame):
            return _query(False,frame.frame_id)
        def close(self):
            pass
    monkeypatch.setattr(wrapper,"dream_session",lambda:Session())
    monkeypatch.setattr(
        experiment,"response_with_availability",
        lambda *_args,**_kwargs:(_ for _ in ()).throw(
            AssertionError("connected arm used laboratory injection")
        ),
    )
    result=experiment._connected_wrapper_handover(
        build.organism,wrapper,chess.Board(SYNTHETIC_PARENT)
    )
    assert result["selection_route"]=="graph_owned_fallback"


def test_scheduler_telemetry_cannot_change_inference(build) -> None:
    organism=pickle.loads(pickle.dumps(build.organism))
    board=chess.Board(build.pools.r0_train[0])
    baseline=organism.emit_action(board)
    for key,value in tuple(organism.graph.scheduler_stats.items()):
        if key!="indexed_scheduler_used" and isinstance(value,(int,float)):
            organism.graph.scheduler_stats[key]=10**9
    organism.graph.runtime_choice_count=10**9
    assert organism.emit_action(board)==baseline

def test_r0_serialization_and_load_normalize_transient_runtime(build) -> None:
    organism=pickle.loads(pickle.dumps(build.organism))
    node=next(iter(organism.graph.graph.nodes.values()))
    node.state=__import__("recon_lite").NodeState.CONFIRMED
    node.tick_entered=77
    node.activation.value=0.75
    organism.graph.scheduler_stats["formal_ticks_run"]=99
    organism.graph.runtime_choice_count=88
    restored=pickle.loads(pickle.dumps(organism))
    restored_node=restored.graph.graph.nodes[node.nid]
    assert restored_node.state==__import__("recon_lite").NodeState.INACTIVE
    assert restored_node.tick_entered==-1
    assert restored_node.activation.value==0.0
    assert restored.graph.scheduler_stats["formal_ticks_run"]==0
    assert restored.graph.runtime_choice_count==0
