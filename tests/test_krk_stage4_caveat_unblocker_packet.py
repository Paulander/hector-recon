#!/usr/bin/env python3
"""Tests for passive KRK Stage 4 caveat unblocker packet."""

import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _load_module(name: str, relative: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_packet = _load_module(
    "write_krk_stage4_caveat_unblocker_packet_v0",
    "scripts/write_krk_stage4_caveat_unblocker_packet_v0.py",
)


def _read_report() -> dict:
    payload = json.loads((ROOT / "reports/krk_stage4_caveat_unblocker_packet_v0.json").read_text())
    assert isinstance(payload, dict)
    return payload


def test_stage4_caveat_unblocker_is_review_ready_but_not_authorized():
    payload = _read_report()

    assert payload["schema_version"] == "krk_stage4_caveat_unblocker_packet.v0"
    assert payload["causal_status"] == "non_causal_stage4_unblocker_packet"
    assert payload["runtime_behavior_changed"] is False
    assert payload["runtime_selector_implemented"] is False
    assert payload["runtime_score_changes"] is False
    assert payload["runtime_direct_routing"] is False
    assert payload["runtime_dtm_or_tablebase_lookup"] is False
    assert payload["gameplay_topology_mutation"] is False
    assert payload["stage7_promotion_allowed"] is False
    assert payload["stage8_training_allowed"] is False

    assert (
        payload["decision"]["status"]
        == "stage4_caveat_unblocker_ready_pending_explicit_runtime_approval"
    )
    assert payload["decision"]["implementation_allowed_by_this_packet"] is False
    assert payload["decision"]["runtime_changes_allowed"] is False
    assert payload["decision"]["selector_training_allowed"] is False
    assert payload["blockers"] == []


def test_stage4_caveat_unblocker_scope_remains_narrow():
    payload = _read_report()
    scope = payload["approved_scope_if_explicitly_approved_later"]

    assert scope["scope"] == "default_off_stage4_candidate_move_first_move_contrast_sandbox_only"
    assert scope["candidate_source"] == "CandidateMoveFrame legal first-move hypotheses"
    assert scope["direct_request"] is False
    assert scope["score_delta"] == 0.0
    assert scope["default_enabled"] is False
    assert scope["exact_state_or_exact_move_exception"] is False
    assert scope["selector_training"] is False
    assert scope["provider_suppression"] is False
    assert scope["stage7_promotion"] is False
    assert scope["stage8_training"] is False


def test_stage4_caveat_unblocker_writer_is_deterministic():
    payload = _packet.build_payload()
    rendered = _packet.write_markdown(payload)

    assert "stage4_caveat_unblocker_ready_pending_explicit_runtime_approval" in rendered
    assert "implementation_allowed_by_this_packet: `False`" in rendered
    assert payload["evidence"]["stratified_gap_variant_count"] == 4
    assert payload["current_stage4_status"]["runtime_review_ready"] is True
