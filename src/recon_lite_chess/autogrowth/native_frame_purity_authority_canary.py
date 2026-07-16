"""Admission-only frame-purity and competence-authority closure canary."""
from __future__ import annotations
from collections import defaultdict
from dataclasses import dataclass
import hashlib,json,random
from pathlib import Path
from time import perf_counter
from typing import Any,Mapping
import chess
from recon_lite import ChildResponse,FrameContext,FrameKind
from recon_lite_hector.nodes import StemCellState,StemCellTerminal
from .native_authority_handover import ChildQuery,NativeHandoverGenome
from .native_authority_lab import NativeAuthorityLabConfig,load_retired_r0_build
from .native_child_availability import FailClosedNativeHandoverGenome,observe_query_completion
from .native_competence_envelope import (
    AvailabilityState,CompetenceContextCell,GraphNativeCompetenceEnvelope,
    NativeR0CompetenceOrganism,evidence_key,extract_active_competence_signals,
)
from .native_competence_envelope_experiment import EXPECTED,_hash_json,_hash_list

OUTPUT="reports/autogrowth/native_authority/native_frame_purity_competence_authority_closure.json"
PERMUTATION_SEED=2026071701
SYNTHETIC_PARENT="8/8/8/8/4K3/8/6R1/7k w - - 0 1"

def run_native_frame_purity_authority_canary()->Mapping[str,Any]:
    started=perf_counter()
    build=load_retired_r0_build(NativeAuthorityLabConfig())
    organism=build.organism; pools=build.pools
    tape=[{"subgroup":"r0_train","fen":fen} for fen in pools.r0_train]+[
        {"subgroup":"train_decoy","fen":fen} for fen in pools.gate_train_decoys
    ]
    random.Random(2026071601).shuffle(tape)
    legacy=[{"class":"positive" if x["subgroup"]=="r0_train" else "failure","fen":x["fen"]} for x in tape]
    if _hash_json(legacy)!=EXPECTED["tape"]: raise RuntimeError("admission tape changed")
    initial=organism.persistent_state_audit()
    real_rows=[_real_observation(organism,item,index) for index,item in enumerate(tape)]
    after_real=organism.persistent_state_audit()
    counts=_counts(real_rows)
    evidence_keys=[row["evidence_key"] for row in real_rows]

    natural=_virtual_pass(organism,tape,tuple(range(64)),"natural")
    repeated=_virtual_pass(organism,tape,tuple(range(64)),"repeated")
    permutation=list(range(64)); random.Random(PERMUTATION_SEED).shuffle(permutation)
    permuted=_virtual_pass(organism,tape,tuple(permutation),"permuted")
    frame_invariance=_compare_virtual_passes(natural,repeated,permuted)
    after_virtual=organism.persistent_state_audit()

    wrapper=NativeR0CompetenceOrganism(
        organism,GraphNativeCompetenceEnvelope()
    )
    restored=NativeR0CompetenceOrganism.loads(wrapper.dumps())
    wrapper_before=restored.persistent_state_audit()
    synthetic_parent=chess.Board(SYNTHETIC_PARENT)
    wrapper_slots,_wrapper_frames=NativeHandoverGenome().query_child_slots(
        synthetic_parent,restored
    )
    wrapper_after=restored.persistent_state_audit()
    wrapper_authority={
        "serialized_wrapper_passed_directly":True,
        "query_count":sum(len(rows) for rows in wrapper_slots.values()),
        "all_unlearned_responses_unavailable":all(
            not query.response.available
            for rows in wrapper_slots.values() for query in rows
        ),
        "persistent_state_identical":wrapper_before==wrapper_after,
        "experiment_response_injection_used":False,
    }
    synthetic=_synthetic_causal_canary()

    final=organism.persistent_state_audit()
    gates={
        "unique_evidence_64":len(set(evidence_keys))==64,
        "both_outcome_classes":counts["overall"]["success"]>0 and counts["overall"]["failure"]>0,
        "at_least_12_successes":counts["overall"]["success"]>=12,
        "at_least_12_failures":counts["overall"]["failure"]>=12,
        "zero_fabricated_reward":all(not row["fabricated_reward"] for row in real_rows),
        "real_tape_persistent_identity":initial==after_real,
        "virtual_order_invariance":frame_invariance["passed"],
        "virtual_persistent_identity":after_real==after_virtual==final,
        "direct_wrapper_authority":all((
            wrapper_authority["serialized_wrapper_passed_directly"],
            wrapper_authority["persistent_state_identical"],
            not wrapper_authority["experiment_response_injection_used"],
        )),
        "synthetic_envelope_causal":synthetic["passed"],
        "zero_competence_growth":len(wrapper.envelope.cells)==0 and len(restored.envelope.cells)==0,
    }
    result={
        "schema_version":"native_frame_purity_competence_authority_closure.v1",
        "engineering_only":True,
        "source_abort_preserved":"1501a18",
        "competence_package_rerun":False,
        "fresh_data_touched":False,
        "validation_touched":False,
        "regression_touched":False,
        "retired_successors_touched":False,
        "r1_learning_updates":0,
        "competence_growth_events":0,
        "tape":{"count":64,"legacy_sha256":EXPECTED["tape"],"permutation_seed":PERMUTATION_SEED,"permutation_sha256":_hash_list(permutation)},
        "counts_before_gates":counts,
        "real_rows":real_rows,
        "persistent_state":{"initial":initial,"after_real":after_real,"after_virtual":after_virtual,"final":final},
        "frame_order_invariance":frame_invariance,
        "direct_wrapper_authority":wrapper_authority,
        "synthetic_mature_envelope":synthetic,
        "gates":gates,
        "passed":all(gates.values()),
        "duration_seconds":perf_counter()-started,
        "next_action":"stop_for_external_review",
    }
    path=Path(OUTPUT); path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    return result

def _real_observation(organism,item,index):
    board=chess.Board(item["fen"]); act=organism.emit_action(board)
    if act is None: raise RuntimeError("R0 emitted no admission action")
    signals=extract_active_competence_signals(organism,board,act)
    raw=ChildQuery(
        ChildResponse(
            organism.provenance.child_id,False,0.0,
            organism.provenance.uncertainty,organism.provenance.grounded,
            organism.provenance.grounding_source,
            policy_response=True,available=False,
        ),
        act,f"admission-purity:{index}",0,(),
    )
    observed=observe_query_completion(organism,board.copy(stack=False),raw)
    return {
        "index":index,"subgroup":item["subgroup"],"fen":item["fen"],
        "action":act.move_uci,
        "evidence_key":evidence_key(
            board,act,organism.provenance.completion_terminal_kind
        ),
        "active_signal_count":len(signals),
        "success":observed.completion_confirmed,
        "failure":not observed.completion_confirmed,
        "observed_terminal":observed.observed_terminal,
        "local_competence_failure":observed.local_competence_failure,
        "fabricated_reward":observed.fabricated_terminal_reward,
    }

def _counts(rows):
    groups={"overall":list(rows)}
    for subgroup in ("r0_train","train_decoy"):
        groups[subgroup]=[row for row in rows if row["subgroup"]==subgroup]
    return {
        name:{
            "total":len(items),
            "success":sum(row["success"] for row in items),
            "failure":sum(row["failure"] for row in items),
            "response_present_failure":sum(row["failure"] for row in items),
        }
        for name,items in groups.items()
    }

def _virtual_pass(organism,tape,order,label):
    session=organism.dream_session(); rows={}
    try:
        for index in order:
            frame=FrameContext(
                f"{label}:{index}",FrameKind.VIRTUAL,
                values={"board":chess.Board(tape[index]["fen"])},
            )
            query=session.request(frame)
            rows[index]={
                "action":None if query.actuation is None else query.actuation.move_uci,
                "actuator_identity":None if query.actuation is None else query.actuation.actuator_identity,
                "response":query.response.to_dict(),
                "persistent_mutation_count":query.persistent_mutation_count,
            }
    finally:
        session.close()
    return rows

def _compare_virtual_passes(natural,repeated,permuted):
    rows=[]; passed=True
    for index in range(64):
        equal=natural[index]==repeated[index]==permuted[index]
        passed=passed and equal
        rows.append({
            "index":index,"equal":equal,
            "action":natural[index]["action"],
            "response":natural[index]["response"],
        })
    return {
        "evaluated_frames":64,
        "natural_equals_repeated":all(natural[i]==repeated[i] for i in range(64)),
        "natural_equals_permuted":all(natural[i]==permuted[i] for i in range(64)),
        "cross_frame_contamination_count":sum(not row["equal"] for row in rows),
        "rows":rows,"passed":passed,
    }

def _query(available,frame_id):
    return ChildQuery(
        ChildResponse(
            "synthetic_grounded_child",available,
            0.8 if available else 0.0,0.1,True,
            "synthetic_observed_outcomes",
            policy_response=True,available=available,
        ),
        None,frame_id,0,(),
    )

def _synthetic_slots(board,target):
    slots={}; frames={}
    for action in sorted(board.legal_moves,key=lambda m:m.uci()):
        after=board.copy(stack=False); after.push(action); queries=[]
        for index,reply in enumerate(sorted(after.legal_moves,key=lambda m:m.uci())):
            successor=after.copy(stack=False); successor.push(reply)
            frame_id=f"{action.uci()}:{reply.uci()}"
            frames[(action.uci(),index)]=FrameContext(
                frame_id,FrameKind.VIRTUAL,values={"board":successor}
            )
            queries.append(_query(action.uci()==target,frame_id))
        slots[action.uci()]=tuple(queries)
    return slots,frames

def _synthetic_causal_canary():
    board=chess.Board(SYNTHETIC_PARENT)
    empty,frames=_synthetic_slots(board,"")
    genome=FailClosedNativeHandoverGenome()
    fallback=genome.decide_from_available_slots(
        board,empty,frames
    ).actuation.move_uci
    strata=defaultdict(list)
    for action,rows in empty.items():
        if rows: strata[len(rows)].append(action)
    pair=next(actions for actions in strata.values() if len(actions)>=2)
    target=next(action for action in pair if action!=fallback)
    shuffled_target=next(action for action in pair if action!=target)
    envelope=GraphNativeCompetenceEnvelope()
    stem=StemCellTerminal("synthetic_context"); stem.state=StemCellState.MATURE
    envelope.cells["synthetic_context"]=CompetenceContextCell(
        "synthetic_context",("synthetic:target",),0,0,stem,
        polarity=AvailabilityState.AVAILABLE,support=4,successes=4,
        success_lower_bound=0.6,uncertainty=0.4,
    )
    envelope.rebuild_graph()
    connected_slots,frames=_synthetic_slots(board,target)
    shuffled_slots,_=_synthetic_slots(board,shuffled_target)
    connected=genome.decide_from_available_slots(board,connected_slots,frames)
    disconnected=genome.decide_from_available_slots(
        board,connected_slots,frames,disconnected=True
    )
    shuffled=genome.decide_from_available_slots(board,shuffled_slots,frames)
    gates={
        "mature_envelope_confirms":envelope.classify(
            ("synthetic:target",),policy_response=True
        ).state==AvailabilityState.AVAILABLE,
        "connected_selects_target":connected.selection_mode=="exploit" and connected.actuation.move_uci==target,
        "disconnected_fails_target":disconnected.actuation.move_uci!=target,
        "shuffled_fails_target":shuffled.actuation.move_uci!=target,
    }
    return {
        "target_action":target,"fallback_action":fallback,
        "shuffled_target":shuffled_target,
        "connected_action":connected.actuation.move_uci,
        "disconnected_action":disconnected.actuation.move_uci,
        "shuffled_action":shuffled.actuation.move_uci,
        "gates":gates,"passed":all(gates.values()),
    }
