# Glossary

## Hector

The planned ReCoN-based chess agent.

## ReCoN

Request-Confirmation Network. A graph-based script execution/control formalism where nodes request subnodes and receive confirmations.

## Terminal

A leaf-like callable node. It may sense state, score state, propose moves, execute an actuator, or monitor internal graph conditions.

## Sensor

A terminal that detects a feature or condition.

## Actuator

A terminal that proposes or scores an action, currently usually a chess move.

## Subgraph

A reusable ReCoN graph region representing a skill, script, endgame method, tactic, or plan.

## Goal Memory / Goal Basin

Stored prototype states or feature-space targets that a stage can move toward.

## Landmark

An intermediate curriculum concept, such as edge trap, fence, drive, box shrink, or opposition.

## Affordance

A currently available opportunity for a skill/subgraph to apply. For example, a fence affordance means a fence/cut skill appears relevant and executable in the current position.

## Handoff

The transition from one subgraph/skill to another. Example: `fence_established` hands off to `edge_trap_wrong_tempo`, or KPK promotion hands off to KQK.

## Stem Cell

A candidate undeveloped node/triplet/structure that may grow into a useful sensor, actuator, or subgraph through exploration.

## Triplet

Informally, a learned relation among before-state/sensor context, action, and after-state/confirmation. In the compiled topology, successful triplets can become explicit hierarchical legs.

## Pruning

Removing weak, unused, redundant, or harmful nodes/actuators/edges.

## Consolidation

Stabilizing useful learned structure and protecting it from ordinary exploration/pruning.

## Local Skill Pass

A stage succeeds on immediate one-ply or local reward criteria.

## Conversion Pass

A stage succeeds when the system can continue from that local skill into a successful longer playout or handoff chain.
