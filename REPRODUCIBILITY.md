# Experiment reproducibility record

## Scope

Two independent OpenClaw identities on separate systems, communicating through
a loopback-only, append-only relay carried by authenticated SSH over Tailscale.
All workload cases are synthetic.

## Fixed artifacts

- Worker scope: `WORKER_CHARTER.md`
- Protocol versions: `CLAWLINK_PROTOCOL.md`
- Cases and expected labels: `benchmark/cases.json`
- Individual case views: `tasks/A01.json` through `tasks/A20.json` (derived
  from the canonical case library; the benchmark runner reads `cases.json`)
- Relay implementation: `relay/clx_relay.py`
- Trial outputs: `benchmark/*.jsonl` and `benchmark/*summary.json`

## Measures

For each trial record: expected label, returned label, elapsed wall time,
request and response bytes, protocol mode, and raw response. Relay records
also retain direction, envelope, timestamp, and deterministic CLX/2 decoding.

## Protocol implementation correction

The first full CLX/2.1 run exposed an off-by-one checkpoint guard: it counted
the incoming task before making the cadence decision. The first repair still
gave the worker an ambiguous “four or fewer” audit assertion, leading it to
conservatively escalate rather than infer that a fifth task was allowed. These
invalid runs are retained as
`benchmark/clx21_full_results_v1_checkpoint_guard_bug.jsonl` and
`benchmark/clx21_full_r2_results.jsonl`; neither is a model-accuracy result.

The final repair counts only completed `ASK` → `RES` exchanges, evaluates the
current request *before* it is appended, and emits an exact deterministic count
in the relay audit context. Boundary tests cover: initial four-task window,
checkpoint reset, blocked task not consuming a slot, and block at the fifth
completed exchange.

## Validated results

- `clx21-full-20-r3`: 20/20 correct synthetic labels; 20 `RES`, 0 `ESC`; four
  checkpoint acknowledgments; mean elapsed time 16.31 seconds; mean compact
  request/response sizes 161.8/526.2 bytes.
- `clx21-recovery-fresh-r1`: a new run-scoped agent session, with no prior
  benchmark conversation, acknowledged the documented protocol, classified
  4/4 selected cases correctly, acknowledged the fourth-task checkpoint, and
  safely escalated an unknown task reference (`A99`).

## Publication-bundle integrity

`INTEGRITY_MANIFEST.sha256` contains SHA-256 hashes for the paper, protocol,
worker charter, inputs, runners, relay implementation, boundary tests, valid
results, recovery results, and both invalid full-run artifacts. From the bundle
root, verify with:

```bash
sha256sum -c INTEGRITY_MANIFEST.sha256
```

The manifest intentionally does not include itself. Regenerate it after any
artifact change and record the reason in `EDITORIAL_LOG.md`.

## Limitations to disclose in a paper

- One worker model/provider and a synthetic 20-case workload.
- Wall time and byte count are proxies, not exact token accounting.
- Synthetic answer labels require human adjudication when reasonable experts
  disagree (as happened for A05 in the first benchmark).
- The relay is SSH-over-Tailscale, not a direct public A2A endpoint.
