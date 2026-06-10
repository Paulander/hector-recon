The existing bridge/gate system should **evolve into** the skill-contract architecture. It should not be replaced.

The bridge demo already has the right primitives: `endgame_gate`, material sensors, continuous KRK/KPK/KQK affordances, weighted routing edges, subgraph locks, activation dynamics, and an observable KPK→KQK handover. The missing layer is not a totally new hub. The missing layer is an **explicit contract interface** around those mechanisms so that a handoff is not merely “activation shifted,” but:

```text
skill requested
→ skill acted
→ skill confirmed what changed
→ router received a structured continuation signal
→ next skill/domain was requested with explainable evidence
```

The clean migration is:

```text
old bridge/gate machinery
  -> typed affordance routers
  -> skill contracts attached to subgraphs/skill groups
  -> runtime handoff packets
  -> optional compiled handoff bridges after evidence
```

Do not throw away the KPK→KQK proof. Wrap it.

---

## 1. Keep `endgame_gate` as a top-level domain router; add skill-level hubs inside domains

Do **not** collapse everything into one global `AffordanceHub`.

A single generic hub that chooses among KPK, KQK, KRK, fence, box-shrink, opposition, tactics, and middlegame plans will become a flat dispatcher. It will be harder to debug, harder to train, and less ReCoN-like.

Use a **hierarchical router design**:

```text
GameRoot
  SUB -> tactics_interrupt_hub
  SUB -> strategy_hub
  SUB -> endgame_gate / domain_affordance_hub
            SUB -> kpk_root
            SUB -> kqk_root
            SUB -> krk_root

krk_root
  SUB -> krk_skill_hub
            SUB -> krk.fence
            SUB -> krk.drive_to_edge
            SUB -> krk.box_shrink
            SUB -> krk.opposition_tempo
            SUB -> krk.mate_basin
            SUB -> krk.edge_trap

kpk_root
  SUB -> kpk_skill_hub
            SUB -> kpk.push
            SUB -> kpk.opposition
            SUB -> kpk.promotion

kqk_root
  SUB -> kqk_skill_hub
            SUB -> kqk.drive
            SUB -> kqk.corner
            SUB -> kqk.mate
```

Implementation-wise, `endgame_gate` can become an instance of a generic router class, but graph-wise it should remain a **domain/material/endgame gate**.

So the answer is:

```text
Class/interface: generic AffordanceRouter
Existing node: keep endgame_gate as domain-level router
New nodes: add skill-level hubs under KRK/KPK/KQK
```

A good migration name would be:

```python
create_endgame_gate(...)
# internally wraps:
create_affordance_router(scope="domain", id="endgame_gate")
```

Preserve the old `env["endgame_gate"]` keys for compatibility, but add richer fields:

```json
{
  "activations": {
    "kpk": 1.0,
    "kqk": 0.0,
    "krk": 0.0
  },
  "active_endgame": "kpk",
  "router_kind": "domain_affordance_router",
  "route_evidence": {
    "kpk": {
      "exact_material_match": true,
      "approach_affordance": 1.0,
      "contract_preconditions_met": true,
      "route_score": 1.0
    }
  }
}
```

---

## 2. Split domain affordances from skill affordances

The existing continuous KRK/KPK/KQK signals are valuable, but they should not be interpreted as direct skill-selection probabilities.

Right now, the bridge artifact can show high nonzero KRK/KQK signals even in a KPK position. That is fine as a **strategic approach signal**, but dangerous as an execution gate. A KQK affordance of `0.67` before a queen exists should mean:

```text
“the position is structurally near a KQK target”
```

not:

```text
“activate KQK move selector now”
```

Use two different concepts:

```text
domain_approach_affordance:
  Soft gradient toward a domain.
  Useful for liquidation, simplification, strategic planning, reward shaping.

domain_execution_eligibility:
  Hard or near-hard check that this subgraph is legally/currently executable.
  Used for subgraph locking and move selection.
```

For example:

```json
{
  "domain": "kqk",
  "approach_affordance": 0.67,
  "execution_eligible": false,
  "reason": "queen_not_present"
}
```

After KPK promotion:

```json
{
  "domain": "kqk",
  "approach_affordance": 1.0,
  "execution_eligible": true,
  "reason": "exact_kqk_material",
  "ret_boost": "kpk.promotion.confirmed"
}
```

Skill-level affordances live below the domain:

```text
KRK domain affordance:
  Is KRK the relevant material/control model?

KRK skill affordances:
  Is fence useful?
  Is drive-to-edge useful?
  Is box shrink available?
  Is opposition/tempo needed?
  Is mate basin active?
```

A route score should look roughly like:

```text
route_score(domain.skill) =
    domain_execution_eligibility
  * skill_affordance
  * safety_score
  * contract_reliability
  * route_edge_weight
  + ret_continuation_boost
```

But for strategic planning before the exact material domain exists:

```text
strategy_score(domain_target) =
    domain_approach_affordance
  * expected_conversion_value
  * simplification_or_tactic_feasibility
```

That means the old affordance-delta reward helpers are still useful. They should just be separated into:

```text
domain affordance delta:
  “Did this move bring us closer to KQK/KPK/KRK?”

skill affordance delta:
  “Did this KRK move create a better fence/drive/box/tempo state?”

handoff affordance delta:
  “Did the confirmed skill make a next skill more available?”
```

---

## 3. `SkillContract` should be static metadata plus separate runtime statistics

Do not make `SkillContract` purely static, and do not let it mutate freely at runtime.

Use this split:

```text
SkillContractSpec:
  stable semantic contract
  stored in topology metadata
  explainable and inspectable

SkillContractStats:
  learned runtime/consolidated statistics
  stored separately
  updated from observed success/failure
```

A static contract should say what the skill **claims** to do:

```python
@dataclass(frozen=True)
class SkillContractSpec:
    skill_id: str
    domain: str
    provider_node: str

    request_preconditions: list[str]
    affordance_inputs: list[str]

    promised_deltas: list[str]
    confirmation_terms: list[str]
    failure_terms: list[str]
    safety_vetoes: list[str]

    continuation_exports: list[str]

    training_origin: dict
    explanation_template: str
```

Runtime stats should say how well that claim has held up:

```python
@dataclass
class SkillContractStats:
    skill_id: str
    context_bucket: str

    attempts: int = 0
    confirmations: int = 0
    local_failures: int = 0
    handoff_successes: int = 0
    conversion_successes: int = 0
    draw_loops: int = 0

    avg_progress_delta: dict[str, float] = field(default_factory=dict)
    failure_modes: dict[str, int] = field(default_factory=dict)

    reliability: float = 0.5
    calibration_error: float = 0.0
```

The contract spec belongs in topology. The stats should live in something like:

```text
contract_stats.json
handoff_stats.json
route_stats.json
```

keyed by:

```text
skill_id + context_bucket
```

For KRK, useful context buckets would include:

```text
cut_established
rook_safe
enemy_king_edge_distance_bin
box_area_bin
box_min_side_bin
side_to_move
can_mate_now
black_king_at_edge
```

Important migration point: **do not create one SkillContract per actuator leg.** Your compiled KRK topology has many actuator legs. The skill contract should usually correspond to a curriculum/landmark group, not one terminal.

Use `curriculum_label` as the grouping key:

```text
krk.fence_established
  owns many learned actuator legs with curriculum_label="fence_established"

krk.edge_trap_wrong_tempo
  owns many learned actuator legs with curriculum_label="edge_trap_wrong_tempo"
```

So change the compiled topology from:

```text
krk_hub
  SUB -> leg_1
  SUB -> leg_2
  SUB -> leg_3
```

toward:

```text
krk_hub
  SUB -> skill_fence_established
            SUB -> leg_1
            SUB -> leg_7
            SUB -> leg_12

  SUB -> skill_edge_trap_wrong_tempo
            SUB -> leg_2
            SUB -> leg_9

  SUB -> skill_mate_basin
            SUB -> leg_3
            SUB -> leg_4
```

This is a better architectural unit for contracts, routing, statistics, pruning, and explanation.

---

## 4. `RET packets` should be runtime records first, graph structure later

Represent RET packets initially as **structured runtime records** emitted by skill execution.

Do not immediately add a permanent graph node for every packet or every observed transition. That will create topology bloat and make debugging worse.

Use runtime packets like:

```python
@dataclass
class HandoffPacket:
    packet_id: str
    tick: int

    from_skill: str
    provider_node: str
    status: str  # confirmed, confirmed_partial, failed, vetoed

    before_fen: str
    after_fen: str | None
    move_uci: str | None

    achieved: list[str]
    failed: list[str]
    safety_flags: list[str]

    progress_delta: dict[str, float]

    affordance_before: dict[str, float]
    affordance_after: dict[str, float]
    continuation_exports: dict[str, float]

    explanation: list[str]
```

Store them in the environment during runtime:

```python
env.setdefault("handoff_packets", []).append(packet.to_dict())
env["last_handoff_packet"] = packet.to_dict()
```

Then the router consumes the latest packet:

```text
skill RET packet
  -> affordance hub
  -> route decision
  -> next request
```

Only after repeated evidence should a handoff become compiled topology.

For example, if `KPK.promotion -> KQK.entry` succeeds reliably, compile a bridge:

```text
handoff_kpk_promotion_to_kqk  [SCRIPT]
  SUB -> promoted_piece_is_queen        [TERMINAL]
  SUB -> exact_kqk_material             [TERMINAL]
  SUB -> kqk_execution_eligible         [TERMINAL]
  POR -> request_kqk_root               [SCRIPT]
```

Be careful with ReCoN formalism: do not attach POR/RET directly to terminals if your architecture requires POR/RET only between script nodes. Use script wrappers.

The rule should be:

```text
Runtime packet = event-level evidence
Compiled bridge = durable topology only after repeated support
```

That preserves explainability without exploding the graph.

---

## 5. Online stem-cell spawning should use all trigger types through a shadow queue

Use all of these:

```text
low-affordance states
handoff gaps
repeated conversion failures
route conflicts
```

But do not attach them immediately as durable live graph nodes.

Use a **shadow candidate queue**.

Different triggers should create different candidate types:

```text
low_affordance_state:
  maybe a missing sensor/affordance concept

handoff_gap:
  maybe a missing bridge between confirmed skill and next route

repeated_conversion_failure:
  maybe local skill is real but continuation contract is wrong

route_conflict:
  maybe router lacks an arbitration feature or calibration is bad
```

Recommended queue record:

```json
{
  "candidate_id": "cand_krk_fence_gap_0017",
  "trigger": "handoff_gap",
  "owner_scope": "krk_skill_hub",
  "parent_skill": "krk.fence_established",
  "failed_route": null,
  "state_signature": {
    "cut_established": true,
    "rook_safe": true,
    "enemy_king_edge_distance_bin": 2,
    "box_area_bin": "large",
    "side_to_move": "white"
  },
  "affordance_snapshot": {
    "krk.fence": 0.81,
    "krk.drive_to_edge": 0.29,
    "krk.box_shrink": 0.25,
    "krk.opposition_tempo": 0.16,
    "krk.mate_basin": 0.03
  },
  "observed_outcome": "draw_loop",
  "repeat_count": 1,
  "promotion_status": "shadow"
}
```

Priority should not be equal across triggers. For the current project, rank them:

```text
1. repeated conversion failures
2. handoff gaps
3. route conflicts
4. low-affordance states
```

Reason: low-affordance is too broad. It can mean novelty, bad features, bad calibration, or simply an irrelevant position. Handoff gaps and repeated conversion failures are more structurally actionable.

The stem-cell queue should propose one of these changes:

```text
new reusable FeatureHub terminal
new skill-level affordance
new handoff bridge
new arbitration terminal
new candidate micro-script under an existing skill
new sibling skill under a domain hub
```

Then offline consolidation decides whether it becomes real topology.

---

## 6. Clean migration path from bridge/gate to contract architecture

Use a compatibility-preserving migration. Do not rewrite the system around a new global hub.

### Phase A — Add common router/contract data structures

Create a small routing module:

```text
recon_lite_chess/routing/contracts.py
recon_lite_chess/routing/handoff.py
recon_lite_chess/routing/affordance_router.py
recon_lite_chess/routing/stem_queue.py
```

Initial types:

```python
AffordanceSignalV2
SkillContractSpec
SkillContractStats
HandoffPacket
RouteDecision
ShadowStemCandidate
```

Do not modify behavior yet. Just add schemas.

---

### Phase B — Wrap `endgame_gate` as a domain-level affordance router

Keep the old node id:

```text
endgame_gate
```

Keep old env output:

```python
env["endgame_gate"]["activations"]
env["endgame_gate"]["active_endgame"]
```

Add new output:

```python
env["routers"]["endgame_gate"] = {
    "scope": "domain",
    "route_scores": ...,
    "route_evidence": ...,
    "selected": ...
}
```

Use both existing mechanisms:

```text
binary/exact material detector
continuous affordance signal
weighted gate edge
```

But separate them:

```text
exact_material_match: execution eligibility
continuous affordance: approach/strategic prior
```

This preserves the bridge demo and makes it semantically cleaner.

---

### Phase C — Attach contracts to KPK, KQK, and KRK roots

Add contract metadata to existing root nodes:

```json
{
  "contract_id": "kpk.entry",
  "contract_scope": "domain_entry",
  "request_preconditions": [
    "exact_kpk_material",
    "attacker_to_move_or_subgraph_lock_valid"
  ],
  "confirmation_terms": [
    "kpk_material_valid",
    "legal_move_proposed"
  ],
  "continuation_exports": [
    "kpk.promotion",
    "kqk.entry",
    "draw_or_stalemate_safety"
  ]
}
```

For KPK promotion:

```json
{
  "contract_id": "kpk.promotion",
  "confirmation_terms": [
    "pawn_promoted",
    "promoted_piece_is_queen"
  ],
  "continuation_exports": [
    "domain.kqk"
  ]
}
```

For KQK entry:

```json
{
  "contract_id": "kqk.entry",
  "request_preconditions": [
    "exact_kqk_material",
    "attacker_has_queen"
  ],
  "safety_vetoes": [
    "stalemate_danger"
  ]
}
```

For KRK compiled scripts, derive contracts from `curriculum_label`, but group them by skill label.

---

### Phase D — Add packet emission without changing routing behavior

First packet slice:

```text
KPK promotion emits HandoffPacket
```

The old activation handover still works. The new packet should explain it.

Expected packet:

```json
{
  "from_skill": "kpk.promotion",
  "status": "confirmed",
  "achieved": [
    "pawn_promoted",
    "promoted_piece_is_queen",
    "material_signature_changed"
  ],
  "progress_delta": {
    "promotion_distance": -1
  },
  "continuation_exports": {
    "domain.kqk": 1.0,
    "kqk.entry": 1.0
  },
  "explanation": [
    "KPK promotion confirmed",
    "material signature changed from KPK to KQK",
    "KQK entry preconditions now satisfied"
  ]
}
```

This does not hardcode phase logic. The KPK skill confirms what happened; the router sees that KQK is now eligible.

---

### Phase E — Add KRK skill hub and contract grouping

Modify the KRK compiled topology path.

Current compiled topology:

```text
krk_entry
  SUB -> krk_hub
            SUB -> leg_<actuator_id>
```

Better:

```text
krk_entry
  SUB -> krk_skill_hub
            SUB -> skill_mate_in_1
            SUB -> skill_stage0_basin
            SUB -> skill_edge_trap_close
            SUB -> skill_edge_trap_enemy_between
            SUB -> skill_edge_trap_wrong_tempo
            SUB -> skill_fence_established
```

Then each skill owns its learned legs:

```text
skill_fence_established
  SUB -> leg_12
  SUB -> leg_19
  SUB -> leg_23
```

This lets the router choose a **skill**, and the skill choose a **leg**.

That is a crucial distinction. Without it, you are routing among actuator fragments, not cognitive skills.

---

### Phase F — Add KRK handoff packets and handoff-gap terminal

For Stage 5 fence, emit:

```json
{
  "from_skill": "krk.fence_established",
  "status": "confirmed",
  "achieved": [
    "cut_established",
    "rook_safe"
  ],
  "progress_delta": {
    "box_area": -4,
    "rook_fence_distance": -1
  },
  "continuation_exports": {
    "krk.drive_to_edge": 0.42,
    "krk.box_shrink": 0.35,
    "krk.edge_trap_wrong_tempo": 0.18,
    "krk.mate_basin": 0.02
  }
}
```

Then the KRK skill hub decides whether there is a strong continuation.

If not:

```text
handoff_gap = true
```

That should feed the shadow stem queue.

This directly attacks the current 30 mate / 70 draw issue.

---

## 7. Which vertical slice first?

Do both, but in different roles.

### First migration slice: `KPK promotion RET -> domain router -> KQK request`

This should be first because it is low risk and protects the existing proof of concept.

You already know the KPK→KQK handover works. Retrofitting it with contracts and packets lets you verify the new architecture without changing the behavior.

Success here means:

```text
same old handover still works
but now the reason is inspectable as a packet + route decision
```

This is the right migration test.

### First architecture-improvement slice: `KRK fence RET -> KRK skill hub -> drive/box/tempo request`

This should be second, immediately after the KPK wrapper.

KRK is the real architectural test because it exposes the failure that activation-only handover does not solve: local success followed by conversion failure.

The migration order should be:

```text
1. KPK promotion -> KQK contract wrapper
2. KRK fence -> drive/box/tempo handoff instrumentation
3. KRK handoff training/consolidation
```

Do not spend weeks perfecting the KPK wrapper. It is a migration regression test, not the bottleneck.

---

## 8. Success criteria for the first milestone

The first milestone should not require improving KRK conversion yet. It should prove that the architecture migration works and that failures are observable.

Define success as follows.

### Required behavior preservation

Existing KPK→KQK bridge behavior still passes:

```text
KPK move selector promotes
material changes to KQK
endgame/domain router selects KQK
KQK move selector proposes legal move
handover latency remains one move / one route cycle
```

No regression in current KRK local tests:

```text
Stage 1 backchain still passes
Stage 5 fence local one-ply still passes
mate-in-1 still passes
```

---

### Required new observability

Every routed move should produce:

```text
active domain
active skill or subgraph
route score components
selected contract
HandoffPacket or explicit no-packet reason
continuation affordances
```

For the KPK promotion test, the trace should show:

```text
kpk.promotion confirmed
material_signature_changed
domain.kqk exported
endgame_gate/domain router selected kqk
kqk.entry requested
```

For KRK fence evaluation, even if mate rate stays 30/70 initially, the trace should show:

```text
fence confirmed
next skill affordances computed
handoff gap detected when no continuation is strong
draw-loop/stagnation tagged when conversion fails
candidate queued in shadow stem queue
```

That is the real milestone: making the bottleneck explicit.

---

### Required metric fixes

Fix the `conversion_passed` semantics.

The Stage 5 artifact currently says `conversion_passed: true` even though `adaptive_playout_max_plies` was `0`, while the separate debug file shows 30 mate / 70 draw. That is semantically misleading.

Use a tri-state:

```text
conversion_status:
  "passed"
  "failed"
  "not_checked"
```

Do not allow this:

```json
"conversion_passed": true
```

when no playout was actually sampled.

Better:

```json
{
  "one_ply_status": "passed",
  "conversion_status": "not_checked",
  "conversion_checked": false
}
```

Then the debug playout can honestly report:

```json
{
  "one_ply_status": "passed",
  "conversion_status": "failed",
  "mate_playout_rate": 0.30,
  "draw_rate": 0.70
}
```

This matters because the whole architecture is now about handoff/conversion, not local stage success.

---

## Concrete implementation recommendations

### Implementation step 1: Add contract and packet schemas

Add:

```text
routing/contracts.py
routing/handoff.py
```

Minimal useful schemas:

```python
@dataclass(frozen=True)
class SkillContractSpec:
    skill_id: str
    domain: str
    provider_node: str
    scope: str  # domain_entry, skill, tactic, strategy

    request_preconditions: tuple[str, ...]
    affordance_inputs: tuple[str, ...]
    promised_deltas: tuple[str, ...]
    confirmation_terms: tuple[str, ...]
    failure_terms: tuple[str, ...]
    safety_vetoes: tuple[str, ...]
    continuation_exports: tuple[str, ...]

    training_origin: dict[str, Any]
```

```python
@dataclass
class HandoffPacket:
    from_skill: str
    status: str
    achieved: list[str]
    failed: list[str]
    progress_delta: dict[str, float]
    affordance_before: dict[str, float]
    affordance_after: dict[str, float]
    continuation_exports: dict[str, float]
    explanation: list[str]
```

Keep them dumb. Do not over-engineer.

---

### Implementation step 2: Retrofit `endgame_gate`

Modify `create_endgame_gate` so it still behaves like the old gate but also emits a richer route decision.

Internally, use:

```text
exact material detection
continuous affordance score
route edge weight
RET packet boost
```

The old `get_gate_routing_decision` can become:

```python
get_domain_route_decision(env, weights=None)
```

but keep the old function as a wrapper for compatibility.

---

### Implementation step 3: Modify `baseline_to_recon.py` to group KRK legs by skill label

Current compiler uses actuator-level legs directly under `krk_hub`.

Change to:

```text
krk_hub
  -> skill_<curriculum_label>
       -> leg_<actuator_id>
```

Attach contract metadata at the skill node:

```json
{
  "contract_id": "krk.fence_established",
  "curriculum_label": "fence_established",
  "training_target_label": "edge_trap_wrong_tempo",
  "contract_scope": "skill",
  "confirmation_terms": [
    "cut_established",
    "rook_safe"
  ],
  "continuation_exports": [
    "krk.drive_to_edge",
    "krk.box_shrink",
    "krk.edge_trap_wrong_tempo",
    "krk.mate_basin"
  ]
}
```

Do not confuse these two fields:

```text
training_target_label:
  what the skill was trained to approach

continuation_exports:
  what the router may request after this skill confirms
```

That distinction is important for the KRK curriculum because the stages are learned by backward chaining.

---

### Implementation step 4: Add packet logging to KPK promotion and KRK fence confirmation

For KPK, packet emission should happen around `promotion_probe` / promotion confirmation.

For KRK, packet emission should happen when the grouped skill node confirms, not merely when one actuator terminal proposes a move.

That means the skill wrapper should aggregate:

```text
selected leg
move proposed
postcondition result
landmark delta
safety result
next affordance snapshot
```

and then emit one skill-level packet.

---

### Implementation step 5: Add shadow candidate queue

Add one JSONL/event sink:

```text
stem_cell_candidates.jsonl
```

Initial triggers:

```text
handoff_gap
repeated_conversion_failure
route_conflict
low_affordance_state
```

Each candidate should reference:

```text
owner router
parent skill
state signature
route scores
packet id
outcome
```

No durable mutation during gameplay yet.

---

## Final recommendation

The clean architecture is:

```text
endgame_gate survives as the domain router
AffordanceHub becomes a reusable router pattern
KRK/KPK/KQK get internal skill hubs
SkillContract is static topology metadata plus runtime stats
RET packets are runtime records first
successful repeated packets may compile into graph bridges later
online growth goes through a shadow queue
```

The first milestone should be:

```text
KPK→KQK bridge still works,
but now the handoff is represented as:
  KPK promotion contract confirmation
  HandoffPacket
  domain router decision
  KQK request
  route explanation
```

Then immediately use the same machinery on:

```text
KRK fence confirmed
  -> KRK skill hub
  -> drive / box_shrink / tempo / edge_trap request
```

That second slice is where the architecture will actually start paying rent.



============

User prompt/follow up: 


Thanks! Just a heads-up: I'm basing this on Joscha Bach's article on ReCoN and want to keep it "true" to the ReCoN formalism to the largest extent possible. That being said obviously I AM expanding on ReCoN but I want to solve the problems/challenges using only "vanilla" ReCoN to as large if an extent as possible without "cheating". Then again I feel we are mostly adding scaffolding/engine environment and we want it more dynamic (growing etc) behaviors. After solving chess (say, 1900 level or at least full games) I'll try other applications. But I feel like once we have working, reliable, topological growth I think we are in a good place for publishing another article and explore other applications/environments. 
Also I will want to move further towards what could be "proto consciousness". Hence the self monitoring (internal terminals) etc, that's one of the main goals with the architecture. One idea I have is to "short circuit" the ReCoN so it "dreams" (connect outputs to inputs and monitor how plausible it is compared to a "real" environment), maybe this is better suited in a different environment than chess though. Either way ita further in the future 

=======
Final answer: 

Your instinct is basically right: **the additions should be ReCoN-shaped scaffolding, not a second architecture hiding inside ReCoN.** The danger is not that `SkillContract`, `AffordanceHub`, or `RET packet` are “non-vanilla” names. The danger is that they become invisible executive objects making decisions outside the graph.

So I would reframe the previous recommendations like this:

```text
SkillContract      = semantic metadata of a SCRIPT node/subgraph
HandoffPacket      = runtime trace of confirmation, not a new cognitive message type
AffordanceHub      = ReCoN SCRIPT pack for competing affordance hypotheses
Stem-cell queue    = growth nursery/compiler scaffold, not a hidden planner
Internal terminals = legitimate TERMINAL nodes sensing graph/environment state
```

That keeps the system close to vanilla ReCoN while still allowing dynamic growth, introspection, and later “dreaming.”

---

## The purity rule I would use

A useful test:

> If a mechanism affects cognition, it must either be a ReCoN node, a ReCoN edge, a terminal measurement, a node state, an activation value, or explicit metadata attached to one of those.

Everything else should be engine scaffolding only:

```text
Allowed engine scaffolding:
  scheduler
  graph compiler
  trace logger
  topology serializer
  candidate-growth queue
  test harness
  environment adapter
  chess board transition function

Not allowed as hidden cognition:
  external planner deciding phases invisibly
  router selecting moves without graph evidence
  growth manager inventing concepts without visible node ancestry
  confidence object not readable by internal terminals
```

That is the line I would enforce hard.

The graph does not need to implement file I/O, Python dataclasses, or serialization internally. But **the reasons for action must be visible in ReCoN topology and activations**.

---

## Reinterpret `SkillContract` in vanilla ReCoN terms

Do not think of `SkillContract` as a new runtime control object.

Think of it as the **claim made by a SCRIPT node**.

In vanilla ReCoN, a SCRIPT is a hypothesis requiring validation from sub-elements. So a skill contract is simply the explicit declaration of:

```text
What this SCRIPT may be requested for.
What children it requests.
What confirmations would make it true.
What failures suppress it.
What successor SCRIPTs become relevant after confirmation.
```

So this:

```text
SkillContract(krk.fence_established)
```

should correspond to a visible ReCoN structure like:

```text
SCRIPT krk.fence_established
  SUB -> SCRIPT krk.fence.preconditions
  SUB -> SCRIPT krk.fence.action_pack
  SUB -> SCRIPT krk.fence.confirmation
  SUB -> SCRIPT krk.fence.safety_vetoes
  POR -> SCRIPT krk.fence.confirmation_after_action
```

The contract metadata can say:

```json
{
  "skill_id": "krk.fence_established",
  "request_preconditions": [
    "material_is_krk",
    "rook_available",
    "rook_not_lost"
  ],
  "confirmation_terms": [
    "cut_established",
    "rook_safe"
  ],
  "continuation_exports": [
    "krk.drive_to_edge",
    "krk.box_shrink",
    "krk.opposition_tempo",
    "krk.edge_trap"
  ]
}
```

But the actual cognitive mechanism should still be graph-based:

```text
precondition SCRIPT confirms
action SCRIPT proposes/executes
postcondition SCRIPT confirms
parent SCRIPT confirms or fails
successor SCRIPT receives activation/request
```

So `SkillContract` should mostly be **compile-time / inspection metadata** attached to SCRIPT nodes. Runtime reliability stats can exist, but they should be readable through internal terminals if they influence behavior.

For example:

```text
TERMINAL krk.fence.reliability_sensor
  reads SkillContractStats["krk.fence_established"]

SCRIPT krk.fence.trust_gate
  SUB -> krk.fence.reliability_sensor
  SUB -> current_affordance_sensor
```

That keeps learned confidence inside the ReCoN-visible loop.

---

## Reinterpret `RET packets` as traces, not new ReCoN messages

This is important.

A literal “RET packet” is not vanilla ReCoN if it becomes a new causal message type. In ReCoN, the causal messages are already there:

```text
SUB request
SUR wait/confirm
POR inhibit_request
RET inhibit_confirm
```

So the safer framing is:

```text
HandoffPacket = structured runtime trace of ReCoN state transitions and confirmations.
```

It records what happened. It does not itself decide what happens.

For example, after KPK promotion:

```json
{
  "from_script": "kpk.promotion",
  "status": "confirmed",
  "observed_confirmations": [
    "pawn_promoted",
    "promoted_piece_is_queen",
    "material_signature_changed"
  ],
  "new_affordances": {
    "domain.kqk": 1.0,
    "kqk.entry": 1.0
  }
}
```

The packet is a trace artifact. The actual ReCoN structure should be something like:

```text
SCRIPT kpk.promotion
  SUB -> TERMINAL pawn_on_promotion_square
  SUB -> TERMINAL promotion_move_selected
  SUB -> SCRIPT promotion_confirmed

SCRIPT promotion_confirmed
  SUB -> TERMINAL promoted_piece_is_queen
  SUB -> TERMINAL material_is_kqk

SCRIPT endgame_gate
  SUB -> SCRIPT kpk_root
  SUB -> SCRIPT kqk_root
  SUB -> SCRIPT krk_root
```

Then the engine trace can say:

```text
kpk.promotion confirmed
material_is_kqk terminal activated
endgame_gate now requests/confirms kqk_root
```

That is ReCoN-clean.

Later, if repeated traces show a robust handoff, compile it into topology:

```text
SCRIPT bridge.kpk_promotion_to_kqk
  SUB -> SCRIPT kpk.promotion_confirmed
  POR -> SCRIPT kqk.entry_requested
  RET -> SCRIPT kpk.promotion_confirmed
```

But again: POR/RET only between SCRIPT nodes. Do not attach temporal links directly to terminals.

---

## Reinterpret `AffordanceHub` as a SCRIPT pack, not a controller

A hub should not be an external router.

It should be a ReCoN SCRIPT whose children are affordance hypotheses.

For example:

```text
SCRIPT krk.skill_hub
  SUB -> SCRIPT krk.mate_affordance
  SUB -> SCRIPT krk.edge_trap_affordance
  SUB -> SCRIPT krk.fence_affordance
  SUB -> SCRIPT krk.drive_affordance
  SUB -> SCRIPT krk.box_shrink_affordance
  SUB -> SCRIPT krk.opposition_tempo_affordance
```

Each affordance SCRIPT can request terminals:

```text
SCRIPT krk.drive_affordance
  SUB -> TERMINAL material_is_krk
  SUB -> TERMINAL enemy_king_not_at_edge
  SUB -> TERMINAL rook_safe
  SUB -> TERMINAL white_king_can_approach
  SUB -> TERMINAL drive_progress_available
```

Then the hub’s activation dynamics select the strongest confirming/requestable child. The engine may implement weighted activation arithmetic, but the inputs and outputs remain graph-inspectable.

A good ReCoN-pure migration from the old `endgame_gate` is:

```text
SCRIPT endgame_gate
  SUB -> SCRIPT domain.krk_affordance
  SUB -> SCRIPT domain.kpk_affordance
  SUB -> SCRIPT domain.kqk_affordance
```

Then inside KRK:

```text
SCRIPT krk_root
  SUB -> SCRIPT krk.skill_hub
```

Do not flatten this into one giant global hub. Keep:

```text
endgame_gate = domain/material router
krk.skill_hub = local skill router
kpk.skill_hub = local skill router
kqk.skill_hub = local skill router
tactics_hub = interrupt/forcing-pattern router
```

That preserves hierarchy, which is central to ReCoN.

---

## How to keep the old bridge demo without cheating

The KPK→KQK bridge proof is valuable because it already demonstrates something ReCoN-ish:

```text
material/sensor change
→ activation shift
→ subgraph handover
```

But to make it more faithful, I would change the explanation from:

```text
The endgame gate switches from KPK to KQK.
```

to:

```text
The KPK promotion SCRIPT confirms.
The board/material TERMINAL now confirms KQK eligibility.
The endgame_gate SCRIPT receives new child confirmations.
The KQK root SCRIPT becomes the best-confirming/requested successor.
```

That turns a phase switch into a request-confirmation story.

The migration target should be:

```text
KPK promotion is not a special case.
It is just one confirming SCRIPT whose confirmation changes downstream affordances.
```

Then the exact same mechanism can handle:

```text
KRK fence confirmed -> drive/box/tempo affordances change
tactic wins queen -> material/endgame affordances change
middlegame plan opens file -> rook-lift/tactical affordances change
```

---

## About dynamic growth and “vanilla” ReCoN

Topological growth is not itself part of the minimal static ReCoN formalism, so some engine scaffolding is unavoidable. But you can keep it honest.

The growth manager should not be a hidden agent. It should only do this:

```text
observe traces
cluster repeated failures/successes
propose candidate ReCoN packs
test them
compile successful candidates into explicit topology
```

A stem-cell candidate should eventually become one of these:

```text
TERMINAL sensor
TERMINAL actuator
SCRIPT AND/OR pack
SCRIPT skill wrapper
POR/RET sequence between SCRIPTs
weighted SUB edge
shared FeatureHub terminal
```

Nothing else.

That is the key discipline.

For example, a handoff-gap stem cell should not become:

```text
external Python function choose_next_skill()
```

It should become:

```text
SCRIPT krk.fence_to_drive_bridge
  SUB -> SCRIPT krk.fence_confirmed
  SUB -> TERMINAL enemy_king_not_at_edge
  SUB -> TERMINAL box_area_large
  POR -> SCRIPT krk.drive_to_edge
```

Or, if it is only a sensor:

```text
TERMINAL fence_confirmed_but_box_large
```

which can then be requested by a larger SCRIPT.

---

## Internal terminals are very ReCoN-compatible

Your self-monitoring direction is not a detour. It actually fits ReCoN well.

A terminal is just a measurement. There is no reason it must only measure the chess board. It can measure:

```text
graph activation state
recent confirmation history
route conflict
unconfirmed request duration
repetition/stagnation
prediction error
novelty
confidence calibration
simulation-vs-reality mismatch
```

So internal terminals are legitimate ReCoN terminals as long as they are explicit.

Examples:

```text
TERMINAL active_skill_id
TERMINAL top_affordance_margin
TERMINAL repeated_state_abstraction
TERMINAL last_script_failed
TERMINAL no_child_confirmed_recently
TERMINAL prediction_error_high
TERMINAL simulated_state_plausible
TERMINAL source_is_real_environment
TERMINAL source_is_imagined_environment
```

Then metacognitive SCRIPTs can request them:

```text
SCRIPT monitor.handoff_gap
  SUB -> TERMINAL last_skill_confirmed
  SUB -> TERMINAL no_strong_successor_affordance

SCRIPT monitor.stagnation
  SUB -> TERMINAL repeated_state_abstraction
  SUB -> TERMINAL no_progress_delta

SCRIPT monitor.route_conflict
  SUB -> TERMINAL top_two_affordances_close
  SUB -> TERMINAL both_routes_historically_reliable
```

This is a good route toward proto-self-monitoring because the system is not merely acting; it is developing explicit hypotheses about its own control state.

The thing to avoid is a single opaque “self-awareness module.” Better:

```text
many small internal terminals
many local monitor SCRIPTs
one or more higher-level integration SCRIPTs
```

That is more ReCoN-like and more publishable.

---

## “Dreaming” can be ReCoN-compatible, but do not short-circuit too literally

The idea of connecting outputs back to inputs is promising, but it needs a guardrail.

Do **not** directly feed actuator outputs into ordinary sensory terminals as if they were real environment observations. That will blur reality and simulation in a way that makes debugging, learning, and explanation ugly.

Instead, create an explicit simulated environment layer:

```text
real_env.board_state
sim_env.board_state
```

Then terminals can be source-aware:

```text
TERMINAL board_feature_real
TERMINAL board_feature_simulated
TERMINAL real_vs_sim_prediction_error
TERMINAL simulation_plausibility
TERMINAL imagined_line_depth
```

A ReCoN-clean “dream” loop could look like:

```text
SCRIPT imagine_move
  SUB -> SCRIPT current_plan
  SUB -> TERMINAL proposed_action
  POR -> SCRIPT predict_next_state
  POR -> SCRIPT evaluate_predicted_state
  POR -> SCRIPT compare_with_goal_memory
```

Where:

```text
TERMINAL transition_model
```

or a chess rules adapter produces a simulated next board.

Then the system can run:

```text
current real state
→ proposed action
→ simulated next state
→ ordinary feature terminals read simulated state
→ plausibility/error terminals monitor simulation quality
→ plan SCRIPT gets confirmation or failure
```

That is close to predictive processing, but still ReCoN-shaped.

For chess specifically, dreaming is less interesting than in a perceptual environment because the legal transition model is deterministic and already known. The useful “dreaming” part in chess is opponent modeling and plan continuation:

```text
What reply is likely?
What affordances survive the reply?
Does this local confirmation lead to conversion?
Where does the line stagnate?
```

So in chess, call it:

```text
counterfactual playout
imagined continuation
handoff rehearsal
```

rather than full dreaming.

A richer future environment with partial observability, perception, or embodied action would make the dream idea more biologically interesting. But chess is still a good place to test the machinery safely.

---

## A possible proto-consciousness ladder

I would not jump straight from KRK to “dreaming.” I would stage it.

### Level 1: External action awareness

The system can answer:

```text
What skill am I using?
What evidence requested it?
What move did it propose?
What confirmation did it expect?
Did confirmation arrive?
```

This is already close to your handoff-packet/trace system.

---

### Level 2: Internal control awareness

The system can answer:

```text
Am I stuck?
Are two subgraphs competing?
Did a skill confirm locally but fail globally?
Is my confidence calibrated?
Am I in a known state family?
```

This is where internal terminals matter.

---

### Level 3: Counterfactual awareness

The system can run simulated branches and answer:

```text
If I do X, what internal affordances will change?
Will a known successor skill become available?
Where does the plan lose confirmation?
```

This is the practical chess version of dreaming.

---

### Level 4: Source awareness

The system distinguishes:

```text
real observation
imagined observation
remembered goal memory
predicted future state
failed prediction
```

This is very important if you care about proto-consciousness. A system that cannot label source is not introspecting; it is just mixing activations.

---

### Level 5: Self-model as graph object

The system has ReCoN nodes representing facts about itself:

```text
my KRK-fence skill is reliable in this bucket
my KQK handoff is well calibrated
my tactic hub often falsely interrupts this plan
my current route was selected under low margin
```

This is where self-reference becomes architectural rather than rhetorical.

---

## What I would adjust in the previous recommendations

I would slightly rename the concepts to avoid drifting away from ReCoN.

Instead of:

```text
AffordanceHub
SkillContract
RET packet
```

use internal terminology closer to:

```text
Affordance SCRIPT pack
SCRIPT contract metadata
confirmation trace / handoff trace
```

You can still use the convenient names in code, but the paper should explain them in ReCoN terms.

A clean formulation:

```text
An affordance hub is not an external router; it is a SCRIPT node whose children are competing affordance hypotheses.

A skill contract is not a planner API; it is the explicit semantic interpretation of a SCRIPT’s confirmation.

A handoff packet is not a new ReCoN message; it is a runtime trace summarizing SUB/SUR/POR/RET state transitions for inspection, learning, and later compilation.
```

That is the line I would put in the architecture notes.

---

## Near-term design recommendation

For the next implementation phase, I would make the architecture stricter, not looser.

Implement this:

```text
SCRIPT endgame_gate
  SUB -> SCRIPT domain.kpk
  SUB -> SCRIPT domain.kqk
  SUB -> SCRIPT domain.krk

SCRIPT domain.krk
  SUB -> SCRIPT krk.skill_hub

SCRIPT krk.skill_hub
  SUB -> SCRIPT krk.fence_established
  SUB -> SCRIPT krk.drive_to_edge
  SUB -> SCRIPT krk.box_shrink
  SUB -> SCRIPT krk.opposition_tempo
  SUB -> SCRIPT krk.edge_trap
  SUB -> SCRIPT krk.mate_basin
```

Attach metadata to each SCRIPT:

```text
contract_id
confirmation_terms
failure_terms
continuation_exports
training_origin
reliability_stats_key
```

Add internal terminals:

```text
handoff_gap
stagnation_detected
route_conflict
low_affordance_state
simulation_source_real_or_imagined
```

Then make the trace logger produce handoff records from normal ReCoN dynamics.

That way, the implementation can support all the future stuff without becoming a non-ReCoN controller.

---

## The important challenge

The hard part will not be adding self-monitoring. It will be preventing self-monitoring from becoming a parallel executive.

A bad version:

```text
meta-controller watches graph
meta-controller decides what graph should do
graph becomes visualization only
```

A good version:

```text
internal terminals measure graph state
monitor SCRIPTs confirm/fail hypotheses about control state
those confirmations modulate requests to ordinary skill SCRIPTs
the graph remains causally responsible
```

Same for dreaming.

A bad version:

```text
Python search simulates lines and tells ReCoN what to play
```

A good version:

```text
ReCoN requests an imagined continuation
simulation terminals provide predicted observations
ordinary affordance/confirmation scripts evaluate them
internal terminals monitor plausibility and source
```

That distinction matters a lot if you want the work to be defensible as a ReCoN-derived cognitive architecture rather than a chess engine with a graph UI.

---

## Publication threshold

I would seriously consider publishing before “1900-level chess.”

A stronger scientific result would be:

```text
A ReCoN system learns local skills,
compiles them into explicit topology,
hands off between independently learned subgraphs,
detects handoff failure,
spawns candidate structures,
prunes/consolidates them,
and preserves trace-level explainability.
```

That is publishable even if the chess strength is modest.

The cleanest “big result” would be:

```text
KPK promotion -> KQK handoff works as before,
KRK fence -> drive/box/tempo handoff improves through learned topology,
a previously missing handoff is discovered from repeated failures,
the new bridge is compiled into ReCoN structure,
and the system can explain the before/after graph difference.
```

That would show actual structural maturation, not just better play.

For the proto-consciousness angle, the first publishable step is not “the system is conscious.” It is:

```text
The system has explicit internal terminals for monitoring its own activation, uncertainty, prediction failure, and source distinction, and those terminals participate in the same request-confirmation grammar as external perception.
```

That is a grounded claim. It avoids overclaiming while clearly pointing toward self-monitoring and self-modeling.
