from __future__ import annotations

import chess
import pytest

from recon_lite import ChildResponse

from recon_lite_chess.autogrowth.native_authority_handover import ChildQuery
from recon_lite_chess.autogrowth.native_authority_lab import (
    NativeAuthorityLabConfig,
    load_retired_r0_build,
)
from recon_lite_chess.autogrowth.native_competence_envelope import (
    GraphNativeCompetenceEnvelope,
    NativeR0CompetenceOrganism,
)
from recon_lite_chess.autogrowth.native_mature_envelope_authority_addendum import (
    _mature_authority_canary,
)


@pytest.fixture(scope="module")
def build():
    return load_retired_r0_build(NativeAuthorityLabConfig())


def test_wrapper_adapter_rejects_host_boolean_authority(build) -> None:
    board = chess.Board(build.pools.r0_train[0])
    actuation = build.organism.emit_action(board)
    assert actuation is not None
    query = ChildQuery(
        response=ChildResponse(
            child_id=build.organism.provenance.child_id,
            confirmed=False,
            expected_value=0.0,
            uncertainty=build.organism.provenance.uncertainty,
            grounded=True,
            grounding_source=build.organism.provenance.grounding_source,
            policy_response=True,
            available=False,
        ),
        actuation=actuation,
        frame_id="typed-adapter",
        persistent_mutation_count=0,
        effect_attempts=(),
    )
    wrapper = NativeR0CompetenceOrganism(
        build.organism, GraphNativeCompetenceEnvelope()
    )
    with pytest.raises(TypeError, match="EnvelopeClassification"):
        wrapper.apply_to_query(
            query,
            True,  # type: ignore[arg-type]
            active_signal_ids=(),
        )


def test_serialized_mature_wrapper_causally_controls_handover(build) -> None:
    result = _mature_authority_canary(build.organism)
    assert result["passed"] is True
    assert result["mature_wrapper"]["restored_mature_cell_count"] == 1
    assert result["authority_observations"]["session_open_count"] == 1
    assert result["authority_observations"]["session_close_count"] == 1
    assert result["authority_observations"]["request_count"] > 0
    assert result["authority_observations"]["injection_tripwire_calls"] == 0
    assert result["consumed_mask"]["equals_direct_classification"] is True
    assert result["decisions"]["connected_action"] == result["target"]["action"]
    assert result["decisions"]["empty_action"] != result["target"]["action"]
    assert result["decisions"]["disconnected_action"] != result["target"]["action"]
