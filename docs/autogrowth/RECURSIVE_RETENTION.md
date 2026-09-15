# Recursive retention: fixed distribution switch

Declared 2026-09-12, before any experimental action. The previous pilot's guided
splits improved acquisition, but lost four prefix successes, the same number as
random splits. This follow-up asks whether that mechanism preserves both contexts
when the frequency of experience shifts in both directions. It changes no learner
code, credit law, terminal vocabulary or split-selection mechanism.

## Protocol

- Fresh seeds 4, 5, 6; same four-bit, two-action Boolean environment as the first
  pilot. The unchanging reward rule chooses x when z=False (A), y when z=True (B).
  The fourth bit is irrelevant. All observations arrive through equality terminals;
  the learner receives only the scalar outcome of its actual chosen action.
- A common 256-action prefix covers each of the eight A rows 32 times. Clone it
  into flat growth, random eligible splits and residual-ranked eligible splits.
- Each arm receives six blocks of 128 actions. The first three show each A row
  twice and each B row fourteen times per block (mostly B); the last three reverse
  those counts (mostly A). Schedules depend only on the declared seed. No score
  changes training length, examples, graph, rates or growth opportunities.
- This is a laboratory distribution-shift probe, not an autonomous curriculum.
  A/B labels and phase boundaries are never supplied to the learner. Both skills
  remain reward-compatible; this tests interference rather than contradictory goals.
- Same eta=.3, exploration=.25, prefix cap16 and continuation cap24, six maximum
  split opportunities, depth4, 12 sampled candidate contexts, 160 definitions and
  4096 physical vertices. Same supplied recursive runtime as the first pilot.
  Candidate contexts may include action coordinates. No goal hierarchy is claimed.
- Evaluate all 16 development rows after the prefix and every continuation block,
  using disposable frozen clones. Compare actual solved row identities, not totals
  alone. Report A retention/B acquisition at episode640; then A recovery/B retention
  at episode1024. Report losses from every prior measurement and from each phase
  anchor, live contributions, physical nodes, definitions and nested split depth.
- Exactly **7680 training + 912 evaluation = 8592 actual actions** if complete.
  A later frozen verification replays the 57 evaluations: 912 additional evaluation
  actions, separately counted, with no training. All seeds/arms run once, even if
  they begin weak or regress. No cherry-picked prefix or adaptive stopping.
- One CPU core, 2 GiB address-space cap, 64 MiB individual-file cap, 600 seconds
  for the entire experiment, including journaling and verification. An independent
  shell timeout terminates the process after 620 seconds, with a five-second kill
  grace. No automatic retry/resume and no cross-turn background dependence.

## Evidence and interpretation

Each 128-action block has an exclusive intent, a per-action fsynced partial log,
an exclusive compressed checkpoint and a write-once completion manifest containing
payload hashes. Only a fully logged/checkpointed block receives its sealed journal
name. Each block is verified before the next begins; whole-run completion requires
all **60 blocks, 72 checkpoints and 7680 distinct scheduled training records**.
If interrupted, partial evidence remains explicit. No missing record is reconstructed.
The two prefix blocks share a single evaluation at episode256.

Actual post-feedback records include the selected pre-exploration prediction,
participating contribution identities, their weights before/after credit and
observed candidate truth values. They are laboratory records only and never feed
back into the actor. These allow credit attribution if losses recur. Evaluations
are separate from training and cannot mutate its state. Historical logs are retained.

The comparison matches initial actors, exercise orders, exploration draws, caps
and growth opportunities, not realized parameter counts or computation. Guided
and random candidate eligibility can diverge. Three deliberately contextual toy
seeds cannot establish general superiority, chess retention or learned internal
developmental control. Scores on this full truth table are development results.

Run from the isolated branch with the established PYTHONPATH:

```bash
timeout --signal=TERM --kill-after=5s 620s python3 scripts/autogrowth/run_recursive_retention.py --output snapshots/autogrowth/recursive-retention-20260912
```

Results will be recorded separately, so this predeclared protocol's hash remains
unchanged through verification.
