# Pre-Autogrowth Archive

This archive preserves the report/control-plane branch state that existed before the `KRK Autogrowth v0` reset.

Archived here:

- `reports/`: old report packets, Stage7/Stage8 artifacts, selector/control-plane outputs, paper artifacts, and historical experiment logs.
- `audit_pack/`: external-review audit pack generated before the reset.
- `legacy_report_tests/`: tests that mainly asserted old report packets, gates, selector reviews, Stage7/Stage8 blockers, or control-plane state.
- `legacy_report_scripts/`: old report writers, selector/stage/control-plane probes, review-packet generators, and diagnostic scripts removed from the active script path.
- `legacy_root_docs/`: old root-level notes and large historical artifacts.

This material is evidence/reference only. It should not drive the active workflow unless a future experiment explicitly mines it as historical data, and it must not provide learner-visible labels or report row IDs.

Active branch instructions now live in:

```text
AGENTS.md
docs/autogrowth/ACTIVE_BRIEF.md
docs/autogrowth/KRK_AUTOGROWTH_V0_PLAN.md
```
