"""Tiny grid-world example for discrete and continuous ReCoN execution."""

from __future__ import annotations

import argparse
import random
from dataclasses import dataclass
from typing import Iterable, List

from recon_lite import ActivationMode, EngineConfig, Graph, LinkType, Node, NodeState, NodeType, ReConEngine
from recon_lite.binding.manager import BindingInstance, BindingTable


@dataclass
class GridState:
    width: int = 5
    height: int = 5
    agent: tuple[int, int] = (0, 0)
    goal: tuple[int, int] = (4, 4)

    def signature(self) -> str:
        return f"{self.width}x{self.height}:agent={self.agent}:goal={self.goal}"

    def step_toward_goal(self) -> None:
        ax, ay = self.agent
        gx, gy = self.goal
        if ax < gx:
            ax += 1
        elif ax > gx:
            ax -= 1
        elif ay < gy:
            ay += 1
        elif ay > gy:
            ay -= 1
        self.agent = (ax, ay)


def build_graph() -> Graph:
    graph = Graph()
    graph.add_node(Node("root", NodeType.SCRIPT))
    graph.add_node(Node("sense", NodeType.SCRIPT))
    graph.add_node(Node("act", NodeType.SCRIPT))
    graph.add_node(Node("goal_sensor", NodeType.TERMINAL, predicate=_sense_goal))
    graph.add_node(Node("move_agent", NodeType.TERMINAL, predicate=_move_agent))
    graph.add_edge("root", "sense", LinkType.SUB)
    graph.add_edge("root", "act", LinkType.SUB)
    graph.add_edge("sense", "goal_sensor", LinkType.SUB)
    graph.add_edge("act", "move_agent", LinkType.SUB)
    graph.add_edge("sense", "act", LinkType.POR)
    return graph


def _sense_goal(node: Node, env: dict) -> tuple[bool, bool]:
    grid: GridState = env["grid"]
    bindings: BindingTable = env["bindings"]
    reached = grid.agent == grid.goal
    node.meta["activation"] = 1.0 if reached else 0.25
    with bindings.begin_tick("grid/sense") as session:
        session.reserve(BindingInstance("agent", {f"cell:{grid.agent[0]},{grid.agent[1]}"}, node.nid))
        session.reserve(BindingInstance("goal", {f"cell:{grid.goal[0]},{grid.goal[1]}"}, node.nid))
    return True, True


def _move_agent(node: Node, env: dict) -> tuple[bool, bool]:
    grid: GridState = env["grid"]
    before = grid.agent
    if before != grid.goal:
        grid.step_toward_goal()
    node.meta["activation"] = 1.0 if grid.agent != before else 0.5
    return True, True


def run_simulation(
    *,
    mode: ActivationMode = ActivationMode.DISCRETE,
    seed: int = 0,
    steps: int = 10,
    microticks: int = 0,
) -> List[str]:
    random.seed(seed)
    grid = GridState()
    bindings = BindingTable()
    graph = build_graph()
    config = EngineConfig(
        activation_mode=mode,
        microtick_steps=microticks,
        record_activation_history=mode == ActivationMode.CONTINUOUS,
    )
    engine = ReConEngine(graph, config=config)
    graph.nodes["root"].state = NodeState.REQUESTED
    lines: List[str] = []

    for step_idx in range(max(0, steps)):
        bindings.invalidate_on_signature(grid.signature())
        engine.reset_states()
        graph.nodes["root"].state = NodeState.REQUESTED
        env = {"grid": grid, "bindings": bindings}
        for _ in range(20):
            engine.step(env)
            if graph.nodes["move_agent"].state == NodeState.CONFIRMED:
                break
        lines.append(
            f"step={step_idx + 1} mode={mode.value} agent={grid.agent} "
            f"goal={grid.goal} bindings={len(bindings.snapshot())}"
        )
        if grid.agent == grid.goal:
            break

    return lines


def _parse_mode(value: str) -> ActivationMode:
    return ActivationMode(value)


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the ReCoN Lite grid-world example.")
    parser.add_argument("--mode", choices=[mode.value for mode in ActivationMode], default=ActivationMode.DISCRETE.value)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--steps", type=int, default=10)
    parser.add_argument("--microticks", type=int, default=0)
    args = parser.parse_args(list(argv) if argv is not None else None)

    for line in run_simulation(
        mode=_parse_mode(args.mode),
        seed=args.seed,
        steps=args.steps,
        microticks=args.microticks,
    ):
        print(line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
