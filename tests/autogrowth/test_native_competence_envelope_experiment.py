from __future__ import annotations
from recon_lite_chess.autogrowth.native_competence_envelope_experiment import (
    EXPECTED, _compare_controls, _derangement, _hash_json, _hash_list,
    _metrics, _permutation,
)

def test_frozen_permutations_match_preregistration() -> None:
    assert _hash_list(_permutation(64,2026071602))==EXPECTED["outcome_perm"]
    assert _hash_list(_permutation(65,2026071603))==EXPECTED["output_perm"]
    assert _hash_list(_permutation(256,2026071604))==EXPECTED["random_perm"]

def test_reply_count_derangement_has_no_avoidable_fixed_points() -> None:
    slots={"a":(1,),"b":(1,),"c":(1,2),"d":(1,2),"e":(1,2,3)}
    mapping=_derangement(slots,2026071605)
    for action,rows in slots.items():
        assert len(slots[mapping[action]])==len(rows)
        if sum(len(other)==len(rows) for other in slots.values())>1:
            assert mapping[action]!=action

def test_balanced_metrics_and_control_comparison_are_conservative() -> None:
    rows=[
        {"observed_completion":True,"state":"available","probability":0.7,"uncertainty":0.3},
        {"observed_completion":False,"state":"refuted","probability":0.0,"uncertainty":0.2},
    ]
    learned=_metrics(rows)
    assert learned["confusion"]=={"tp":1,"fp":0,"tn":1,"fn":0}
    assert learned["selective_risk"]==0.0
    controls={
        "connected":learned,
        "constant_available":_metrics([
            {"observed_completion":True,"state":"available","probability":1.0,"uncertainty":0.0},
            {"observed_completion":False,"state":"available","probability":1.0,"uncertainty":0.0},
        ]),
        "constant_unavailable":_metrics([
            {"observed_completion":True,"state":"refuted","probability":0.0,"uncertainty":0.0},
            {"observed_completion":False,"state":"refuted","probability":0.0,"uncertainty":0.0},
        ]),
        "global_evidence":_metrics([
            {"observed_completion":True,"state":"available","probability":0.75,"uncertainty":0.0},
            {"observed_completion":False,"state":"available","probability":0.75,"uncertainty":0.0},
        ]),
        "outcome_shuffled":_metrics([
            {"observed_completion":True,"state":"refuted","probability":0.0,"uncertainty":0.0},
            {"observed_completion":False,"state":"available","probability":1.0,"uncertainty":0.0},
        ]),
    }
    assert _compare_controls(controls)["passed"] is True
