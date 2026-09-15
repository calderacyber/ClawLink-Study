# Editorial log

## Revision: 2026-09-15

This log records the disposition of the first Worker Agent shadow-review task
(`shadow-case-study-001`). The reviewer did not edit the paper; the primary
agent validated the findings against the local artifacts before applying the
changes below.

| Review finding | Evidence checked | Disposition |
|---|---|---|
| Replication instructions were too high level. | Benchmark runners, relay test, protocol, and reproducibility record. | Added an explicit reproduction procedure, prerequisites, command sequence, and a release-metadata requirement. |
| CLX/1 vs. CLX/2 byte claims were not like-for-like. | `benchmark/results.jsonl`, `benchmark/clx2_pilot.jsonl`, and the runner templates. | Removed percentage-reduction claims and retained only directly observed compact-envelope values. |
| A05 needed reconciliation. | `benchmark/cases.json`, exploratory results, pilot result, and final r3 result. | Stated the synthetic-label disagreement precisely; documented that final r3 returned `suspicious`; did not label the earlier output a model error. |
| Safety/auditability claims were too broad. | Worker charter, relay source, protocol, and recovery artifacts. | Narrowed all conclusions to the controlled synthetic workload and observed relay records. |
| Latency attribution was unsupported. | Summary files provide wall time only. | Removed causal attribution to inference/relay components. |
| Invalid runs needed traceability. | Worker Agent benchmark directory and copied v1/r2 artifacts. | Added both invalid result files to the local publication bundle and artifact inventory. |
| Fresh-worker test needed selection/context detail. | `run_fresh_worker_recovery.py` and its summary. | Disclosed the selected task IDs and narrowed the inference to a recovery demonstration. |
| Integrity coverage was incomplete. | Artifact inventory and SHA-256 checks. | Added `INTEGRITY_MANIFEST.sha256` covering paper, protocol, inputs, runners, tests, valid results, and invalid results. |

## Editorial boundary

The edits improve documentation and reproducibility. The public bundle uses
pseudonymous `coordinator` and `worker` role labels and generic local paths;
this sanitization did not change task IDs, classifications, timings, byte
counts, or protocol semantics. Any future substantive change to an experiment
result should be logged here with the source artifact and reason.
