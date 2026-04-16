import json
import importlib.util
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from recon_lite import FormalReConEngine, ReConEngine
from recon_lite.graph import Graph, LinkType, Node, NodeType
from recon_lite_chess.graph.builder import (
    build_graph_from_topology,
    ensure_formal_pairs,
    validate_formal_pairs,
)
from recon_lite_chess.spawn_point import SpawnPoint, TrialMicroScript
from recon_lite_chess.spawn_point import SpawnPointManager
from recon_lite_hector.engine import create_recon_engine

_baseline_to_recon = importlib.util.module_from_spec(
    importlib.util.spec_from_file_location(
        "baseline_to_recon",
        Path(__file__).resolve().parents[1] / "scripts" / "baseline_to_recon.py",
    )
)
assert _baseline_to_recon.__spec__ is not None
assert _baseline_to_recon.__spec__.loader is not None
_baseline_to_recon.__spec__.loader.exec_module(_baseline_to_recon)
create_root_node = _baseline_to_recon.create_root_node
create_hub_node = _baseline_to_recon.create_hub_node
create_leg_micro_script = _baseline_to_recon.create_leg_micro_script


def test_engine_selector_preserves_pragmatic_default_and_exposes_formal():
    pragmatic = create_recon_engine(Graph())
    assert isinstance(pragmatic, ReConEngine)

    graph = Graph()
    graph.add_node(Node("root", NodeType.SCRIPT))
    graph.add_node(Node("sensor", NodeType.TERMINAL, predicate=lambda _n, _e: (True, True)))
    graph.add_hierarchy_pair("root", "sensor")

    formal = create_recon_engine(graph, mode="formal")
    assert isinstance(formal, FormalReConEngine)


def test_topology_builder_can_normalize_or_validate_formal_pairs(tmp_path):
    topology_path = tmp_path / "topology.json"
    topology_path.write_text(
        json.dumps(
            {
                "nodes": [
                    {"id": "root", "type": "SCRIPT"},
                    {"id": "sensor", "type": "TERMINAL"},
                ],
                "edges": [
                    {"src": "root", "dst": "sensor", "type": "SUB"},
                ],
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="requires reverse SUR"):
        build_graph_from_topology(topology_path, formal_pairs="validate")

    graph = build_graph_from_topology(topology_path, formal_pairs="normalize")
    validate_formal_pairs(graph)
    assert _has_edge(graph, "root", "sensor", LinkType.SUB)
    assert _has_edge(graph, "sensor", "root", LinkType.SUR)


def test_baseline_compiled_triplet_topology_passes_formal_pair_validation(tmp_path):
    topology = {"nodes": {}, "edges": [], "meta": {}}
    sensor = _dummy_sensor()
    actuator = _dummy_actuator()

    create_root_node(topology)
    create_hub_node(topology)
    create_leg_micro_script(topology, actuator, [sensor])

    topology_path = tmp_path / "baseline_triplet.json"
    topology_path.write_text(json.dumps(topology), encoding="utf-8")

    graph = build_graph_from_topology(topology_path, formal_pairs="validate")

    validate_formal_pairs(graph)
    assert _has_edge(graph, "precond_7", "act_script_7", LinkType.POR)
    assert _has_edge(graph, "act_script_7", "precond_7", LinkType.RET)
    assert _has_edge(graph, "act_script_7", "postcond_7", LinkType.POR)
    assert _has_edge(graph, "postcond_7", "act_script_7", LinkType.RET)


def test_spawn_point_promoted_trial_materializes_formal_triplet_pairs():
    graph = Graph()
    graph.add_node(Node("leg_parent", NodeType.SCRIPT))
    sensor = Node("sensor_1", NodeType.TERMINAL, predicate=lambda _n, _e: (True, True))
    sensor.meta.update({
        "readout_type": "identity",
        "feature_mask_keys": ["feature_0"],
        "readout_params": {},
    })
    graph.add_node(sensor)

    manager = SpawnPointManager(graph=graph)
    spawn_point = SpawnPoint(spawn_point_id="spawn_leg_parent", leg_id="leg_parent")
    trial = TrialMicroScript(
        trial_id="trial_1",
        spawn_point_id=spawn_point.spawn_point_id,
        sensor_ids=["sensor_1"],
        delta_mean=np.array([1.0], dtype=np.float32),
    )

    manager._promote_trial_to_graph(spawn_point, trial)

    validate_formal_pairs(graph)
    assert _has_edge(graph, "trial_1_precond", "trial_1_act_script", LinkType.POR)
    assert _has_edge(graph, "trial_1_act_script", "trial_1_precond", LinkType.RET)
    assert _has_edge(graph, "trial_1_act_script", "trial_1_postcond", LinkType.POR)
    assert _has_edge(graph, "trial_1_postcond", "trial_1_act_script", LinkType.RET)
    assert _has_edge(graph, "trial_1_precond", "sensor_1", LinkType.SUB)
    assert _has_edge(graph, "sensor_1", "trial_1_precond", LinkType.SUR)


def test_ensure_formal_pairs_adds_missing_ret_for_existing_por():
    graph = Graph()
    graph.add_node(Node("parent", NodeType.SCRIPT))
    graph.add_node(Node("a", NodeType.SCRIPT))
    graph.add_node(Node("b", NodeType.SCRIPT))
    graph.add_node(Node("a_done", NodeType.TERMINAL, predicate=lambda _n, _e: (True, True)))
    graph.add_node(Node("b_done", NodeType.TERMINAL, predicate=lambda _n, _e: (True, True)))
    graph.add_hierarchy_pair("parent", "a")
    graph.add_hierarchy_pair("parent", "b")
    graph.add_hierarchy_pair("a", "a_done")
    graph.add_hierarchy_pair("b", "b_done")
    graph.add_edge("a", "b", LinkType.POR)

    assert ensure_formal_pairs(graph) == 1
    assert _has_edge(graph, "b", "a", LinkType.RET)
    validate_formal_pairs(graph)


def _dummy_sensor():
    return SimpleNamespace(
        id=3,
        stage=0,
        xp=0.8,
        is_mature=True,
        activations=10,
        cycles_alive=5,
        sensor_spec=SimpleNamespace(
            feature_mask=np.array([True, False, False], dtype=bool),
            readout_type="identity",
            readout_params={},
        ),
    )


def _dummy_actuator():
    return SimpleNamespace(
        id=7,
        stage=1,
        xp=0.9,
        activations=12,
        cycles_alive=6,
        actuator_spec=SimpleNamespace(
            sensor_indices=[0],
            goal_delta=np.array([1.0], dtype=np.float32),
            match_mode="l2",
        ),
    )


def _has_edge(graph, src, dst, ltype):
    return any(e.src == src and e.dst == dst and e.ltype == ltype for e in graph.edges)
