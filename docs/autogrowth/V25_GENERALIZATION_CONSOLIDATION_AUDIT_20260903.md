# V25: evidence continuity, generalization, and consolidation

## Verdict and scope

The next intervention should repair the **learning lifecycle**, not add more
training time or switch on legacy M4. Keep local budding, residual refinement,
native action competition, numerical learning, protected R0 routing, and
all-reply verification. Give an unchanged hypothesis one continuous prospective
evidence history, and stop its rebirth from erasing applicable counterexamples.

Exact audited experiment source:
`e11ad9c2ee939cc16550ad1cb6b01ab4dbc119ca`, in the clean detached checkout
`/Users/banquo/Documents/ChatGPT/Hector-Recon/v25-overnight-e11ad9c2`.
Main documentation checkout: `codex/native-adaptive-organism`, HEAD
`c225fe6a4356af5f2b7b643e52deeab92fab4d24` before these uncommitted notes.

This investigation used source/history, the already-viewed epoch32 development
snapshots of seeds 2026090108/0109, seven focused unit tests, and two data-free
counterexamples. Three independent agent audits covered numerical learning,
lineage evidence, and game-learning architecture. No learner implementation,
parameters, saved network contents, or old experimental scores were changed.
No new chess evaluation, curriculum run, external chess oracle, or protected
fresh outcome was used.

## 1. What the observed lineages actually establish

| Epoch32 evidence | Seed 0108 | Seed 0109 |
| --- | ---: | ---: |
| Distinct positive REAL receipts | 18 | 25 |
| All REAL receipts | 228 | 189 |
| Authority cells / certified | 42 / 6 | 41 / 0 |
| Maximum structural depth | 1 | 2 |
| Post-contact action choices | 98 | 104 |
| Handoffs | 3, new root | 2, original core |
| Mate-in-2 validation | 0/4 | 0/4 |
| Initial and final frozen R0 validation | 16/16 | 15/16 |

0109 did not simply lack successful experiences. Its broad hypotheses acquired
both support and contradictions; its clean final hypotheses had prospective
support histogram `0:1, 1:6, 2:3, 3:5`. None reached four.

Three late 0109 refinements matched 23 of the 25 recorded positive traces and
none of the 164 negative traces. All three had the same observed match set;
they are not three independent discoveries. They were born at authority
frontier156, leaving only positive receipts162/167/171 as eligible witnesses.
This is retrospective training-set separation, **not** certification, held-out
generalization, or proof that the representation is sufficient for all M2.
It does refute the simple diagnosis that no reasonably broad separating rule
was expressible in this observed stream.

The same three-feature semantic pattern occurs in both seeds: observed
`gives_check_and_rook_safe_after`, rook-to-black-king-edge-line distance zero,
and king-support Manhattan distance two. These are existing observed local
signals, not features proposed for injection from this audit. The 0109 root
suffix `cbc851e972da` was a sketch at121, promoted at135 after matching
121/122/124/135, and gained only one later positive143 under the current
authority clock. The corresponding sixth 0108 root had 17 retrospective
positive matches and zero negative matches.

Repeated successful boards can still update numerical values, but the
board-level duplicate index prevents them from adding new certification
receipts. No new positive REAL receipt appeared after160 in0108 or171 in0109.
This exhausts witnesses in the recorded stream, not all possible future
successors: an unvisited state or changed policy could still produce new data.
There is no proof of irreversible nontermination or global impossibility.

## 2. A concrete known-counterexample defect

Five of 0108's six certified roots fully match the stored failure at REAL
ordinal11, before those candidates were born. This is not merely overlapping
atoms: the canonical structural matcher accepts the trace, member roles are
permitted, and source-organism/source-state identities are unchanged across
the seed's 228 receipts. Failure11 is explicitly present in these roots'
discovery-exclusion lists.

Those lists prevent old evidence from counting toward certification. They do
not make the positive rule abstain on a known conflicting observation.
Ecology's full promotion audit starts at the candidate's birth, and authority's
promotion audit starts at its trigger. Thus a known failure can disappear as a
constraint when a rule is born again. Five early certificates additionally
share their first four witnesses52/67/68/75; certificate count overstates the
diversity of successful evidence.

This does **not** establish that one of these rules actually produced a false
handoff during the run. No new query was executed on that old failure. It
establishes a lifecycle consistency defect despite successful post-birth
leakage checks. "No discovery leakage" and "no known counterexample" are
different properties.

Code anchors in the exact checkout:

- [Ecology audit starts at birth](/Users/banquo/Documents/ChatGPT/Hector-Recon/v25-overnight-e11ad9c2/src/recon_lite_chess/autogrowth/native_prospective_boundary_candidate_ecology.py:2006).
- [Authority promotion only examines the trigger-forward interval](/Users/banquo/Documents/ChatGPT/Hector-Recon/v25-overnight-e11ad9c2/src/recon_lite_chess/autogrowth/native_prospective_evidence_authority_v2.py:11183).
- [Post-birth eligibility excludes old evidence](/Users/banquo/Documents/ChatGPT/Hector-Recon/v25-overnight-e11ad9c2/src/recon_lite_chess/autogrowth/native_prospective_evidence_authority_v2.py:874).

A data-free reproduction using the actual ecology class fed one false
`opaque-pattern` observation, then four true observations of the same pattern.
At ordinal4, the full promotion audit returned `eligible=True, support=4,
contradictions=0`, although the proposed rule matched the known earlier failure.
The false observation preceded its birth at1. No chess or saved network was
involved in this reproduction.

## 3. The second evidence clock is materially costly

Today a sketch first needs evidence to qualify for graph promotion. At
materialization, authority creates a new frozen hypothesis, sets a new birth
frontier, excludes the whole existing evidence prefix, and starts an empty
certification state. Even when the predicate is unchanged, its valid earlier
prospective experience is treated as discovery again.

See [materialization and empty authority state](/Users/banquo/Documents/ChatGPT/Hector-Recon/v25-overnight-e11ad9c2/src/recon_lite_chess/autogrowth/native_prospective_evidence_authority_v2.py:11462).

There is a legitimate scientific reason for a new clock **when the hypothesis
changes after inspecting outcomes**. There is no inherent learning requirement
to reset the clock merely because the same frozen hypothesis moves from a
cheap representation into graph circuitry. This is the clearest place where
scientific-harness lifecycle rules currently constrain learning unnecessarily.

Proposed new semantics: record the immutable hypothesis and its latest
discovery-read frontier at initial birth. Prospective observations strictly
after that frontier belong to that hypothesis once. Graph promotion preserves
them if the full semantics match. Refinement, a changed source policy, changed
actuator binding, or changed observation/matching semantics creates a new
hypothesis and a new prospective frontier.

For the 0109 example, receipts122/124/135/143 are four distinct events after
sketch birth121. They illustrate the information discarded by the second clock.
They must **not** be retroactively installed as certificates in the saved V25
run: evidence continuity is a new protocol that needs an explicit identity and
provenance contract, then prospective testing.

## 4. Numerical learning works, but consolidation has incompatible meanings

R1 is not growing without learning weights. Each observed decision supplies
TD to an actuator-specific graph value and to mutable native nodes/edges.
These edge updates persist across episodes; they are not the old ephemeral
M3 delta buffers.

For a previously experienced local option, graph Q is the sole estimate used
by selection and TD. Unexperienced options instead inherit the strongest
confirmed generalized score, mapped into [-1,1]. Consequently, updating or
consolidating generalized edges alone cannot alter an experienced option's
ranking. This boundary was deliberately introduced to stop stronger aliased
priors from masking actual learning; simply adding the old scores back would
reintroduce that defect.

- [Prior versus exact-Q selection](/Users/banquo/Documents/ChatGPT/Hector-Recon/v25-overnight-e11ad9c2/src/recon_lite_chess/autogrowth/native_single_graph_curriculum.py:770).
- [TD dispatch uses that selected prediction](/Users/banquo/Documents/ChatGPT/Hector-Recon/v25-overnight-e11ad9c2/src/recon_lite_chess/autogrowth/native_intrinsic_curriculum.py:4938).
- [Actuator-specific Q and native M3 update](/Users/banquo/Documents/ChatGPT/Hector-Recon/v25-overnight-e11ad9c2/src/recon_lite_chess/autogrowth/native_single_graph_curriculum.py:1993).

The generic credit engine also owns a separate `fast_value`, initialized at
zero and keyed by triplet rather than triplet-plus-actuator. Its TD is computed
against graph Q, not against itself. For one fixed R1 action, without clipping:

`Q_next = Q + 0.08 * TD`

`F_next = F + 0.06 * TD`, hence `F = F_initial + 0.75*(Q-Q_initial)`.

An actual data-free engine run starting Q at0.94 and supplying net environmental
return0.65 for300 events ended at Q≈0.65 but F≈-0.2175. F in this path is an
accumulated correction, not a calibrated duplicate expected return. Blindly
consolidating F would therefore stabilize the wrong numerical quantity.
Current V2 shell providers use prospective evidence scores instead, so this
is a proven compatibility problem for future consolidation, **not** an
established cause of the present zero validation scores.

The old M4 engine is not a drop-in fix. Its signed episode weighting can
multiply an already-negative TD delta by a negative outcome and obtain a
positive consolidation update. Its positive weight bounds, episode reset,
and lack of native frozen-component guards also differ from this path.
See [credit F update](/Users/banquo/Documents/ChatGPT/Hector-Recon/v25-overnight-e11ad9c2/src/recon_lite_hector/learning/intrinsic_credit.py:1065)
and [legacy signed consolidation](/Users/banquo/Documents/ChatGPT/Hector-Recon/v25-overnight-e11ad9c2/src/recon_lite_hector/plasticity/consolidate.py:151).

The strongest remaining transfer hypothesis is that learned local corrections
do not sufficiently alter competition in new contexts. Exact Q is keyed by
local features plus concrete actuator rather than directly by FEN; that fact
alone does not establish useful generalization. Frozen generalized
sources can still supply optimistic priors elsewhere. This is source-supported
but has not been causally assigned to every validation miss.

Two further qualifications matter for the intended architecture:

- The exact value key includes raw UCI. Even if another position activates the
  same relational pattern, a different concrete actuator does not retrieve that
  exact action value; it falls back to a generalized prior. Raw coordinates
  should remain necessary for executing a legal move, but need not define the
  reusable learned action role. A role-equivalent/different-UCI control test
  is needed before designing a safe relational binding; simply deleting UCI
  from the key would recreate known opposite-return alias collisions.
- The grounded successor signal really does take the minimum over every legal
  reply. However, [the terminal fallback](/Users/banquo/Documents/ChatGPT/Hector-Recon/v25-overnight-e11ad9c2/src/recon_lite_chess/autogrowth/native_intrinsic_curriculum.py:3871)
  rewards the first move when the single executed continuation mates even if
  the full envelope is UNKNOWN. This is valid observed-outcome learning, not
  fabricated certification, but the same first-action Q therefore mixes
  worst-reply handoff targets with single-challenge terminal targets. It is
  **not purely a worst-reply value estimator**. Existing tests deliberately
  permit this fallback; both were rerun successfully in0.77s.

In evaluation the first move uses the plastic graph; second moves pass through
[R0 authority and its availability admission](/Users/banquo/Documents/ChatGPT/Hector-Recon/v25-overnight-e11ad9c2/src/recon_lite_chess/autogrowth/native_intrinsic_curriculum.py:6968).
Boundary ecology chiefly learns where that successor policy is competent;
it does not by itself produce a reusable first-move value representation.
Some exploratory training wins are therefore possible before the composed
evaluation policy can claim any conversion. These routes explain an important
mechanism/competence distinction, not the exact cause of each validation miss.

## 5. Recommended next implementation, in order

### A. One hypothesis lifetime, including its negative knowledge

1. Give each cheap bud an immutable semantic identity at discovery completion:
   predicate/members and roles, source-policy content identity, actuator
   semantics, matching semantics, and the latest frontier actually read to
   construct it. The birth receipt and all construction reads remain excluded.
2. Preserve applicable previously observed negative constraints. A coarse rule
   matching a known failure abstains or refines; renaming/reincarnating the same
   semantics must not clean it. Constraints are local to that rule/source,
   never a global negative veto over other positive siblings or the R0 core.
3. Maintain one prospective ledger for the unchanged hypothesis. Keep the
   existing four-distinct-case requirement and score threshold; materialization
   preserves eligible post-birth evidence rather than demanding four more.
   If semantic equality cannot be verified, fail closed and start a new lifetime.
4. Keep numerical rehearsal distinct from certification diversity. Repeated
   executed cases may train Q/weights, as they already can, but add no duplicate
   certification witness. A read-only/dream query remains non-evidence. Never
   fake diversity by changing counters, move numbers, receipt IDs, or FEN labels.
5. Retain event-local settlement after TD. The receipt completing eligibility
   cannot bootstrap its own decision. Keep atomic rollback, source checks,
   immutable core parameters, and exact resume accounting.

Use the existing authority signal index and local evidence/provenance records;
do not scan lifetime history on every frame or create a monitoring subsystem.
Applicable-history checks must be complete before a certificate is exposed;
if a bounded check cannot finish, defer/abstain rather than silently forget.
Index-assisted matching does not by itself prove constant lifetime cost.

Files whose semantics need changes:

- `src/recon_lite_chess/autogrowth/native_prospective_boundary_candidate_ecology.py`:
  immutable discovery identity/frontier, separate discovery versus prospective
  counters, and preserved local counterexamples across incarnation/refinement.
- `src/recon_lite_chess/autogrowth/native_prospective_evidence_authority_v2.py`:
  distinguish semantic birth from graph materialization in hypotheses/escrow,
  verify continuity, retain constraints, and transfer the ledger atomically.
- `src/recon_lite_chess/autogrowth/native_intrinsic_curriculum.py`:
  pass the exact identity/provenance through promotion; retain TD-before-settle
  ordering and truthful executed-versus-distinct-evidence accounting.

This changes the scientific protocol. Implement it on a new `codex/` branch;
do not rewrite/re-certify existing snapshots, alter frozen results, or change
legacy V25 fingerprints to make old artifacts appear compatible.

### B. Value transfer/consolidation only after its cause is isolated

Preserve existing numerical learning during A, so its result is interpretable.
Treat that as a lifecycle-only discriminator, not approval for a full curriculum.
Then test one trained context, a different context sharing relevant local
patterns, and a distinguishable contrast context. Does observed credit change
the second context's native ranking appropriately? Does the contrast refine
instead of spreading a wrong value? No correct-move teacher is needed.

The same control should include an equivalent local action role with different
concrete UCI, and a same-looking but opposite-return actuator. A future binding
must transfer the former without collapsing the latter. Prefer explicit local
role/actuator bindings in the existing graph over a board-state lookup table.

Before calling the learned first-action value adversarial, also separate
single-reply experience from the value of the complete choice. Preserve the
actual terminal reward for the executed continuation and its local learning;
do not erase the positive outcomes that drive budding. But a success against
one reply must not overwrite a known worse reply's action-level value. A small
per-reply learned-value fixture, aggregated by the existing all-reply minimum,
can discriminate this before changing production semantics. UNKNOWN coverage
must remain explicit, with curiosity separate from certified successor value.
Do not repair the mismatch merely by suppressing every early reward until a
global admission gate passes.

If two-timescale value storage is then implemented, there must be one explicit
effective action estimate driving choice, TD, and any value provider. For
example, `effective = slow + fast_residual`; moving an amount from the residual
into slow storage must preserve the effective value and must not apply reward
twice. This identity-preserving storage operation is not itself generalization.
Shared-pattern transfer requires its own demonstrated local learning rule and
tests, with frozen-core immunity. Do not simply enable the old M4 call.

Potential second-stage files:
`native_single_graph_curriculum.py`, the R1 dispatch in
`native_intrinsic_curriculum.py`, and
`src/recon_lite_hector/learning/intrinsic_credit.py`. Keep legacy plasticity
modules unchanged unless a separate compatibility repair is explicitly selected.

## 6. Tests and stop/go criteria

Already rerun at the exact source: five focused tests passed in **1.80s**:
causal TD changes a later action in a tiny control comparison; exact-Q resists
an unrelated stronger alias; aliased actuators receive independent credit;
an already-certified duplicate query can reuse authority; and the complete
all-reply minimum reaches TD. These synthetic/code-defined fixtures are
mechanism tests, not learned chess results. The two counterexamples above
also reproduced successfully without data or saved-network mutation. Two
additional terminal-fallback/repeated-outcome tests passed in **0.77s**, for
seven focused tests total. Their passing confirms the mixed-target behavior;
it does not prove that behavior optimizes a worst-reply objective.

Required before a new chess canary:

- Birth/construction evidence excluded; three later distinct successes cannot
  certify, four can; unchanged graph promotion adds no second waiting period.
- A known pre-birth failure blocks the matching coarse positive rule. A new
  separating residual earns only its own future evidence. Rebirth cannot
  erase the same applicable failure; another positive sibling remains usable.
- Changing predicate, actuator, source-policy content, or matching semantics
  prevents inappropriate evidence inheritance.
- Duplicate REAL execution trains numerical state but adds zero distinct-case
  support; VIRTUAL execution adds neither environmental evidence nor certificates.
- Eligibility does not bootstrap its qualifying event; rollback and interrupted
  snapshot/resume preserve evidence, predictions, and subsequent choices.
- Learned credit affects a genuinely different local context in a paired
  control test, not just retrieval of the same experienced option.
- At least one small multiple-opponent-reply fixture preserves minimum-value
  credit; a single unknown/failing reply cannot masquerade as a forced mate.
- A good outcome against one reply cannot raise an asserted worst-reply value
  past a known bad sibling reply; local reward/budding remains active. Check
  different-UCI transfer without collapsing opposite-return aliases.

Then run one tiny development mechanism canary. Only if its lifecycle tests
pass, compare a small number of independent development seeds in bounded
1–2-hour windows, one numerical thread per process and independent directories.
Hold R0 setup, learner rates, candidate widths and evidence thresholds fixed.
Use new development data for prospective conclusions; old tapes may illustrate
counterfactual chronology but cannot become new independent test results.

Require prospective eligible roots/refinements, native handoffs, later use of
their credit, baseline core retention, bounded active populations, replay
integrity and an actual exhaustive M2 conversion before extending. Replicated
validation improvement is required before a full curriculum. Stop on any
known-counterexample bypass, duplicate/discovery leakage, core damage, replay
failure, uncontrolled growth, or continuing absence of functional learning.
Final regression remains final-only, not a selection signal.

## 7. Expert objections and limits

- **Mathematics/statistics:** many adaptively selected hypotheses with four
  distinct successes do not yield calibrated confidence or universal chess
  correctness. Treat the current bound as a heuristic admission score, not a
  theorem. Any formal reliability claim would require additional assumptions
  and selection-aware analysis; no new statistics framework is proposed here.
- **ML:** a slow copy cannot invent generalization, and evidence fixes do not
  prove that learned values rank the right new move. Separate lifecycle,
  cross-context transfer, and interference tests; do not combine all repairs
  into one uninterpretable run.
- **Evolutionary learning:** three rules sharing one match set are not three
  independent competences. Measure coverage and prospective outcomes, not
  population size. Do not permanently discard distinct predicates solely
  because they happen to agree on the tiny observed sample.
- **Adversarial games:** a win against one sampled reply is not forced mate.
  Keep worst-reply grounding and exhaustive evaluation; do not replace them
  with average reward or an oracle-supplied first move.
- **ReCoN/cognitive architecture:** local plasticity should retain consequences
  while testing refinements. Repeated graph admission resets and forgetting
  applicable contrasts are not necessary to self-organization. Atomic commit
  points and resource limits remain legitimate substrate constraints; they
  must not choose chess answers.

The fast-experience/slow-structured-memory analogy is useful as a design lens,
not evidence that a particular implementation will work. Complementary
learning-systems theory distinguishes fast experience-specific learning from
structured knowledge and their interaction; it does not reduce consolidation
to freezing a successful component. See the authors' [CLS review](https://web.stanford.edu/~jlmcc/papers/KumaranHassabisMcClelland16FinalMS.pdf).

No external expert endorsement or convergence proof is claimed. The remaining
failure modes include insufficient novel experience, incomplete reply coverage,
feature aliasing on unobserved cases, selection-driven optimism, harmful shared
credit, and resource exhaustion. A single-lifetime ledger removes a specific
avoidable barrier; it does not guarantee mate-in-2 mastery.

## 8. Authorized network archival

125 older development `.pkl` files in 21 explicitly inventoried directories
were losslessly compressed, without importing or unpickling them. Original
size 4,288,765,370 bytes; compressed size 405,028,016 bytes; **3,883,737,354 bytes
reclaimed** (3.88 GB / 3.62 GiB). Each archive was streamed through decompression
and SHA256/byte-count checked before its uncompressed copy was removed.

All V25 directories, the epoch35 reference directory, reports, manifests and
tracked files were excluded. Both current epoch32 snapshot hashes still match
their pre-cleanup values. No network information was discarded. Older archived
snapshots require decompression before their original runner can resume them.

The per-file paths, original sizes, compressed sizes, original SHA256 hashes,
and completed-removal receipts are in the local
`reports/autogrowth/development/NETWORK_ARCHIVE_20260903.jsonl`. Free space was
about7.4 GiB after cleanup; unrelated system changes mean the free-space delta
is not an exact measure of savings. Restore one chosen archive with
`gzip -dk /absolute/path/to/checkpoint.pkl.gz` after ensuring the destination
does not already exist and sufficient space is available. This preserves the
archive and recreates the original bytes; do not launch a run implicitly.
