import importlib.util
import json
from pathlib import Path


_summary_spec = importlib.util.spec_from_file_location(
    "summarize_stage7_unresolved_legal_first",
    Path(__file__).resolve().parents[1] / "scripts" / "summarize_stage7_unresolved_legal_first.py",
)
assert _summary_spec is not None
assert _summary_spec.loader is not None
_summary = importlib.util.module_from_spec(_summary_spec)
_summary_spec.loader.exec_module(_summary)


def test_stage7_unresolved_legal_first_summary_marks_selection_gap_and_capacity_probe(tmp_path):
    probe = {
        "records": [
            {
                "state_id": "state.actiongap",
                "post_reply_fen": "8/8/8/8/4K3/4R3/3k4/8 w - - 2 2",
                "diagnosis": "unresolved_by_existing_forced_providers_at_h80",
                "legal_first_probes": [
                    {
                        "move": "e4d4",
                        "horizon": 40,
                        "result": "mate",
                        "plies": 5,
                        "move_shape_audit": {
                            "move_shape_terms": ["candidate_is_king_move"],
                            "post_move_terms": ["rook_safe_after_move"],
                            "current_terms": ["rook_safe"],
                        },
                    }
                ],
            },
            {
                "state_id": "state.capacity",
                "post_reply_fen": "8/8/8/R7/4k3/8/8/3K4 w - - 2 2",
                "diagnosis": "unresolved_by_existing_forced_providers_at_h80",
                "legal_first_probes": [
                    {"move": "a5a1", "horizon": 50, "result": "max_plies", "plies": 50}
                ],
            },
        ]
    }
    path = tmp_path / "probe.json"
    path.write_text(json.dumps(probe), encoding="utf-8")

    payload = _summary.summarize([path])

    assert payload["causal_status"] == "non_causal"
    assert payload["diagnosis_counts"] == {
        "legal_first_action_selection_gap": 1,
        "no_legal_first_conversion_under_current_graph": 1,
    }
    candidates = {item["state_id"]: item for item in payload["candidates"]}
    assert candidates["state.actiongap"]["promotion_status"] == "sandbox_ready_if_terms_separate"
    assert candidates["state.actiongap"]["proposed_change"]["kind"] == "visible_move_shape_role_candidate"
    assert candidates["state.actiongap"]["legal_first_mating_moves"][0]["move"] == "e4d4"
    assert candidates["state.capacity"]["promotion_status"] == "needs_longer_horizon_or_new_provider_probe"
    assert candidates["state.capacity"]["proposed_change"]["max_tested_horizon"] == 50
