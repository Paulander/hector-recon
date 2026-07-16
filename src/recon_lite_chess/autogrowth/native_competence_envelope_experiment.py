"""Frozen touched-data competence-envelope engineering package."""
from __future__ import annotations
from collections import defaultdict
from dataclasses import dataclass, replace
import hashlib, json, pickle, random
from pathlib import Path
from time import perf_counter
from typing import Any, Mapping, Sequence
import chess
from recon_lite import ChildResponse
from recon_lite_hector.nodes import StemCellState
from .native_authority_handover import ChildQuery, NativeHandoverGenome, native_authority_tripwires
from .native_authority_lab import NativeAuthorityLabConfig, load_retired_r0_build
from .native_child_availability import FailClosedNativeHandoverGenome, observe_query_completion, observe_real_child, response_with_availability
from .native_competence_envelope import (
    AvailabilityState, CompetenceContextCell, CompetenceEvidenceRecord,
    GraphNativeCompetenceEnvelope, GrowthProposal, GrowthRequestEmission,
    NativeR0CompetenceOrganism, evidence_key, extract_active_competence_signals,
)

PREREGISTRATION_COMMITS=("6e55baa","c8ce114","4ef6916")
EXPECTED={
"source_organism":"bb58b7d64bd3ab5b696713a7253555e051bd0e9fdef4637db7c27e7517495eaf",
"source_artifact":"c55a4097547713edb5d9ef27a250bbfac62fb9886d86afae87b387b72869c792",
"prior":"e946abccb4e846ca260f034174c6f440683155ebf17b617c0de8b2ae3a5baf2b",
"r0_train":"296ed4354ecf1830dec45911f8d95ee01a0e9618f19074efb862383eca6c0e04",
"gate_train_decoys":"5fa00a68f2651cba6da86d3fe6585bf04baa16d7dc53b32064619539ec48d74d",
"r0_validation":"2100368431445bf95f045f4387858f662c4510320b12a6907cdeca1d46022599",
"gate_validation_decoys":"196c5bfec16b1d5efa1f41d1a868ebf90f0401d5cc5b353c05cd4a204a5ab44f",
"r0_regression":"964c8d543e03cc6d756eb0f52218133e9af95fdb6c97dc9c0aff8b8e58858f69",
"gate_regression_decoys":"acdafa01d92b7ee77053de438168c828bbf94d5006cc6dfe5d0cf42299ee64e8",
"retired":"f52228d6b0be6a9e3bb9f47862e9fb50d076c40612bbeaecf7d1c80a463b055a",
"tape":"91a195b2feed4f59dad49437163af5c24588af9622cacaabe4ecf8270a84a3b2",
"outcome_perm":"501f16f2cce5cfff487152ed5a444ecadb7ebc76e29fdc032c9b6f016df90d0e",
"output_perm":"949bfd8d3ad8824f1e2f1bd905d66364c8ee90971e2d1ffde06c121fa742fc8d",
"random_perm":"d086d768512e1d3c92e66afbc1a25f53b3a51524902084ab278884dcb4b9237f",
"reply_derangement":"0c06d83276bd71c10343e005806905b70836c58043251d73f8e710c9f703e3a7",
}

@dataclass(frozen=True)
class CompetenceExperimentConfig:
    source_artifact:str="reports/autogrowth/native_from_scratch/r0_r1_balanced96_240_seed_20260719_compact.json"
    source_organism:str="snapshots/autogrowth/native_authority/r0_organism.pkl"
    build_report:str="reports/autogrowth/native_authority/r0_organism_build.json"
    prior:str="reports/autogrowth/native_authority/retired_r0_child_availability_diagnostic.json"
    output:str="reports/autogrowth/native_authority/touched_r0_competence_envelope_engineering.json"
    organism_output:str="snapshots/autogrowth/native_authority/r0_competence_envelope_touched.pkl"
    tape_seed:int=2026071601
    outcome_seed:int=2026071602
    output_seed:int=2026071603
    random_seed:int=2026071604
    reply_seed:int=2026071605

def run_touched_competence_envelope(config:CompetenceExperimentConfig|None=None)->Mapping[str,Any]:
    cfg=config or CompetenceExperimentConfig(); started=perf_counter()
    _verify_sources(cfg)
    build=load_retired_r0_build(NativeAuthorityLabConfig(source_artifact=cfg.source_artifact,organism_path=cfg.source_organism,build_report_path=cfg.build_report))
    p=build.pools; pool_hashes=_verify_pools(p)
    prior=json.loads(Path(cfg.prior).read_text()); retired_fens=[r["successor_fen"] for r in prior["successor_decomposition"]]
    if _hash_list(retired_fens)!=EXPECTED["retired"]: raise RuntimeError("retired order changed")
    tape=[{"class":"positive","fen":f} for f in p.r0_train]+[{"class":"failure","fen":f} for f in p.gate_train_decoys]
    random.Random(cfg.tape_seed).shuffle(tape)
    if _hash_json(tape)!=EXPECTED["tape"]: raise RuntimeError("event tape changed")
    r0_before=_digest_r0(build.organism)
    result={"schema_version":"touched_r0_competence_envelope.v1","development_only":True,"fresh_data_touched":False,"final_pool_touched":False,"r1_learning_updates":0,"confirmation_claim":False,"preregistration_commits":list(PREREGISTRATION_COMMITS),"source":{"expected":EXPECTED,"pool_hashes":pool_hashes},"stage":"admission","binding_boundary":None}
    with native_authority_tripwires() as tripwires:
        obs=[_observe(build.organism,x["fen"],x["class"],f"train:{i}") for i,x in enumerate(tape)]
        result["admission"]=_admission(obs)
        if not result["admission"]["passed"]: return _close(cfg,result,started,"evidence_admission",tripwires)
        records=tuple(x["evidence"] for x in obs)
        connected=GraphNativeCompetenceEnvelope(); connected.grow(records)
        perm=_permutation(64,cfg.outcome_seed)
        if _hash_list(perm)!=EXPECTED["outcome_perm"]: raise RuntimeError("outcome permutation changed")
        outcomes=[r.observed_completion for r in records]
        shuffled_records=tuple(replace(r,observed_completion=outcomes[perm[i]]) for i,r in enumerate(records))
        shuffled=GraphNativeCompetenceEnvelope(); shuffled.grow(shuffled_records)
        random_control,random_report=_random_control(records,connected,cfg.random_seed)
        result["training"]={"rows":[_artifact_observation(x) for x in obs],"connected":connected.to_manifest(),"outcome_shuffled":shuffled.to_manifest(),"random_composite":random_report}
        if not connected.cells: return _close(cfg,result,started,"topology_growth",tripwires)
        if not any(c.is_mature for c in connected.cells.values()): return _close(cfg,result,started,"lifecycle",tripwires)
        wrapper=NativeR0CompetenceOrganism(build.organism,connected)
        forbidden=(*p.r0_train,*p.gate_train_decoys,*p.r0_validation,*p.gate_validation_decoys,*p.r0_regression,*p.gate_regression_decoys,*retired_fens)
        result["serialization"]=_serialization(wrapper,cfg.organism_output,forbidden,records)
        if not all(result["serialization"][k] for k in ("parity","no_serialized_fen")): return _close(cfg,result,started,"stability",tripwires)
        before=_digest_envelope(connected)
        val_obs=_observe_pool(build.organism,p.r0_validation,p.gate_validation_decoys,"validation")
        val=_eval_arms(val_obs,connected,shuffled,random_control); val["zero_mutation"]=_digest_envelope(connected)==before
        val["gate"]={"fp_0_of_16":val["connected"]["confusion"]["fp"]==0,"tp_at_least_14":val["connected"]["confusion"]["tp"]>=14,"zero_mutation":val["zero_mutation"]}
        val["passed"]=all(val["gate"].values()); result["validation"]=val
        if not val["passed"]:
            result["r0_integrity"]=_integrity(build.organism,r0_before)
            return _close(cfg,result,started,"selectivity",tripwires,stage="closed_before_regression")
        before=_digest_envelope(connected)
        reg_obs=_observe_pool(build.organism,p.r0_regression,p.gate_regression_decoys,"regression")
        reg=_eval_arms(reg_obs,connected,shuffled,random_control); reg["zero_mutation"]=_digest_envelope(connected)==before
        comparison=_compare_controls(reg); combined=val["connected"]["confusion"]["tp"]+reg["connected"]["confusion"]["tp"]
        reg["control_comparison"]=comparison; reg["combined_positive"]=combined
        reg["gate"]={"fp_0_of_16":reg["connected"]["confusion"]["fp"]==0,"tp_at_least_14":reg["connected"]["confusion"]["tp"]>=14,"combined_at_least_29":combined>=29,"metrics_beat_controls":comparison["passed"],"zero_mutation":reg["zero_mutation"]}
        reg["passed"]=all(reg["gate"].values()); result["regression"]=reg
        if not reg["passed"]:
            boundary="abstention_collapse" if reg["connected"]["coverage"]==0 else "selectivity"
            result["r0_integrity"]=_integrity(build.organism,r0_before)
            return _close(cfg,result,started,boundary,tripwires,stage="closed_before_retired")
        before=_digest_envelope(connected)
        retired_obs=[_observe(build.organism,f,"retired",f"retired:{i}") for i,f in enumerate(retired_fens)]
        retired=_retired(build.organism,connected,shuffled,random_control,retired_obs,prior,cfg)
        retired["zero_mutation"]=_digest_envelope(connected)==before; result["retired"]=retired
        boundary=None if retired["passed"] else ("control_identification" if not retired["controls_identified"] else "retired_generalization")
        result["r0_retention"]={"completed":sum(x["completion"] for x in (*val_obs[:16],*reg_obs[:16])),"total":32}
        result["r0_integrity"]=_integrity(build.organism,r0_before)
        result["authority_tripwires"]=dict(tripwires)
    integrity={"r0_retention_32_of_32":result["r0_retention"]["completed"]==32,"r0_bit_identical":result["r0_integrity"]["bit_identical"],"serialization_parity":result["serialization"]["parity"],"no_serialized_fen":result["serialization"]["no_serialized_fen"],"zero_tripwires":all(v==0 for v in result["authority_tripwires"].values()),"nonzero_topology":bool(connected.cells),"zero_host_fallback":retired["zero_host_fallback"],"zero_dream_updates":retired["zero_dream_updates"]}
    result["integrity"]=integrity
    if boundary is None and not all(integrity.values()): boundary="stability"
    result["binding_boundary"]=boundary; result["passed"]=boundary is None; result["stage"]="passed_touched_engineering_stop_before_R1" if result["passed"] else "closed"
    result["next_action"]="request_external_fresh_freeze_do_not_run_R1" if result["passed"] else f"preserve_first_boundary:{boundary}"
    return _finalize(cfg,result,started)

def _observe(organism,fen:str,group:str,frame_id:str)->dict[str,Any]:
    board=chess.Board(fen); act=organism.emit_action(board)
    if act is None: raise RuntimeError("R0 emitted no action")
    signals=extract_active_competence_signals(organism,board,act)
    raw=ChildQuery(ChildResponse(organism.provenance.child_id,False,0.0,organism.provenance.uncertainty,organism.provenance.grounded,organism.provenance.grounding_source,policy_response=True,available=False),act,frame_id,0,())
    observed=observe_query_completion(organism,board.copy(stack=False),raw)
    terminal=organism.provenance.completion_terminal_kind
    record=CompetenceEvidenceRecord(evidence_key(board,act,terminal),signals,True,observed.completion_confirmed,act.actuator_identity,terminal)
    return {"fen":fen,"group":group,"evidence":record,"action":act.move_uci,"completion":observed.completion_confirmed,"terminal":observed.observed_terminal,"local_failure":observed.local_competence_failure,"fabricated_reward":observed.fabricated_terminal_reward}

def _artifact_observation(x):
    return {k:v for k,v in x.items() if k!="evidence"}|{"evidence_key":x["evidence"].evidence_key,"active_signal_ids":list(x["evidence"].active_signal_ids)}

def _admission(obs):
    pos=[x for x in obs if x["group"]=="positive"]; neg=[x for x in obs if x["group"]=="failure"]
    gates={"count_64":len(obs)==64,"positive_48_of_48":len(pos)==48 and all(x["completion"] for x in pos),"failure_16_of_16":len(neg)==16 and all(not x["completion"] for x in neg),"response_failures_at_least_12":sum(x["evidence"].policy_response and not x["completion"] for x in neg)>=12,"unique_keys_64":len({x["evidence"].evidence_key for x in obs})==64,"zero_fabricated_reward":all(not x["fabricated_reward"] for x in obs)}
    return {"gates":gates,"passed":all(gates.values()),"response_present_failures":sum(x["evidence"].policy_response and not x["completion"] for x in neg)}

def _observe_pool(organism,positive,negative,split):
    return [_observe(organism,f,"positive",f"{split}:p:{i}") for i,f in enumerate(positive)]+[_observe(organism,f,"negative",f"{split}:n:{i}") for i,f in enumerate(negative)]

def _eval_arms(obs,connected,shuffled,random_control):
    arms={"connected":_metrics_envelope(obs,connected),"outcome_shuffled":_metrics_envelope(obs,shuffled)}
    if random_control is not None: arms["random_composite"]=_metrics_envelope(obs,random_control)
    labels=[x["completion"] for x in obs]
    arms["constant_available"]=_constant(labels,1.0,True)
    arms["constant_unavailable"]=_constant(labels,0.0,False)
    arms["global_evidence"]=_constant(labels,0.75,True)
    return arms

def _metrics_envelope(obs,envelope):
    rows=[]
    for x in obs:
        c=envelope.classify(x["evidence"].active_signal_ids,policy_response=x["evidence"].policy_response)
        rows.append({"fen":x["fen"],"group":x["group"],"observed_completion":x["completion"],"state":c.state.value,"probability":c.probability,"uncertainty":c.uncertainty,"available_cell_ids":list(c.available_cell_ids),"refuted_cell_ids":list(c.refuted_cell_ids),"formal_available":c.formal_available,"formal_refuted":c.formal_refuted})
    return _metrics(rows)

def _constant(labels,p,available):
    state=AvailabilityState.AVAILABLE.value if available else AvailabilityState.REFUTED.value
    value=_metrics([{"observed_completion":y,"state":state,"probability":p,"uncertainty":0.0} for y in labels]); value.pop("rows",None); return value

def _metrics(rows):
    tp=fp=tn=fn=available=0; pe=[]; ne=[]
    for r in rows:
        y=bool(r["observed_completion"]); a=r["state"]==AvailabilityState.AVAILABLE.value; e=(float(r["probability"])-float(y))**2
        (pe if y else ne).append(e); available+=int(a)
        if y and a: tp+=1
        elif y: fn+=1
        elif a: fp+=1
        else: tn+=1
    pb=sum(pe)/len(pe) if pe else None; nb=sum(ne)/len(ne) if ne else None
    return {"confusion":{"tp":tp,"fp":fp,"tn":tn,"fn":fn},"balanced_brier":None if pb is None or nb is None else (pb+nb)/2,"positive_brier":pb,"negative_brier":nb,"selective_risk":None if not available else fp/available,"coverage":available/max(1,len(rows)),"available_count":available,"uncertainty":{"mean":sum(float(r["uncertainty"]) for r in rows)/max(1,len(rows)),"values":[float(r["uncertainty"]) for r in rows]},"rows":list(rows)}

def _compare_controls(reg):
    connected=reg["connected"]; comparisons={}; passed=True
    for name in ("constant_available","constant_unavailable","global_evidence","outcome_shuffled"):
        c=reg[name]; b=connected["balanced_brier"]<c["balanced_brier"]
        if c["selective_risk"] is None: risk=connected["coverage"]>c["coverage"]
        elif connected["selective_risk"] is None: risk=False
        else: risk=connected["selective_risk"]<c["selective_risk"] or (connected["selective_risk"]==c["selective_risk"] and connected["coverage"]>c["coverage"])
        comparisons[name]={"balanced_brier_better":b,"selective_risk_or_coverage_better":risk}; passed=passed and b and risk
    return {"controls":comparisons,"passed":passed}

def _random_control(records,connected,seed):
    targets=[c for c in connected.cells.values() if c.stem_cell.is_composition]
    if not targets: return None,None
    control=GraphNativeCompetenceEnvelope(); universe=tuple(sorted({s for r in records for s in r.active_signal_ids})); perm=_permutation(256,seed)
    if _hash_list(perm)!=EXPECTED["random_perm"]: raise RuntimeError("random permutation changed")
    rows=[]; used=set(); identified=True
    for index,target in enumerate(targets):
        arity=len(_flatten(connected,target,set())); selected=None
        for attempt in perm:
            ranked=sorted(universe,key=lambda s:hashlib.blake2b(f"{seed}|{index}|{attempt}|{s}".encode(),digest_size=16).digest()); members=tuple(ranked[:arity])
            if len(members)!=arity or members in used: continue
            support=sum(set(members).issubset(r.active_signal_ids) for r in records)
            if support==target.support: selected=members; break
        if selected is None:
            identified=False; rows.append({"target":target.cell_id,"support":target.support,"arity":arity,"identified":False}); continue
        used.add(selected); proposal=GrowthProposal(selected,min(2,max(0,arity-1)),index,seed); emission=GrowthRequestEmission(True,0.5,"LAB_YOKED_RANDOM","LAB_YOKED_RANDOM")
        control.audit.proposal_attempts+=1; control._materialize_proposal(proposal,emission)
        rows.append({"target":target.cell_id,"support":target.support,"arity":arity,"identified":True,"random_members":list(selected)})
    for r in records: control.add_unique_evidence(r)
    control._review_lifecycle(final=True); control.rebuild_graph()
    return control,{"laboratory_only":True,"outcome_blind_support_matching":True,"target_count":len(targets),"identified_count":sum(x["identified"] for x in rows),"all_identified":identified,"same_capacities":control.config==connected.config,"rows":rows,"manifest":control.to_manifest()}

def _flatten(envelope,cell,visiting):
    if cell.cell_id in visiting: raise RuntimeError("cyclic context")
    visiting={*visiting,cell.cell_id}; out=[]
    for m in cell.members:
        if m.startswith("context:"): out.extend(_flatten(envelope,envelope.cells[m.split(":",1)[1]],visiting))
        else: out.append(m)
    return tuple(sorted(set(out)))

def _retired(organism,connected,shuffled,random_control,obs,prior,cfg):
    classes=[connected.classify(x["evidence"].active_signal_ids,policy_response=True) for x in obs]
    shuffled_classes=[shuffled.classify(x["evidence"].active_signal_ids,policy_response=True) for x in obs]
    random_classes=None if random_control is None else [random_control.classify(x["evidence"].active_signal_ids,policy_response=True) for x in obs]
    success=[x["completion"] for x in obs]; flags=[c.state==AvailabilityState.AVAILABLE for c in classes]
    parent=chess.Board(prior["retired_r1_fen"])
    wrapper=NativeR0CompetenceOrganism(organism,connected)
    raw,frames=NativeHandoverGenome().query_child_slots(parent,wrapper)
    keys=[(a,i) for a in sorted(raw) for i in range(len(raw[a]))]
    if len(keys)!=65: raise RuntimeError("retired slot count changed")
    perm=_permutation(65,cfg.output_seed)
    if _hash_list(perm)!=EXPECTED["output_perm"]: raise RuntimeError("output permutation changed")
    vectors=_by_action(keys,flags); swapped=dict(vectors); swapped["d8c8"],swapped["d8c7"]=vectors["d8c7"],vectors["d8c8"]
    mapping=_derangement(raw,cfg.reply_seed)
    if _hash_json(mapping)!=EXPECTED["reply_derangement"]: raise RuntimeError("derangement changed")
    deranged=_flatten_vectors(keys,{a:vectors[src] for a,src in mapping.items()})
    arms={
      "connected":_connected_premeasured_handover(
          organism,parent,raw,frames
      ),
      "learned_output_shuffle":_laboratory_control_handover_with_injected_availability(organism,parent,raw,frames,[flags[perm[i]] for i in range(65)]),
      "outcome_shuffled_learning":_laboratory_control_handover_with_injected_availability(organism,parent,raw,frames,[c.state==AvailabilityState.AVAILABLE for c in shuffled_classes]),
      "disconnected":_laboratory_control_handover_with_injected_availability(organism,parent,raw,frames,[False]*65,disconnected=True),
      "global_evidence":_laboratory_control_handover_with_injected_availability(organism,parent,raw,frames,[True]*65),
      "any_policy_response":_laboratory_control_handover_with_injected_availability(organism,parent,raw,frames,[True]*65),
      "forced_d8_swap":_laboratory_control_handover_with_injected_availability(organism,parent,raw,frames,_flatten_vectors(keys,swapped)),
      "reply_count_derangement":_laboratory_control_handover_with_injected_availability(organism,parent,raw,frames,deranged),
    }
    if random_classes is not None: arms["random_composite"]=_laboratory_control_handover_with_injected_availability(organism,parent,raw,frames,[c.state==AvailabilityState.AVAILABLE for c in random_classes])
    controls=all(not row["converted"] for name,row in arms.items() if name!="connected")
    exact=sum(flags)==1 and flags==success
    gates={"exact_policy_mask":exact,"no_failure_available":all(not f for f,y in zip(flags,success,strict=True) if not y),"selects_d8c8":arms["connected"]["selected_parent_action"]=="d8c8" and arms["connected"]["selection_route"]=="exploit","connected_converts":arms["connected"]["converted"],"controls_do_not_convert":controls,"zero_host_fallback":all(r["host_fallback_count"]==0 for r in arms.values())}
    rows=[]
    for x,c in zip(obs,classes,strict=True):
        rows.append(_artifact_observation(x)|{"state":c.state.value,"probability":c.probability,"uncertainty":c.uncertainty,"available_cell_ids":list(c.available_cell_ids),"refuted_cell_ids":list(c.refuted_cell_ids)})
    return {"rows":rows,"policy_success_count":sum(success),"available_count":sum(flags),"mapping":mapping,"arms":arms,"gates":gates,"controls_identified":controls,"zero_host_fallback":gates["zero_host_fallback"],"zero_dream_updates":all(q.persistent_mutation_count==0 for qs in raw.values() for q in qs),"passed":all(gates.values())}

def _connected_wrapper_handover(organism,wrapper,parent):
    """Connected authority path: wrapper responses flow directly into handover."""

    raw,frames=NativeHandoverGenome().query_child_slots(parent,wrapper)
    return _connected_premeasured_handover(organism,parent,raw,frames)

def _connected_premeasured_handover(organism,parent,slots,frames):
    decision=FailClosedNativeHandoverGenome().decide_from_available_slots(
        parent,slots,frames
    )
    after=parent.copy(stack=False)
    after.push(chess.Move.from_uci(decision.actuation.move_uci))
    replies=[]
    for reply in sorted(after.legal_moves,key=lambda m:m.uci()):
        successor=after.copy(stack=False); successor.push(reply)
        observed=observe_real_child(organism,successor)
        replies.append({
            "reply":reply.uci(),
            "r0_action":None if observed.actuation is None else observed.actuation.move_uci,
            "completion":observed.completion_confirmed,
            "terminal":observed.observed_terminal,
            "fabricated_reward":observed.fabricated_terminal_reward,
        })
    return {
        "selected_parent_action":decision.actuation.move_uci,
        "selection_route":"exploit" if decision.selection_mode=="exploit" else "graph_owned_fallback",
        "exploit_actuator":None if decision.exploit_actuation is None else decision.exploit_actuation.move_uci,
        "fallback_actuator":None if decision.exploration_actuation is None else decision.exploration_actuation.move_uci,
        "host_fallback_count":decision.host_fallback_count,
        "actuator_multiplicity":decision.actuator_multiplicity,
        "converted":bool(replies and all(r["completion"] for r in replies)),
        "replies":replies,
        "response_authority":"NativeR0CompetenceOrganism.dream_session",
        "laboratory_response_injection":False,
    }

def _laboratory_control_handover_with_injected_availability(
    organism,parent,raw,frames,flags,disconnected=False
):
    slots={}; cursor=0
    for action in sorted(raw):
        rows=[]
        for q in raw[action]: rows.append(response_with_availability(organism,q,available=bool(flags[cursor]))); cursor+=1
        slots[action]=tuple(rows)
    decision=FailClosedNativeHandoverGenome().decide_from_available_slots(parent,slots,frames,disconnected=disconnected)
    after=parent.copy(stack=False); after.push(chess.Move.from_uci(decision.actuation.move_uci)); replies=[]
    for reply in sorted(after.legal_moves,key=lambda m:m.uci()):
        successor=after.copy(stack=False); successor.push(reply); observed=observe_real_child(organism,successor)
        replies.append({"reply":reply.uci(),"r0_action":None if observed.actuation is None else observed.actuation.move_uci,"completion":observed.completion_confirmed,"terminal":observed.observed_terminal,"fabricated_reward":observed.fabricated_terminal_reward})
    return {"selected_parent_action":decision.actuation.move_uci,"selection_route":"exploit" if decision.selection_mode=="exploit" else "graph_owned_fallback","exploit_actuator":None if decision.exploit_actuation is None else decision.exploit_actuation.move_uci,"fallback_actuator":None if decision.exploration_actuation is None else decision.exploration_actuation.move_uci,"host_fallback_count":decision.host_fallback_count,"actuator_multiplicity":decision.actuator_multiplicity,"converted":bool(replies and all(r["completion"] for r in replies)),"replies":replies}

def _by_action(keys,flags):
    out=defaultdict(list)
    for (a,_),f in zip(keys,flags,strict=True): out[a].append(bool(f))
    return {a:tuple(v) for a,v in out.items()}

def _flatten_vectors(keys,vectors): return [bool(vectors[a][i]) for a,i in keys]

def _derangement(slots,seed):
    strata=defaultdict(list)
    for a,rows in sorted(slots.items()): strata[len(rows)].append(a)
    rng=random.Random(seed); out={}
    for _,actions in sorted(strata.items()):
        order=list(actions); rng.shuffle(order)
        if len(order)==1: out[order[0]]=order[0]
        else:
            for i,a in enumerate(order): out[a]=order[(i+1)%len(order)]
    return out

def _serialization(wrapper,path,forbidden,records):
    payload=wrapper.dumps(); target=Path(path); target.parent.mkdir(parents=True,exist_ok=True); target.write_bytes(payload); restored=NativeR0CompetenceOrganism.loads(payload)
    parity=all(wrapper.envelope.classify(r.active_signal_ids,policy_response=r.policy_response)==restored.envelope.classify(r.active_signal_ids,policy_response=r.policy_response) for r in records)
    return {"path":path,"sha256":hashlib.sha256(payload).hexdigest(),"bytes":len(payload),"parity":parity,"no_serialized_fen":all(f.encode() not in payload for f in forbidden),"trainer_required_for_inference":False}

def _digest_r0(o):
    return hashlib.sha256(pickle.dumps((o.graph,o.credit,o.provenance,o.frozen_triplet_ids,o.retrieval_budget_per_actuator),protocol=pickle.HIGHEST_PROTOCOL)).hexdigest()
def _integrity(o,before):
    after=_digest_r0(o); return {"before":before,"after":after,"bit_identical":before==after,"retrieval_budget":o.retrieval_budget_per_actuator}
def _digest_envelope(e): return hashlib.sha256(pickle.dumps(e,protocol=pickle.HIGHEST_PROTOCOL)).hexdigest()

def _verify_sources(cfg):
    actual={"source_organism":_file_sha(cfg.source_organism),"source_artifact":_file_sha(cfg.source_artifact),"prior":_file_sha(cfg.prior)}
    for k,v in actual.items():
        if v!=EXPECTED[k]: raise RuntimeError(f"source changed: {k}")

def _verify_pools(p):
    result={}
    for name in ("r0_train","gate_train_decoys","r0_validation","gate_validation_decoys","r0_regression","gate_regression_decoys"):
        result[name]=_hash_list(list(getattr(p,name)))
        if result[name]!=EXPECTED[name]: raise RuntimeError(f"pool changed: {name}")
    return result

def _permutation(n,seed):
    values=list(range(n)); random.Random(seed).shuffle(values); return values
def _hash_list(v): return hashlib.sha256(json.dumps(list(v),separators=(",",":")).encode()).hexdigest()
def _hash_json(v): return hashlib.sha256(json.dumps(v,separators=(",",":"),sort_keys=True).encode()).hexdigest()
def _file_sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def _close(cfg,result,started,boundary,tripwires,stage="closed"):
    result["binding_boundary"]=boundary; result["stage"]=stage; result["authority_tripwires"]=dict(tripwires); result["passed"]=False; result["next_action"]=f"preserve_first_boundary:{boundary}"; return _finalize(cfg,result,started)
def _finalize(cfg,result,started):
    result["duration_seconds"]=perf_counter()-started; target=Path(cfg.output); target.parent.mkdir(parents=True,exist_ok=True); target.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n"); return result
