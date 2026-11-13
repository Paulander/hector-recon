# Chess modular reuse: start here

Branch: `codex/chess-modular-reuse-v2`. Worktree:
`/Users/banquo/Documents/ChatGPT/Hector-Recon/chess-modular-reuse-v2`.
Parent: published documentation update `1fd332c16eeb2ac27c5ef2dba8520cb55284cab2`.

This branch prepares reuse of the validated M1 foundation, sparse terminal
discovery and native module ownership. Neither experimental source patch below
has been applied wholesale. An opt-in Setup-practice component is implemented
after the source review below. No combined sparse/modular learner or new scientific
training result is implied. Published `main` and its defaults remain unchanged.

Read the [research handoff](RESEARCH_HANDOFF_20261113.md), then the
[evidence index](RESEARCH_EVIDENCE_20261113.md). These two pages are the central
summary; earlier experiment packets remain evidence, not cumulative instructions.

## Preserved source inputs

The [source manifest](../research/chess-modular-reuse-v2/SOURCE_BASELINES.json)
pins two reference patches against M1 commit
`989cfb7e3f826ab71c05c590deacda259d72da2d`:

- [Sparse discovery](../research/chess-modular-reuse-v2/sparse-discovery-f942b93a.patch):
  the seven added files from `f942b93af15f4b527bd4d289a3a2d2f54ffff796`.
  Minimal initialization, trials, review, admission and retirement remain an
  opt-in integration candidate.
- [Qualified modular pilot](../research/chess-modular-reuse-v2/modular-pilot-20261010.patch):
  25 new and three changed files from the pilot's declared 77-file source slice.
  This includes native request/return, owned credit and the pilot's supporting
  evaluation code. It is not the complete historical execution environment or
  the later fixed512 runtime capsule.

Both patches passed application checks in disposable directories. The reconstructed
sparse files match their Git source; all 77 modular files match the pilot's recorded
SHA-256 values. The modular patch changes `formal_engine.py`, `context_decision.py`
and `terminal_development.py`: merging it with sparse discovery requires semantic
review, not merely a clean text merge. Do not apply both patches blindly.

## Reconciliation decision — 13 November

The user-supplied Claude/Fable 5.2 review identified the missing dependency:
competent children must exist before a learned parent can reliably coordinate
them. The July/October failures do not disprove hierarchy. They also do not show
that moving host code into nodes would, by itself, fix learning. Retain ordinary
credit and the selected-outcome boundary; keep skill formation and local growth
as explicit later goals. Do not silently replace them with endless leaf tuning.

The [saved-record reconciliation](../research/chess-modular-reuse-v2/SAVED_CONTINUATION_REVIEW.json)
authenticates all 1,052 materialized producer files (61,529,391 bytes) and joins
all 1,024 episode records to the completed independent own-choice replays. It
checks actual R/C/V guards, actor/schedule identities, Setup clocks, structural
births and credit counts. It executes no network and loads no checkpoint.

| Additional 512 episodes | Frozen-M1 arm | Plastic-M1 arm |
| --- | ---: | ---: |
| Applied Setup observations | 323 | 234 |
| Cumulative Setup observations | 62 → 385 | 59 → 293 |
| Setup births | 6 | 4 |
| First birth, continuation episode | 15 | 31 |
| M2 episodes requesting Setup first / 384 | 163 | 124 |
| Setup selections for the second M2 move | 141 | 91 |
| Setup selections on one-move M1 episodes | 19 | 19 |
| Rewarded Setup → M1 training completions | 17 | 15 |
| Setup frames giving a nonzero update to a nonbias contributor | 25 | 26 |
| Such frames with a positive outcome target | 1 | 3 |

Those last two rows count action frames, not contributor updates: multiple terms
can receive credit on one frame. Total nonbias contributor updates were 37/38.
Negative outcomes can teach useful distinctions too; positive counts alone do
not establish an adequate or inadequate learning dose. Some late terms had no
subsequent credit. Births, distinguishable scores, credited terms and useful
behavior are separate observations.

This is stronger than "Setup never grew": it did grow in the continuation. It
still does not establish a competent reusable Setup child. Practice mixed first
and finishing roles; parent choices and, in one arm, the changing M1 finisher
affected the outcomes. The provisional endpoint all-reply scores 0/32 and 9/32
remain semantically unclosed, with saved M1 safety regressions. Do not promote
these counts to the original study's PASS or claim a universal credit defect.

**Do not restart the old campaign as a prerequisite.** Source inspection of
`continuation_census.run_phase` shows that final V comprises a saved census
semantic pass plus a second actual endpoint control pass. Byte authentication
cannot stand in for either. A separately identified saved-only census check may
later settle its limited claims; full historical closure also needs the missing
native control pass and terminal integrity/sealing. Preserve the old failure.

## Source compatibility and the smallest next component

Direct substitution of sparse discovery into the modular ledger is unsafe:

- Sparse discovery has an implicit separate bias, lazy schema, one immediate
  frame and flat trial evidence. The modular learner expects explicit owner bias
  conditions and frozen owner/candidate/refinement/birth participation fields.
- Modular credit explicitly dispatches the prospective owner's observer, so
  substituting a sparse subclass would not automatically invoke its credit law.
- Sparse capture can create and request probe nodes after a composed module has
  been mounted; those new local node IDs are absent from the composed view.
- Sparse development rebuilds at 32 observations, including trial changes that
  do not advance its scoring structure version. The modular code services its
  64-observation owner schedule after pending credit closes and then remounts.

These are source findings, not failed behavioral experiments. The references are
the pinned `sparse_discovery.py`, `context_decision.py`, `selective_episode.py`,
`modular_credit.py` and `terminal_development.py` in `SOURCE_BASELINES.json`.

The next component is **separate Setup practice with the existing prospective
owner learner and a frozen, authenticated M1 finisher**. This is the expert's
child-training stage. Its supplied Setup → M1 schedule is visible experimental
scaffolding; it does not claim autonomous coordination or minimal sparse discovery.
Each child still chooses and actuates its own move through its native graph.
This uses the October prospective owner's bias-only initial scorer and supplied
candidate-reader machinery (42 state equality readers and 64 sampled ordinary
birth candidates). It is not the sparse branch's five-control-node initialization.
That distinction is deliberate for this component test and must remain visible;
it is not a claim that sparse minimal-start modular discovery has been integrated.

Implementation contract:

1. Fresh Setup uses the pilot's unchanged 20-coordinate current-geometry port,
   prospective owner learner, resource limits, exploration, growth and pruning.
   No supplied successful move, condition, after-state label or reward gate.
2. Setup commits one actual White move. The existing environment opponent chooses
   one legal Black reply only afterward. A disposable frozen M1 copy then chooses
   the actual finish, unless a real terminal condition has already ended play.
3. Setup alone receives one outcome bound to its saved action and prediction.
   Preserve October's weight multiplier: 0.8 if a second White move commits,
   otherwise 1. Raw reward/residual and evidence counts remain unscaled.
   Technical errors stop the episode rather than becoming negative rewards.
4. No synthetic parent frames. The October parent runtime mandates a real parent
   and selected child on every commit; a supplied-practice mode should not fake
   that contract. Later use `EpisodicSelectiveDevelopment.from_actor` for a checked
   mount of the completed child, preserving its learned state and RNG.
5. Keep the accepted M1 master immutable. No learning, new sensor schema or
   replacement solver is introduced into it. Actual successor coverage must be
   checked separately: 1,512/1,512 on its known population is not a guarantee on
   every board a Setup learner can produce.

The pending scientific comparison must pin fresh seeds, training opportunities,
a no-learning Setup control, disjoint D4 development/final pools, a fixed endpoint
and retention block, minimum useful all-reply performance and resource costs
before running. Learning success requires useful greedy Setup → M1 completion
beyond the control, retained under further plastic Setup learning, with M1 intact.
More births, more requests or exploratory wins are not success criteria. A failure
under inadequate opportunity remains a behavioral failure at that budget, with
its causal interpretation limited; do not exclude the actor or extend it afterward.

**Falsifier:** under the declared practice budget and verified finisher support,
trained Setup fails the predeclared improvement/retention criterion against the
same supplied-sequence control. Diagnose the measured failure once; do not open
an automatic learning-rate, pruning or credit-rule sweep. If it succeeds, the next
substantive experiment is mounting the competent child and learned coordination,
then experience allocation for immature children and growth at new owned sites.

## Remaining work and evidence boundaries

The scoped reconciliation and source review above are complete. Do not repeat
them merely because a new runner or directory is introduced. The original report
remains `m2-modular-512-verification-recovery-20261021-saved-closure/REPORT.md`
under the Hector workspace. Preserve all original records and STOPs.

1. The opt-in child-practice API and focused synthetic checks are complete.
   No historical checkpoint load or scientific initialization was part of them.
2. Bind an authenticated pristine M1 foundation and fresh Setup/no-learning-control
   identities in one prospective comparison. Price its real execution, restored
   all-reply evaluation, replay and closure. Use guarded empirical costs, not a
   source-exhaustive proof about every possible Python state.
3. Measure useful Setup behavior and finisher support separately. A saved
   successful episode is not a reusable-skill certificate. Do not select an
   easier pool after seeing results or feed evaluator labels into learning.
4. Integrate sparse discovery with module ownership only through an explicit
   adapter design and parity checks; the source incompatibilities above remain.
   This work need not block the existing-law child-practice component.

No old producer rerun, scientific launch, default change or broad runtime
qualification campaign is authorized by this preparation note.

## Implemented component

[setup_practice.py](../src/recon_lite_chess/coach/setup_practice.py) exposes
`create_setup_actor(seed=...)` and
`play_setup_practice(setup, finisher, fen, event_id=..., learn=...)`.
The finisher is caller-supplied; the module does not silently load a checkpoint,
pick a scientific seed or start a cohort. Records retain actual moves, outcome,
selected participation, weight snapshots, local clocks and structural identities.
Boost-subtracted score summaries are diagnostic floats, not capacity certificates.

`learn=False` means greedy evaluation on disposable copies. It is **not** an
exploration-preserving training control with weight updates disabled. Define the
control explicitly in the future scientific protocol.

The [focused checks](../research/chess-modular-reuse-v2/FOCUSED_TESTS.txt) exercise
authored synthetic graphs only, including actual mate, stalemate, draw and rook
capture, delayed timeout, invalid/stale feedback, finisher immutability, native
replay/resume, unchanged ordinary credit, and a bud whose recorded identity matches
the zero-weight contributor actually added. These fixtures are not learned M2
successes. The [preparation record](../research/chess-modular-reuse-v2/COMPONENT_PREPARATION.json)
pins current sources, checks and remaining limitations.

Preserve the broader order: competent children → learned coordination → practice
for immature children → growth at new skill sites. General M2 completion may
legitimately use M1 → M1; strict Setup → M1 is a separate dependence claim.
More structure or successful exploratory episodes alone do not establish greedy
all-reply M2 competence or M1 retention.

## Cross-project boundary

Active vision lives in `ReCoN-Active-Vision`, even where its worktree is physically
inside the Hector workspace. Its completed audits inform the questions above;
its retinal features, lease timing and experimental credit changes are not chess
defaults. The separately authorized fresh retinal-reader/lease-value diagnostic
was running when this branch was prepared. Do not interrupt or duplicate it.

Update this entry point and the central handoff when a material decision changes.
Keep experiment-specific receipts with their own repository and archive. External
SSD storage is available for large evidence; this branch stores only compact
source references, not duplicate historical archives.
