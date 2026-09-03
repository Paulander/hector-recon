# V27: local exploration, task-optimal opposition, and attempted competence

Investigation base: `17e5cad6f7c5ea3d6dbb4ee3471e76079f727d29`; learner source
unchanged since V26's `48dd21a68f283a9c5da87c99f8a9b943af1aa2aa`.
Implementation branch: `codex/v27-local-interaction`.

## Adjudication

The user's goal is outcome-driven network learning, not a host-selected chess
solution. A strong opponent belongs to the environment and may use exact chess
knowledge if it exposes only its played move/board. It must not supply White
with first-move labels, features derived from solution scores, shaped rewards,
or hypothetical successful continuations as training observations.

Three bounded changes are justified independently of a larger growth redesign:

1. Remove mandatory first-contact precedence in the new R1 mode. An experienced
   useful branch can compete with untried branches immediately.
2. Select Black's actual reply independently of the learner's confidence. For
   the current KRK mate-in-two horizon an exact rules-only opponent is small;
   no Stockfish process, downloaded tablebase, or global reply database is needed.
3. Separate permission to attempt a legal finishing action from permission to
   emit trusted bootstrap value. Evaluation should observe the learned action,
   not manufacture a failure merely because the action lacks certification.

These changes do NOT make the whole architecture endogenous. The old candidate
ecology, exact action-value storage, protected source policy, and explicit
episode credit adapter remain. The code already reports that it does not claim
pure in-graph arbitration or a wholly endogenous curriculum.

## What already exists, and what does not

| Mechanism | Present implementation | Important boundary |
| --- | --- | --- |
| Board terminals | `native_single_graph_curriculum.py`: shared before/action/after feature terminals, actuator affordances, learned node and edge weights | The adapter enumerates legal actions and assembles local activation scores; the network is not learning the chess rules or feature extractor. |
| Delta signals | `_triplet_keys` includes bucketed changes in permitted before/after features | A simulated one-move delta is not persistent memory across real opponent turns. |
| Lag primitives | `LagMetaTerminal` in `src/recon_lite_hector/nodes/stem_cell.py` has previous/current values, increase/decrease tests and recursive lag support | Not integrated into this native curriculum. The old `lag_terminals.py` experiment is a different runner, not something to switch on blindly. |
| Internal terminals | Anonymous choice measurements, provider responses and all-reply conjunctions are represented as internal graph terminals/circuits | Their inputs and lifecycle are partly assembled by Python adapters. Local software rules are still designed rules, not automatically self-learned rules. |
| POR/RET | `ensure_triplet` creates before → action → after POR pairs with RET counterparts | There is no learned cross-episode POR chain from the first-move branch to the downstream finisher. |
| Fast plasticity | `apply_intrinsic_td` updates actuator-specific graph Q and mutable nodes/edges | The exact Q key includes a concrete actuator; relational transfer depends on separate shared-feature priors. |
| Credit traces | `IntrinsicCreditEngine` supports decayed responsibility | The current runner collapses a two-White-move episode into one first-decision update and explicitly supplies that triplet and a stage parent. It is not discovering an arbitrary temporal responsibility chain. |
| Growth | Surprise observed finishing success births small conjunctions; failures refine them; later evidence certifies them | Cheap sketches live in a learning-owned Python ecology before graph materialization. This is not yet direct competition among newly grown temporal graph branches. |
| Slow knowledge | 48 nonzero R0 slow values in the V26 checkpoints; independently certified boundary cells | Zero legacy graph M4 events is not zero consolidation. The audit in `V25_GENERALIZATION_CONSOLIDATION_AUDIT_20260903.md` also shows why blindly consolidating the separate fast-credit accumulator is numerically wrong. |

The V26 matched snapshot had 126 first-contact choices and only two revisits
out of 128. This describes a compulsory exploration policy, not evidence that
weights never affected choices. R0 received 96 attempts per training position;
this matched R1 frontier received only 16.

## One actual interaction, in plain language

1. Board features activate relational terminals. Candidate action effects also
   activate before/after and delta terminals. These are observations and legal
   affordances, not lists of good moves.
2. Active branches contribute learned values and local uncertainty. The
   anonymous choice circuit emits one legal actuator. Python still assembles
   its measurement inputs; this is not yet a wholly self-contained persistent
   graph choosing from raw sensory input.
3. White executes that move. Black independently chooses its task-optimal
   defence. The learner receives the played move/board, not Black's search data.
4. The learned mate-in-one policy emits a finishing move. The environment
   reports checkmate, loss, or failure to finish within the episode horizon.
   Virtual all-reply competence queries cannot mint observed-success evidence.
5. Outcome versus prediction produces a TD error. It changes the chosen
   first-move branch's graph value and associated mutable weights/edges.
   Currently the episode adapter names this responsibility; a learned temporal
   trace does not yet discover all responsible upstream paths.
6. An unexpected observed finish may grow a tentative local-pattern hypothesis.
   Subsequent real outcomes support, refine, or retire it. The present ecology
   stores cheap sketches outside the graph before materializing them. That
   limitation is real, not merely an unfortunate choice of wording.
7. Repeat. In this version the R0 finishing policy itself remains protected;
   learning a new boundary around it is not the same as improving the finisher.

## New exploration rule

For each currently relevant legal option, let `n` be its actual recorded REAL
exposures and `N` the sum for this local population. The new generic internal
uncertainty signal is:

`bonus = sqrt(2 * log(1 + N) / (1 + n))`

The deployed activation is `min(1, learned_value + bonus)`: imagined upside
cannot exceed the same return ceiling as the learned value. Internal terminals
also measure the value without its exploration bonus and the REAL exposure
count. On equal optimistic activations, the formal graph compares value first,
then exposure. Familiarity therefore cannot conceal a lower value caused by
negative feedback. Neither tie measurement overrides a strictly higher primary
activation. TD continues to read only the learned value. Neither the
denominator regularizer nor the evidence terminal adds an observation, reward,
or certification receipt. There is no separate first-contact tier, host epoch
counter, correct-move detector, or forced chess-specific successful-move repeat.
Read-only policy evaluation uses neither exploration nor this tie preference.

The initial finite, uncapped prototype is retained as `finite_local_ucb_v1`
for reproducing its canary. A counterexample rejects it as the final rule:
with one local observation, a maximal experienced value1 receives activation
1.833, but an untried prior0.95 receives2.127. The bounded rule instead ties
them at1 and preserves the experienced option's higher learned value. Synthetic
negative outcomes show that
the incumbent can subsequently lose attention; it is not permanently locked.

This is a bounded optimistic-attention heuristic, not a statistically calibrated
confidence bound for a changing graph. A maximal incumbent can intentionally
suppress further exploration. We therefore claim neither compulsory eventual
coverage nor convergence. Lucky outcomes, aliased contexts, overconfident values
and insufficient recurrence can still produce self-confirming fixation. One
ordinary win need not immediately make the learned value maximal.

## Exact opponent contract

`mate_horizon_opponent.choose_mate_horizon_reply(board)` accepts only the board
after White has already committed its first move. It returns one `chess.Move`.
It has no network, value, evidence, curriculum label, or seed argument.

For every considered Black reply it privately asks whether White has an
immediate mating move. It chooses a reply without one whenever such a defence
exists; otherwise all Black replies permit mate next and a fixed UCI tie break
selects one. Therefore a White mate against this defender cannot be caused by
Black overlooking a defence against mate within the task horizon.

This is perfect for denying mate on White's next move, NOT perfect full-game
WDL/DTM play among continuations outside that horizon. It rejects non-KRK,
nonstandard/invalid, terminal and draw-claim positions rather than silently
overclaiming its scope. It runs bounded shallow exhaustive search inside the
OPPONENT, not the learner. No full table is built or persisted.

The existing read-only all-reply probe is retained for conservative successor
bootstrap values. It cannot override the environment's actual reply. Audit
records distinguish its diagnostic counterexample from the actually played
reply. This change does not yet remove the cost of those virtual learner probes.

A fixed optimal opponent can still choose only one of several equally optimal
replies. The learner may fail on another, even though perfect White could win
there. Actual all-reply network evaluation therefore remains essential. Winning
against this opponent is not reported as all-reply learned competence.

## Actuation and evidence

In V27 evaluation, an emitted legal finisher move is attempted even when its
competence classification is UNKNOWN or REFUTED. Actual environmental checkmate
determines success. Reports separately count uncertified attempts and mates.
This matches the existing training behavior; no new action chooser is inserted.

This does not grant a certificate, create a REAL receipt from evaluation, or
unlock successor value. All-reply bootstrap still requires the existing
pre-outcome grounded providers, actual selected finishing success, and identity
parity. Discovery exclusion, negative constraints and post-credit structural
settlement remain unchanged. Old checkpoints/results are not reinterpreted.

## Usage and scope

The historical development mode remains the default. The new contract is opted
into with `--local-interaction` on `native_adaptive_boundary_development`.
This sets only these R1 fields:

- `r1_local_exploration_mode = bounded_local_optimism_v1`;
- `r1_black_policy = exact_mate_horizon_v1`;
- `r1_require_certified_finisher_for_action = false`.

Use `--continuous-hypothesis-evidence` separately for the V26 evidence repair.
All three fields enter snapshot behavior identity. R0 training, numerical
learning rates, core freeze, candidate limits and reward magnitudes are unchanged.
This bundle is not a one-factor performance experiment. No long run is authorized
or launched by this document. A pretrained-R0 canary must disclose reuse rather
than describe itself as same-run empty-start pretraining.

## Focused verification

- A useful incumbent can recur before complete contact. A maximal experienced
  return beats untried optimistic ties, independently of option ordering;
  negative updates are not hidden by familiarity when activations saturate,
  and negative outcomes can release that incumbent again. The retained finite
  prototype has a separate synthetic renewable-exploration test.
- Choice/read-only queries create no REAL contacts and exploration is excluded
  from TD; graph values and decisions survive exact pickle round trips.
- For every legal first move in four already-viewed development positions,
  the defender allows an immediate mating finish iff no reply can avoid one.
- An environment-supplied reply wins over a different learner challenge without
  changing the all-reply envelope or minting evidence during the probe.
- An uncertified emitted finisher can succeed in an all-reply evaluation without
  gaining authority or leaking evaluation outcomes into learning.
- The complete new interaction path has exact interrupted/uninterrupted resume
  parity for graph, credit, authority, choices and reply records.
- Re-run the established graph, credit, authority, curriculum and runner tests.

## Next native-mechanism work (not implemented by V27)

1. Persist the actual participating nodes/action bindings across REAL turns;
   lag state must advance on environment steps, not on virtual engine ticks.
2. Let a successful downstream competence reinforce a tentative upstream POR
   connection through that trace. Context-sensitive sibling finishers belong
   under alternative downstream paths; POR supplies temporal order, not the
   universal quantifier over opponents.
3. Give newly born temporal branches local TRIAL nodes and bounded attention,
   rather than merely renaming the current off-graph sketch pool. Use local
   residual usefulness and resource competition for survival/refinement.
4. Use one numerically consistent value/eligibility update. Do not consolidate
   the current correction accumulator as if it were an expected return.
5. Permit finisher adaptation only with source-versioned/local evidence
   invalidation. Mutating a policy while retaining certificates about its old
   behavior is unsound. Keeping a protected slow core plus plastic extensions
   is a safe intermediate design, not a claim that permanent freezing is ideal.

Before a longer run, discriminate delayed exploitation, actual finishing gaps,
and cross-context value transfer. Prove the intended temporal connection in a
tiny data-free branching world before adding another chess-scale mechanism.

## Bounded natural canary result

Initial finite-prototype learner commit `2c8db186`, seed2026090301: transferred only the immutable,
already-viewed V26 pretrained R0; started new source identity and empty boundary
authority. Two viewed development positions, four epochs, eight interactions,
one numerical thread. Training snapshot duration232.545s; the240s overall budget
was crossed at an exact epoch at273.365s including setup. Final read-only probe
and serialization brought total duration to363.981s. No protected, validation
or regression outcomes were opened; final evaluation used the training positions.

No training win, surprise bud, handoff or successor value occurred. There were
seven unique REAL successor observations and eight first-contact action choices.
The natural stream therefore does not yet verify reward-driven early revisits;
the focused positive-incumbent test does. Full all-reply trained-policy probe:
0/2 positions, one mating finish out of five reply paths, no illegal/null first
moves. The successful finisher was uncertified and was permitted to act without
gaining certification. The pretrained core's semantic state remained unchanged.

The subsequently bounded exploration revision was not used in this canary;
its evidence is the focused synthetic/native-choice and exact resume tests.
This passes a bounded execution/safety canary, not a learning/performance gate.
There is no evidence here for starting a long curriculum run unchanged. Keep the
next work focused on genuine temporal responsibility/composition and a mutable,
source-versioned finisher, not another global schedule or legacy M4 switch.
