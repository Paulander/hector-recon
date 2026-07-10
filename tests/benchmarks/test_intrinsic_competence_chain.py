from __future__ import annotations

import json
from pathlib import Path

from recon_lite_hector.benchmarks.intrinsic_competence_chain import (
    ChainBenchmarkConfig,
    run_intrinsic_competence_chain,
)


def test_planted_chain_learns_two_intrinsic_handoffs_from_one_terminal_anchor() -> None:
    summary = run_intrinsic_competence_chain()

    assert summary["pass"] is True
    assert summary["root_reward_source"] == "terminal outcome only"
    assert summary["gates"]["intermediate_reward_labels_used"] is False
    assert summary["grounding_levels"] == {
        "cell_000": 0,
        "cell_001": 1,
        "cell_002": 2,
    }
    assert summary["grounding_ancestors"]["cell_002"] == ["cell_000", "cell_001"]


def test_planted_chain_writes_compact_auditable_artifact(tmp_path: Path) -> None:
    output = tmp_path / "intrinsic_chain.json"
    summary = run_intrinsic_competence_chain(
        ChainBenchmarkConfig(output_path=str(output))
    )

    saved = json.loads(output.read_text(encoding="utf-8"))
    assert saved["pass"] is True
    assert saved["values"] == summary["values"]
    assert output.stat().st_size < 100_000
