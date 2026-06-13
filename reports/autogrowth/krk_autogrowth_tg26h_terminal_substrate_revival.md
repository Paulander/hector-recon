# TG26h Terminal Substrate Revival

Artifact: `reports/autogrowth/krk_autogrowth_tg26h_terminal_substrate_revival.json`

TG26h restores a FeatureHub/generic feature-vector TERMINAL pathway for the
foundation curriculum before returning to edge/fence. `ActionRanker` is kept in
the artifact as a diagnostic baseline, not the main learning claim.

Main bounded run:

- Mate_In_1: 300 train, 100 heldout, 40 mirrored.
- Mate_In_2: 300 train, 100 heldout.
- Terminal-native Mate_In_1 heldout: 100/100; mirrored: 40/40.
- Terminal-native Mate_In_2 heldout conversion: 90/100.
- Diagnostic ActionRanker Mate_In_2 heldout conversion on same split: 83/100.
- Terminal substrate: 630 Mate_In_1 terminals; 700 Mate_In_2 first-move terminals.
- M4 event count: Mate_In_1 = 1, Mate_In_2 = 1, only after heldout confirmation.

Interpretation:

This is a foundation success, not an edge/fence competence result. It shows that
the dense foundation curriculum can be represented through first-class
`StemCellTerminal` feature-vector terminals and local M3 weights. The run still
uses synchronous Python legal-move enumeration as the environment interface, so
the artifact marks that batch loop as remaining scaffold.

Next:

Rerun bounded edge/fence validation with the terminal-native foundation path and
keep `ActionRanker` only as an ablation baseline. Do not proceed to broad KRK,
ecological spawning, SCRIPT/LAG expansion, or fence M4 consolidation until that
transfer test is reported.
