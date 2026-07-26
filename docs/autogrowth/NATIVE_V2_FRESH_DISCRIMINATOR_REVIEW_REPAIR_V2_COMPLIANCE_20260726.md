# V2 fresh discriminator review repair V2 — compliance matrix

Date: 2026-07-26

| Frozen requirement | Replacement implementation | Closure evidence |
|---|---|---|
| Learner and graph behavior unchanged | New outer driver imports the protected V2.1 learner and existing snapshot/registry code | Exact source hashes match; prior 1,013-test certificate remains applicable |
| C association break is binding | Cohort engagement separately counts C planted contradiction dose and requires at least 24/32 | Focused 23/32, 24/32, and C-never-breaks cases pass |
| Every relevant contradiction clears decision weight | Every row records available cells, contradiction cells, and graph-emitted clearing IDs; every intersection is checked | Missing, present, selected-spurious B, and multiple-event cases pass |
| Committed values rebuilt from rows | Exact 16-row order, A/B/C coverage, 48 ordered result reads, recalculated endpoints and clearing summaries | Changed total/target, duplicate/missing/reordered row, and journal-transition cases pass |
| Final graph independently agrees | Restore all three final graphs; compare complete state, support, contradictions, clearing, continuation, sequence position, journal, and last row | Changed final graph and changed continuation cases pass |
| Admission rebuilt immediately before play | Restore all 96 graphs; recheck prefix/candidate metadata; rerun row parity, target counts, registry scan, and admission with zero result reads | Seed 31/C, prefix, exposure, parity, and candidate-metadata failure cases pass |
| Exposure-to-play boundary frozen | Execution manifest binds source, package, seed/ecology, prefix/candidates, 96 snapshots, exposure, parity, admission, and zero reads | Exact rebuild equality and changed-input rejection pass |
| Complete board-position separation | Excluded-position manifest contains starts and results from every earlier V2 ecology/canary; new starts and results are internally unique and absent | Superseded result-board overlap is 28; replacement overlap is zero in all four categories and has 320 unique boards |
| Command restart is connected | Top-level uses the journal's next unfinished seed and verifies committed seeds before remaining work | Seed 0, middle, and seed 31 restart cases pass with no repeated result reads |
| No new learner interaction in this package | Discovery, snapshot, exposure, and science remain separate future commands and all future paths remain absent | Module absence check passes; only the retired canary artifacts exist |

## Executed closure evidence

- Focused package: 31 passed in 24.11 seconds (measured command elapsed 23.83 seconds).
- Retired actual-graph canary: passed; 96 snapshots, 17 injected stage/durable-write failures, exactly 48 truthful result accesses, exact no-replay reconstruction, and exact 48/48 journal-to-transition agreement. The ecology-to-result file interval was 1h55m21s across its safe stop/resume. Canary JSON SHA-256: 569f22fc9bcfa8118f9295ea3e26ec742c7949e5ed93f603cafa817486a01352; canary digest: 94639984435bf2599e6843bbda6a4543a728483d734337a1ec35af0917a7cd31.
- Selected adjacent suite: 71 passed; pytest reported 9,420.87 seconds (2h37m00s), while the shell elapsed timer reported 8,923.68 seconds; both measurements are preserved.
- Protected learner SHA-256: 25945864fd998caf22ae12cbcb9bcb4779447337c0079f705640c63d2356f029.
- Protected registry SHA-256: f3aee5cccf761af1cb6a5de94b886d5e758c0a07cb0f6d77b8898f662ca73b58.
- Protected snapshot runner SHA-256: 8611853ca56c2dab3e2a44ebad18997f9d9d55578627acbaff6e727a578fd894.
- Superseded driver SHA-256: 2bc7413df95ee910bf18eb465ffdc111fdf9fb1f64a75e452cdd5ae848871036.
- Independently measured superseded overlap with earlier boards: 0 starts, 28 results, 0 complete transitions, 0 stable interaction IDs.
- Independently measured replacement overlap with the complete excluded set: 0 starts, 0 results, 0 complete transitions, 0 stable interaction IDs; 160 unique starts plus 160 unique results.

A positive future result remains impossible unless both frozen primary comparisons
pass and the complete engagement decision passes. The driver changes no learner,
nomination, polarity, lifecycle, threshold, topology, arm, endpoint, or test.
