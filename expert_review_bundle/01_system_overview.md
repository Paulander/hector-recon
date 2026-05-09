# System Overview

## Project

ReCoN-lite is a small chess sandbox for Request-Confirmation Networks. The system is intended to become an explainable chess cognition architecture, not a conventional monolithic chess engine.

The long-term agent is called Hector.

## ReCoN Formalism

Core ideas:

- A ReCoN is a graph of script nodes, terminal nodes, sensors, actuators, and control structures.
- Nodes can request subnodes and receive confirmations.
- The graph is intended to be inspectable: active nodes, fired edges, terminal outputs, and goal memories should be visible.
- Learned components are compiled into explicit topology rather than hidden inside a single opaque model.

Important edge semantics:

- `SUB`: child/sub-script relationship.
- `POR`: procedural/request/ordering relationship.
- `RET`: return/confirmation relationship.

Important node roles:

- Sensor terminals: detect features or internal state.
- Actuator terminals: propose/score moves.
- Script/subgraph nodes: organize local skills.
- Goal memories: store learned basins or prototype states.
- Meta/internal terminals: planned nodes that monitor confidence, novelty, conflict, affordance, stagnation, and growth pressure.

## Current Chess Strategy

We are using chess because it gives a structured, adversarial, measurable domain.

The desired path is:

1. Learn KRK from controlled curriculum stages.
2. Learn KQK and KPK.
3. Learn handoff between KPK promotion and KQK/KRK conversion.
4. Learn tactical subgraphs.
5. Compose endgame and tactical subgraphs in more complex positions.
6. Eventually add opening/middlegame plans and full-game play.

## Important Distinction

We are not trying to beat Stockfish by search. We are trying to build an architecture that can:

- discover or use local skills,
- explain why a skill is relevant,
- choose between subgraphs,
- hand off between subgraphs,
- grow new structure when existing affordances are weak,
- prune and consolidate over time.

KRK is a testbed for this because it exposes phase transitions: mate now, edge trap, fence, drive, box shrink, opposition, tempo, and full conversion.
