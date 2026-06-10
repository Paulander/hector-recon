I read the bundle. My main diagnosis is this:

**ReCoN-lite has enough local KRK competence to justify adding composition machinery now.** Waiting until KRK is “fully solved” before adding routing would probably make the architecture worse, because more stage-local legs will accumulate without a clean interface for reuse. The artifact data already shows the mismatch: local Stage 5 fence selection is perfect on the sampled one-ply metric, but adversarial playout from fence positions still gives roughly **30 mate / 70 draw**. That is exactly the failure mode an affordance/handoff layer is supposed to expose.

The most important correction is this:

> Stop treating curriculum labels as if they are already composable skills.
> A label like `fence_established` is currently doing three jobs: state predicate, local reward target, and implied next phase. Split those apart.

A reusable ReCoN skill should have this shape:

```text
Skill = affordance + request interface + promised progress + confirmation + continuation export
```

That gives you a clean way to compose KRK, KQK, KPK, tactics, and later middlegame plans without turning Hector into a hidden monolithic policy.

---

## Priority architectural decisions

### 1. Introduce an explicit affordance-routing layer now

Yes, add it now.

But make it **thin, inspectable, and seeded**, not a learned black-box router.

The router should not “know chess” in the broad sense. It should read terminal outputs, assemble an affordance vector, and decide which subgraph to request. Its job is to answer:

```text
What kind of opportunity is currently available,
which skill is licensed to act,
what evidence supports that request,
and what should happen if the skill confirms or fails?
```

A good v0 structure:

```text
KRK_ENTRY
  SUB -> AFFORDANCE_HUB
    SUB -> mate_affordance
    SUB -> fence_affordance
    SUB -> edge_trap_affordance
    SUB -> drive_affordance
    SUB -> box_shrink_affordance
    SUB -> opposition_tempo_affordance
    SUB -> low_affordance
    SUB -> route_conflict
  POR -> selected skill capsule
  RET <- skill confirmation packet
```

For now, seed affordances from `krk_rich_v1` and current landmark predicates. Do not learn the router from scratch yet. There is not enough cross-domain data for that, and you would risk creating exactly the opaque controller ReCoN is trying to avoid.

The router score should be decomposed, not a single magic number:

```text
route_score(skill) =
    applicability
  + expected_progress
  + safety
  + continuation_readiness
  + prior_success_in_similar_context
  - conflict_penalty
  - novelty_penalty
```

Each component should be explainable. For example:

```json
{
  "selected_skill": "krk.drive_to_edge",
  "score": 0.74,
  "evidence": {
    "enemy_king_edge_distance": "high",
    "rook_safe": true,
    "fence_exists": true,
    "box_area_can_decrease": true,
    "mate_affordance": "low"
  },
  "alternatives": {
    "krk.mate_basin": 0.12,
    "krk.edge_trap": 0.45,
    "krk.opposition_tempo": 0.31
  }
}
```

This preserves ReCoN’s inspectability: you can animate not only the selected move, but the reason the graph requested a subgraph.

The key warning: **do not let the affordance layer become a hidden policy network.** It should be a routing and arbitration layer, not the real chess brain.

---

### 2. Represent handoff through explicit skill contracts and RET packets

Do not represent handoff mainly as “after stage A, go to stage B.”

That is too brittle. It will fail as soon as two independently learned subgraphs have overlapping applicability, or when a tactic changes the material signature.

Use **skill contracts**.

Each learned subgraph should export a small contract:

```json
{
  "skill_id": "krk.fence_established",
  "domain": "KRK",
  "affordance_terms": [
    "rook_can_cut",
    "rook_safe",
    "enemy_king_not_yet_boxed",
    "white_king_support_available"
  ],
  "request_preconditions": [
    "material_signature == KRK",
    "side_to_move == white",
    "rook_not_en_pris"
  ],
  "promised_delta": [
    "establish_or_preserve_cut",
    "reduce_enemy_king_mobility",
    "avoid_stalemate",
    "avoid_rook_loss"
  ],
  "confirmation_terms": [
    "fence_exists",
    "rook_safe",
    "black_king_box_area_not_increased"
  ],
  "failure_terms": [
    "rook_lost",
    "stalemate_created",
    "cut_broken",
    "no_progress_after_reply"
  ],
  "continuation_exports": [
    "mate_affordance",
    "drive_affordance",
    "box_shrink_affordance",
    "opposition_tempo_affordance"
  ]
}
```

Then the subgraph returns a structured confirmation, not just “success”:

```json
{
  "from_skill": "krk.fence_established",
  "status": "confirmed_partial",
  "achieved": [
    "fence_exists",
    "rook_safe"
  ],
  "progress_delta": {
    "box_area": -4,
    "enemy_king_edge_distance": -1
  },
  "violations": [],
  "next_affordance_snapshot": {
    "mate": 0.05,
    "drive_to_edge": 0.68,
    "box_shrink": 0.47,
    "opposition_tempo": 0.22
  },
  "explanation": [
    "rook cut preserved",
    "black king legal area reduced",
    "mate not yet available"
  ]
}
```

This is a natural fit for ReCoN semantics:

```text
SUB = skill owns subordinate terminals/subscripts
POR = router requests the next skill in a procedural order
RET = skill returns achieved predicates, failed predicates, and continuation affordances
```

The important design move is that **handoff edges should connect confirmations to future requests**, not actuators to actuators.

For example:

```text
KRK.fence_established.RET:fence_exists
  POR -> AFFORDANCE_HUB.KRK_PHASE_ROUTER
  POR -> KRK.drive_to_edge.REQUEST
```

But that edge should be statistical and inspectable:

```json
{
  "from": "ret.fence_exists",
  "to": "request.drive_to_edge",
  "context": "enemy_king_not_on_edge && box_area_large",
  "support_count": 412,
  "success_rate": 0.71,
  "avg_plies_to_next_confirmation": 5.3,
  "known_failure_modes": [
    "rook_cut_breaks_after_black_reply",
    "wrong_tempo_loop"
  ]
}
```

That gives you a composable bridge structure.

For KPK promotion, the handoff should not hard-code “KPK calls KQK.” Instead:

```text
KPK.promotion.RET
  -> material_signature_changed
  -> promoted_piece == queen
  -> AFFORDANCE_HUB
  -> KQK.entry
```

For tactics:

```text
TACTIC.win_material.RET
  -> material_signature_changed
  -> opponent_king_safety_changed
  -> AFFORDANCE_HUB
  -> endgame_or_strategy_router
```

That is more scalable than hand-coded module chains.

---

### 3. Add only a minimal set of meta terminals first

The candidate list in the docs is directionally right, but too broad. Do not add all of these as first-class terminals yet:

```text
known_position_confidence
plan_confidence
strategy_conflict
goal_distance_uncertainty
low_affordance_state
high_novelty_state
stagnation_detected
growth_pressure
exploit_pressure
```

Several of those are not primitive observations. They are derived control decisions.

Start with five meta/internal terminals:

#### `affordance_margin`

Measures how clearly one route wins over alternatives.

```text
top_route_score - second_route_score
```

Use this to detect ambiguity.

#### `low_affordance_state`

Fires when no known skill has enough support.

```text
max(route_scores) < threshold
```

This should trigger exploration logging, not immediate topology mutation.

#### `handoff_gap`

Fires when a skill confirms locally, but no continuation affordance is strong.

This is probably your most important KRK terminal right now.

```text
last_skill_status in {confirmed, confirmed_partial}
AND max(next_affordances) < threshold
```

This directly targets the 30 mate / 70 draw issue.

#### `stagnation_detected`

Fires when the active plan is locally “valid” but global progress is not happening.

For KRK, this might mean no meaningful improvement over N plies in:

```text
enemy king edge distance
box area
box minimum side
rook safety
mate distance proxy
repeated abstract state
```

In full chess, the same idea becomes:

```text
same plan active,
same structural evaluation,
no irreversible progress,
or repeated state abstraction
```

#### `novelty_or_low_support`

Fires when the current terminal pattern is far from known goal memories or learned support regions.

This should be based on explicit feature-space distance or bucket rarity, not vague model uncertainty.

---

Avoid adding `growth_pressure` as an independent terminal at first. It should be derived:

```text
growth_pressure =
  low_affordance
  OR handoff_gap
  OR stagnation_detected
  OR repeated_conversion_failure
```

Similarly, `plan_confidence` is too vague unless it is decomposed into:

```text
affordance strength
route margin
historical success of selected handoff
progress after reply
safety invariants
```

Also, be careful with current “confidence” numbers. The Stage 2A history shows mate confidences around `1,000,001+`, which are obviously not calibrated probabilities. Do not use raw actuator scores as routing confidence. They need normalization or calibration before the affordance hub depends on them.

---

## Recommended architecture shape

A scalable ReCoN chess architecture should look roughly like this:

```text
BOARD / GAME STATE
  -> shared terminal space
      -> geometry terminals
      -> material terminals
      -> attack-defense terminals
      -> king-safety terminals
      -> confinement terminals
      -> tempo/opposition terminals
      -> promotion terminals
      -> internal/meta terminals

  -> affordance hub
      -> tactical interrupt router
      -> endgame/material router
      -> strategic-plan router
      -> exploration/growth router

  -> skill capsule
      -> local sensors
      -> local actuators
      -> goal memories
      -> confirmation terminals

  -> RET packet
      -> achieved predicates
      -> failed predicates
      -> progress delta
      -> continuation affordances
      -> explanation trace

  -> affordance hub again
```

Tactics should probably act as an **interrupt layer**, not merely another ordinary subgraph.

Reason: tactics often invalidate the current plan. A mating tactic, blunder prevention, hanging piece, pin, fork, or discovered attack may need to override a slow endgame conversion or middlegame plan.

So full-game routing should eventually have this priority:

```text
1. Legality and safety veto
2. Immediate mate / avoid being mated
3. Forcing tactic / avoid tactical loss
4. Material-signature/endgame router
5. Strategic plan router
6. Growth/exploration fallback
```

This does not mean tactics are opaque search. They can still be ReCoN subgraphs with explicit affordances:

```text
loose_piece_affordance
overloaded_defender_affordance
pin_affordance
fork_affordance
back_rank_mate_affordance
discovered_attack_affordance
```

But tactically urgent affordances should be able to preempt a quiet endgame script.

---

## Reusable concept structure

Do not build KRK, KQK, KPK, and tactics as separate feature universes. That will kill transfer.

Use a two-layer concept design:

```text
shared concept terminals
  -> domain-specific affordance terminals
      -> skill-specific request/confirmation contracts
```

Examples of shared concept families:

```text
geometry:
  edge_distance
  corner_distance
  rank_file_alignment
  diagonal_alignment
  box_area
  box_min_side

king relation:
  king_distance
  opposition
  legal_king_zone
  enemy_king_mobility
  mating_net_pressure

slider control:
  line_control
  cut_exists
  cut_stability
  slider_safety
  protected_slider

pawn structure:
  passed_pawn
  promotion_distance
  king_in_front
  pawn_race_margin

attack-defense:
  attacked_square
  defended_piece
  loose_piece
  pinned_piece
  overloaded_defender
  discovered_attack_line

outcome/safety:
  check
  checkmate
  stalemate
  repetition_risk
  material_loss_risk
```

Then bind them to domains:

```text
KRK:
  confinement + rook line control + rook safety + king support

KQK:
  confinement + queen line/diagonal control + queen safety + stalemate avoidance

KPK:
  opposition + promotion race + king support + zugzwang/tempo

Tactics:
  attack-defense relations + forcing move affordance + material/king-safety delta
```

Do not make everything piece-agnostic in a naive way. A rook fence and a queen mating net are not identical. But they should share lower-level concepts:

```text
confinement
enemy king mobility
slider control
safe checking piece
box shrink
stalemate risk
```

A useful rule:

> Shared terminals should describe relations.
> Domain-specific affordances should describe opportunities.
> Skill capsules should describe actions and confirmations.

---

## Online stem-cell spawning and pruning

Do not let gameplay-time spawning immediately mutate durable topology yet.

That would make debugging much harder and could corrupt currently reliable foundation skills.

Use a **shadow stem-cell queue** first.

During gameplay, when a trigger fires, log a candidate:

```json
{
  "trigger": "handoff_gap",
  "parent_skill": "krk.fence_established",
  "state_signature": "KRK|fence_exists|box_large|enemy_not_edge|rook_safe",
  "route_vector": {
    "mate": 0.04,
    "drive": 0.31,
    "box_shrink": 0.28,
    "opposition": 0.19
  },
  "chosen_move": "Rh5",
  "observed_delta": {
    "box_area": -2,
    "rook_safe": true
  },
  "failure_trace_id": "fence_draw_017",
  "status": "candidate"
}
```

Promotion should require evidence:

```text
candidate spawned
  -> clustered with similar failures
  -> tested on held-out states
  -> improves conversion, not just local reward
  -> passes foundation non-regression
  -> gets compiled into explicit topology
  -> receives provenance metadata
```

Good spawning triggers:

```text
handoff_gap after local success
stagnation under high local confidence
low_affordance with legal safe moves available
route conflict where one branch later clearly succeeds
repeated draw loop from same abstract state
local improvement followed by conversion failure
```

Bad spawning triggers:

```text
any single loss
any low raw confidence score
any unexplained novelty
any failed move without a reusable context signature
```

Give candidates a budget and TTL:

```text
max new candidates per game
max candidates per abstract state bucket
expire if no repeated support
merge if equivalent to existing candidate
demote if it harms foundation tests
```

For pruning, use role-aware pruning, not simple usage frequency.

Rare tactical skills may be low-frequency but high-value. A back-rank mate detector, stalemate-avoidance rule, or queen blunder veto should not be pruned just because it rarely fires.

Use something closer to:

```text
node_value =
    verified_success_rate
  * impact_when_used
  * uniqueness
  * safety_importance
  * transfer_usefulness
  - maintenance_cost
  - harm_rate
```

Foundation nodes should be frozen or heavily protected:

```text
mate-in-1
legality
avoid self-check
avoid stalemate when winning
avoid rook/queen loss
basic king safety
core geometry/confinement terminals
```

For mature nodes, prefer **disable/quarantine** over permanent deletion. Keep provenance and allow rollback. That matters for explainability.

---

## The next 2–3 implementation steps

### Step 1: Add `SkillContract`, `AffordanceHub`, and `HandoffPacket`

This is the highest-leverage implementation step.

Add a lightweight contract object around existing landmark specs.

In `krk_landmarks.py`, each landmark should expose more than reward:

```python
LandmarkSkillSpec(
    label="fence_established",
    affordance_terms=[...],
    request_preconditions=[...],
    confirmation_terms=[...],
    promised_delta=[...],
    failure_terms=[...],
    continuation_exports=[...],
)
```

In `baseline_to_recon.py`, compile these into explicit topology:

```text
KRK_ENTRY
  -> AFFORDANCE_HUB
  -> skill request nodes
  -> skill confirmation nodes
  -> handoff edges
```

In `krk_baseline_nodes.py`, return a structured RET packet from skill execution/evaluation.

Do this before adding many more KRK stages. Otherwise `drive_to_edge`, `box_shrink`, and `opposition_tempo` will become more isolated stage-local legs.

---

### Step 2: Build a handoff/conversion evaluator, not just a landmark evaluator

Your current distinction between local pass and conversion pass is correct, but it needs to become central.

Right now there is a suspicious inconsistency: the Stage 5 clean curriculum history says `conversion_passed: true`, but the run manifest has `adaptive_playout_max_plies: 0`, and the separate conversion debug shows 30 mate / 70 draw. I would treat the debug result as the real signal. Do not let a stage claim conversion success when playout was not actually checked.

Add a `HandoffEvalResult` with fields like:

```json
{
  "from_skill": "krk.fence_established",
  "local_success_rate": 1.0,
  "handoff_success_rate": 0.43,
  "mate_playout_rate": 0.30,
  "draw_loop_rate": 0.70,
  "avg_handoff_gap": 0.28,
  "most_common_failed_next_routes": [
    "drive_to_edge",
    "box_shrink"
  ],
  "phase_confusion": {
    "routed_drive_when_box_shrink_needed": 17,
    "routed_fence_again_when_drive_needed": 24
  }
}
```

Also log traces:

```text
position
active skill
move chosen
RET packet
affordance vector before move
affordance vector after black reply
selected next skill
progress delta
loop/stagnation flag
final result
```

Then mine the 70 draw traces from the fence conversion debug. Those traces are not merely failures; they are your first handoff dataset.

The next KRK training target should be something like:

```text
fence_confirmed -> drive_or_box_or_tempo selection
```

not merely:

```text
train drive_to_edge in isolation
```

---

### Step 3: Add minimal meta terminals and shadow stem-cell logging

Implement these first:

```text
affordance_margin
low_affordance_state
handoff_gap
stagnation_detected
novelty_or_low_support
```

Then add a `stem_cell_candidates.jsonl` or equivalent event log.

Do not mutate durable topology during gameplay yet. Log candidates, cluster them, and promote them offline after conversion and non-regression tests.

This gives you staged growth without giving up control.

---

## Metrics to prioritize next

The next metrics should be composition metrics, not more local KRK accuracy metrics.

Prioritize these:

```text
handoff success rate
conversion after local confirmation
handoff gap rate
affordance calibration
route activation precision/recall
stagnation/draw-loop rate
foundation non-regression
stem-cell promotion yield
graph complexity per conversion gain
```

For affordance calibration, track whether a route score actually predicts success:

```text
When drive_affordance is 0.8, does drive succeed about 80% of the time?
```

For routing, track a phase confusion matrix:

```text
selected route vs route that later proved useful
```

For explanation quality, keep it simple at first:

```text
Every selected move should be explainable as:
  active skill
  active affordance evidence
  promised progress
  confirmation/failure result
  next requested skill
```

Do not invent a complex natural-language explanation system yet. The graph trace is the explanation.

---

## The main architectural challenge

The biggest risk is that ReCoN-lite accidentally becomes a conventional staged policy with nicer visualization.

That would happen if the topology keeps growing like this:

```text
stage label -> local reward -> actuator leg -> next stage label
```

That is not enough for self-organizing cognition.

The better pattern is:

```text
shared terminals
  -> affordance evidence
    -> skill contract request
      -> local action
        -> confirmation packet
          -> handoff/router update
            -> growth/pruning/consolidation
```

The second pattern gives you inspectable composition.

For KRK specifically, I would not spend the next cycle trying to squeeze more one-ply performance out of fence, edge trap, or mate basin. The local skills are already strong enough for architectural testing.

The next cycle should answer:

```text
Can Hector know which skill should own the next move after a local skill confirms?
Can it explain why that handoff is valid?
Can it detect when no learned handoff applies?
Can it log that gap as a candidate for growth?
```

That is the real proving ground. KRK is just the first small domain where the failure is visible.
