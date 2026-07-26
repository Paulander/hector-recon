from __future__ import annotations

import copy
from enum import Enum
import json

import pytest

from recon_lite_chess.autogrowth import (
    native_v2_frozen_cohort_canonical_contract_reclosure as closure,
)
from recon_lite_chess.autogrowth import (
    native_v2_fresh_discriminator_review_repair_v2 as stopped,
)


class StringMode(str, Enum):
    PROSPECTIVE = "prospective"
    LEGACY = "legacy_same_ledger"


def _contract() -> dict:
    structure = {
        "candidate_population_identity": "candidate-population",
        "structural_invariants": {
            "cell-1": {
                "members": ("terminal-a", "terminal-b"),
                "polarity": StringMode.PROSPECTIVE,
                "authority_node_ids": ("node-a", "node-b"),
            }
        },
    }
    topology = {"root": "root-1", "members": ("cell-1",)}
    value = {
        "schema_version": "native_v2_fresh_arm_identity_contract.v1",
        "common_structure": structure,
        "common_structure_digest": closure.digest(structure),
        "suffix_topology_identity": topology,
        "suffix_topology_identity_digest": closure.digest(topology),
        "common_identity_fields": {
            "candidate_population_identity": "candidate-population",
            "topology_identity": "topology-1",
            "polarity_manifest": {"cell-1": StringMode.PROSPECTIVE},
        },
        "lawfully_different_fields": (
            "mode",
            "authority_manifest",
            "continuation_digest",
        ),
        "expected_modes": {
            "A": StringMode.PROSPECTIVE,
            "B": StringMode.LEGACY,
            "C": StringMode.PROSPECTIVE,
        },
        "expected_authority": {
            "A": {"cell-1": False},
            "B": {"cell-1": True},
            "C": {"cell-1": False},
        },
        "per_arm_semantic_identity": {
            arm: {
                "mode": mode,
                "authority_manifest": {"cell-1": arm == "B"},
                "lawful_initial_authority": True,
                "continuation_digest": f"continuation-{arm}",
            }
            for arm, mode in {
                "A": StringMode.PROSPECTIVE,
                "B": StringMode.LEGACY,
                "C": StringMode.PROSPECTIVE,
            }.items()
        },
    }
    return closure.sign_contract(value)


def _resign(value: dict) -> dict:
    if "common_structure" in value:
        value["common_structure_digest"] = closure.digest(
            value["common_structure"]
        )
    if "suffix_topology_identity" in value:
        value["suffix_topology_identity_digest"] = closure.digest(
            value["suffix_topology_identity"]
        )
    return closure.sign_contract(value)


def test_contract_survives_json_roundtrip_and_compares_canonically() -> None:
    observed = _contract()
    expected = json.loads(json.dumps(observed))
    assert expected != observed
    result = closure.compare_complete_contracts(
        expected, observed, seed_ordinal=0
    )
    assert result["canonical_equal"] is True
    assert result["raw_python_equal"] is False
    assert result["contract_digest"] == observed["contract_digest"]


def test_tuple_list_normalization_is_accepted() -> None:
    observed = _contract()
    expected = closure.canonical_json_value(observed)
    assert isinstance(
        observed["common_structure"]["structural_invariants"]["cell-1"][
            "members"
        ],
        tuple,
    )
    assert isinstance(
        expected["common_structure"]["structural_invariants"]["cell-1"][
            "members"
        ],
        list,
    )
    closure.compare_complete_contracts(expected, observed, seed_ordinal=1)


def test_string_enum_normalization_is_accepted() -> None:
    observed = _contract()
    expected = closure.canonical_json_value(observed)
    assert type(observed["expected_modes"]["A"]) is StringMode
    assert type(expected["expected_modes"]["A"]) is str
    closure.compare_complete_contracts(expected, observed, seed_ordinal=2)


@pytest.mark.parametrize(
    ("case", "expected_path"),
    (
        ("member", "/common_structure/structural_invariants/cell-1/members/1"),
        ("member_order", "/common_structure/structural_invariants/cell-1/members/0"),
        ("missing", "/common_identity_fields/topology_identity"),
        ("additional", "/unexpected_field"),
        ("polarity", "/common_identity_fields/polarity_manifest/cell-1"),
        ("candidate", "/common_identity_fields/candidate_population_identity"),
        ("topology", "/suffix_topology_identity/root"),
        ("mode", "/expected_modes/B"),
        ("initial_state", "/per_arm_semantic_identity/A/authority_manifest/cell-1"),
    ),
)
def test_semantic_contract_changes_are_rejected(
    case: str, expected_path: str
) -> None:
    expected = closure.canonical_json_value(_contract())
    observed = copy.deepcopy(expected)
    if case == "member":
        observed["common_structure"]["structural_invariants"]["cell-1"][
            "members"
        ][1] = "terminal-c"
    elif case == "member_order":
        observed["common_structure"]["structural_invariants"]["cell-1"][
            "members"
        ].reverse()
    elif case == "missing":
        del observed["common_identity_fields"]["topology_identity"]
    elif case == "additional":
        observed["unexpected_field"] = "unexpected"
    elif case == "polarity":
        observed["common_identity_fields"]["polarity_manifest"][
            "cell-1"
        ] = "refuted"
    elif case == "candidate":
        observed["common_identity_fields"]["candidate_population_identity"] = (
            "other-population"
        )
    elif case == "topology":
        observed["suffix_topology_identity"]["root"] = "other-root"
    elif case == "mode":
        observed["expected_modes"]["B"] = "prospective"
    elif case == "initial_state":
        observed["per_arm_semantic_identity"]["A"]["authority_manifest"][
            "cell-1"
        ] = True
    else:  # pragma: no cover
        raise AssertionError(case)
    observed = _resign(observed)
    with pytest.raises(closure.CanonicalContractMismatch) as raised:
        closure.compare_complete_contracts(expected, observed, seed_ordinal=7)
    paths = {row["path"] for row in raised.value.manifest["differences"]}
    assert expected_path in paths
    assert raised.value.manifest["seed_ordinal"] == 7
    assert raised.value.manifest["difference_count"] >= 1


def test_missing_or_invalid_self_digest_fails_before_comparison() -> None:
    expected = closure.canonical_json_value(_contract())
    observed = copy.deepcopy(expected)
    observed["contract_digest"] = "0" * 64
    with pytest.raises(
        closure.CanonicalContractIntegrityError,
        match="observed seed 9 self-digest mismatch",
    ):
        closure.compare_complete_contracts(expected, observed, seed_ordinal=9)


def test_actual_seed_zero_reproduces_abort_and_passes_canonical_contract() -> None:
    static = closure.verify_static_bindings()
    manifest, reconstruction = closure.reconstruct_snapshot_manifest()
    assert reconstruction["raw_size"] == closure.RAW_SNAPSHOT_MANIFEST_SIZE
    assert reconstruction["raw_sha256"] == closure.RAW_SNAPSHOT_MANIFEST_SHA256
    expected = manifest["metadata"]["per_seed_identity_contracts"]["0"]
    arms = {
        arm: stopped._restore_snapshot_entry(manifest, 0, arm)
        for arm in stopped.ARMS
    }
    codec = stopped.V2SnapshotCodec()
    before = {arm: codec.semantic_identity(arms[arm]) for arm in stopped.ARMS}
    observed = stopped.exact_arm_identity_contract(arms)
    after = {arm: codec.semantic_identity(arms[arm]) for arm in stopped.ARMS}
    assert closure.canonical_bytes(before) == closure.canonical_bytes(after)
    assert expected != observed
    with pytest.raises(
        stopped.FreshScientificIntegrityError,
        match="snapshot candidate contract mismatch:0",
    ):
        closure.legacy_raw_contract_check(expected, observed, seed_ordinal=0)
    result = closure.compare_complete_contracts(
        expected, observed, seed_ordinal=0
    )
    assert result == {
        "seed_ordinal": 0,
        "contract_digest": closure.SEED_ZERO_CONTRACT_DIGEST,
        "canonical_equal": True,
        "canonical_size": len(closure.canonical_bytes(expected)),
        "raw_python_equal": False,
    }
    assert static["receipt"]["outcome_access"] == {"count": 0, "event_ids": []}
    assert all(
        not (closure.ROOT / path).exists()
        for path in closure.STOPPED_OUTPUT_PATHS
    )


def test_outer_module_has_no_exposure_or_outcome_command() -> None:
    source = open(closure.__file__, encoding="utf-8").read()
    assert 'commands.add_parser("run-exposure")' not in source
    assert 'commands.add_parser("run-science")' not in source
    assert 'commands.add_parser("run-outcome")' not in source
    assert set(closure.ORDER_MAP) == {"ascending", "descending", "even_then_odd"}
