# TG46b Real Clean-Slate KRK Foundation

Checkpoint pass: `False`
Interpretation: `real_clean_slate_foundation_failed_at_mate2`

TG46b audits the earlier TG46 synthetic scaffold and does not use it for the result.
The run uses generated KRK Mate-in-1 and forced Mate-in-2 FENs, legal move labels,
fresh terminal/stem-cell graph weights, and real heldout failures.

## Metrics

- Mate-in-1 heldout: 100/100 (1.000)
- Mate-in-2 heldout conversion: 78/100 (0.780)
- Same-graph continuation count: 78
- Failure pool entries: 22
- Terminal nodes: 1334
- M3 updates: 5555792

## Next

`repair_real_mate2_foundation`

## Artifacts

- main: `reports/autogrowth/clean_slate_krk/tg46b_real_foundation/krk_tg46b_real_clean_slate_foundation.json`
- progress: `reports/autogrowth/clean_slate_krk/tg46b_real_foundation/krk_tg46b_real_clean_slate_foundation_progress.json`
- markdown: `reports/autogrowth/clean_slate_krk/tg46b_real_foundation/krk_tg46b_real_clean_slate_foundation.md`
- mate1_train_trace: `reports/autogrowth/clean_slate_krk/tg46b_real_foundation/pools/tg46b_mate1_train_traces.jsonl.gz`
- mate1_eval_trace: `reports/autogrowth/clean_slate_krk/tg46b_real_foundation/pools/tg46b_mate1_eval_traces.jsonl.gz`
- mate2_train_trace: `reports/autogrowth/clean_slate_krk/tg46b_real_foundation/pools/tg46b_mate2_train_traces.jsonl.gz`
- mate2_eval_trace: `reports/autogrowth/clean_slate_krk/tg46b_real_foundation/pools/tg46b_mate2_eval_traces.jsonl.gz`
- failure_pool: `reports/autogrowth/clean_slate_krk/tg46b_real_foundation/pools/tg46b_failure_pool.jsonl.gz`
- graph_summary: `reports/autogrowth/clean_slate_krk/tg46b_real_foundation/pools/tg46b_graph_summary.json`
