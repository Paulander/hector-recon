from __future__ import annotations

import json
from pathlib import Path

from recon_lite_chess.autogrowth.native_authority_lab import _config_from_prior_artifact
from recon_lite_chess.autogrowth.native_intrinsic_curriculum import _build_pools


def test_retired_authority_lab_reconstructs_exact_touched_pool_manifest() -> None:
    source = Path(
        "reports/autogrowth/native_from_scratch/"
        "r0_r1_balanced96_240_seed_20260719_compact.json"
    )
    artifact = json.loads(source.read_text(encoding="utf-8"))
    pools = _build_pools(_config_from_prior_artifact(artifact))
    assert pools.manifest()["combined_sha256"] == artifact["pool_manifest"]["combined_sha256"]
    assert pools.manifest()["final_test_created_or_touched"] is False
