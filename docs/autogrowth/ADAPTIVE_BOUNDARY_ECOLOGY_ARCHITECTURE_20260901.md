# Adaptive boundary ecology: architecture handoff

## Status and scope

This note describes the current working-tree design on branch
`codex/adaptive-boundary-ecology` in
[`Paulander/hector-recon`](https://github.com/Paulander/hector-recon).

- Prior architecture anchor: `52f666d3111e39c57fb6e16889678540c2fb6d62`.
- Current adaptive-local implementation: `444b927f07882ae1c197b6006fad1c0672ef2245`.
- Native admission/alias repair: `67414302390040bc1047ef4c43489467a2162b38`.
- Local retrieval and selective-credit repair: `deedcb90`.
- Retention/jurisdiction reporting repair: `58abe72d`.
- Current empty-shell strict adaptive mechanism: `b1a8ed1f`.
- Original audited base: `2f1b68c992eb6868b468148004d8e5a4746c88ab`.

The current implementation closes the concrete V15–V18 control-loop defects:
R0 and R1 experience are no longer chosen by host schedules; adaptive
evaluation no longer routes through a prototype gate or a host-side
core/child/plastic fallback cascade; exact and generalized candidates cannot
silently evict the credited local incumbent; and TD responsibility is no
longer copied at full strength into every shared atom. The previous modes
remain for historical runners, while the adaptive entrypoint now fails closed
if a caller tries to re-enable them.

The native admission/alias repair makes R0 authority coverage/specificity
report-only. Once the existing R0 validation-mastery curriculum transition has
been met, only outcome-blind authority runtime integrity can veto R1 entry. An
`UNKNOWN` authority response abstains locally, while formally confirmed trace
evidence is unioned across aliases of one actuator without merging local option
identity or activation/strength.

The adaptive boundary now starts empty: no discovery tape, negative roots,
candidate cells, scheduled frontiers, or bootstrap certification. The frozen
mate-in-1 graph can act on a REAL successor, but the boundary may claim that
region only after a surprise success creates a tentative positive bud and
later distinct REAL events certify it. This removes the old mixed-polarity
32/32 authority initialization from the adaptive path; that factory remains
only for legacy reproduction.

This is still a development architecture, not evidence of mate-in-2 learning.
The V18 canary below predates `deedcb90`, `58abe72d`, and `b1a8ed1f`. A fresh
bounded canary at the current commit is the next gate. No mate-in-2 result is
claimed in this note.

The fresh V16 canary bound to `8e1583972cca391fc10a0d689ebd89f86387471b`
(`2026090106`, exact wall `645.8366680829786 s`) stopped after R0: validation
was `16/16`, report-only regression was `14/16`, and no R1 arm ran. It has no
mate-in-2 result. Its old native admission report is preserved as a
coverage/specificity diagnostic; repair `67414302` makes
that diagnostic report-only and uses outcome-blind runtime integrity for the
native-authority portion of stage entry. Post-repair verification passed 106
focused core tests and 61 additional ecology/authority tests; 31 historical
compatibility cases could not run because their pre-existing result fixtures
are absent from this checkout.

The later V18 canary at exact commit `0373c0cc26f719997dd1c8a6e723ef9ce32c92d0`
completed in `2916.2569021661766 s`. It retained the isolated frozen R0 policy
at `16/16`, but report-only R0 regression was `14/16`; the evolving V2 shell
covered only `6/16`. It produced 32 R1 episodes, three AVAILABLE all-reply
envelopes, one handoff, nonzero successor value, and two TD events, but
exhaustive mate-in-2 conversion remained `0/4`. All 32 local first-move
patterns were first exposures, so neither credited decision was revisited.
The run started from legacy mixed bootstrap roots and produced zero adaptive
buds. These facts motivated the empty-shell, local-retrieval, and selective-
credit changes above; V18 is evidence about the old mechanism, not efficacy
evidence for `b1a8ed1f`.

## The idea in plain language

The intended organism begins with a learned mate-in-1 competence skeleton. On
a harder position it tries a first move using local patterns and values already
stored in its graph, plus a bounded preference for underexplored patterns. The
environment then supplies the consequences. If the move reaches positions that
the frozen mate-in-1 authority can finish after **every** legal opponent reply,
the weakest reply supplies the successor value credited to that exact first
move pattern.

Unexpected successes just outside known competence can bud tentative boundary
structures. A bud is cheap and has no authority. It must recur on later,
distinct REAL interactions before it can answer prospectively. Contradictions
make a coarse structure abstain in the failed region and can trigger narrower
residual children. Weak or exhausted structures become dormant or die; useful
children can become anchors for the next outward shell.

The central loop is therefore:

```text
learned local value + bounded curiosity
                  |
                  v
        emit exactly one first move
                  |
                  v
      observe environmental consequence
                  |
                  +--> exact-pattern TD/eligibility credit
                  |
                  +--> local support, contrast, budding and refinement
                  |
                  v
  atomically settle pending mutations at a quiescent safe point
                  |
                  v
       repeat with the changed native state
```

No correct move, mate-distance label, tablebase, Stockfish answer, held-out
answer, epoch-specific prescription, or absolute-position identity is supplied
to the learner's action competition. Legal action generation and observed game
outcomes come from the environment. Exhaustive mate evaluation is report-only.

## Vocabulary

| Term | Meaning here |
| --- | --- |
| **R0 / core** | The learned native mate-in-1 competence. “R0” is a curriculum index, not a second kind of network. |
| **R1 / boundary task** | Learning a first move whose successors are finishable after every opponent reply. In this curriculum it is mate-in-2. |
| **Local action pattern** | The canonical before/delta/after triplet induced by one legal action. It contains local graph features, not FEN, epoch, stage, or an answer label. |
| **REAL receipt** | An immutable record of an action/outcome interaction actually opened to the learner. |
| **VIRTUAL query** | A read-only authority query. It can test jurisdiction but cannot train or certify. |
| **Bud / sketch** | A cheap tentative conjunction of locally active graph-visible signals. It has no authority. |
| **Promotion** | Atomic materialization of an eligible sketch as a dormant authority child. Promotion still gives it zero authority. |
| **Certification** | Distinct post-birth REAL evidence makes a promoted child prospectively authoritative. Discovery evidence is excluded. |
| **Handoff** | A complete all-reply envelope exposes grounded successor value to the exploratory first move. |
| **Safe point** | A content-blind quiescent boundary at which pending graph mutations commit atomically. It decides when mutation is safe, not what deserves to grow. |

## One R1 learning step

### 1. Generate local competitors

For every legal first move, the graph derives the same canonical local triplet
identity used by its before-state, action/delta, and after-state machinery.
Existing exact or shared-feature graph sources contribute their stored raw
native value. A legal pattern with no source is assigned a neutral exploitation
value only while training, so unexplored behavior remains reachable.

The training activation is:

```text
v / (1 + |v|)
+ min(1, sqrt(2 log(1 + current-competitor exposures)
              / (1 + this-pattern exposures)))
```

An unseen local pattern receives novelty `1`. The second term thereafter is a
generic bounded optimism bonus. It uses only exposures belonging to the
patterns competing in this decision, so unrelated positions cannot inflate
novelty indefinitely. Legal moves sharing one abstract pattern form an alias
group; exposure rotates its representative deterministically, so the same
alias is not chosen forever.

### 2. Emit one action through a formal ReCoN choice

One `AnonymousChoiceOption` is created per local pattern. An
`AnonymousChoiceGenome` performs exactly-one arbitration and emits the legal
actuator. Only the emitted exact triplet is then materialized and formally
confirmed. The implementation refuses to execute it if emitted identity,
materialized triplet, and confirmation disagree.

This ordering matters: candidate inspection does not eagerly grow a branch for
every legal move. Growth follows the one action actually emitted.

### 3. Observe, credit, and record exposure

After the environment transition, `apply_intrinsic_td` must return the same
triplet identity that was emitted. The TD prediction is the pre-emission raw
native value, never the curiosity bonus. The exact pattern and graph root gain
one exposure only after this outcome-grounded update; merely asking the policy
does not consume an exposure.

A bounded, digest-chained action-event ledger records emitted and credited
identities, raw value, curiosity, successor value, and TD error for replay and
audit. It is diagnostic state, not an action source.

When several formally confirmed local triplet aliases can emit the same legal
actuator, their captured graph signals are deterministically unioned before the
trace is recorded. Emitted-action trace evidence is therefore alias-invariant:
the anonymous winner does not change the formally observed evidence attached to
that actuator. Option identity and activation/strength remain local to each
triplet alias, so this does not collapse local competition or alias-specific
choice semantics. The union uses only formally confirmed graph captures; no
outcome, label, or board identity participates.

Main implementation:

- [`src/recon_lite_chess/autogrowth/native_single_graph_curriculum.py`](../../src/recon_lite_chess/autogrowth/native_single_graph_curriculum.py)
  - `choose_local_training_action` performs exploratory local competition;
  - `choose_local_policy_action` performs read-only learned-policy emission;
  - `apply_intrinsic_td` credits the observed exact branch and records exposure.
- [`src/recon_lite_chess/autogrowth/native_intrinsic_curriculum.py`](../../src/recon_lite_chess/autogrowth/native_intrinsic_curriculum.py)
  - `_select_r1_training_action` selects the adaptive-local path;
  - `_run_r1_arm` enforces emitted/credited triplet identity.

## What is native state, and what remains an adapter?

The current action mechanism deliberately removes the host from choosing a
move, but it would be inaccurate to claim that every arithmetic operation is
already embodied as a persistent graph circuit.

Persistent learned/native state includes:

- graph nodes, edges, triplets, weights, shared-feature sources, and exposure
  counts;
- formal confirmation of the selected branch;
- competence values, eligibility/responsibility, and outcome-grounded TD
  updates;
- authority cells, lineages, REAL receipts, certification evidence, and
  retirement tombstones;
- formal exactly-one emission by `AnonymousChoiceGenome`.

A generic Python adapter currently:

- enumerates legal environmental affordances;
- derives their canonical local triplet identities;
- retrieves confirmed exact/shared graph sources and takes a deterministic
  best source for each move;
- computes value normalization, the UCB-like optimism term, the resource cap,
  and alias rotation;
- packages those activations as anonymous choice options.

That adapter cannot read a correct move, mate label, FEN identity, epoch,
curriculum stage, held-out answer, or external oracle. Its rule is domain-generic
and replayable, but it is still substrate code surrounding the persistent graph.
The precise claim is therefore **native learned evidence with formal ReCoN
emission**, not “the complete arbitration circuit is already inside the graph.”

The candidate scan also has an explicit finite cap. Exact and generalized
sources coexist; the exact local branch and the learned incumbent for every
remaining legal action are reserved before challenger capacity is filled.
Reports expose pair counts before and after the cap, so a run cannot silently
present a truncated action competition as an unbounded one.

When one decision credits a branch containing many shared atoms, the TD update
is responsibility-conserving: private/exact state receives full local credit,
while shared features divide responsibility according to the graph's
normalization (`1`, `1/sqrt(n)`, or `1/n`). One outcome can therefore influence
general features without being copied at full strength into every alias.

## Evaluation uses the learned policy, not a second picker

Training and evaluation now differ only where exploration should differ:

- training admits unsupported legal patterns at neutral value and adds the
  curiosity bonus;
- evaluation disables curiosity and materialization;
- evaluation retains only options backed by a persistent, formally confirmed
  graph source;
- if no such source exists, the policy abstains.

For mate-in-2 evaluation, that local exploitation policy chooses the first
move. Each opponent successor then goes directly to the native V2 authority.
If the authority is `UNKNOWN`, `REFUTED`, null, or illegal, evaluation abstains
for that reply and the candidate does not count as converted. There is no
prototype-gate call, no `_choose_with_child_priority` cascade, and no fallthrough
to the plastic graph.

Two R0 measurements are deliberately separate. **Frozen native-policy
retention** asks whether the immutable mate-in-1 graph still chooses a mating
move; **V2 shell coverage** asks whether the prospectively certified boundary
currently authorizes that move. Shell abstention is not mislabeled as graph
forgetting.

`UNKNOWN` is a local abstention, not a global R1 stage veto: it cannot provide
successor bootstrap/value for that reply, while unrelated R1 environmental
experience remains admissible.

This makes evaluation stricter and conceptually cleaner: a success must be
produced by the learned first-move policy and grounded successor authority, not
rescued by a host router.

## Frozen R0 core and initially empty prospective closure

The adaptive path no longer fits or uses `OutcomeCalibratedPrototypeGate`.
After the fixed R0 training budget, the graph's exploration-free local policy
is re-executed on its already experienced training environment. If that
training-outcome probe meets the curriculum threshold, the harness commits
maturity, consolidation, and freezing, then copies the immutable R0 organism
into `NativeProspectiveAuthorityV2`. This is an explicit host-controlled
curriculum boundary, not a learned move picker and not claimed to be
endogenous ReCoN lifecycle.

The V2 boundary around that core is initially empty. Its construction is
forbidden from reading any pool rows and asserts zero receipts, cells,
candidates, states, accepted REAL references, discovery fingerprints,
promotions, pending requests, and scheduled frontiers. The core may still emit
one action on a later REAL successor; only ordinary outcome receipts can then
grow prospective jurisdiction around successful local traces.

A read-only native admission audit reports initial coverage and specificity:

- every R0 validation positive must receive an AVAILABLE legal response that
  actually mates in the copied environment;
- every validation decoy must receive no AVAILABLE response;
- all queries are VIRTUAL and both authority continuation and frozen-R0
  inference identity must remain unchanged.

The outcome coverage/specificity result is report-only; it does not control R1
stage entry. The native-authority entry check uses only the outcome-blind
`runtime_integrity_pass`: unchanged
authority/source continuation, every emitted actuation legal, and every
AVAILABLE response backed by a legal non-null actuation. The implementation
records these boundaries explicitly as
`coverage_specificity_controls_r1_stage_entry=false` and
`runtime_integrity_controls_r1_stage_entry=true`. The audit never selects
training actions or provides runtime answers to the learner. If authority is
`UNKNOWN`, the local policy abstains and sends no successor bootstrap/value;
that local abstention does not block unrelated R1 environmental experience.

The phrase “validation is report-only” is intentionally narrowed: validation
**outcomes/mastery** cannot stop, mature, consolidate, freeze, or select an
action. The outcome-blind runtime-integrity audit may still veto R1 as a safety
check if the supposedly immutable authority mutates or emits an invalid
AVAILABLE actuation.

Main implementation:

- [`src/recon_lite_chess/autogrowth/native_intrinsic_curriculum.py`](../../src/recon_lite_chess/autogrowth/native_intrinsic_curriculum.py)
  - `_native_v2_r0_admission_audit` implements the report and integrity audit;
  - `_native_v2_authority_ready_for_r1` makes the native-authority entry
    decision without reading coverage or outcome labels;
  - `_evaluate_r0` and `_evaluate_r1` use direct, fail-closed native authority
    in adaptive-local mode.
- [`src/recon_lite_chess/autogrowth/native_prospective_evidence_authority_v2.py`](../../src/recon_lite_chess/autogrowth/native_prospective_evidence_authority_v2.py)
  owns the immutable core, prospectively certified descendants, and atomic
  structural journal.

## Discovery is one event; certification is later experience

The adaptive authority does not receive a construction tape. Nomination closes
empty. During R1 interaction, each previously unseen successor opens one REAL
event. The frozen R0 emits an action, the environment executes it, and the
authority records the result.

If the result is a success outside current AVAILABLE jurisdiction, that one
receipt may trigger a bud. It is permanently discovery evidence for that bud
and cannot certify it. Only later distinct REAL receipts whose physical
interactions occurred after birth may add certification support or
contradiction. Promotion materializes an initially dormant authority child;
the child still needs post-birth evidence before it can answer AVAILABLE.

After each consumed REAL event, pending local growth/refinement requests are
committed at a content-blind quiescent safe point. The safe point decides when
mutation is atomic, never which chess content should grow. Exact receipt
identity, physical-interaction identity, compact interval commitments,
continuation digests, and dump/load replay guard discovery exclusion.
Validation, regression, and held-out answers never enter this evidence stream.

The legacy `build_same_run_v2_r0_authority` 32/32 tape remains available only
for historical reproduction. The adaptive runner is bound to
`build_empty_event_driven_v2_r0_authority` and rejects configurations that
attempt to restore the old path.

Main implementation:

- [`src/recon_lite_chess/autogrowth/native_intrinsic_v2_development.py`](../../src/recon_lite_chess/autogrowth/native_intrinsic_v2_development.py)
  - `build_empty_event_driven_v2_r0_authority` constructs and round-trips the
    evidence-empty shell;
- [`src/recon_lite_chess/autogrowth/native_intrinsic_curriculum.py`](../../src/recon_lite_chess/autogrowth/native_intrinsic_curriculum.py)
  - `_v2_r0_observe_training_successor` consumes REAL successor outcomes and
    connects them to the ecology and atomic safe point.

## All-reply adversarial value

For one emitted first move, every legal opponent reply gets an authority row:

- any `REFUTED` reply makes the move `REFUTED`;
- every reply must be grounded `AVAILABLE` for the move to be `AVAILABLE`;
- otherwise the move stays `UNKNOWN`;
- positive successor value is the minimum grounded reply value;
- the weakest reply becomes the next counterexample challenge.

Different certified cells may cover different reply contexts, so sibling
composition is allowed. The envelope asks whether their union handles all
replies; it does not require one global cell to memorize an entire position.
Only a grounded AVAILABLE envelope can hand positive successor value back to
the first move.

Training performs an exhaustive **VIRTUAL** query over every legal reply, then
executes one weakest/counterexample reply as the next REAL environmental event.
TD receives the minimum grounded envelope value when the envelope is complete;
it does not execute or credit every reply as a separate REAL transition. The
opponent challenge ranker is currently host substrate code and is intentionally
classified as the adversarial environment, not as a learned white-move policy.

Main implementation:

- [`src/recon_lite_chess/autogrowth/native_all_reply_envelope.py`](../../src/recon_lite_chess/autogrowth/native_all_reply_envelope.py)
  - `evaluate_all_reply_envelope` implements unanimity, veto, minimum value,
    and exact replay;
  - `rank_counterexample_challenges` chooses the weakest reply without a
    correct-action label.
- [`src/recon_lite_hector/learning/intrinsic_credit.py`](../../src/recon_lite_hector/learning/intrinsic_credit.py)
  - `IntrinsicCreditEngine` owns grounded successor credit, competence value,
    responsibility, and eligibility.

## Event-driven positive-shell ecology

The boundary ecology may read only:

- opaque graph-visible signal identities and their roles;
- unique REAL receipt/physical-interaction identity and ordinal;
- one grounded Boolean environmental outcome.

On each REAL observation it updates matching sketches. A family is born only
on **surprise success**: the observed outcome is positive while pre-outcome
authority was not already AVAILABLE. Up to one best conjunction at widths 1,
2, and 3 is proposed. A bounded evidence-ranked beam is mixed with a fixed
share of content-blind hash exploration so a temporarily weak feature is not
permanently excluded.

A matching positive receipt is support; a matching negative receipt is a
contradiction. Promotion eligibility currently requires at least four
supports, zero contradictions, and Wilson lower bound at least `0.55` with
`z=1.6448536269514722`. The Wilson score is a conservative competition/gating
quantity, not an IID confidence guarantee for chess positions.

A contradiction does not merely delete a coarse pattern. The parent enters
`REFINING` and abstains in the contradicted region. Residual children add local
contrast features absent from the parent. Refinement has finite event and child
budgets. Exhausted parents become dormant when a strict residual remains, or
dead otherwise. Redundancy and capacity pressure can also retire sketches.

Current active-work bounds are:

| Bound | Current value |
| --- | ---: |
| Active sketches | 32 |
| Conjunction width | 1–3 |
| Candidate beam | 16 |
| Candidate search budget per demand | 4096 |
| Local observation proposal window | 256 |
| Residual children per contradiction event | 3 |
| Refinement events per sketch | 4 |
| Live/dormant specialization children | 192 |

Lifetime exploration remains open because retired slots can be reused, while
the active ecology and live authority occupancy remain finite. Exact historical
receipts and unique tombstones preserve replay; lifetime artifact size is not
therefore claimed to be bounded.

Main implementation:

- [`src/recon_lite_chess/autogrowth/native_prospective_boundary_candidate_ecology.py`](../../src/recon_lite_chess/autogrowth/native_prospective_boundary_candidate_ecology.py)
  owns surprise-success birth, bounded candidate competition, refinement,
  dormancy, and retirement.
- [`src/recon_lite_chess/autogrowth/native_prospective_evidence_authority_v2.py`](../../src/recon_lite_chess/autogrowth/native_prospective_evidence_authority_v2.py)
  owns post-birth certification, recursive requests, atomic settlement, slot
  reuse, rollback, and tombstones.
- [`src/recon_lite_chess/autogrowth/native_intrinsic_curriculum.py`](../../src/recon_lite_chess/autogrowth/native_intrinsic_curriculum.py)
  connects outcome-grounded receipts to the ecology and safe-point promotion.

## Learner versus scientific harness

This boundary is the answer to the “plumbing versus ReCoN” concern.

| Inside the learning mechanism | Allowed harness responsibility |
| --- | --- |
| Local pattern identities and stored native values | Start episodes and enumerate legal environment actions/replies |
| Anonymous exactly-one emission | Enforce wall-time, memory, and active-resource ceilings |
| Outcome-grounded TD, eligibility, and exposure | Provide the outcome of the action actually taken |
| Surprise-success budding and local contrast | Invoke a content-blind quiescent transaction boundary |
| Prospective certification and recursive refinement | Snapshot, replay, and check invariants |
| Worst-reply minimum/veto and handoff | Select/execute one adversarial counterexample reply from the exhaustive virtual envelope |
| Retirement and slot reuse | Select deterministic development seeds, fixed budgets, and independent data partitions |

The harness must not choose the R1 move, override authority jurisdiction,
rescue an abstention through a fallback policy, or expose validation outcomes to
learning. The committed adaptive-local path satisfies those exclusions.

The harness is not globally gate-free. R0 and R1 now use the same native local
competition, and validation outcome mastery is report-only. After the fixed R0
budget, however, a **training-outcome policy probe** still controls the global
maturity/consolidation/freeze commit and entry into R1. An outcome-blind
authority-integrity audit may also veto unsafe entry. These are outer
curriculum/safety decisions, not runtime move pickers, but they do affect
learned lifecycle state and must not be called endogenous.

The complete R0→R1 curriculum is therefore not described as pure in-graph
ReCoN. Generic Python substrate still enumerates legal affordances, retrieves
local sources, computes bounded curiosity/alias rotation, packages formal
choice options, and ranks the opponent's counterexample reply. The precise
claim is: **native persistent evidence and local credit, formal ReCoN
exactly-one emission, event-driven local ecology, plus an explicit generic
curriculum/environment adapter**.

The `no_bootstrap` comparison arm is also named narrowly: it runs the same
authority and ecology but suppresses successor-value handoff. It isolates value
transfer; it is not a no-authority or no-growth organism.

## Defensible invariants after the adaptive-local change

The implementation and focused tests are intended to establish:

- adaptive R0 and R1 action choice cannot reach legacy schedules;
- adaptive profiles cannot enable memoized R0 replay as a hidden move provider;
- the adaptive authority starts with zero evidence, cells, candidates, states,
  promotions, pending requests, and scheduled frontiers;
- the environment never supplies FEN/epoch/stage/oracle data to local action
  competition;
- only the emitted exact branch is materialized;
- an outcome update credits exactly the emitted triplet and records one
  exposure;
- evaluation is read-only, exploration-free, and abstains without persistent
  confirmed support;
- adaptive evaluation cannot reach the prototype gate, host priority cascade,
  or plastic fallback;
- emitted-action trace evidence is invariant across aliases of one actuator,
  while option identity and activation/strength remain alias-local;
- R0 authority coverage/specificity is report-only, and after R0 mastery the
  native-authority entry check uses only outcome-blind runtime integrity;
- an `UNKNOWN` authority response abstains locally, cannot bootstrap successor
  value, and does not globally veto unrelated R1 experience;
- discovery evidence is excluded from later certification, and certification
  physical interactions are post-birth and distinct;
- VIRTUAL queries cannot certify or train;
- promoted children start with zero prospective authority;
- any refuted opponent reply vetoes a first move, and positive value is the
  worst grounded reply value;
- structural mutations are atomic and replay-exact or roll back;
- active candidate search, ecology population, and live authority occupancy
  have explicit finite caps;
- immutable core state and unique retirement tombstones survive snapshot and
  resume.

The design does **not** establish:

- convergence to mate-in-2 or to an optimal policy;
- that UCB-like exploration is the best local metabolism;
- that all abstract action aliases are strategically sound;
- IID evidence or calibrated statistical confidence;
- bounded lifetime receipt/tombstone storage;
- eventual discovery of every useful region;
- a completely in-graph arbitration circuit or endogenous curriculum stage
  transition;
- any chess-performance improvement before a fresh experiment measures it.

## Exact code lineage

| Commit | Role |
| --- | --- |
| `2f1b68c9` | Audited V2 intrinsic R0→R1 base and failed one-shot authority. |
| `55e940a9` | Implemented positive-shell event-driven ecology, refinement, retirement, and atomic integration. |
| `4cf1711b` | Corrected compact promotion commitment auditing. |
| `4a87eaa0` | Added bounded post-promotion follow-through profile. |
| `58fbd0d8` | Predeclared the V15 mechanism gate. |
| `ad3b0777` | Added follow-through tests and exact audit assertions. |
| `52f666d3` | Documented the architecture and V15 forensic evidence. |
| `444b927f` | Replaces adaptive R1 hash selection and prototype/fallback routing with local learned action emission and direct native authority; adds disjoint closure certification and stricter gates. |
| `67414302` | Makes authority coverage local/report-only and emitted-action traces alias-invariant. |
| `0373c0cc` | Preserves exact prospective history through boundary ecology. |
| `deedcb90` | Preserves exact/local action incumbents, localizes curiosity, and conserves TD responsibility across shared atoms. |
| `58abe72d` | Separates frozen R0 retention from V2 shell coverage and fixes fail-closed reporting. |
| `b1a8ed1f` | Makes both stages local, validation outcome mastery report-only, starts adaptive authority empty, and fails closed on retired controls. |

Use [`BRANCH_LOGBOOK.md`](../../BRANCH_LOGBOOK.md) for the experiment ledger.
The evidence motivating this repair is in
[`ADAPTIVE_BOUNDARY_V15_FORENSICS_20260901.md`](ADAPTIVE_BOUNDARY_V15_FORENSICS_20260901.md).

## Focused verification plan

Before any fresh chess claim, run the data-free focused suites:

- [`tests/autogrowth/test_native_single_graph_curriculum.py`](../../tests/autogrowth/test_native_single_graph_curriculum.py)
- [`tests/autogrowth/test_native_intrinsic_curriculum.py`](../../tests/autogrowth/test_native_intrinsic_curriculum.py)
- [`tests/autogrowth/test_native_intrinsic_v2_development.py`](../../tests/autogrowth/test_native_intrinsic_v2_development.py)
- [`tests/autogrowth/test_native_adaptive_boundary_development.py`](../../tests/autogrowth/test_native_adaptive_boundary_development.py)
- [`tests/autogrowth/test_native_prospective_boundary_candidate_ecology.py`](../../tests/autogrowth/test_native_prospective_boundary_candidate_ecology.py)
- [`tests/autogrowth/test_native_prospective_evidence_authority_v2.py`](../../tests/autogrowth/test_native_prospective_evidence_authority_v2.py)
- [`tests/autogrowth/test_native_intrinsic_all_reply_policy.py`](../../tests/autogrowth/test_native_intrinsic_all_reply_policy.py)

At `b1a8ed1f`, the six directly affected compatibility suites passed
`137/137`; targeted compilation and `git diff --check` were clean.

The highest-value tripwires are:

- native-local training raises if any scheduled/hash selector is reached;
- adaptive evaluation raises if prototype-gate or host-priority routing is
  reached;
- unsupported local evaluation abstains;
- authority abstention cannot fall through to another policy;
- alias-equivalent emitted actions receive the same formally captured trace
  evidence while retaining local option identity and activation/strength;
- R0 coverage/specificity failure is reported but does not block R1 when
  outcome-blind runtime integrity passes;
- choice and audit do not increment exposure, while exact observed TD does;
- fresh snapshot/resume reproduces action-event digest and authority history;
- contradiction-driven requests settle before the next REAL certification
  event;
- strict no-gate R1 snapshots fingerprint and resume exactly;
- the empty adaptive factory cannot read any pool field and seeds no evidence.

If these pass, run one tiny fresh development canary with numerical-library
threads fixed to one and an independent output directory. Stop rather than
extend if outcome-blind runtime integrity fails, the run does not enter R1 for
that integrity reason, legacy routing appears, emission/credit identity
diverges, certification leaks, replay differs, or an active cap is
uncontrolled. A native R0 coverage/specificity failure is recorded as a
report-only diagnostic and is not itself a stage-entry stop.

Only after that canary behaves mechanically should several short independent
seeds be considered. The predeclared mechanism gate requires, at minimum:

- R0 retention;
- a surviving positive promoted lineage with disjoint post-birth
  certification;
- a nonzero AVAILABLE all-reply envelope, handoff, and successor value;
- a revisited local pattern whose learned score or emitted action changes;
- at least one exhaustive mate-in-2 conversion;
- bounded ecology turnover and authority slot reuse;
- exact snapshot/resume and zero certification leakage.

One development run can pass its mechanism checks, but it cannot make the
scientific gate pass. A real curriculum run requires replicated independent
evidence and a separate explicit go decision.

## Remaining architectural questions

1. Does the current local abstraction distinguish strategically different move
   aliases, or must contradictions learn an action-relative residual split?
2. Does weakest-reply experience produce enough sibling coverage for a complete
   all-reply envelope without starving alternative boundary regions?
3. Does credited value measurably alter later local competition after the same
   pattern is revisited?
4. Can the host-controlled R0 maturity/freeze boundary become a local
   evidence-driven lifecycle decision without destabilizing the mate-in-1
   skeleton?
5. Which parts of the generic Python selection adapter are scientifically
   material enough to deserve later embodiment as persistent graph circuitry?

Those questions should be answered by the focused tests and bounded canary
before adding more candidate types, gates, routers, or monitoring machinery.
