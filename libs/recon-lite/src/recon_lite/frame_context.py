"""Typed, side-effect-free frame-local terminal evaluation."""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from enum import Enum
import math
from types import MappingProxyType
from typing import Any, Mapping, MutableMapping

from .graph import Graph, Node, NodeState


class FrameKind(str, Enum):
    REAL = "real"
    VIRTUAL = "virtual"


@dataclass(frozen=True)
class FrameContext:
    """Immutable identity and snapshotted values for one evaluation frame."""
    frame_id: str
    kind: FrameKind
    values: Mapping[str, Any] = field(default_factory=dict)
    parent_frame_id: str | None = None
    hypothetical_action: str | None = None

    def __post_init__(self) -> None:
        if not self.frame_id:
            raise ValueError("frame_id must be non-empty")
        object.__setattr__(self, "kind", FrameKind(self.kind))
        object.__setattr__(
            self,
            "values",
            MappingProxyType(deepcopy(dict(self.values))),
        )
        if self.kind is FrameKind.REAL and self.hypothetical_action is not None:
            raise ValueError("real frames cannot carry a hypothetical action")

    @property
    def is_virtual(self) -> bool:
        return self.kind is FrameKind.VIRTUAL

    def to_env_overlay(self) -> dict[str, Any]:
        """Create one deep-isolated runtime snapshot for terminal evaluation.

        Direct environment values and ``__frame_context__.values`` refer to the
        same isolated objects within the evaluation. Neither path exposes the
        values retained by this source context or the caller's original values.
        """

        runtime = FrameContext(
            frame_id=self.frame_id,
            kind=self.kind,
            values=self.values,
            parent_frame_id=self.parent_frame_id,
            hypothetical_action=self.hypothetical_action,
        )
        overlay = dict(runtime.values)
        overlay["__frame_context__"] = runtime
        return overlay


@dataclass(frozen=True)
class ChildResponse:
    """Frame-local child contract with applicability separate from provenance.

    ``confirmed`` remains the wire-compatible alias for ``available``. It does
    not mean merely that the child policy emitted an action.
    """
    child_id: str
    confirmed: bool
    expected_value: float
    uncertainty: float
    grounded: bool
    grounding_source: str | None = None
    policy_response: bool | None = None
    available: bool | None = None

    def __post_init__(self) -> None:
        if not self.child_id:
            raise ValueError("child_id must be non-empty")
        if not math.isfinite(self.expected_value) or not -1 <= self.expected_value <= 1:
            raise ValueError("expected_value must be finite and in [-1, 1]")
        if not math.isfinite(self.uncertainty) or not 0 <= self.uncertainty <= 1:
            raise ValueError("uncertainty must be finite and in [0, 1]")
        if self.grounded and not self.grounding_source:
            raise ValueError("grounded child responses require grounding_source")
        policy_response = bool(self.confirmed) if self.policy_response is None else bool(self.policy_response)
        available = bool(self.confirmed) if self.available is None else bool(self.available)
        if available and not policy_response:
            raise ValueError("AVAILABLE requires POLICY_RESPONSE")
        object.__setattr__(self, "policy_response", policy_response)
        object.__setattr__(self, "available", available)
        object.__setattr__(self, "confirmed", available)

    @property
    def selection_strength(self) -> float:
        if not self.grounded or not self.available:
            return 0.0
        return max(0.0, self.expected_value) * (1.0 - self.uncertainty)

    def to_dict(self) -> dict[str, Any]:
        return {
            "child_id": self.child_id,
            "policy_response": self.policy_response,
            "available": self.available,
            "confirmed": self.confirmed,
            "expected_value": self.expected_value,
            "uncertainty": self.uncertainty,
            "grounded": self.grounded,
            "grounding_source": self.grounding_source,
            "selection_strength": self.selection_strength,
        }


class VirtualFrameSideEffectError(RuntimeError):
    pass


class DreamStateLeakError(RuntimeError):
    pass


class FrameEffectFirewall:
    """Capability object that rejects persistent dream-time effects."""
    def __init__(self) -> None:
        self.attempts: list[dict[str, Any]] = []

    def _reject(self, operation: str, *args: Any, **kwargs: Any) -> None:
        self.attempts.append({
            "operation": operation,
            "args": [repr(x) for x in args],
            "kwargs": {k: repr(v) for k, v in sorted(kwargs.items())},
        })
        raise VirtualFrameSideEffectError(
            f"virtual frames cannot perform persistent effect {operation}"
        )

    def actuate(self, *args: Any, **kwargs: Any) -> None:
        self._reject("actuate", *args, **kwargs)
    def reward(self, *args: Any, **kwargs: Any) -> None:
        self._reject("reward", *args, **kwargs)
    def update_weight(self, *args: Any, **kwargs: Any) -> None:
        self._reject("update_weight", *args, **kwargs)
    def update_lifecycle(self, *args: Any, **kwargs: Any) -> None:
        self._reject("update_lifecycle", *args, **kwargs)
    def update_reservoir(self, *args: Any, **kwargs: Any) -> None:
        self._reject("update_reservoir", *args, **kwargs)
    def update_topology(self, *args: Any, **kwargs: Any) -> None:
        self._reject("update_topology", *args, **kwargs)
    def set_maturity(self, *args: Any, **kwargs: Any) -> None:
        self._reject("set_maturity", *args, **kwargs)


@dataclass(frozen=True)
class VirtualFrameEvaluation:
    frame_id: str
    root_id: str
    root_state: NodeState
    node_states: Mapping[str, NodeState]
    activations: Mapping[str, float]
    effect_attempts: tuple[Mapping[str, Any], ...]
    trace: tuple[Mapping[str, Any], ...]


def child_response_terminal(node: Node, env: Mapping[str, Any]) -> tuple[bool, bool]:
    """Graph-native CHILD_RESPONSE terminal backend."""
    frame = env.get("__frame_context__")
    response = env.get(str(node.meta.get("response_key", "child_response")))
    if not isinstance(frame, FrameContext):
        node.meta["last_failure"] = "missing_frame_context"
        node.activation.value = 0.0
        return True, False
    if not isinstance(response, ChildResponse):
        node.meta["last_failure"] = "missing_child_response"
        node.activation.value = 0.0
        return True, False
    node.activation.value = response.selection_strength
    node.meta.update({
        "last_frame_id": frame.frame_id,
        "last_frame_kind": frame.kind.value,
        "last_child_response": response.to_dict(),
    })
    success = bool(response.grounded and response.available)
    if not success:
        node.meta["last_failure"] = "child_not_grounded_and_available"
    return True, success


def prediction_residual_terminal(
    node: Node,
    env: Mapping[str, Any],
) -> tuple[bool, bool]:
    """Measure raw imagined-versus-observed error on a real frame.

    This diagnostic is deliberately not actionable surprise. Confidence,
    calibration, and effective experience must gate any later attention signal.
    """
    frame = env.get("__frame_context__")
    imagined = env.get(str(node.meta.get("imagined_key", "imagined_child_response")))
    observed = env.get(str(node.meta.get("observed_key", "observed_child_response")))
    if not isinstance(frame, FrameContext) or frame.kind is not FrameKind.REAL:
        node.meta["last_failure"] = "prediction_residual_requires_real_frame"
        node.activation.value = 0.0
        return True, False
    if not isinstance(imagined, ChildResponse) or not isinstance(observed, ChildResponse):
        node.meta["last_failure"] = "missing_prediction_response"
        node.activation.value = 0.0
        return True, False
    if not imagined.grounded or not observed.grounded:
        node.meta["last_failure"] = "prediction_response_not_grounded"
        node.activation.value = 0.0
        return True, False
    raw = abs(imagined.expected_value - observed.expected_value)
    node.activation.value = min(1.0, raw / 2.0)
    node.meta.update({"last_frame_id": frame.frame_id, "raw_prediction_residual": raw})
    return True, True


def prediction_surprise_terminal(
    node: Node,
    env: Mapping[str, Any],
) -> tuple[bool, bool]:
    """Backward-compatible alias for the raw prediction-residual terminal."""

    done, success = prediction_residual_terminal(node, env)
    if "raw_prediction_residual" in node.meta:
        node.meta["raw_prediction_surprise"] = node.meta[
            "raw_prediction_residual"
        ]
    return done, success


class VirtualFrameExecutor:
    """Evaluate a cloned graph with value isolation and capability protection.

    This boundary protects declared state and supplied capabilities. It is not,
    and does not claim to be, a universal sandbox for arbitrary Python closures.
    """
    def evaluate(
        self,
        graph: Graph,
        root_id: str,
        frame: FrameContext,
        *,
        env: Mapping[str, Any] | None = None,
        protected_state: MutableMapping[str, Any] | None = None,
        max_ticks: int = 32,
    ) -> VirtualFrameEvaluation:
        if frame.kind is not FrameKind.VIRTUAL:
            raise ValueError("VirtualFrameExecutor requires a virtual FrameContext")
        if root_id not in graph.nodes:
            raise KeyError(f"unknown root node: {root_id}")
        original_graph = deepcopy(graph)
        graph_before = _graph_runtime_state(graph)
        state_before = deepcopy(protected_state) if protected_state is not None else None
        virtual_graph = deepcopy(graph)
        scoped_env = deepcopy(dict(env or {}))
        scoped_env.update(frame.to_env_overlay())
        firewall = FrameEffectFirewall()
        scoped_env["__frame_effects__"] = firewall

        from .formal_engine import FormalReConEngine
        engine = FormalReConEngine(virtual_graph, record_trace=True)
        engine.request(root_id)
        engine.run(
            max_ticks=max_ticks,
            env=scoped_env,
            until=lambda e: e.g.nodes[root_id].state in {NodeState.CONFIRMED, NodeState.FAILED},
        )
        graph_leaked = _graph_runtime_state(graph) != graph_before
        state_leaked = protected_state is not None and protected_state != state_before
        if graph_leaked:
            graph.__dict__.clear()
            graph.__dict__.update(deepcopy(original_graph.__dict__))
        if state_leaked and protected_state is not None and state_before is not None:
            protected_state.clear()
            protected_state.update(state_before)
        if graph_leaked or state_leaked:
            target = "graph" if graph_leaked else "protected state"
            raise DreamStateLeakError(
                f"virtual evaluation mutated persistent {target}; mutation was rolled back"
            )
        return VirtualFrameEvaluation(
            frame_id=frame.frame_id,
            root_id=root_id,
            root_state=virtual_graph.nodes[root_id].state,
            node_states=MappingProxyType({k: n.state for k, n in virtual_graph.nodes.items()}),
            activations=MappingProxyType({k: float(n.activation.value) for k, n in virtual_graph.nodes.items()}),
            effect_attempts=tuple(dict(x) for x in firewall.attempts),
            trace=tuple(engine.trace),
        )


def _graph_runtime_state(graph: Graph) -> Any:
    return deepcopy((
        graph.to_snapshot(),
        {
            nid: (
                n.state, n.tick_entered, n.activation.value, n.activation.target,
                n.activation.k, n.activation.meta, n.meta,
            )
            for nid, n in graph.nodes.items()
        },
    ))
