import json

from recon_lite_chess.autogrowth import (
    KRKPositionSet,
    TopologicalGrowthRunwayConfig,
    build_triplet_chain_view,
    run_topological_growth_runway,
    validate_learner_record,
)


def _candidate(key: str, before_edge: float, after_edge: float) -> dict:
    return {
        "candidate_key": key,
        "source_candidate_key": key.replace("m16", "m15"),
        "before_cluster": {
            "feature_names": ["black_king_nearest_edge_distance", "rook_attacked_by_black"],
            "prototype": {
                "black_king_nearest_edge_distance": before_edge,
                "rook_attacked_by_black": 0.0,
            },
        },
        "after_cluster": {
            "feature_names": ["black_king_nearest_edge_distance", "rook_attacked_by_black"],
            "prototype": {
                "black_king_nearest_edge_distance": after_edge,
                "rook_attacked_by_black": 0.0,
            },
        },
        "script_plan": {
            "node_type": "SCRIPT",
            "actions": [],
            "relation_plan": {
                "chooses_move_directly": False,
            },
        },
    }


def test_tg17_builds_terminal_triplet_chain_view() -> None:
    candidates = [
        _candidate("m16_fragment_a", before_edge=2.0, after_edge=1.0),
        _candidate("m16_fragment_b", before_edge=1.0, after_edge=0.0),
    ]
    view = build_triplet_chain_view(candidates, max_distance=0.1, max_edges=10)

    assert view["triplet_model"] == "before_terminal -> actuator_delta -> after_terminal"
    assert view["direct_move_choice"] is False
    assert view["runtime_provider_override"] is False
    assert view["chainable"] is True
    assert view["chain_edge_count"] == 1
    assert view["chain_edges"][0]["source_after_candidate_key"] == "m16_fragment_a"
    assert view["chain_edges"][0]["target_before_candidate_key"] == "m16_fragment_b"
    assert view["triplets"][0]["actuator_delta"]["represented_as"] == "ACTION vector between terminal states"
    validate_learner_record(candidates)


def test_tg17_runway_writes_control_and_curriculum_artifact(tmp_path) -> None:
    fen = "8/8/8/8/2K5/6k1/2R5/8 w - - 0 1"
    result = run_topological_growth_runway(
        config=TopologicalGrowthRunwayConfig(
            seed=1,
            train_count=2,
            heldout_weakness_count=1,
            heldout_broader_count=0,
            min_support=1,
            max_candidates=2,
            min_sequence_credit=0.01,
            horizon=4,
            activation_max_distance=1.0,
            chain_max_distance=4.0,
            legacy_manifest_paths=("does/not/exist.json",),
        ),
        positions=KRKPositionSet(seed=1, train=(fen, fen), heldout_weakness=(fen,), heldout_broader=()),
    )
    output = result.write_json(tmp_path / "tg17.json")
    payload = json.loads(output.read_text(encoding="utf-8"))

    assert payload["schema_version"] == "krk_autogrowth_tg_runway.v0"
    assert payload["research_milestone"]["name"] == "topological_growth"
    assert payload["legacy_predefined_topology_inventory"][0]["exists"] is False
    assert payload["triplet_chain_view"]["direct_move_choice"] is False
    assert payload["triplet_chain_view"]["runtime_provider_override"] is False
    assert payload["curriculum_decision"]["direct_move_override"] is False
    assert payload["curriculum_decision"]["runtime_teacher_or_provider"] is False
