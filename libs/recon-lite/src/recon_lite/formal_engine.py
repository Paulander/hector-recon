"""Article-style symbolic ReCoN message-passing executor.

``FormalReConEngine`` is deliberately separate from ``ReConEngine``. The
existing engine remains the pragmatic, high-level executor used by legacy
applications. This module implements the explicit SUB/SUR/POR/RET message
semantics from the Bach/Herger ReCoN state-machine description.
"""

from dataclasses import dataclass
from enum import Enum
import math
from typing import Any, Callable, Dict, Iterable, List, Optional

from .graph import Graph, LinkType, Node, NodeState, NodeType
from .frame_context import FrameContext


class FormalMessage(Enum):
    """Messages emitted by the symbolic ReCoN state machine."""

    REQUEST = "request"
    WAIT = "wait"
    CONFIRM = "confirm"
    FAIL = "fail"
    INHIBIT_REQUEST = "inhibit_request"
    INHIBIT_CONFIRM = "inhibit_confirm"


@dataclass(frozen=True)
class EdgeMessage:
    """One message sent over one graph edge during a formal tick."""

    tick: int
    src: str
    dst: str
    link_type: LinkType
    message: FormalMessage

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tick": self.tick,
            "src": self.src,
            "dst": self.dst,
            "link_type": self.link_type.name,
            "message": self.message.value,
        }


class FormalReConEngine:
    """
    Explicit symbolic ReCoN executor.

    Each ``step`` is a two-phase update:

    1. emit messages from every node based on its state at tick start
    2. group incoming messages by target and compute all next states

    This mirrors the message-passing definition. The compact neural equations
    are a separate implementation milestone and are not mixed into this class.
    """

    def __init__(
        self,
        graph: Graph,
        *,
        validate_pairs: bool = True,
        record_trace: bool = True,
    ) -> None:
        if validate_pairs:
            graph.validate_formal_pairs()
        self.g = graph
        self.tick = 0
        self.trace: List[Dict[str, Any]] = []
        self._external_requests = set()
        self.record_trace = record_trace

    def request(self, nid: str) -> None:
        """Request validation of a root script."""
        if nid not in self.g.nodes:
            raise KeyError(f"Unknown node id: {nid}")
        self._external_requests.add(nid)
        node = self.g.nodes[nid]
        # Actuator emissions are one-decision runtime state. Clearing them at
        # request time prevents a restored or reused graph from exposing a
        # stale choice to its environment adapter.
        node.meta.pop("emitted_actuator_identity", None)
        node.meta.pop("choice_selected_child", None)
        if node.state == NodeState.INACTIVE:
            node.state = NodeState.REQUESTED
            node.tick_entered = self.tick

    def clear_request(self, nid: str) -> None:
        """Remove an external root request."""
        self._external_requests.discard(nid)

    def step(self, env: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Run one formal two-phase tick and return its trace frame."""
        return self.step_subset(env=env, active_nodes=None)

    def step_subset(
        self,
        env: Optional[Dict[str, Any]] = None,
        *,
        active_nodes: Optional[Iterable[str]] = None,
    ) -> Dict[str, Any]:
        """Run one formal tick, optionally restricted to an active node set.

        The subset mode is a scheduler optimization: messages still travel only
        on real graph edges and node transitions use the same state machine.
        Nodes outside the set are left untouched.
        """
        env = env or {}
        active_set = None if active_nodes is None else set(active_nodes)
        self.tick += 1
        states_before = self._node_states(active_set) if self.record_trace else {}
        messages = self._emit_messages(active_set)
        incoming = self._group_by_target(messages)
        if active_set is None:
            node_items = (
                (nid, node)
                for nid, node in self.g.nodes.items()
                if node.state != NodeState.INACTIVE
                or incoming.get(nid)
                or nid in self._external_requests
            )
        else:
            node_items = (
                (nid, self.g.nodes[nid])
                for nid in active_set
                if nid in self.g.nodes
                and (
                    self.g.nodes[nid].state != NodeState.INACTIVE
                    or incoming.get(nid)
                    or nid in self._external_requests
                )
            )
        next_states = {
            nid: self._next_state(node, incoming.get(nid, []), env)
            for nid, node in node_items
        }

        for nid, state in next_states.items():
            node = self.g.nodes[nid]
            if node.state != state:
                node.state = state
                node.tick_entered = self.tick

        frame = {"tick": self.tick}
        if self.record_trace:
            frame = {
                "tick": self.tick,
                "states_before": states_before,
                "messages": [message.to_dict() for message in messages],
                "states_after": self._node_states(active_set),
                "activations": {
                    nid: round(float(node.activation.value), 6)
                    for nid, node in self._iter_nodes(active_set)
                },
            }
            self.trace.append(frame)
        return frame

    def run(
        self,
        *,
        max_ticks: int = 32,
        env: Optional[Dict[str, Any]] = None,
        until: Optional[Callable[["FormalReConEngine"], bool]] = None,
        active_nodes: Optional[Iterable[str]] = None,
    ) -> List[Dict[str, Any]]:
        """Run formal ticks until ``max_ticks`` or an optional stop predicate."""
        active_set = None if active_nodes is None else set(active_nodes)
        for _ in range(max(0, max_ticks)):
            self.step_subset(env, active_nodes=active_set)
            if until is not None and until(self):
                break
        return self.trace

    def to_trace(self, *, name: str = "formal-recon") -> Dict[str, Any]:
        """Return a visualizer-neutral JSON-ready formal trace."""
        return {
            "schema_version": 1,
            "example": name,
            "engine": "FormalReConEngine",
            "graph": self.g.to_snapshot(),
            "frames": list(self.trace),
        }

    def emitted_actuator_identities(self, root_id: str) -> tuple[str, ...]:
        """Return actuator identities emitted by one formally confirmed root.

        The environment may execute this identity, but it must not reconstruct
        a winner from candidate scores. The anonymous ``choice`` genome
        primitive is the sole producer of this field.
        """

        root = self.g.nodes[root_id]
        if root.state != NodeState.CONFIRMED:
            return ()
        emitted = root.meta.get("emitted_actuator_identity")
        if emitted is None:
            return ()
        if isinstance(emitted, str):
            return (emitted,)
        if isinstance(emitted, (tuple, list)):
            return tuple(str(value) for value in emitted)
        raise TypeError("emitted_actuator_identity must be a string or sequence")

    def emit_exactly_one_actuator(self, root_id: str) -> str:
        """Return the graph emission or fail hard on zero/multiple authority."""

        emitted = self.emitted_actuator_identities(root_id)
        if len(emitted) != 1:
            raise RuntimeError(
                f"formal graph emitted {len(emitted)} actuators for {root_id!r}"
            )
        return emitted[0]

    def _emit_messages(self, active_nodes: Optional[set[str]] = None) -> List[EdgeMessage]:
        messages: List[EdgeMessage] = []
        if active_nodes is not None:
            for src in active_nodes:
                if src not in self.g.nodes:
                    continue
                state = self.g.nodes[src].state
                if state == NodeState.INACTIVE:
                    continue
                for link_type in LinkType:
                    for dst in self.g.out.get((src, link_type), []):
                        if dst not in active_nodes:
                            continue
                        message = self._message_for(link_type, state)
                        if (
                            message == FormalMessage.REQUEST
                            and link_type == LinkType.SUB
                            and not self._lazy_sub_target_selected(src, dst)
                        ):
                            continue
                        if message is not None:
                            messages.append(
                                EdgeMessage(
                                    tick=self.tick,
                                    src=src,
                                    dst=dst,
                                    link_type=link_type,
                                    message=message,
                                )
                            )
            return messages
        for edge in self.g.edges:
            state = self.g.nodes[edge.src].state
            if state == NodeState.INACTIVE:
                continue
            message = self._message_for(edge.ltype, state)
            if (
                message == FormalMessage.REQUEST
                and edge.ltype == LinkType.SUB
                and not self._lazy_sub_target_selected(edge.src, edge.dst)
            ):
                continue
            if message is not None:
                messages.append(
                    EdgeMessage(
                        tick=self.tick,
                        src=edge.src,
                        dst=edge.dst,
                        link_type=edge.ltype,
                        message=message,
                    )
                )
        return messages

    def _lazy_sub_target_selected(self, src: str, dst: str) -> bool:
        node = self.g.nodes[src]
        if str(node.meta.get("request_policy", "")).lower() != "lazy_k_of_n":
            return True
        if str(node.meta.get("confirm_policy", "")).lower() not in {"k_of_n", "quorum"}:
            return True
        threshold = int(node.meta.get("confirm_k", node.meta.get("quorum_k", 1)))
        if threshold != 1:
            return True

        children = self.g.children(src)
        if any(self.g.nodes[child].state in (NodeState.TRUE, NodeState.CONFIRMED) for child in children):
            return False

        active_states = {NodeState.REQUESTED, NodeState.ACTIVE, NodeState.SUPPRESSED, NodeState.WAITING}
        for child in children:
            if self.g.nodes[child].state in active_states:
                return dst == child
        for child in children:
            if self.g.nodes[child].state == NodeState.INACTIVE:
                return dst == child
        return False

    def _message_for(self, link_type: LinkType, state: NodeState) -> Optional[FormalMessage]:
        if state in (NodeState.REQUESTED, NodeState.ACTIVE, NodeState.SUPPRESSED, NodeState.WAITING, NodeState.FAILED):
            if link_type == LinkType.POR:
                return FormalMessage.INHIBIT_REQUEST
        if state in (
            NodeState.REQUESTED,
            NodeState.ACTIVE,
            NodeState.SUPPRESSED,
            NodeState.WAITING,
            NodeState.TRUE,
            NodeState.CONFIRMED,
            NodeState.FAILED,
        ):
            if link_type == LinkType.RET:
                return FormalMessage.INHIBIT_CONFIRM
        if state in (NodeState.ACTIVE, NodeState.WAITING):
            if link_type == LinkType.SUB:
                return FormalMessage.REQUEST
        if state in (NodeState.REQUESTED, NodeState.ACTIVE, NodeState.WAITING):
            if link_type == LinkType.SUR:
                return FormalMessage.WAIT
        if state == NodeState.CONFIRMED and link_type == LinkType.SUR:
            return FormalMessage.CONFIRM
        if state == NodeState.FAILED and link_type == LinkType.SUR:
            return FormalMessage.FAIL
        return None

    def _group_by_target(self, messages: Iterable[EdgeMessage]) -> Dict[str, List[EdgeMessage]]:
        grouped: Dict[str, List[EdgeMessage]] = {}
        for message in messages:
            grouped.setdefault(message.dst, []).append(message)
        return grouped

    def _next_state(
        self,
        node: Node,
        incoming: List[EdgeMessage],
        env: Dict[str, Any],
    ) -> NodeState:
        request = self._has(incoming, FormalMessage.REQUEST) or node.nid in self._external_requests
        inhibit_request = self._has(incoming, FormalMessage.INHIBIT_REQUEST)
        inhibit_confirm = self._has(incoming, FormalMessage.INHIBIT_CONFIRM)
        confirm = self._has(incoming, FormalMessage.CONFIRM)
        fail = self._has(incoming, FormalMessage.FAIL)
        wait = self._has(incoming, FormalMessage.WAIT)

        if node.ntype == NodeType.TERMINAL:
            return self._next_terminal_state(node, request, inhibit_request, env)

        if node.state == NodeState.INACTIVE:
            return NodeState.REQUESTED if request else NodeState.INACTIVE
        if node.state == NodeState.REQUESTED:
            return NodeState.SUPPRESSED if inhibit_request else NodeState.ACTIVE
        if node.state == NodeState.SUPPRESSED:
            if not request:
                return NodeState.INACTIVE
            return NodeState.SUPPRESSED if inhibit_request else NodeState.REQUESTED
        if node.state == NodeState.ACTIVE:
            return NodeState.WAITING
        if node.state == NodeState.WAITING:
            choice_state = self._next_choice_script_state(node)
            if choice_state is not None:
                return choice_state
            quorum_state = self._next_quorum_script_state(node)
            if quorum_state is not None:
                return quorum_state
            if confirm:
                return NodeState.TRUE
            if fail and not wait:
                return NodeState.FAILED
            return NodeState.WAITING
        if node.state == NodeState.TRUE:
            return NodeState.TRUE if inhibit_confirm else NodeState.CONFIRMED
        return node.state

    def _next_terminal_state(
        self,
        node: Node,
        request: bool,
        inhibit_request: bool,
        env: Dict[str, Any],
    ) -> NodeState:
        if node.state == NodeState.INACTIVE:
            return NodeState.REQUESTED if request else NodeState.INACTIVE
        if node.state == NodeState.REQUESTED:
            return NodeState.SUPPRESSED if inhibit_request else NodeState.ACTIVE
        if node.state == NodeState.SUPPRESSED:
            if not request:
                return NodeState.INACTIVE
            return NodeState.SUPPRESSED if inhibit_request else NodeState.REQUESTED
        if node.state in (NodeState.ACTIVE, NodeState.WAITING):
            return self._evaluate_terminal(node, env)
        if node.state == NodeState.TRUE:
            return NodeState.CONFIRMED
        return node.state

    def _evaluate_terminal(self, node: Node, env: Dict[str, Any]) -> NodeState:
        if node.predicate is None:
            return NodeState.TRUE
        try:
            env["__graph__"] = self.g
            done, success = node.predicate(node, self._env_for_node(node.nid, env))
        except Exception:
            return NodeState.FAILED
        if not done:
            return NodeState.WAITING
        return NodeState.TRUE if success else NodeState.FAILED

    def _env_for_node(self, nid: str, env: Dict[str, Any]) -> Dict[str, Any]:
        virtual_frames = env.get("virtual_frames")
        if not isinstance(virtual_frames, dict):
            return env

        lineage: list[str] = []
        cur: Optional[str] = nid
        while cur is not None:
            lineage.append(cur)
            cur = self.g.parent_of(cur)

        overlay: Dict[str, Any] = {}
        for node_id in reversed(lineage):
            frame = virtual_frames.get(node_id)
            if isinstance(frame, FrameContext):
                overlay.update(frame.to_env_overlay())
            elif isinstance(frame, dict):
                overlay.update(frame)

        if not overlay:
            return env
        scoped_env = dict(env)
        scoped_env.update(overlay)
        scoped_env["__graph__"] = self.g
        scoped_env["__root_env__"] = env
        return scoped_env

    def _next_choice_script_state(self, node: Node) -> Optional[NodeState]:
        """Anonymous exactly-one arbitration over settled graph options.

        Each child owns an activation and actuator identity. The primitive
        waits for every option and declared strength source, selects one
        confirmed option, and emits one identity. It sees no domain semantics.
        """

        if str(node.meta.get("confirm_policy", "")).lower() != "choice":
            return None
        children = self.g.children(node.nid)
        if not children:
            return NodeState.FAILED
        terminal_states = {NodeState.TRUE, NodeState.CONFIRMED, NodeState.FAILED}
        strength_nodes: set[str] = set()
        for child_id in children:
            child = self.g.nodes[child_id]
            strength_nodes.update(map(str, child.meta.get("choice_strength_node_ids", ())))
        if any(
            child_id not in self.g.nodes
            or self.g.nodes[child_id].state not in terminal_states
            for child_id in (*children, *sorted(strength_nodes))
        ):
            return NodeState.WAITING

        confirmed = [
            self.g.nodes[child_id]
            for child_id in children
            if self.g.nodes[child_id].state in {NodeState.TRUE, NodeState.CONFIRMED}
        ]
        if not confirmed:
            return NodeState.FAILED

        def strength(option: Node) -> float:
            ids = tuple(sorted(map(
                str, option.meta.get("choice_strength_node_ids", ())
            )))
            require_all = bool(option.meta.get("choice_strength_require_all", False))
            if not ids:
                return float(option.activation.value)
            sources = [self.g.nodes[source_id] for source_id in ids]
            if require_all and any(
                source.state not in {NodeState.TRUE, NodeState.CONFIRMED}
                for source in sources
            ):
                return 0.0
            values = [float(source.activation.value) for source in sources]
            aggregation = str(
                option.meta.get("choice_strength_aggregation", "minimum")
            ).lower()
            if aggregation == "minimum":
                return min(values, default=0.0)
            if aggregation == "mean":
                return math.fsum(values) / max(1, len(values))
            if aggregation == "sum":
                return math.fsum(values)
            raise ValueError(f"unsupported anonymous choice aggregation: {aggregation}")

        ranked = sorted(
            ((strength(option), option.nid, option) for option in confirmed),
            key=lambda row: (row[0], row[1]),
            reverse=True,
        )
        selected_strength, selected_id, selected = ranked[0]
        actuator_identity = selected.meta.get("actuator_identity")
        if not isinstance(actuator_identity, str) or not actuator_identity:
            return NodeState.FAILED
        for _value, _child_id, option in ranked:
            option.meta["choice_selected"] = option.nid == selected_id
        selected.activation.value = selected_strength
        node.activation.value = selected_strength
        node.meta["choice_selected_child"] = selected_id
        node.meta["emitted_actuator_identity"] = actuator_identity
        return NodeState.TRUE

    def _next_quorum_script_state(self, node: Node) -> Optional[NodeState]:
        declared_policy = node.meta.get("confirm_policy")
        if declared_policy is None:
            # Unspecified scripts retain the legacy message-race behavior.
            # Only an explicit policy opts into settled child-state aggregation.
            return None
        policy = str(declared_policy).lower()
        if policy not in {"and", "or", "xor", "k_of_n", "quorum"}:
            return None

        children = self.g.children(node.nid)
        if not children:
            return None
        if policy == "and":
            threshold = len(children)
        elif policy == "or":
            threshold = 1
        else:
            threshold = int(node.meta.get("confirm_k", node.meta.get("quorum_k", 1)))
        threshold = max(1, min(threshold, len(children)))

        confirmed = sum(1 for child in children if self.g.nodes[child].state == NodeState.CONFIRMED)
        failed = sum(1 for child in children if self.g.nodes[child].state == NodeState.FAILED)
        pending = len(children) - confirmed - failed
        if policy == "xor":
            if confirmed > 1:
                return NodeState.FAILED
            if pending == 0:
                return NodeState.TRUE if confirmed == 1 else NodeState.FAILED
            return NodeState.WAITING
        if confirmed >= threshold:
            return NodeState.TRUE
        if confirmed + pending < threshold:
            return NodeState.FAILED
        return NodeState.WAITING

    def _node_states(self, active_nodes: Optional[set[str]] = None) -> Dict[str, str]:
        return {nid: node.state.name for nid, node in self._iter_nodes(active_nodes)}

    def _iter_nodes(self, active_nodes: Optional[set[str]] = None) -> Iterable[tuple[str, Node]]:
        if active_nodes is None:
            return self.g.nodes.items()
        return ((nid, self.g.nodes[nid]) for nid in active_nodes if nid in self.g.nodes)

    def _has(self, incoming: List[EdgeMessage], message: FormalMessage) -> bool:
        return any(edge_message.message == message for edge_message in incoming)
