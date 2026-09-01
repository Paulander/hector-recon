# Adaptive boundary ecology: architecture handoff

## Status and scope

This note describes the current working-tree design on branch
`codex/adaptive-boundary-ecology` in
[`Paulander/hector-recon`](https://github.com/Paulander/hector-recon).

- Prior architecture anchor: `52f666d3111e39c57fb6e16889678540c2fb6d62`.
- Current adaptive-local implementation: `444b927f07882ae1c197b6006fad1c0672ef2245`.
- Original audited base: `2f1b68c992eb6868b468148004d8e5a4746c88ab`.

The current implementation closes two concrete V15 control-loop defects: R1
experience is no longer chosen by the host's hash schedule, and adaptive
evaluation no longer routes through a learned prototype gate or a host-side
core/child/plastic fallback cascade. The previous modes remain only for exact
historical replay; the adaptive runner selects the new local mode explicitly.

This is still a development architecture, not evidence of mate-in-2 learning.
The focused 87-test suite passed at the implementation commit; a fresh bounded
canary is the next gate. No not-yet-run chess result is claimed in this note.

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
bounded native value + sqrt(2 log(1 + total exposures) / (1 + pattern exposures))
```

The second term is a generic, bounded optimism bonus. It uses graph-owned
exposure counts, not chess labels or position identities. Legal moves sharing
one abstract pattern form an alias group; exposure rotates its representative
deterministically, so the same alias is not chosen forever.

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

The candidate scan also has an explicit finite cap. Reports expose pair counts
before and after that cap, so a run cannot silently present a truncated action
competition as an unbounded one.

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
to the plastic graph. R0 retention evaluation likewise queries native V2
authority directly and fails closed on abstention.

This makes evaluation stricter and conceptually cleaner: a success must be
produced by the learned first-move policy and grounded successor authority, not
rescued by a host router.

## Frozen R0 authority and prospective closure

The adaptive path no longer uses `OutcomeCalibratedPrototypeGate` as a runtime
provider. The immutable learned R0 organism lives inside
`NativeProspectiveAuthorityV2`, alongside its prospectively certified boundary
descendants. A validation-only native admission audit asks whether that
authority itself has clean R0 jurisdiction:

- every R0 validation positive must receive an AVAILABLE legal response that
  actually mates in the copied environment;
- every validation decoy must receive no AVAILABLE response;
- all queries are VIRTUAL and both authority continuation and frozen-R0
  inference identity must remain unchanged.

This audit is a scientific stage gate: it may stop a bad run, but it neither
selects training actions nor provides runtime answers to the learner.

Main implementation:

- [`src/recon_lite_chess/autogrowth/native_intrinsic_curriculum.py`](../../src/recon_lite_chess/autogrowth/native_intrinsic_curriculum.py)
  - `_native_v2_r0_admission_audit` implements the read-only gate;
  - `_evaluate_r0` and `_evaluate_r1` use direct, fail-closed native authority
    in adaptive-local mode.
- [`src/recon_lite_chess/autogrowth/native_prospective_evidence_authority_v2.py`](../../src/recon_lite_chess/autogrowth/native_prospective_evidence_authority_v2.py)
  owns the immutable core, prospectively certified descendants, and atomic
  structural journal.

## Discovery and certification are an exact training-only partition

Construction of the same-run V2 authority uses a 64-row **training-only**
source. It is split by canonical-content digest into:

- 32 discovery rows; and
- a disjoint 32-row certification tape from the remaining source.

For a 64-row production source, the code requires that these two tapes form an
exact 32/32 partition. Selection does not inspect pool role, expected move, or
outcome. Nomination closes after discovery and before any certification row is
opened.

Each certification row is a new REAL interaction. The frozen R0 emits the
action, the environment supplies only whether its successor is checkmate, and
the authority consumes the receipt. In event-driven mode, after **each** REAL
consumption the runner invokes the existing content-blind quiescent safe point.
All currently pending bounded requests—including contradiction-driven recursive
refinement—settle atomically before the next REAL row is admitted.

The audit requires row, receipt, and physical-interaction disjointness;
post-birth certification ordinals; zero discovery/certification leakage; and
exact dump/load history. Validation, regression, and held-out answers never
enter discovery or certification.

Main implementation:

- [`src/recon_lite_chess/autogrowth/native_intrinsic_v2_development.py`](../../src/recon_lite_chess/autogrowth/native_intrinsic_v2_development.py)
  - `_neutral_discovery_tape` and `_neutral_certification_tape` construct the
    exact training-only partition;
  - `_certify_real_rows` consumes prospective REAL evidence and settles every
    post-consumption safe point.

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
| Worst-reply minimum/veto and handoff | Use validation only for stop/go and exhaustive evaluation only for reporting |
| Retirement and slot reuse | Select deterministic development seeds and training-only tape partitions |

The harness must not choose the R1 move, override authority jurisdiction,
rescue an abstention through a fallback policy, or expose validation outcomes to
learning. The committed adaptive-local path satisfies those exclusions.

One important limitation remains: **R0 pretraining still uses a content-blind
scheduled legal-action exploration policy.** It is not an oracle—it supplies no
correct moves or labels—but it is external experience selection. Consequently
the complete R0→R1 curriculum must not yet be described as fully pure-native.
The present change closes the learned R1 loop and removes runtime routing
handholding; replacing the R0 schedule is a later, separately testable purity
step, not a reason to expand this bounded implementation now.

## Defensible invariants after the adaptive-local change

The implementation and focused tests are intended to establish:

- adaptive R1 action choice cannot reach the legacy hash schedule;
- the environment never supplies FEN/epoch/stage/oracle data to local action
  competition;
- only the emitted exact branch is materialized;
- an outcome update credits exactly the emitted triplet and records one
  exposure;
- evaluation is read-only, exploration-free, and abstains without persistent
  confirmed support;
- adaptive evaluation cannot reach the prototype gate, host priority cascade,
  or plastic fallback;
- discovery and certification rows, receipts, and physical interactions are
  disjoint;
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
- whole-curriculum pure-native action selection while R0 remains scheduled;
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

The highest-value tripwires are:

- native-local training raises if any scheduled/hash selector is reached;
- adaptive evaluation raises if prototype-gate or host-priority routing is
  reached;
- unsupported local evaluation abstains;
- authority abstention cannot fall through to another policy;
- choice and audit do not increment exposure, while exact observed TD does;
- fresh snapshot/resume reproduces action-event digest and authority history;
- contradiction-driven requests settle before the next REAL certification
  event;
- the production training-only source is exactly partitioned 32/32.

If these pass, run one tiny fresh development canary with numerical-library
threads fixed to one and an independent output directory. Stop rather than
extend if native R0 admission fails, the run does not enter R1, legacy routing
appears, emission/credit identity diverges, certification leaks, replay differs,
or an active cap is uncontrolled.

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
4. Once R1 is mechanically sound, can R0's content-blind schedule be replaced
   by the same local curiosity/emission rule without losing its mate-in-1
   skeleton?
5. Which parts of the generic Python selection adapter are scientifically
   material enough to deserve later embodiment as persistent graph circuitry?

Those questions should be answered by the focused tests and bounded canary
before adding more candidate types, gates, routers, or monitoring machinery.
