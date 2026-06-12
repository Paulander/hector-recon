import json

from recon_lite_chess.autogrowth import KRKPositionSet, RetryDiagnosticsConfig, run_retry_diagnostics
from recon_lite_chess.autogrowth.retry_diagnostics import _diagnostic_decision, _trace_summary


def test_tg22_diagnostic_decision_marks_redundant_retry_edges() -> None:
    records = [
        {
            "arm": "tg21_retry_edges_h40",
            "classification": "edge_bonus_used",
            "retry_success": 1,
            "event_led_to_completion": False,
            "event_led_to_mate": False,
        }
    ]
    comparisons = [
        {
            "edge_bonus_hit": 1,
            "choice_changed": False,
            "same_outcome": True,
        }
    ]
    summary = _trace_summary(records=records, comparisons=comparisons)

    decision = _diagnostic_decision(
        retry_edge_weights={"a->b": 1.0},
        summary=summary,
        training_metrics={"retry_success_count": 1},
    )

    assert decision["status"] == "tg22_retry_diagnostics_complete"
    assert decision["finding"] == "retry_edges_redundant"
    assert decision["direct_move_override"] is False


def test_tg22_retry_diagnostics_writes_artifact(tmp_path) -> None:
    fen = "8/8/8/8/2K5/6k1/2R5/8 w - - 0 1"
    result = run_retry_diagnostics(
        config=RetryDiagnosticsConfig(
            seed=1,
            train_count=2,
            heldout_weakness_count=1,
            heldout_broader_count=0,
            min_support=1,
            max_candidates=2,
            horizons=(4,),
            min_sequence_credit=0.01,
            activation_max_distance=1.0,
            after_max_distance=4.0,
            chain_max_distance=4.0,
            max_chain_edges=8,
            max_event_records=20,
        ),
        positions=KRKPositionSet(seed=1, train=(fen, fen), heldout_weakness=(fen,), heldout_broader=()),
    )
    output = result.write_json(tmp_path / "tg22_retry_diagnostics.json")
    payload = json.loads(output.read_text(encoding="utf-8"))

    assert payload["schema_version"] == "krk_autogrowth_tg22_retry_diagnostics.v0"
    assert payload["local_recon_structure"]["diagnostic_only"] is True
    assert payload["local_recon_structure"]["direct_move_override"] is False
    assert payload["decision"]["diagnostic_only"] is True
    assert "trace_summary" in payload
