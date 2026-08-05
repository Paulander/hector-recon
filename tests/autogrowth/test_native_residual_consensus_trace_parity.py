from __future__ import annotations

from dataclasses import asdict, replace
import hashlib
from pathlib import Path

from recon_lite import FrameKind
from recon_lite_chess.autogrowth.native_authority_handover import (
    GraphActuation,
    GraphSignalTrace,
    GraphTerminalSignal,
)
from recon_lite_chess.autogrowth.native_residual_consensus_candidate_allocation_run import (
    _load_regression,
    _load_source,
    _trace_digest,
    _trace_parity_failures,
)


STOPPED_ARTIFACTS = {
    Path(
        "reports/autogrowth/native_authority/"
        "native_residual_consensus_candidate_allocation.json.gz"
    ): "9ba7de982b76c52f83f4f2bcd37dd1b199c1552be3b3bbb11b4852e644110f2c",
    Path(
        "reports/autogrowth/native_authority/"
        "native_residual_consensus_candidate_allocation.md"
    ): "90ead3650c8943df66dd89a47cac0f02cbde80a3166d41bc554188e91617a083",
}


def _trace(*, frame_id: str, frame_kind: str) -> GraphSignalTrace:
    actuation = GraphActuation(
        actuator_identity="opaque:actuator",
        move_uci="a1a2",
        option_identity="opaque:option",
        activation=1.0,
        candidate_count=2,
        formal_ticks=3,
    )
    signals = (
        GraphTerminalSignal(
            identity="opaque:a",
            role="BASE_TERMINAL",
            source_node_identity="opaque:source:a",
            terminal_kind="opaque",
            provenance="graph",
        ),
        GraphTerminalSignal(
            identity="opaque:b",
            role="MATURE_COMPOSITE",
            source_node_identity="opaque:source:b",
            terminal_kind="opaque",
            provenance="graph",
            stem_cell_identity="opaque:stem:b",
        ),
    )
    return GraphSignalTrace(
        frame_id=frame_id,
        frame_kind=frame_kind,
        source_organism_identity="opaque:organism",
        source_state_identity="opaque:state",
        option_identity=actuation.option_identity,
        actuation=actuation,
        confirmed_base_terminal_node_ids=("opaque:a",),
        confirmed_mature_composite_ids=("opaque:b",),
        terminal_signals=signals,
    )


def _reference(trace: GraphSignalTrace) -> dict[str, object]:
    return {
        "actuation": asdict(trace.actuation),
        "ordered_signal_identities": list(trace.ordered_signal_identities),
        "terminal_signals": [asdict(item) for item in trace.terminal_signals],
        "semantic_trace_digest": _trace_digest(trace),
    }


def test_different_real_frame_ids_have_exact_semantic_parity() -> None:
    reference_trace = _trace(frame_id="real:reference", frame_kind="REAL")
    runtime_trace = replace(reference_trace, frame_id="real:runtime")
    assert reference_trace.digest() != runtime_trace.digest()
    assert _trace_parity_failures(runtime_trace, _reference(reference_trace)) == ()


def test_changed_actuation_fails_semantic_parity() -> None:
    reference_trace = _trace(frame_id="real:reference", frame_kind="REAL")
    changed = replace(
        reference_trace,
        actuation=replace(reference_trace.actuation, move_uci="a1b1"),
    )
    failures = _trace_parity_failures(changed, _reference(reference_trace))
    assert "GraphActuation" in failures
    assert "frame_neutral_semantic_trace" in failures


def test_changed_ordered_signal_identity_fails_semantic_parity() -> None:
    reference_trace = _trace(frame_id="real:reference", frame_kind="REAL")
    changed_signal = replace(
        reference_trace.terminal_signals[0], identity="opaque:changed"
    )
    changed = replace(
        reference_trace,
        terminal_signals=(changed_signal, *reference_trace.terminal_signals[1:]),
    )
    failures = _trace_parity_failures(changed, _reference(reference_trace))
    assert "ordered_signal_identities" in failures
    assert "typed_terminal_signals" in failures
    assert "frame_neutral_semantic_trace" in failures


def test_changed_typed_terminal_source_fails_semantic_parity() -> None:
    reference_trace = _trace(frame_id="real:reference", frame_kind="REAL")
    changed_signal = replace(
        reference_trace.terminal_signals[0],
        source_node_identity="opaque:changed-source",
    )
    changed = replace(
        reference_trace,
        terminal_signals=(changed_signal, *reference_trace.terminal_signals[1:]),
    )
    failures = _trace_parity_failures(changed, _reference(reference_trace))
    assert "ordered_signal_identities" not in failures
    assert "typed_terminal_signals" in failures
    assert "frame_neutral_semantic_trace" in failures


def test_real_virtual_equivalence_requires_frame_neutral_projection() -> None:
    real = _trace(frame_id="real:one", frame_kind=FrameKind.REAL.name)
    virtual = replace(
        real, frame_id="virtual:one", frame_kind=FrameKind.VIRTUAL.name
    )
    assert real.digest() != virtual.digest()
    assert _trace_digest(real) == _trace_digest(virtual)
    assert _trace_parity_failures(virtual, _reference(real)) == ()


def test_preserved_stopped_artifacts_are_byte_identical() -> None:
    for path, expected in STOPPED_ARTIFACTS.items():
        assert hashlib.sha256(path.read_bytes()).hexdigest() == expected


def test_frozen_v1_source_cohort_continuation_digests_load_exact() -> None:
    regression = _load_regression()
    items = [
        row["source_artifact"]
        for row in regression["organisms"]
        if row["arm"] == "local_contrast_specialization"
    ]
    assert len(items) == 32
    for item in items:
        assert _load_source(item).continuation_digest_v3() == item[
            "continuation_v3_sha256"
        ]
