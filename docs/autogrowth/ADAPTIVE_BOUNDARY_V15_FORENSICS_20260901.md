# Adaptive-boundary V15 lineage and policy forensics

## Conclusion first

V15 answered several mechanism questions, but it remains a **NO-GO** for a
longer mate-in-2 run.

What it established:

1. Local positive buds can be born, promoted, and prospectively certified from
   strictly post-birth REAL evidence. Seed `0104` certified three roots.
2. Certified roots can participate in per-reply authority, open an all-reply
   handoff, produce nonzero successor value, and generate a TD update.
3. The two TD updates measurably changed later graph rankings relative to the
   no-bootstrap control.
4. The all-reply composition operator is functioning. The learned structures
   simply did not cover every reply of any nontrivial multi-reply envelope.

What it did not establish:

- neither seed nor arm solved any of four exhaustive mate-in-2 positions;
- both positive handoffs occurred on first moves with only one legal opponent
  reply, so adversarial multi-reply competence was not demonstrated;
- no credited first-move decision was encountered again by the training
  schedule;
- the R0 “protected core” was configured but not operational in either seed,
  because both jurisdiction gates were `mature=false`;
- core retention/generalization was not reliable across both withheld splits.

The leading learning bottleneck is therefore not “TD failed to write.” It is a
disconnected experience-control loop: learned credit changes scores, but the
open-loop first-move schedule does not use those scores to choose future
experience. The resulting functional symptom is incomplete coverage across
opponent replies. Candidate recurrence and redundancy contribute, but the
evidence does not justify globally widening or deepening the candidate system
yet.

## Exact evidence boundary

- Branch: `codex/adaptive-boundary-ecology`
- Current audit/report commit:
  `ad3b0777ad22c26694e7496ef620eb7712ea05ad`
- V15 preregistered experiment source:
  `58fbd0d8`
- Adaptive implementation:
  `55e940a9`, with compact promotion audit repair `4cf1711b`
- Seeds: `2026090103` and `2026090104`
- Conditions: eight R1 epochs, random development-only `8/4/4` R1 pools, one
  process and one numerical thread per seed, independent full-intrinsic and
  no-bootstrap arms, exact snapshots after every epoch.
- Scientific label: `DEVELOPMENT_VIEWED_NOT_SCIENTIFIC`

Raw artifacts:

- [`reports/autogrowth/development/adaptive_followthrough_v15_seed_2026090103_58fbd0d8_epoch8`](../../reports/autogrowth/development/adaptive_followthrough_v15_seed_2026090103_58fbd0d8_epoch8)
- [`reports/autogrowth/development/adaptive_followthrough_v15_seed_2026090104_58fbd0d8_epoch8`](../../reports/autogrowth/development/adaptive_followthrough_v15_seed_2026090104_58fbd0d8_epoch8)

The lineage trace below is for each seed's `full_intrinsic` arm, because that is
the arm in which handoff and successor TD are enabled. The paired
`no_bootstrap` arm is included in aggregate and ranking comparisons. It can
still grow/certify structural candidates, but by intervention it cannot pass
successor value into the first move.

### Aggregate result

| Seed/arm | Promoted roots | Post-birth match incidences | Certified roots | Aggregate AVAILABLE envelopes | Handoffs | R0 validation retention | R0 regression retention | Mate-in-2 val. (reg.) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `0103` full | 8 | 5 | 0 | 0 | 0 | 15/16 | 16/16 | 0/4 (0/4) |
| `0103` control | 10 | 5 | 0 | 0 | 0 | 15/16 | 16/16 | 0/4 (0/4) |
| `0104` full | 15 | 41 | 3 | 2 | 2 | 16/16 | 12/16 | 0/4 (0/4) |
| `0104` control | 17 | 39 | 2 | 2 | 0 by intervention | 16/16 | 12/16 | 0/4 (0/4) |

“Post-birth match incidences” counts lineage-receipt matches, not independent
physical interactions. One REAL receipt can match several overlapping roots.
That distinction completely explains the superficially puzzling “five
receipts” in seed `0103`.

## Trace of every promoted full-intrinsic lineage

IDs are unambiguous eight-character prefixes within these snapshots. `b/p`
means ecology-sketch birth ordinal / authority-child birth frontier. `Opp` is
the number of later REAL ordinals available to match. `S/C` is post-birth
support/contradiction. Receipt ordinals in parentheses are the exact matching
post-birth receipts. `Ctx (multi)` counts individual reply contexts containing
the certified root, with the number belonging to multi-reply envelopes in
parentheses. It does **not** mean the aggregate envelope was available.

Pattern shorthand:

- `A:` / `B:` means after-successor / before-successor feature;
- `KSM2` is king-support Manhattan distance 2;
- `KSC2` is king-support Chebyshev distance 2;
- `N0`/`SE0` means that black-king neighboring direction is unavailable;
- `safe` means rook not attacked;
- `check-safe` is the action projection “gives check and rook safe after”;
- `Δcheck` means the action changes gives-check from 0 to 1.

### Seed `0103`

| Candidate → child | Local pattern | b/p | Opp | S/C (receipt ordinals) | LB / certified | Ctx (multi) | Handoffs |
| --- | --- | ---: | ---: | --- | --- | ---: | ---: |
| `0dc1edd4` → `662df53e` | A:axis-opposite=0 + A:N0 + A:KSM2 | 33/55 | 39 | 1/0 (`87`) | .270 / no | 0 | 0 |
| `4628f506` → `c65647d0` | A:N0 + B:KSM2 | 33/55 | 39 | 1/0 (`87`) | .270 / no | 0 | 0 |
| `a1d3a616` → `3a929175` | A:N0 + A:KSM2 | 33/55 | 39 | 1/0 (`87`) | .270 / no | 0 | 0 |
| `d03e3818` → `96cb3395` | Δ king-distance=0 + A:KSM2 | 33/55 | 39 | 1/0 (`87`) | .270 / no | 0 | 0 |
| `37bb8671` → `0937521a` | A:king-distance=2 + A:N0 + B:KSM2 | 33/62 | 32 | 1/0 (`87`) | .270 / no | 0 | 0 |
| `51fe179a` → `2f8b9d80` | A:KSM2 | 37/94 | 0 | 0/0 | 0 / no | 0 | 0 |
| `95fa1a5c` → `550d7b09` | B:KSC2 + A:KSM2 | 37/94 | 0 | 0/0 | 0 / no | 0 | 0 |
| `ade5b0c5` → `077a4885` | check-safe + A:N0 + A:KSM2 | 33/94 | 0 | 0/0 | 0 / no | 0 | 0 |

The first five roots all matched the **same one** REAL interaction at ordinal
`87`. That produced five lineage-receipt incidences, not five independent
post-birth receipts for one lineage. Each root needs four clean post-birth
supports, so none could certify. The first four had 39 opportunities and the
fifth had 32, giving only `2.56%` and `3.13%` match rates. The final three were
materialized at the terminal frontier `94` and had no follow-through window.

This is mixed evidence: five roots were genuinely low-recurrence; three were
judged at an experiment horizon that provided zero chance to certify.

### Seed `0104`

| Candidate → child | Local pattern | b/p | Opp | S/C (receipt ordinals) | LB / certified | Ctx (multi) | Handoffs |
| --- | --- | ---: | ---: | --- | --- | ---: | ---: |
| `0b12b1aa` → `c2073324` | B:safe + A:KSM2 | 35/47 | 47 | 6/0 (`50,52,54,56,71,89`) | .689 / **yes @56** | 23 (21) | 2 |
| `2b291776` → `20ea8a96` | check-safe + A:KSM2 | 35/47 | 47 | 6/0 (`50,52,54,56,71,89`) | .689 / **yes @56** | 16 (14) | 2 |
| `c7272604` → `917bcdff` | Δcheck + A:KSM2 | 35/47 | 47 | 6/0 (`50,52,54,56,71,89`) | .689 / **yes @56** | 16 (14) | 2 |
| `1b7091a5` → `bc2e3105` | Δ east-neighbor=0 + A:safe + A:KSM2 | 40/55 | 39 | 2/0 (`56,89`) | .425 / no | 0 | 0 |
| `2c97b28b` → `3e3f407c` | check-safe + B:KSM2 | 45/55 | 39 | 3/0 (`56,71,89`) | .526 / no | 0 | 0 |
| `8a9c89ae` → `1b417074` | B:KSM2 + A:safe | 40/55 | 39 | 3/0 (`56,71,89`) | .526 / no | 0 | 0 |
| `ccdafdd3` → `534aa963` | A:KSM2 | 40/55 | 39 | 3/0 (`56,71,89`) | .526 / no | 0 | 0 |
| `eb6df4dc` → `5530e8b6` | B:KSM2 | 44/55 | 39 | 3/0 (`56,71,89`) | .526 / no | 0 | 0 |
| `2c90c9c8` → `cfcbbe86` | A:white-king/rook-distance=2 + B:black-king-on-edge | 34/63 | 31 | 3/1 (`71,87,89`) | .254 / no | 0 | 0 |
| `5f4591ab` → `620ad6b7` | Δcheck + B:KSM2 | 50/63 | 31 | 2/0 (`71,89`) | .425 / no | 0 | 0 |
| `b6427890` → `e66d9ef9` | A:black-king-on-edge + rook-not-attacked-after + A:KSM2 | 45/63 | 31 | 2/0 (`71,89`) | .425 / no | 0 | 0 |
| `d57a4a6f` → `e536243c` | Δcheck + decreasing rook/edge-line distance + B:KSM2 | 50/63 | 31 | 1/0 (`89`) | .270 / no | 0 | 0 |
| `447f8b51` → `827d9be9` | check-safe + A:SE0 + A:KSM2 | 52/71 | 23 | 1/0 (`89`) | .270 / no | 0 | 0 |
| `8a0e9017` → `53ffc698` | B:safe + B:KSM2 | 54/94 | 0 | 0/0 | 0 / no | 0 | 0 |
| `fee844d6` → `8aa5d17e` | A:black-king-on-edge + B:safe + A:KSM2 | 54/94 | 0 | 0/0 | 0 / no | 0 | 0 |

The first three roots were born from the same surprise-success family,
promoted at frontier `47`, and matched the same six later receipts. They
crossed the four-support certification threshold together at ordinal `56`.
Their post-birth match rate was `6/47 = 12.77%`, about five times the early
`0103` rate. Four more roots ended one support short at `3/4`; one root had
three successes plus a contradiction and correctly remained uncertified.

The three certified roots are strongly correlated siblings, not three
independent demonstrations: they share `A:KSM2`, the same six support receipts,
the same certification transition, and both handoffs. This is evidence that
the lifecycle works, but weaker evidence of representational diversity than
“three roots” suggests.

## Certification, reply coverage, and handoff trace

After certification, root `c2073324` appeared as an AVAILABLE provider in 23
individual reply contexts belonging to 23 envelopes; 21 of those envelopes
had multiple legal replies. The two sibling roots appeared in 16 contexts each,
14 in multi-reply envelopes.

For envelopes containing each root:

| Root | Aggregate AVAILABLE | Aggregate UNKNOWN | Aggregate REFUTED | Multi-reply aggregate AVAILABLE |
| --- | ---: | ---: | ---: | ---: |
| `c2073324` | 2 | 7 | 14 | 0 |
| `20ea8a96` | 2 | 4 | 10 | 0 |
| `917bcdff` | 2 | 4 | 10 | 0 |

Thus the roots often recognized **one** reply of a multi-reply candidate, but
another reply remained unknown or refuted. The all-reply envelope correctly
refused to pass value. No evidence shows a case where different certified
siblings collectively covered all replies but the composition code failed.

The only two aggregate AVAILABLE/handoff envelopes were singleton-reply cases:

1. Event `88`, epoch 5: predecessor
   `R7/8/8/8/8/K7/8/1k6 w - - 0 1700135`, first move `a8c8`, sole reply
   `b1a1`, successor value `0.5965213748`.
2. Event `107`, epoch 8: predecessor
   `8/5R2/k7/2K5/8/8/8/8 w - - 0 1700130`, first move `f7g7`, sole reply
   `a6a5`, successor value `0.6488834992`.

All three certified roots participated in both handoffs. This proves plumbing
through certification → reply authority → envelope → handoff. It does not yet
prove the intended adversarial composition across several opponent replies.

## Did the two TD events change later first-move ranking?

Yes, locally and measurably. No, not enough to change held-out chess behavior.

### Event 88: `a8c8`

- Decision/triplet: `tg26o_triplet_7b7daff8798bac2b`
- Predicted value: `-0.093400`
- Successor value: `0.596521`
- TD error: `0.662026`
- Updated triplet value: `0.039722`
- Exact scheduled decision was never encountered again in later training.

Offline reconstruction from exact epoch snapshots:

| Epoch | Full credited-move score/rank | Control score/rank | Full selected move | Control selected move |
| ---: | --- | --- | --- | --- |
| 4, before credit | absent | absent | `a8b8` | `a8b8` |
| 5 | `.5151`, rank 3 | `-.0167`, outside top 16 | `a8b8` | `a8b8` |
| 6 | `.5126`, rank 3 | `-.0192`, outside top 16 | `a8b8` | `a8b8` |
| 7 | `.5099`, rank 2 | `-.0218`, outside top 16 | `a8b8` | `a3b3` |
| 8 | `.5050`, rank 2 | `-.0265`, rank 13 | `a8b8` | `a3b3` |

At epochs 7–8 the full arm's selected **triplet** is the credited triplet, but
the selected move is `a8b8`, not credited move `a8c8`. Several moves instantiate
the same abstract local triplet. This is genuine micropattern generalization,
but it also means the evidence cannot claim that credit distinguished the exact
successful move from its abstract aliases.

### Event 107: `f7g7`

- Decision/triplet: `tg26o_triplet_bb3d3e51c9e1f65f`
- Predicted value: `-0.006075`
- Successor value: `0.648883`
- TD error: `0.625492`
- Updated triplet value: `0.037530`
- The event occurred in the final epoch, so it had no later consolidation or
  training-revisit window.

At the epoch-8 snapshot, the exact move scored `.5550` and ranked 8 in the full
arm, versus `-.0096` and outside the top 16 in control. Both arms still selected
`f7f6` at score `1.0659`.

### Causal interpretation

The full and control arms made identical final first-move choices on all four
validation positions and all four regression positions, and both scored `0/4`.
Therefore:

- the handoff/TD path **does influence graph competition**;
- it did not overcome pre-existing higher scores;
- abstraction aliases can redirect the benefit to a different move;
- neither credited decision was replayed by training;
- the second credit arrived too late for any follow-through;
- no performance improvement is supported.

The exact source-level reason is
`_scheduled_confirmed_action` in
[`native_intrinsic_curriculum.py`](../../src/recon_lite_chess/autogrowth/native_intrinsic_curriculum.py):
it takes an epoch/position index into a stable-hash legal-action permutation,
then confirms that predetermined action. It does not ask the learned graph to
choose the R1 training action. Evaluation uses graph rankings, but training
experience remains open-loop.

## Exact diagnosis of seed `0103` R0 retention failure

There are three R0-related metrics that must not be conflated:

- the unmutated post-R0 report scored `16/16` on seed `0103` validation and
  `16/16` regression;
- after entering R1, validation retention was `15/16` from epoch 1 through
  epoch 8 in both full and control arms;
- after entering R1, regression retention remained `16/16`.

The sole missed validation position was:

```text
8/4R3/8/8/8/8/2K5/k7 w - - 0 1700057
```

Exact route reconstruction:

| Component | Selected move | Immediate mate | Selected triplet/score |
| --- | --- | --- | --- |
| Frozen R0 core snapshot | `e7a7` | yes | `tg26o_triplet_d5f8fc6d600738d9`, score `.534668` |
| V2 descendant authority | no grounded response | — | `UNKNOWN` |
| Grown/plastic graph fallback | `e7e1` | no | same abstract triplet ID, score `1.260845` |
| Reported policy | `e7e1` | no | incorrect |

The frozen core was not mutated and still solved the position. The failure was
already present at epoch 1, before certification or handoff, and was identical
in the no-bootstrap arm. It therefore did not come from TD credit, promoted
children, or destructive mutation of core topology.

The jurisdiction gate was globally `mature=false`. Its held-out gate metrics
were 16 true positives, 0 false negatives, but 7 false positives
(`precision=.696`, `recall=1.0`); the maturity contract requires a clean gate.
`_protected_core_r0_available` correctly refuses to call such a gate grounded.
Nevertheless, top-level `availability_ready` treats the presence of a V2 child
authority as sufficient to enter R1 without also requiring this gate to be
mature. Routing then tries V2 and ultimately returns `graph.choose(board)` from
the plastic graph. That fallback reused the same coarse triplet identity but
its changed shared weights favored the nonmating alias `e7e1`.

There is also a sequencing defect to repair: `_fit_r0_gate` currently runs
before `graph.mature_existing_graph()`, while routing later uses the matured and
frozen graph. It did not cause this exact failure—the gate was already globally
immature—but a future gate that passes on the pre-maturation feature
distribution could still be stale at runtime.

Adjudication:

- **Primary cause: routing/admission semantics.** R1 was allowed to proceed and
  reporting said core routing was “enabled” although the gate made it
  operationally unavailable everywhere.
- **Proximate mechanism: shared abstract topology/action aliasing in the
  plastic fallback.** It selected a different move under the same triplet ID.
- **Not the cause: mutation of the frozen core.** The isolated core remained
  correct.
- **Evaluation context:** the evaluation did not fabricate the loss; it exposed
  the actual configured routing chain. The ambiguity is in calling that chain
  “protected” when its gate is globally immature.

Seed `0104` is a different issue. Its validation retention was `16/16`, while
its regression retention was `12/16` in both arms. Replaying those four misses
through the frozen core produced the same four nonmates. They are failures of
the original R0 core's withheld generalization, not R1 forgetting. This is why
the two splits and two seeds must remain explicit.

## Which hypothesized bottleneck is supported?

### 1. Overly specific micropatterns: contributing, not established as primary

Evidence for specificity/low recurrence:

- the first five `0103` roots matched only once in 32–39 later opportunities;
- several `0104` roots reached only one to three matches;
- three `0103` and two `0104` roots were promoted too late to receive any
  post-birth evidence.

Evidence against a simple “make patterns shallower” conclusion:

- width-1 patterns existed and did not automatically solve coverage;
- three width-2 `0104` roots recurred and certified;
- most roots shared the broad `KSM2` atom, and multiple siblings matched the
  same receipts, indicating redundancy/correlation as much as over-specificity;
- aggressively broad patterns would increase contradictions and false
  authority.

Conclusion: improve follow-through horizon and family diversity diagnostics
before changing width or atom vocabulary. Do not globally loosen candidate
specificity yet.

### 2. Insufficient sibling composition across replies: coverage failure, not operator failure

The envelope already composes arbitrary grounded providers per reply. Certified
roots appeared in 21 multi-reply envelopes, proving they reached the
composition input. Every such envelope failed because some *other* reply was
unknown/refuted. No aggregator failure was found.

Conclusion: the functional bottleneck is insufficient learned **reply
coverage**. Adding another global sibling-composition layer would be redundant
scaffolding. The existing counterexample reply should drive local experience
and budding at uncovered boundaries.

### 3. Failure of credit to influence competition: false in the narrow sense, true at policy level

TD changed exact/local scores by roughly `+.53` to `+.56` relative to control
and moved credited actions into ranks 2, 3, and 8. The write and ranking paths
work.

But the training policy ignores ranking, exact decisions were never revisited,
and shared triplets can alias several moves. Credit therefore failed to control
future experience or improve held-out choices.

Conclusion: the primary control defect is **credit-to-action disconnection**,
not credit arithmetic.

### Ranked diagnosis

1. **Correctness prerequisite:** nonoperational core jurisdiction was allowed
   into R1; retention claims are therefore unsafe.
2. **Main learning-control bottleneck:** open-loop scheduled first moves do not
   exploit learned value or deliberately revisit credited local patterns.
3. **Main adversarial symptom:** no learned all-reply coverage beyond singleton
   replies.
4. **Secondary representation issue:** low recurrence, highly correlated
   sibling roots, and abstract action aliases.
5. **Not supported as primary:** broken TD update or missing all-reply
   composition code.

## Adversarial expert review

No external human reviewers were consulted. This section is an internal
red-team pass that adopts the strongest objections those disciplines should
raise, then narrows the conclusions accordingly.

| Lens | Strongest valid pushback | Resulting correction |
| --- | --- | --- |
| Statistical ML | Two seeds, four held-out positions, and six correlated certification receipts cannot support efficacy or convergence. Wilson bounds assume more independence than these receipts provide. | Claim only mechanism reachability. Treat Wilson as a deterministic conservative score, not calibrated confidence. Require replication and context-diverse support before stronger claims. |
| Mathematical/formal methods | Finite active caps and atomic replay do not imply convergence; lifetime ledgers/tombstones can grow. A fail-closed envelope proves safety only relative to current grounded providers. | State bounded *active computation/occupancy*, not bounded lifetime storage or eventual competence. Make no convergence claim. |
| Adversarial game learning | Singleton-reply handoffs evade the central minimax difficulty. Average success and one recognized reply are irrelevant if another legal reply escapes. | A non-singleton AVAILABLE envelope becomes a mandatory next mechanism gate. Worst-reply minimum/veto remains unchanged. |
| Reinforcement learning | An off-policy value write cannot improve behavior if behavior never consults it; pure greedy closure would then collapse exploration around noisy values. | Close the action loop with local incumbent/challenger competition, retaining deterministic novelty exploration and exact replay. Do not switch to pure greedy. |
| Evolutionary algorithms | Three “independent” roots share the same six receipts and core atom; the ecology lacks strong niching/subsumption pressure and can waste slots on correlated variants. | Count families and novel reply coverage, not raw root count. Add only bounded exact-support/subsumption retirement if capacity or repeated redundancy is observed; do not build a broad speciation framework now. |
| ReCoN-purist / cognitive architecture | A global epoch schedule choosing experience or structural frontiers is outside planning, not self-organization. A host-side safe point is acceptable only if content-blind. | Keep growth causes local/event-driven. Let safe points commit atomically but never choose content. Replace the action schedule with a local graph-visible competition rule; retain hash only as a content-blind novelty/tie source. |
| Representation learning | The same triplet represented credited `a8c8` and selected `a8b8`; “credit reached the move” overstates action resolution. | Say credit reached an abstract action pattern. Add an alias-separation canary before inventing absolute move features; split only through local action-relative residual atoms if required. |
| Systems/reproducibility | More dashboards or broad instrumentation could obscure the scientific defect. | Reuse existing snapshot/history/reply/credit artifacts. Add only gate fields needed to distinguish configured vs operational routing and selected-vs-scheduled actions. |

After these corrections, the conclusions are defensible: V15 proves several
individual transitions, exposes a routing correctness defect and a closed-loop
control defect, and does not support a learning-performance claim.

## Minimal recommended next design

The next patch should be deliberately smaller than another ecology redesign.

### A. Fail closed before R1 when the core is not operational

1. Mature and freeze the R0 graph first; then fit or revalidate the local
   jurisdiction gate against that exact final response distribution. Require
   the gate to be genuinely `mature` and its frozen-core route to pass the
   predeclared R0 validation-retention contract.
2. If not, stop before R1 and report `core_routing_configured=true` but
   `core_routing_operational=false`. Never call that run a protected-core R1
   experiment.
3. Preserve withheld regression for final reporting; do not select/tune on it.
4. Add the exact `0103` position as a data-free routing regression: immature
   core gate must not silently produce a protected-retention claim, and the
   frozen core source must remain unchanged.
5. Do not force the core using an R0/R1 stage label. Jurisdiction must remain a
   learned local property.

This fixes experimental validity and the concrete `0103` failure. It does not
pretend to solve seed `0104`'s original R0 regression-generalization gap.

### B. Close the first-move loop with bounded local incumbent/challenger competition

Replace “hash schedule chooses the move” with this minimal semantic contract:

1. The graph supplies a current locally ranked **incumbent**.
2. The existing stable-hash stream supplies one replay-exact, content-blind
   **novelty challenger**, preferring an underexposed local action pattern.
3. A never-opened local pattern receives a bounded exploration opportunity;
   otherwise incumbent and challenger compete by current native value, with
   stable hash only breaking exact ties.
4. Exposure is keyed to local abstract action-pattern identity, not FEN or UCI
   position identity.
5. Grounded TD therefore affects later matching competitions, while the
   challenger stream keeps lifetime exploration open.
6. The opponent-reply selector remains worst-reply/counterexample-first.

This is deterministic and exactly replayable, contains no correct-move label,
and avoids both pure random scheduling and pure greedy collapse. Its one open
design detail is the smallest existing graph-visible exposure statistic that
can implement “underexposed” without a new subsystem. Resolve that in code
inspection before adding state.

### C. Keep the present reply envelope; gate on learned non-singleton coverage

Do not add another sibling-composition layer. Instead:

1. continue presenting the envelope's worst unknown/refuted reply as the REAL
   challenge;
2. allow surprise success there to bud from the locally active signals exactly
   as now;
3. judge a promoted root only after a fixed number of post-birth REAL
   opportunities, not merely a global epoch endpoint;
4. require at least one envelope with two or more legal replies to become
   grounded AVAILABLE before a longer run;
5. report lineage families with identical support sets as correlated evidence.

Only if closed-loop experience repeatedly reaches successful replies but the
existing candidate beam still cannot produce recurrent coverage should the
next branch add bounded subsumption/diversity retirement or action-relative
residual atoms.

## Exact files for the next implementation

First patch:

- [`src/recon_lite_chess/autogrowth/native_intrinsic_curriculum.py`](../../src/recon_lite_chess/autogrowth/native_intrinsic_curriculum.py)
  - fail-closed R1 core admission;
  - distinguish configured/operational routing;
  - replace `_scheduled_confirmed_action` as the sole chooser with the local
    incumbent/challenger selector;
  - record whether the executed action came from novelty or learned ranking.
- [`src/recon_lite_chess/autogrowth/native_adaptive_boundary_development.py`](../../src/recon_lite_chess/autogrowth/native_adaptive_boundary_development.py)
  - stop before R1 on nonoperational core;
  - make non-singleton handoff and later credit-influenced action selection
    explicit mechanism gates.
- [`tests/autogrowth/test_native_intrinsic_curriculum.py`](../../tests/autogrowth/test_native_intrinsic_curriculum.py)
  - immature-gate admission stop;
  - exact `0103` routing regression;
  - learned credit changes a later executed action while novelty remains live;
  - direct/snapshot/resume parity for selector state.
- [`tests/autogrowth/test_native_intrinsic_all_reply_policy.py`](../../tests/autogrowth/test_native_intrinsic_all_reply_policy.py)
  - retain fail-closed multi-reply minimum/veto and core precedence tests.

Do **not** initially change:

- `native_all_reply_envelope.py`: composition worked;
- `intrinsic_credit.py` or `apply_intrinsic_td`: the write path worked;
- candidate width/thresholds or authority depth: V15 does not isolate them as
  the leading defect;
- monitoring infrastructure.

Potential second patch, only if the first gate supplies evidence:

- [`native_prospective_boundary_candidate_ecology.py`](../../src/recon_lite_chess/autogrowth/native_prospective_boundary_candidate_ecology.py)
  - bounded support-set/subsumption retirement for redundant sibling families;
  - action-relative residual splitting only after an exact alias canary.

## Focused tests and bounded experiment gate

### Data-free and synthetic tests

1. Core configured but `mature=false` cannot enter R1.
2. Frozen core remains byte/semantic exact across routing and R1 attempts.
3. A positive TD event changes a later *executed* local competition relative
   to no-bootstrap, not merely an offline score.
4. The novelty challenger continues to receive bounded opportunities after a
   positive incumbent exists.
5. Two moves sharing a triplet are either behaviorally exchangeable in the
   canary or expose the need for a local residual split; no absolute move atom
   is introduced.
6. Multi-reply envelope remains UNKNOWN with one uncovered reply, REFUTED with
   one veto, and AVAILABLE only with all replies grounded.
7. Snapshot/resume and uninterrupted action sequences are exact.

### Tiny development canary

- one viewed seed and tiny pool;
- stop immediately if core routing is nonoperational;
- otherwise run until either one credited local pattern participates in a
  later executed first-move competition or the bounded opportunity ceiling is
  reached;
- require exact replay and no discovery/certification overlap.

### 1–2 hour mechanism gate

Use several independent seeds/processes with one numerical thread each. Give
each its own output directory. Do not select on final held-out answers.

Advance only if at least two usable seeds show:

- operational core routing and initial/final R0 validation retention `16/16`;
- at least one positive bud certified from strictly later REAL receipts;
- at least one certified provider on multiple reply contexts;
- at least one **non-singleton** all-reply AVAILABLE envelope and handoff;
- nonzero successor value and TD;
- a later executed first-move competition measurably influenced by that credit;
- active ecology/authority bounds respected;
- exact snapshot/resume parity and zero certification leakage.

Evaluate actual exhaustive mate-in-2 only at the preregistered report boundary.
One real conversion is encouraging but not a convergence claim. If the
mechanism criteria fail, preserve artifacts and stop; do not compensate by
blindly extending epochs.

## Is the next work clear?

The first implementation step is clear: make protected-core admission honest
and connect learned graph value to future R1 actions while preserving local
novelty exploration and exact replay. That can be implemented and tested
without more broad architecture work.

One bounded design choice remains appropriate for the separate conceptual
discussion: whether the incumbent/challenger selector can reuse an existing
local exposure statistic or needs one minimal per-pattern counter. It should
not become a new planning or monitoring framework. Candidate-width tuning,
global frontier scheduling, and a new sibling-composition layer should remain
out of scope unless the closed-loop canary supplies new evidence.
