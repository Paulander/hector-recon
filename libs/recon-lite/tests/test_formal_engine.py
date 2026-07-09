import pytest

from recon_lite import FormalMessage, FormalReConEngine, Graph, LinkType, Node, NodeState, NodeType


def success_terminal(nid):
    return Node(nid, NodeType.TERMINAL, predicate=lambda _node, _env: (True, True))


def test_formal_validation_catches_missing_reverse_links():
    graph = Graph()
    graph.add_node(Node("root", NodeType.SCRIPT))
    graph.add_node(success_terminal("sensor"))
    graph.add_edge("root", "sensor", LinkType.SUB)

    with pytest.raises(ValueError, match="requires reverse SUR"):
        FormalReConEngine(graph)


def test_single_terminal_child_confirms_parent_through_sur():
    graph = Graph()
    graph.add_node(Node("root", NodeType.SCRIPT))
    graph.add_node(success_terminal("sensor"))
    graph.add_hierarchy_pair("root", "sensor")

    engine = FormalReConEngine(graph)
    engine.request("root")
    engine.run(max_ticks=12, until=lambda formal: formal.g.nodes["root"].state == NodeState.CONFIRMED)

    assert graph.nodes["sensor"].state == NodeState.CONFIRMED
    assert graph.nodes["root"].state == NodeState.CONFIRMED
    assert _message_seen(engine.trace, "sensor", "root", LinkType.SUR, FormalMessage.CONFIRM)


@pytest.mark.parametrize(
    ("left", "right", "confirmed"),
    [(False, False, False), (False, True, True), (True, False, True), (True, True, False)],
)
def test_formal_xor_confirmation_requires_exactly_one_child(left, right, confirmed):
    graph = Graph()
    graph.add_node(Node("xor", NodeType.SCRIPT, meta={"confirm_policy": "xor"}))
    graph.add_node(Node("left", NodeType.TERMINAL, predicate=lambda _node, _env: (True, left)))
    graph.add_node(Node("right", NodeType.TERMINAL, predicate=lambda _node, _env: (True, right)))
    graph.add_hierarchy_pair("xor", "left")
    graph.add_hierarchy_pair("xor", "right")

    engine = FormalReConEngine(graph)
    engine.request("xor")
    engine.run(
        max_ticks=12,
        until=lambda formal: formal.g.nodes["xor"].state in {NodeState.CONFIRMED, NodeState.FAILED},
    )

    assert (graph.nodes["xor"].state == NodeState.CONFIRMED) is confirmed


def test_subset_scheduler_updates_only_active_real_edges():
    graph = Graph()
    graph.add_node(Node("root", NodeType.SCRIPT))
    graph.add_node(success_terminal("active_sensor"))
    graph.add_node(success_terminal("inactive_sensor"))
    graph.add_hierarchy_pair("root", "active_sensor")
    graph.add_hierarchy_pair("root", "inactive_sensor")

    engine = FormalReConEngine(graph)
    engine.request("root")
    engine.run(
        max_ticks=12,
        active_nodes={"root", "active_sensor"},
        until=lambda formal: formal.g.nodes["active_sensor"].state == NodeState.CONFIRMED,
    )

    assert graph.nodes["active_sensor"].state == NodeState.CONFIRMED
    assert graph.nodes["inactive_sensor"].state == NodeState.INACTIVE
    assert _message_seen(engine.trace, "root", "active_sensor", LinkType.SUB, FormalMessage.REQUEST)
    assert not _message_seen(engine.trace, "root", "inactive_sensor", LinkType.SUB, FormalMessage.REQUEST)


def test_ret_blocks_parent_confirmation_until_final_sequence_element_confirms():
    graph = _sequence_graph()
    engine = FormalReConEngine(graph)
    engine.request("root")
    engine.run(max_ticks=40, until=lambda formal: formal.g.nodes["root"].state == NodeState.CONFIRMED)

    assert graph.nodes["root"].state == NodeState.CONFIRMED
    assert graph.nodes["A"].state == NodeState.TRUE
    assert graph.nodes["B"].state == NodeState.TRUE
    assert graph.nodes["C"].state == NodeState.CONFIRMED

    root_confirm_tick = _first_tick_with_state(engine.trace, "root", NodeState.CONFIRMED)
    c_confirm_tick = _first_tick_with_state(engine.trace, "C", NodeState.CONFIRMED)

    assert root_confirm_tick is not None
    assert c_confirm_tick is not None
    assert root_confirm_tick > c_confirm_tick
    assert _message_seen(engine.trace, "B", "A", LinkType.RET, FormalMessage.INHIBIT_CONFIRM)
    assert _message_seen(engine.trace, "C", "B", LinkType.RET, FormalMessage.INHIBIT_CONFIRM)


def _sequence_graph():
    graph = Graph()
    for nid in ["root", "A", "B", "C"]:
        graph.add_node(Node(nid, NodeType.SCRIPT))
    for nid in ["A_done", "B_done", "C_done"]:
        graph.add_node(success_terminal(nid))

    for child in ["A", "B", "C"]:
        graph.add_hierarchy_pair("root", child)
        graph.add_hierarchy_pair(child, f"{child}_done")
    graph.add_sequence_pair("A", "B")
    graph.add_sequence_pair("B", "C")
    return graph


def _first_tick_with_state(trace, nid, state):
    for frame in trace:
        if frame["states_after"][nid] == state.name:
            return frame["tick"]
    return None


def _message_seen(trace, src, dst, link_type, message):
    for frame in trace:
        for edge_message in frame["messages"]:
            if (
                edge_message["src"] == src
                and edge_message["dst"] == dst
                and edge_message["link_type"] == link_type.name
                and edge_message["message"] == message.value
            ):
                return True
    return False
