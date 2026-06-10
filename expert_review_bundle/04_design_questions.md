# Focused Design Questions

## 1. Affordance Routing

Should Hector have an explicit affordance layer made of internal terminals?

Candidate terminals:

- `mate_affordance`
- `edge_trap_affordance`
- `fence_affordance`
- `drive_affordance`
- `box_shrink_affordance`
- `tactic_affordance`
- `promotion_affordance`
- `endgame_handoff_affordance`

Should these be engineered, learned, or seeded and then refined?

## 2. Handoff Between Subgraphs

How should one learned subgraph hand off to another?

Examples:

- KPK promotes into KQK/KRK.
- KRK fence hands off to drive/edge trap/tempo.
- A tactic wins material, then hands off to endgame conversion.
- A middlegame plan hands off to a tactic or defensive resource.

Possible representations:

- goal memories,
- explicit `RET` confirmations,
- learned `POR` edges,
- routing hub,
- shared terminal-space classifier,
- affordance-weighted move synthesis.

Which representation best fits ReCoN?

## 3. Meta/Internal Terminals

Candidate self-monitoring terminals:

- `known_position_confidence`
- `plan_confidence`
- `strategy_conflict`
- `goal_distance_uncertainty`
- `low_affordance_state`
- `high_novelty_state`
- `stagnation_detected`
- `growth_pressure`
- `exploit_pressure`

Which should be added first?

Should they be engineered initially, discovered later, or hybrid?

## 4. Online Stem-Cell Spawning

Current growth mostly happens during training runs. Longer term we want gameplay-time exploration.

Possible triggers:

- no known affordance is strong,
- chosen subgraph repeatedly fails,
- state is high novelty,
- actuator proposals are low-confidence,
- local improvement occurs but conversion fails,
- repeated draw/stagnation loop is detected.

Should gameplay-time spawning modify topology immediately, or only log candidates for offline consolidation?

## 5. Pruning And Consolidation

Current pruning is conservative and foundation skills are protected.

In a larger graph:

- How should rare but important tactical skills be protected?
- Should pruning depend on reward, usage, confidence, novelty, or graph role?
- Should foundation subgraphs be frozen?
- Should pruning happen stage-locally or globally?

## 6. Transfer Across Endgames And Tactics

Potentially reusable concepts:

- opposition,
- king distance,
- edge distance,
- fence/cut,
- box/confinement,
- rook/queen safety,
- promotion race,
- mating net,
- zugzwang/tempo,
- attack/defense relation,
- loose piece,
- overloaded defender.

Should these be piece-agnostic terminal families or endgame-specific learned sensors?

How should KRK knowledge transfer into KQK and KPK?

## 7. Topology Growth Discipline

When a useful new skill is found, should topology grow as:

- a child under the current state,
- a sibling alternative under an affordance hub,
- a reusable terminal shared by many subgraphs,
- a duplicated context-specific node,
- a new goal-memory basin,
- a new routing edge between existing subgraphs?

What rules prevent the topology from becoming too flat, too duplicated, or too tangled?

## 8. Evaluation Metrics

Current metrics:

- one-ply improved rate,
- optimal rate,
- worsened rate,
- average reward,
- playout mate/draw/max-plies.

Needed metrics may include:

- handoff success rate,
- affordance calibration,
- subgraph activation precision/recall,
- exploration yield,
- pruning safety,
- transfer success,
- graph complexity vs performance,
- explanation quality.

Which should be prioritized next?
