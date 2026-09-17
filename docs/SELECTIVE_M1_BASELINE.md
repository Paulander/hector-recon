# Validated selective mate-in-one baseline

Source: `12fa306c` (`codex/selective-m1-curriculum`). Modern-main integration
target: `2aa1ce47a6a93e2571aaa0b02101e9543fe94955`, tree
`6f6fc10b6d0fbfd7c6fc83d5f7b45237ff583960`. The older candidate `cbfdf9cb`
was built against stale local main and is preserved as evidence, not merged.
Publish only the explicit modern-main delta; preserve every unmentioned path.

## Demonstrated result and scope

The seed61/event2048 actor trained from scalar outcomes of its actually played
moves. Without further training it solved:

- 1,080/1,080 training positions and 224/224 separate development positions.
- Development remained 224/224 at all nine checkpoints across another 1,024
  ordinary training moves; weights, births and pruning remained active.
- One-shot untouched confirmation: 80/80 positions, ten complete D4 orbits.
- After the user retired the old reservation, the remaining 128 M1 placements
  also passed on the same checkpoint; no old result file was consulted.

The combined population is **1,512/1,512 legal White-to-move KRK mate-in-one
placements, 189 D4 symmetry orbits**, including all corner orientations. The
enumeration covers distinct piece placements; repetition/50-move history,
different material, Black-to-move attacks and arbitrary KRK positions are outside
this claim. Greedy evaluation is perfect on this scope; deliberately exploratory
training is not. These receipts are now regression material, not fresh evidence
for selecting future tuned networks.

This does not prove seed-robust convergence, perpetual retention, calibrated
recognition of competence on non-M1 boards, M2 performance or learned temporal
handover. The first M2 implementation is a separate work branch.

## Mechanism and information boundary

The 16 existing relational board/move coordinates enter through graph terminals.
The formal graph competes over legal primitive actuator bindings. The environment
returns +1 if the actually played move mates, -1 if that one-move exercise fails.
No correct move, engine/tablebase value, position identifier, authored corner rule
or alternative-action outcome enters learning. Curation establishes exercise
membership separately; it does not send the mating move to the learner.

Existing generic state-route/action-reader buds start with zero weight. Actual
selected-action residuals support later weighting and prospective selective
refinement. Growth, retirement and ordinary weight plasticity remain active.
Reclosure and whole-owner splitting are off. No separate finisher, externally
chosen branch, virtual look-ahead or POR chain produced this M1 result.

The checkpoint has 12 live conditions, 3,405 physical nodes, 13,564 SUB/SUR edges
and 168 registered expression definitions. Node copies across action bindings
are not independent learned concepts. Defaults retained: exploration .25,
learning rate .3, development every 64 actions, 96 owned parameters. Slow
consolidation currently transfers the bias only, not all condition weights.

## Minimal integration and compatibility

The actual modern main already contains the exact formal engine, graph, frame
support, full stem-cell module, chess terminal adapter and namespace packages
used by the validated source. None is replaced. There is no Graph migration,
legacy API rewrite, namespace transplant or extracted stem-cell subset here.

The runtime delta is eleven selected generic learning modules plus the selective
chess factory and bundled-artifact loader. Ten learning modules are new; only
`terminal_development.py` changes an existing runtime file. Its additions are a
default no-op pre-execution hook and a default uniform exploration hook, retaining
the original base learner's behavior and defaults.

After loading the artifact, all 72 imported repository modules were audited
against live-main Git blob identities: the thirteen proposed runtime files are
the only differences; the other 59 match main byte-for-byte. This prevents the
work branch's unrelated experiment modules from silently becoming dependencies.
The eleven generic modules and selective factory remain exact validated-source
code. Main's existing terminal tests are unchanged. Added tests use small pure
Boolean fixtures, not closed experiment runners. Historical experiment runners,
authority variants and large result directories are not promoted.

## Artifact and usage

Original checkpoint SHA256:
`ae8d5c2e64f6c14e98cca5440db9885e3bfde4e67e728e628838427889f99b96`.

Packaged actor: `src/recon_lite_chess/checkpoints/selective_m1_seed61.pkl.gz`,
375,475 bytes; SHA256:
`52c226628e5f8d09520c82a0b24dcb2e88ecf4e81ebb1746850df852a16000ff`.
The adjacent JSON records provenance, complete knobs, topology and evidence
hashes. The actor-only export omits the experiment's outer schedule container,
not any actor weights, topology, histories, settings or RNG state.

Use Python 3.12 and install the local `libs/recon-lite` core before this project
(or use `PYTHONPATH=src:libs/recon-lite/src` in a checkout).

```python
from recon_lite_chess.coach.pretrained import load_pretrained_m1
from recon_lite_chess.coach.exercise import play_mate_one

actor = load_pretrained_m1()
result = play_mate_one(actor, "k7/8/1K6/8/8/8/8/7R w - - 0 1",
                       event_id=0, learn=False)
print(result.action, result.reason)
```

Each load returns an independent, still-plastic graph. Learning must use a copy;
do not overwrite the baseline. The loader verifies a code-pinned hash before
unpickling and accepts only the shipped payload. It is not a safe general-purpose
loader for arbitrary pickle files. The exporter checks executing original source
identity against the checkpoint before conversion and refuses changed runtimes.
Python and chess runtime versions are recorded in the manifest.

## Verification

Modern-source results: **105 focused tests passed** (250.79 seconds), including
full-population exact-action reproduction. The unchanged main-boundary suite
passed **93 tests**, and all **127 standalone core tests** passed. These suites
overlap and are not additive independent evidence. Separately built core/Hector
wheels were installed into an isolated directory; the packaged manifest and
hash-pinned actor loaded there and the graph executed an actual mating move.

Focused tests cover prospective refinement, contradictions, local credit,
checkpoint/resume, typed terminals, information boundaries and artifact tampering.
The full-population regression chooses every move anew, checks exact agreement
with all 1,512 original receipts, confirms actual checkmate, and verifies unchanged
learned conditions/RNG states during evaluation. Shared condition/edge weight
identity and independent plastic loads are also checked.

```sh
PYTHONHASHSEED=0 PYTHONPATH=src:libs/recon-lite/src:tests/autogrowth python -m pytest -q \
  tests/autogrowth/test_context_compatibility.py \
  tests/autogrowth/test_context_decision.py \
  tests/autogrowth/test_owner_birth_search.py \
  tests/autogrowth/test_owner_development.py \
  tests/autogrowth/test_recursive_context.py \
  tests/autogrowth/test_refining_route_action.py \
  tests/autogrowth/test_route_action_bud.py \
  tests/autogrowth/test_selective_m1.py \
  tests/autogrowth/test_selective_m1_pretrained.py \
  tests/autogrowth/test_terminal_development.py
```

All 127 standalone core tests pass without core changes. Additional unchanged
main-boundary tests and an installed-wheel artifact smoke test are recorded with
the publication audit. Full experiment history remains on the work branches.
