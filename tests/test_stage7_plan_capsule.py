#!/usr/bin/env python3
"""Tests for the non-causal Stage 7 plan capsule artifact helpers."""

import importlib.util
import json
from pathlib import Path

from recon_lite_chess.routing import PlanCapsuleSpec, StructuralCandidate


ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "audit_stage7_post_box_plan_capsule.py"


def _load_script_module():
    spec = importlib.util.spec_from_file_location("audit_stage7_post_box_plan_capsule", SCRIPT)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_plan_capsule_candidate_export_is_non_causal():
    module = _load_script_module()
    payload = module.build_plan_capsule_candidate(evidence_artifacts=["stage7.json"])

    assert payload["schema_version"] == "plan_capsule_candidate.v1"
    assert payload["causal_status"] == "non_causal"
    assert payload["promotion_status"] == "proposed"
    assert payload["candidate_id"] == "cand.krk.box_shrink.post_box_continuation_capsule.v1"

    capsule = PlanCapsuleSpec.from_dict(json.loads(json.dumps(payload["plan_capsule"])))
    candidate = StructuralCandidate.from_dict(json.loads(json.dumps(payload["structural_candidate"])))

    assert capsule.schema_version == "plan_capsule_spec.v1"
    assert capsule.capsule_id == "krk.post_box_shrink_continuation"
    assert capsule.causal_status == "non_causal"
    assert capsule.ttl_white_moves == 3
    assert "not a fixed Stage 7.5 curriculum stage" in " ".join(capsule.notes)
    assert candidate.schema_version == "structural_candidate.v1"
    assert candidate.candidate_type == "plan_capsule"
    assert candidate.causal_status == "non_causal"
    assert candidate.credit == 0.0
    assert candidate.proposed_change["kind"] == "plan_capsule_commitment_bias"
