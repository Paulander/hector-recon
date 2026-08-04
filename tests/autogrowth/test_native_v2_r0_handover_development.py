from __future__ import annotations

import chess

from recon_lite import FrameContext, FrameKind

from recon_lite_chess.autogrowth.native_prospective_evidence_authority_v2 import (
    NativeProspectiveAuthorityV2,
    V2Mode,
)
from recon_lite_chess.autogrowth.native_v2_r0_handover_development import (
    NativeV2R0CompetenceOrganism,
    _certify,
    _load_regression,
    _load_source,
    _local_sources,
    _selectivity_metrics,
)


def _source_and_rows():
    regression = _load_regression()
    item = _local_sources(regression, 32)[0]
    return item, regression["reference_rows"]


def test_v2_r0_adapter_reads_graph_availability_without_virtual_learning() -> None:
    item, rows = _source_and_rows()
    authority = NativeProspectiveAuthorityV2.from_organism(
        _load_source(item), mode=V2Mode.PROSPECTIVE
    )
    authority.close_nomination()
    organism = NativeV2R0CompetenceOrganism(authority)
    before = authority.continuation_digest()
    session = organism.dream_session()
    try:
        query = session.request(FrameContext(
            "focused-v2-r0-virtual",
            FrameKind.VIRTUAL,
            values={"board": chess.Board(rows[0]["fen"])},
        ))
    finally:
        session.close()
    assert query.graph_signal_trace is not None
    assert query.availability_provenance == {
        "authority": "NativeProspectiveAuthorityV2_graph_emission",
        "classification": query.availability_provenance["classification"],
        "certification_evidence_added": 0,
    }
    assert query.persistent_mutation_count == 0
    assert authority.pending_event is None
    assert authority.consumed_receipts == {}
    assert authority.continuation_digest() == before


def test_real_certification_transactions_roundtrip_the_existing_v2_authority() -> None:
    item, rows = _source_and_rows()
    organism, record = _certify(item, rows[:4])
    assert record["later_real_interactions"] == 4
    assert record["serialization"]["roundtrip_exact"] is True
    assert organism.authority.pending_event is None
    assert len(organism.authority.consumed_receipts) == 4
    assert len(organism.authority.event_transactions) == 4


def test_selectivity_metrics_keep_abstention_distinct_from_negative() -> None:
    rows = [
        {"state": "available", "actual_completion": True},
        {"state": "available", "actual_completion": False},
        {"state": "refuted", "actual_completion": True},
        {"state": "refuted", "actual_completion": False},
        {"state": "unknown", "actual_completion": True},
        {"state": "unknown", "actual_completion": False},
    ]
    metrics = _selectivity_metrics(rows)
    assert {key: metrics[key] for key in ("tp", "fp", "tn", "fn")} == {
        "tp": 1,
        "fp": 1,
        "tn": 1,
        "fn": 1,
    }
    assert metrics["abstentions"] == 2
    assert metrics["positive_abstentions"] == 1
    assert metrics["negative_abstentions"] == 1
    assert metrics["availability_coverage"] == 2 / 6
    assert metrics["resolved_coverage"] == 4 / 6
