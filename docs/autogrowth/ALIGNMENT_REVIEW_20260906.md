# Cross-check request to the previous Codex instance

Status: completed. The returned review supported this branch as the continuation
base and its accepted corrections are recorded in
[OFFICIAL_CONTINUATION_20260906.md](OFFICIAL_CONTINUATION_20260906.md). This file
remains the question asked, not the active project instructions.

Oskar requests an independent alignment review before choosing the new official
main line. Review the implementation and its interpretation; do not assume that
agreement is the desired result. This is a review request, not authorization to
merge, change the learner, start training, or open the final test.

Repository: `Paulander/hector-recon`.
Candidate continuation branch: `codex/mate-in-one-coach`.
Implementation being reviewed: `e3900df7a9e4167bd4c66a0ed55596e751504a16`.
Later documentation commits do not change this measured implementation.

If your checkout is on an older branch, fetch the candidate branch and inspect it
without overwriting local work. Read this brief, the constitution and the actual
implementation before judging from a branch name or historical status report.
Return your findings to Oskar so he can bring them back to the current instance.

## 1. The objective and clarified boundary

The two intended capabilities are (a) developmental graph growth and (b) learned
strategic handover between independently trained subgraphs. Chess is the initial
learning environment: M1, M2, outward KRK, then KQK/KPK and their composition.
Neither a good chess score alone nor a graph full of generated nodes proves both.

The controlling clarification from Oskar is:

- The environment owns the chess board and executes the rules. The graph
  observes through its input terminals and acts through output terminals.
- The feature basis has fixed length with heterogeneous coordinate domains,
  e.g. Boolean, bounded integer or other explicitly defined scalar domains. It
  is not an m-by-n matrix, and readers need not use every coordinate.
- Geometric measurements are permitted: piece separation, edge and alignment
  measurements are examples. Sparse coordinate/region readers are valid. Dense
  learned projections and raw-square-only inputs are not prerequisites.
- Useful terminals, combinations and eventually plans should be selected and
  developed internally. Generic learning/birth operators are legitimate prior
  machinery; supplied opposition strategies, mating sequences or answer scores
  are not the target.
- Two individually uninformative terminals must be allowed to form a useful
  conjunction. Marginal usefulness or maturity must not be a birth prerequisite.
- The coach curates positions, lets the organism act and returns scalar outcome
  feedback after the game/exercise. It does not inspect graph/virtual states to
  decide reward, growth, consolidation or scheduling. Offline audits may inspect
  internals. M1 explicitly allows +1 actual mate / -1 failure within one own move.
- Independently trained modules should eventually learn contextual delegation
  through competence, value and graph plasticity. A hand-coded material switch
  is not evidence of this. Universal joint retraining is not established as
  necessary; learned coordination and correction of mistaken competence matter.

Canonical interpretation: [ARCHITECTURE_CONSTITUTION.md](ARCHITECTURE_CONSTITUTION.md).
Do not restore conflicting instructions from old handoffs as if Oskar had not
clarified them.

## 2. What was changed and why

The first restart used an opaque coach around `NativeOrganism`. That removed
coach-side policy meddling, but the organism still reconstructed a board and
assembled candidate scores in Python before feeding an anonymous choice graph.
Its 67/128 smoke was therefore retained as a historical hybrid result.

The new default is `coach/terminal.py:TerminalOrganism`, backed by
`recon_lite_hector/learning/terminal_development.py`:

1. A catalog terminal reads legal action bindings. Input terminals alone call
   the environment's coordinate measurement port.
2. Each condition contains one to three equality readers and an AND, OR or
   exactly-one operator. The three-input exactly-one operation is not parity.
3. Conditions feed plastic SUR weights into a generic `weighted_evidence`
   SCRIPT. The existing formal choice primitive selects the action in the
   persistent graph. A requested actuator terminal executes the actual move.
4. Final reward updates the prediction used for that selected action, excluding
   its exploration bonus. Only participating conditions receive the outcome
   weight update; actual earlier actions can retain decaying eligibility.
5. Slow consolidation transfers fast weight into slow weight without changing
   the effective sum. Fast learning remains available. Whole-condition pruning
   preserves any terminal still needed by a retained composition.

The 16-coordinate supplied basis includes action-target geometry relative to
current pieces. It does not push hypothetical boards or supply mate/opposition/
action-quality predicates. Please explicitly assess whether these declared
measurements stay within Oskar's permitted embodiment boundary.

Reuse: existing Graph, FormalReConEngine, choice/Boolean semantics,
StemCellState and CandidateLocalStats. New work includes the typed port,
weighted-evidence aggregation and a small developmental adapter. It does not
reuse the full historical M5 controller or grounded child-value credit engine.
Those entry points assumed richer board/trace access, delayed graph materialization
or competence certification. Please challenge whether this adapter was justified
or whether a cleaner integration of existing code was missed.

## 3. Exact current growth law and its limitations

After every completed exercise, irrespective of reward sign, make up to two
random proposal attempts. Sample one to three distinct coordinates and equality
targets from their declared domains. Sample AND/OR/exactly-one with weights
8:1:1; a single-reader condition uses AND. Skip duplicates. Stop at 96 live
condition definitions. New readers can join compositions immediately.

Birth is not residual-directed. Targets do not mutate after birth. Conditions
cannot yet compose other learned SCRIPTs recursively. Binding slots instantiate
separate terminal/SCRIPT request state while sharing learned parameters. The
birth scheduler, plasticity and pruning rules are generic Python learning
machinery; do not describe them as learned graph policies themselves.

The important null is that behavior is explained by weight learning over a
random Boolean representation. The run does not isolate any advantage of online
birth over supplying a comparable random representation at initialization.

Pruning begins only after a 256-exercise grace period and uses small effective
whole-condition weight. This is a heuristic, not demonstrated causal importance.
Repeated participation can enter PROBATION and enable slow transfer; observed
correlation is never written into intervention counters or called causal MATURE
certification. Please assess these limitations rather than treating the lifecycle
state name as proof of competence.

Two further semantic limitations should receive explicit review:

- The node named `goal` is currently the action-choice root. Its CONFIRMED state
  means that an action was selected, not that checkmate occurred. Reusing that
  state as a successful child-goal response would recreate the old handover bug.
- Fast-to-slow transfer preserves the sum; subsequent reward updates still add
  to the fast part, and policy/pruning consume the sum. On this path, transfer
  alone does not alter the effective future learning law. Nonzero slow weights
  establish persistence of the bookkeeping, not a demonstrated behavioral
  benefit of consolidation or protection against forgetting.

## 4. What was measured

The profile and budget were fixed before the engineering run; no mechanism or
training parameter changed in response to its outcomes.

- Seed 1; 256-position training pool; 128-position development validation pool.
- Budget: 2,048 real exercises or 180 seconds, whichever first.
- Actual run: 182 real White moves, 99 mates, 180.675 seconds including completion
  of the last transaction/checkpoint. No illegal moves or abstentions.
- Nonlearning validation: 4/128 before training, 124/128 afterward (96.875%).
- Validation has 25 D4 symmetry orbits, not 128 independent families. Train and
  validation orbits are separated; validation was already development data.
- Final test remains unopened. This is one short engineering run, not replicated
  confirmation or a comparison proving superiority to the historical hybrid.
- 96 condition definitions, 70 distinct reader definitions, 20 binding slots,
  3,385 instantiated vertices. Twenty-five conditions have nonzero slow weight.
- No condition was pruned during chess: the grace period was not reached.
- 79 focused tests passed, including empty-start scalar-outcome XOR, terminal
  mask/type boundaries, Boolean semantics, actual graph-edge intervention,
  selective delayed credit, composition-member retention, bounded noisy growth,
  persistence and regressions. Two boundary tests were rechecked after a final
  protocol typing/doc clarification.

[Aggregate report](../../reports/autogrowth/development/TERMINAL_DEVELOPMENT_SMOKE_20260905.json)
and [run guide](MATE_ONE_COACH.md). Code SHA-256:
`8562d4da3b186a02fab471426e315dad18123123744c125897c0cc000044f974`.
The checkpoint and move-log archive are supplied separately to Oskar, not stored
in GitHub. Do not assume they are missing evidence merely because they are not
in the repository, or claim to have inspected them without receiving them.

## 5. Lessons to preserve from both sides

Historical findings, to verify against your own context:

- Node materialization, graph authority, usable competence and causal behavioral
  benefit are separate claims. A successful protocol/identity audit is not a
  successful chess-learning experiment.
- The July handover audit retained a working M1 policy, yet the child confirmed
  all 65 successor queries. Producing an action did not mean being competent.
  Other audited gates had zero successor coverage. Neither extreme supports
  learned handover.
- V25's evidence audit identified known failures excluded by rebirth, duplicated
  witnesses and unnecessary evidence resets at materialization. Protecting
  scientific confirmation must not erase what an organism has already learned.
- Generic residual-guided composition already showed useful results in July.
  The new XOR test is not its invention, and the simpler current proposal rule
  must not be advertised as more advanced merely because its chess path is new.
- Existing mechanisms are reusable assets; being present in the repository does
  not establish that they cooperate in the active runtime.

Mistakes or overstatements in this current conversation:

- Initially treating the opaque board-snapshot wrapper as sufficient; it was
  not the terminal-only implementation Oskar meant.
- Over-specifying dense projections and under-recognizing permitted geometry
  and sparse heterogeneous feature readers.
- Initially understating learned coordination needed when composing modules;
  a material detector does not establish scalable learned handover.
- Language around the latest result initially risked conflating random birth
  plus weight learning with experience-guided structural discovery.
- The current adapter omits several older mechanisms; simplification needs a
  measured integration justification, not an assumption that old work is bad.
- We left stale README/handoff instructions behind even after correcting the
  constitution. This documentation pass marks those contradictions explicitly.

Historical anchors:
[NATIVE_FROM_SCRATCH_KRK_PLAN.md](NATIVE_FROM_SCRATCH_KRK_PLAN.md),
[EXTERNAL_AUTONOMY_AUDIT_RESPONSE_20260712.md](EXTERNAL_AUTONOMY_AUDIT_RESPONSE_20260712.md),
[GENERIC_CORE_ONLINE_COMPOSITION_RESULT_20260712.md](GENERIC_CORE_ONLINE_COMPOSITION_RESULT_20260712.md),
[NATIVE_R0_R1_AUTHORITY_HANDOVER_DEVELOPMENT_RESULT_20260716.md](NATIVE_R0_R1_AUTHORITY_HANDOVER_DEVELOPMENT_RESULT_20260716.md),
[V25_GENERALIZATION_CONSOLIDATION_AUDIT_20260903.md](V25_GENERALIZATION_CONSOLIDATION_AUDIT_20260903.md),
[V27_LOCAL_INTERACTION.md](V27_LOCAL_INTERACTION.md).
These are provenance, not blanket instructions to rerun retired experiments.

## 6. What to inspect and what to return

Inspect at least:

- `src/recon_lite_hector/learning/terminal_development.py`
- `src/recon_lite_chess/coach/{terminal,exercise,interface,runner}.py`
- `libs/recon-lite/src/recon_lite/formal_engine.py`
- `tests/autogrowth/test_terminal_development.py`
- The aggregate result and the historical anchors relevant to any disagreement.

Review the real request/measurement/action/credit path. Check response invariance,
shared parameter identity, potential hidden action scoring, activation versus
value, residual/eligibility consistency and what pruning could erase. Identify
any untested shortcut that could explain 124/128. State whether you reviewed
code, ran tests, or merely assessed the written account.

Return these concrete outputs:

1. An alignment verdict: supported direction, needed corrections, or incompatible
   assumptions. Separate Oskar's requirements from your preferred implementation.
2. Specific disagreements with file/function/commit evidence; identify any claims
   this summary makes too strongly or any historical mechanism it overlooks.
3. A reuse map: existing components worth reconnecting, their dependencies, and
   the boundary problem each would solve. Do not propose switching everything on.
4. The smallest next experiment that distinguishes useful growth from random
   representation/weight learning, and the first decisive learned-handover test.
5. Review [SUCCESSOR_GUIDANCE_DRAFT.md](SUCCESSOR_GUIDANCE_DRAFT.md): missing lessons,
   conflicting instructions to retire, and whether this branch is the right
   continuation base. A favorable opinion is not a completed merge review.

One remaining documentation question deserves an explicit answer: the
constitution's older curriculum section prescribes 100% validation and mature
child value for M2. Distinguish scientific confirmation gates from permission
for a young graph to play and receive final scalar reward. Child value should
be an internal learned mechanism, not a coach-supplied replacement reward.
Flag any revision needed to express that distinction consistently; do not
silently treat every historical experimental threshold as a property of ReCoN.

Suggested progression for critique: unchanged longer M1/multiple seeds; growth
controls; integration of existing residual-based composition using terminal
responses; contextual competence and learned delegation; actual M2 reuse;
then broader endgames and imagination where a demonstrated need calls for it.

Do not equate raw activation or exploration bonus with transferable competence.
A child's goal success must acquire meaning relative to its parent's goal.
Do not impose globally frozen children or universal joint retraining as axioms.
Preserve child skill while allowing outcome-driven corrections and learned
coordination.
