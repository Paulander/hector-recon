from pathlib import Path

from recon_lite_chess.autogrowth.approach_discovery_probe import (
    ApproachDiscoveryProbeConfig,
    run_approach_discovery_probe,
)


def test_phase29b_probe_writes_zero_leak_artifacts(tmp_path: Path) -> None:
    summary = run_approach_discovery_probe(
        config=ApproachDiscoveryProbeConfig(
            output_dir=str(tmp_path / "phase2_9b_probe"),
            seeds=(20272921,),
            train_row_limit=2,
            heldout_row_limit=2,
            top_atom_pool=12,
            max_atoms=8,
            max_quorums=4,
            min_atom_support=1,
            min_quorum_support=1,
            min_quorum_precision=0.0,
        )
    )

    assert (tmp_path / "phase2_9b_probe" / "design_spec.json").exists()
    assert (tmp_path / "phase2_9b_probe" / "summary.json").exists()
    assert summary["decision"]["all_seeds_leak_free"] is True
    assert summary["seed_results"]["20272921"]["structure"]["leak_count"] == 0
    assert summary["tables"]["wins_nonwins_repetitions_violations"]
    assert summary["tables"]["discovered_node_edge_counts"]
