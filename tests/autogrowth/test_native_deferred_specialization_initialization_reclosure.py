from __future__ import annotations

import copy
import inspect
import json

import pytest

from recon_lite_chess.autogrowth import (
    native_deferred_specialization_fresh_discriminator as science,
)
from recon_lite_chess.autogrowth import (
    native_deferred_specialization_initialization_reclosure as reclosure,
)
from recon_lite_chess.autogrowth import (
    native_deferred_specialization_performance_reclosure as performance,
)


@pytest.fixture(scope="module")
def frozen_discovery_fixture():
    _manifest, original, rows = (
        reclosure._FROZEN_VERIFY_PERFORMANCE_MANIFEST()
    )
    source = copy.deepcopy(
        science._load_source(original["source_r0"]["source_item"])
    )
    cache = performance.load_and_verify_cache(
        reclosure.VERIFIED_CACHE_PATH, source, rows
    )
    return (
        source,
        reclosure._discovery_rows_only(rows),
        cache,
        tuple(map(int, original["seed_derivation"]["genome_seeds"])),
    )


def test_historical_runners_failed_attempt_and_cache_remain_byte_exact():
    actual = reclosure.verify_historical_immutability()
    assert actual[str(science.SOURCE_PATH)] == (
        reclosure.HISTORICAL_FRESH_RUNNER_SHA256
    )
    assert actual[str(performance.SOURCE_PATH)] == (
        reclosure.HISTORICAL_PERFORMANCE_RUNNER_SHA256
    )
    assert actual[str(reclosure.FAILED_ATTEMPT_PATH)] == (
        reclosure.FAILED_ATTEMPT_SHA256
    )
    assert actual[str(reclosure.VERIFIED_CACHE_PATH)] == (
        reclosure.VERIFIED_CACHE_SHA256
    )


def test_actual_production_order_rejects_premature_close_and_passes_reclosure(
    frozen_discovery_fixture,
):
    source, discovery_rows, cache, seeds = frozen_discovery_fixture
    result = reclosure.diagnose_seed_initialization(
        ordinal=0,
        seed=seeds[0],
        source=source,
        discovery_rows=discovery_rows,
        cache=cache,
    )
    assert result["premature_error"] == (
        "experimental initialization identity mismatch"
    )
    assert result["nomination_closed_immediately_before_premature_from_organism"]
    assert not result[
        "nomination_closed_immediately_before_corrected_from_organism"
    ]
    assert result["premature_actual_experimental_identity"] is None
    assert result["experimental_identity_exact"]
    assert result["mixed_outcome_shadow_parent_count"] >= 1
    assert result["arm_count"] == 3
    assert len(set(
        result["pre_factor_arm_candidate_digests"].values()
    )) == 1
    assert len(set(
        result["post_factor_decision_topology_digests"].values()
    )) == 1
    assert result["pre_parent_invariant_checks"] == 3
    assert result["parent_prospective_events"] == 0
    assert result["exposure_scans"] == 0
    assert result["stage_b_events"] == 0
    assert result["unopened_outcome_events"] == 0


def test_historical_and_corrected_production_sequences_are_explicit():
    fresh_source = inspect.getsource(
        science._clone_candidate_identical_arms
    )
    performance_source = inspect.getsource(
        performance._clone_candidate_identical_arms_cached
    )
    corrected_source = inspect.getsource(
        reclosure._clone_candidate_identical_arms_cached
    )
    for historical in (fresh_source, performance_source):
        assert historical.index("organism.close_prospective_nomination()") < (
            historical.index("NativeProspectiveAuthorityV2.from_organism")
        )
    assert "organism.close_prospective_nomination()" not in corrected_source
    assert corrected_source.index(
        "NativeProspectiveAuthorityV2.from_organism"
    ) < corrected_source.index("template.close_nomination()")


def test_32_seed_canary_stops_before_parent_prospective_boundary():
    artifact = json.loads(reclosure.CANARY_PATH.read_text(encoding="utf-8"))
    assert artifact["status"] == "ENGINEERING_CANARY_COMPLETE"
    assert artifact["seed_count"] == artifact["seed_pass_count"] == 32
    assert artifact["wrapper_construction_count"] == 32
    assert artifact["wrapper_closure_count"] == 32
    assert artifact["experimental_identity_exact_count"] == 32
    assert artifact["candidate_identical_arm_count"] == 96
    assert artifact["pre_parent_invariant_pass_count"] == 96
    assert artifact["parent_prospective_event_count"] == 0
    assert artifact["exposure_scan_count"] == 0
    assert artifact["stage_b_event_count"] == 0
    assert artifact["new_outcome_access_count"] == 0
    assert artifact["stopped_at"] == (
        "IMMEDIATELY_BEFORE_FIRST_PARENT_PROSPECTIVE_ROW"
    )


def test_reclosed_manifest_and_placeholder_are_not_executed():
    manifest, original, rows = reclosure._verify_reclosure_manifest()
    placeholder = json.loads(
        reclosure.RESULT_PLACEHOLDER.read_text(encoding="utf-8")
    )
    assert manifest["status"] == "INITIALIZATION_RECLOSED_NOT_EXECUTED"
    assert not manifest["execution_authorized"]
    assert not manifest["new_attempt_started"]
    assert not manifest["parent_prospective_rows_accessed_by_reclosure"]
    assert not manifest["exposure_rows_accessed_by_reclosure"]
    assert not manifest["stage_b_rows_accessed_by_reclosure"]
    assert manifest["frozen_science_identity"]["genome_seeds"] == (
        original["seed_derivation"]["genome_seeds"]
    )
    assert manifest["frozen_science_identity"]["stream_row_order"] == [
        row.row_id for row in rows
    ]
    assert placeholder["status"] == "INITIALIZATION_RECLOSED_NOT_EXECUTED"
    assert not placeholder["scientific_execution_authorized"]
    assert not placeholder["scientific_execution_started"]
    assert placeholder["scientific_result"] is None
