import json

import chess

from recon_lite_chess.autogrowth import (
    KRKPositionSet,
    PrecisionGateConfig,
    audit_confinement_sign_semantics,
    run_precision_gate_experiment,
)
from recon_lite_chess.autogrowth.precision_gate import LocalPrecisionGate
from recon_lite_chess.training.krk_curriculum import did_box_grow


def test_tg25_confinement_sign_audit_matches_did_box_grow() -> None:
    audit = audit_confinement_sign_semantics()

    assert audit["box_min_side_delta_sign"].startswith("positive means looser")
    assert audit["example_did_box_grow"] == (audit["example_delta"] > 0)
    assert audit["used_by_gate"] is True


def test_tg25_gate_suppresses_confinement_worsening_move() -> None:
    board = chess.Board("8/8/8/8/2K5/6k1/2R5/8 w - - 0 1")
    worsening = None
    for move in board.legal_moves:
        after = board.copy(stack=False)
        after.push(move)
        if did_box_grow(board, after):
            worsening = move
            break
    assert worsening is not None
    gate = LocalPrecisionGate(
        immediate_progress_threshold=0.0,
        suppress_confinement_worsening=True,
        suppress_rook_safety_regression=True,
        suppress_negative_immediate_progress=True,
        training_evidence={"negative_or_confinement_regression_changed_count": 1},
    )

    result = gate.evaluate(board, worsening, node={"candidate_key": "test"})

    assert result["suppress"] is True
    assert result["reason"] in {"confinement_would_worsen", "rook_safety_regression", "negative_immediate_progress"}
    assert result["box_min_side_delta"] > 0


def test_tg25_precision_gate_writes_artifact(tmp_path) -> None:
    fen = "8/8/8/8/2K5/6k1/2R5/8 w - - 0 1"
    result = run_precision_gate_experiment(
        config=PrecisionGateConfig(
            seed=1,
            train_count=2,
            heldout_weakness_count=1,
            heldout_broader_count=0,
            min_support=1,
            max_candidates=2,
            horizons=(4,),
            min_sequence_credit=-1.0,
            activation_max_distance=4.0,
            after_max_distance=4.0,
            chain_max_distance=4.0,
            max_chain_edges=8,
            max_rollout_samples=2,
        ),
        positions=KRKPositionSet(seed=1, train=(fen, fen), heldout_weakness=(fen,), heldout_broader=()),
    )
    output = result.write_json(tmp_path / "tg25.json")
    payload = json.loads(output.read_text(encoding="utf-8"))

    assert payload["schema_version"] == "krk_autogrowth_tg25_local_precision_gate.v0"
    assert payload["checkpoint"] == "TG25_local_precision_gate"
    assert payload["local_recon_structure"]["gate_suppresses_only_candidate_action"] is True
    assert payload["local_recon_structure"]["gate_chooses_replacement_move"] is False
    assert payload["credit_protocol"]["confirmation_update_nodes"] is False
    assert set(payload["arms"]) == {"baseline", "ungated_candidate", "gated_candidate", "yoked_random"}
    assert "baseline_vs_gated" in payload["paired_delta_metrics"]
    assert payload["decision"]["runtime_tablebase_or_dtm_move_source"] is False
