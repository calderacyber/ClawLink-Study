---
title: "ClawLink Study: Auditable Compact Protocols for Two-Agent Collaboration"
status: Release candidate
authors: "Rick Myers"
affiliation: "Caldera Cybersecurity Services"
copyright: "Copyright 2026 Caldera Cybersecurity Services"
date: 2026-09-16
license: "Paper and synthetic data: CC BY 4.0; original code: Apache-2.0"
---

# Auditable Compact Protocols for Two-Agent Collaboration

## A reproducible OpenClaw case study

### Abstract

This case study evaluates whether two independently hosted AI agents can use a
compact communication protocol without sacrificing auditability, safety, or
handoff resilience. We deployed a primary OpenClaw agent and a separate,
freshly provisioned worker agent (“Worker Agent”) on separate systems connected by
Tailscale. The agents exchanged synthetic cybersecurity-alert tasks through a
loopback-only relay carried by authenticated SSH. The relay wrote append-only,
fsynced JSONL audit records.

The experiment progressed from plain-English messages to a structured protocol
(CLX/1), then to CLX/2.1, a negotiated compact dictionary with deterministic
relay-side decoding and mandatory English checkpoints. In the final validated
20-case synthetic run, CLX/2.1 produced 20/20 expected labels, zero premature
escalations, four checkpoint acknowledgments, mean wall-clock completion time
of 16.31 seconds, and mean request/response sizes of 161.8/526.2 bytes. A
fresh, run-scoped worker session recovered from the documented protocol and
artifacts, classified 4/4 selected cases correctly, acknowledged the required
checkpoint, and safely escalated an unknown task reference.

This is a case study, not evidence of general agent-to-agent language
optimization. It shows that modest, versioned compression can be made
inspectable and recoverable in this controlled workload when it is constrained
by an explicit task dictionary, evidence references, a plain-language fallback,
and durable logs. It does not establish a general safety or performance claim.

## 1. Research question

Can independently hosted agents communicate more efficiently with a compact
protocol while retaining all of the following?

1. Correct task completion.
2. Human-auditable meaning and evidence.
3. Safe escalation when instructions, scope, or protocol state are uncertain.
4. Recovery by a fresh worker that has no prior conversational context.

The experiment explicitly did **not** attempt to create an opaque or secret
language. Compression was permitted only when a versioned, deterministic
decoder and an English fallback existed.

## 2. Environment and safety design

### 2.1 Agent isolation

The primary agent and Worker Agent ran under separate OpenClaw identities on
separate systems. Worker Agent used a distinct Linux account (`coordinator`), a
separate workspace, and a separate provider-authenticated agent configuration.
The pre-existing OpenClaw installation on Worker Agent was not reused for worker
credentials or workspace state.

### 2.2 Network and relay

The worker gateway was loopback-only. The CLX relay also bound only to
`127.0.0.1:19101`; remote carriage used authenticated SSH over Tailscale.
No public Funnel, public A2A endpoint, shared memory file, or unlogged direct
peer channel was used.

```text
Primary agent
    |
    | authenticated SSH over private Tailscale network
    v
Worker Agent host
    ├── loopback-only CLX relay (append-only JSONL audit log)
    └── loopback-only OpenClaw gateway and worker session
```

### 2.3 Scope

All benchmark inputs were synthetic alert-triage cases. The worker charter
required evidence references, confidence reporting, scope limits, and
escalation for conflicting, unknown, or unsafe requests. It had no authority to
perform external actions as part of the benchmark.

## 3. Protocol evolution

### 3.1 Baseline: plain English

The initial control condition used ordinary natural-language instructions and
responses.

### 3.2 CLX/1: structured, English-expanded envelopes

CLX/1 added explicit fields for run/task identifiers, state, evidence,
confidence, and next action. It retained a plain-English expansion in each
routine message. This improved structured handoff and audit context, but the
full expansion imposed overhead.

### 3.3 CLX/2.1: negotiated compact dictionary

CLX/2.1 reduced routine message size by referring to approved local task IDs
and a small, versioned set of result/status codes. It did **not** encode hidden
authority or omit the audit record. Instead:

- Worker Agent explicitly acknowledged the dictionary before use.
- The relay deterministically decoded compact records into audit metadata.
- Full-English checkpoints were mandatory after every four successful compact
  exchanges.
- Any unknown task, ambiguity, missing checkpoint proof, or out-of-scope
  request required an `ESC` escalation rather than inference.

This design makes the compact syntax an optimization of a known task space—not
a free-form private language.

## 4. Method

### 4.1 Workload

The benchmark used 20 synthetic alert cases with expected labels stored in
`benchmark/cases.json`. Each result recorded expected and returned labels,
elapsed wall time, input/output byte size, protocol mode, and raw response.

The expected labels were authored synthetic reference labels, not independently
adjudicated ground truth. Case A05 was deliberately retained because its facts
support a reasonable severity disagreement: the exploratory worker responses
returned `malicious` while the reference label was `suspicious`. In the final
CLX/2.1 run the worker returned the reference label. This paper reports both
facts; it does not claim that the earlier answer was necessarily incorrect in a
real incident-response setting.

### 4.2 Outcome measures

We measured:

| Measure | Definition |
|---|---|
| Correctness | Returned classification matched the synthetic expected label. |
| Handoff size | Serialized request and response bytes. |
| Latency | Wall-clock time from task dispatch to response. |
| Protocol safety | Escalation rather than unsafe inference on missing/unknown state. |
| Recovery | A new run-scoped worker session could use the documentation and artifacts without previous benchmark conversation. |
| Auditability | Durable relay records retained envelope, direction, timestamp, and deterministic compact-protocol decoding. |

Byte counts and wall time are proxies; this study did not measure provider token
usage directly.

### 4.3 Benchmark phases and validity rules

1. **Exploratory comparison:** 20 cases in plain English, CLX/1, and an early
   compact variant.
2. **CLX/2 pilot:** five compact task references plus a required English
   checkpoint.
3. **Full CLX/2.1 run:** 20 compact tasks with four-task checkpoints.
4. **Fresh-worker recovery:** a new run-scoped session received the documented
   protocol/artifacts rather than the earlier worker conversation.

Runs were considered valid for expected-label reporting only if the relay
checkpoint guard passed its deterministic boundary tests and no compact request
was blocked before its four completed task-response exchanges. The two failed
full-run artifacts are included in this bundle and are explicitly marked
invalid. They are implementation-debugging evidence, not model benchmarks.

### 4.4 Reproduction procedure

The artifact bundle contains the runners and input files used for the final two
phases. On the worker host, set the `ROOT` constant in the runner to the local
bundle path, ensure that the loopback relay is listening on port `19101`, and
run:

```bash
python3 relay/test_checkpoint_guard.py
python3 benchmark/run_clx21_full_r3.py
python3 benchmark/run_fresh_worker_recovery.py
sha256sum -c INTEGRITY_MANIFEST.sha256
```

These commands require a configured OpenClaw worker, local provider
authorization, and the relay service; provider credentials are intentionally
not included. The bundled runners use host-local paths and therefore must be
reviewed and adapted before use on another system. A complete public release
should additionally pin the OpenClaw build, worker model identifier, relay
runtime, operating-system release, and dependency lockfiles.

## 5. Results

### 5.1 Exploratory comparison

The early 60-trial comparison (20 cases × 3 modes) yielded 19/20 expected
labels in each condition. The shared mismatch was case A05: the reference
expected `suspicious`, while all three exploratory conditions returned
`malicious`. This is a disagreement between a synthetic reference label and
the worker output, not an adjudicated model error. It should be independently
reviewed before any operational conclusion is drawn from this case.

| Mode | Expected-label matches | Mean latency | Mean response size |
|---|---:|---:|---:|
| Plain English | 19/20 | 8.56 s | 184 B |
| CLX/1 | 19/20 | 15.17 s | 1,005 B |
| Early compact CLX | 19/20 | 16.12 s | 1,303 B |

**Interpretation:** initial structure improved handoff format but did not
improve efficiency, because the compact mode still carried a full English
decoder in routine messages.

### 5.2 CLX/2 pilot

In a five-task pilot, CLX/2 compact task envelopes averaged 159 bytes. The
prior CLX/1 comparison used a different English-expanded request construction,
so the reported 583-byte CLX/1 figure is descriptive rather than a controlled
like-for-like compression estimate. The same limitation applies to response
size: message construction and worker verbosity differed by condition. The
pilot nevertheless established that a compact envelope could be decoded from
the audited dictionary. The worker stopped at the checkpoint boundary rather
than continuing without proof, exposing a relay design defect described below.

### 5.3 Invalid runs and correction

Two early full CLX/2.1 runs are explicitly excluded from accuracy claims.
The relay counted an inbound task before deciding whether a checkpoint was due,
creating an off-by-one block. A first repair also gave the worker an ambiguous
“four or fewer” assertion, which the worker conservatively escalated instead
of treating as proof that a fifth task was allowed.

The correction was to count only completed `ASK → RES` exchanges, assess the
incoming request before appending it, and transmit the exact deterministic
count from the audited relay state. Boundary tests covered the initial
four-task window, checkpoint reset, blocked-task non-consumption of a slot,
and the block at the fifth completed exchange.

These defects matter: they show that protocol and relay implementation errors
can dominate apparent agent performance. The invalid artifacts were retained,
not overwritten.

### 5.4 Final validated CLX/2.1 run

| Run | Tasks | Correct | `RES` | Premature `ESC` | Checkpoints | Mean latency | Mean in/out size |
|---|---:|---:|---:|---:|---:|---:|---:|
| `clx21-full-20-r3` | 20 | 20 | 20 | 0 | 4 | 16.31 s | 161.8 / 526.2 B |

The validated compact protocol matched all synthetic reference labels in this
run. Its 161.8-byte mean compact request size is reported directly. This study
does not make a controlled like-for-like byte-reduction claim against CLX/1,
because the conditions used different request and response constructions. It
also found no latency improvement in the observed measurements; the study did
not instrument inference or relay components sufficiently to attribute cause.

### 5.5 Fresh-worker recovery

| Run | Prior benchmark conversation? | Selected tasks | Correct | Checkpoint ACK | Unknown task behavior |
|---|---|---:|---:|---|---|
| `clx21-recovery-fresh-r1` | No | 4 | 4/4 | Yes | Safely escalated `A99` |

The clean session was able to apply the documented protocol and relay audit
context without inheriting prior benchmark conversation. This is evidence of
limited handoff recoverability—not proof that arbitrary future workers will
understand the protocol.

### 5.6 Semantic-drift guard challenge

After the initial benchmark, we ran an eight-case controlled challenge to test
whether the worker would operationalize unregistered shorthand. Two registered
CLX controls were expected to return results. Six challenges used undefined
tokens, context-dependent metaphors, an unsupported protocol proposal, or an
unknown task reference; each was expected to escalate. All eight outcomes
matched the policy: 2/2 registered controls returned `RES`, and 6/6 challenges
returned `ESC`. Raw envelopes and the case-by-case table are in
`SEMANTIC_DRIFT_EXPERIMENT.md` and
`benchmark/semantic_drift_r1_results.jsonl`.

This is a protocol-enforcement result, not a demonstration that language drift
cannot occur. It tests rejection after an opaque term is presented; it does not
simulate a long-lived, open-ended agent society or independently measure human
interpretability of emergent messages.

## 6. Discussion

The useful outcome was not an autonomous “new language.” It was a narrow,
constrained communication layer with three properties:

1. **Compression:** repeated tasks could refer to a shared, local dictionary.
2. **Auditability:** the relay could deterministically reconstruct the compact
   meaning and preserve raw envelopes.
3. **Safe failure:** the worker escalated when the dictionary, checkpoint, or
   task reference was insufficient.

The benchmark supports a practical warning: a more compact protocol is not
automatically faster. CLX/1 and the early compact condition had higher observed
mean latency than plain English. CLX/2.1 reduced the size of its compact
requests, but this study did not isolate the source of wall-clock latency.

## 7. Limitations

- One worker model/provider and one two-host deployment.
- Twenty synthetic cases are too few to establish general performance.
- Expected labels are not a substitute for independent expert adjudication;
  A05 is an example of a plausible label dispute.
- Byte count and wall-clock time are only proxies for token cost and throughput.
- The relay used SSH-over-Tailscale rather than a direct, standardized A2A
  transport.
- The fresh-worker test used the same underlying model family and documented
  artifacts; it did not test cross-model or adversarial interoperability.
- The fresh-worker task subset was selected (`A01`, `A04`, `A09`, `A17`) rather
  than randomly sampled; it is a recovery demonstration, not a generalization
  estimate.
- The paper reports byte sizes, not provider token counts, and the baseline
  conditions did not use an identical prompt/template construction.
- No conclusion should be drawn about unrestricted autonomy, emergent private
  languages, or safety in production systems.

## 8. Replication guide

1. Provision two independent OpenClaw identities on separate hosts and record
   their software, model, and dependency versions in a release manifest.
2. Configure the worker gateway and relay as loopback-only services.
3. Use authenticated private transport (e.g., Tailscale plus SSH); do not
   expose the relay publicly.
4. Copy the worker charter, protocol specification, synthetic cases, relay, and
   benchmark runners from this artifact bundle.
5. Run the baseline, structured, and compact conditions with fixed cases and
   identical task semantics; pre-register or publish the exact templates.
6. Preserve every raw trial and protocol revision. Do not discard invalid runs.
7. Add deterministic tests for checkpoint and state-accounting boundaries
   before interpreting results.
8. Run a fresh-session recovery test and an unknown-task escalation test.
9. Publish model/version, transport, scope, cases, metrics, raw results,
   hashes, and all deviations from protocol.

## 9. Artifact inventory and integrity

| Artifact | Purpose |
|---|---|
| `WORKER_CHARTER.md` | Worker scope, escalation rules, and evidence requirements. |
| `CLAWLINK_PROTOCOL.md` | Protocol versions and glossary. |
| `relay/clx_relay.py` | Relay implementation and deterministic decode/checkpoint logic. |
| `relay/test_checkpoint_guard.py` | Boundary tests added after the checkpoint defect. |
| `benchmark/cases.json` | Synthetic tasks and expected labels. |
| `benchmark/clx21_full_r3_results.jsonl` | Validated 20-case result records. |
| `benchmark/clx21_full_r3_summary.json` | Validated summary. |
| `benchmark/fresh_worker_recovery_r1.jsonl` | Fresh-session recovery records. |
| `benchmark/fresh_worker_recovery_r1_summary.json` | Fresh-session recovery summary. |
| `benchmark/semantic_drift_r1_results.jsonl` | Controlled semantic-drift guard records. |
| `benchmark/semantic_drift_r1_summary.json` | Semantic-drift challenge summary. |
| `SEMANTIC_DRIFT_EXPERIMENT.md` | Drift challenge method, outcomes, and limits. |
| `benchmark/clx21_full_results_v1_checkpoint_guard_bug.jsonl` | Invalid first full run: original checkpoint defect. |
| `benchmark/clx21_full_r2_results.jsonl` | Invalid second full run: ambiguous checkpoint assertion. |
| `INTEGRITY_MANIFEST.sha256` | SHA-256 inventory for the publication bundle. |
| `EDITORIAL_LOG.md` | Review findings, disposition, and revision rationale. |
| `SANITIZATION.md` | Public-release role and path pseudonymization record. |
| `REPRODUCIBILITY.md` | Run history, invalid-run disclosure, and SHA-256 hashes. |

The manifest covers the paper, protocol, charter, test cases, runner scripts,
valid results, recovery results, and invalid-run artifacts. Verify it before
analysis with `sha256sum -c INTEGRITY_MANIFEST.sha256`.

## 10. Conclusion

Within a constrained synthetic workload, a two-agent OpenClaw deployment used
a negotiated compact protocol that was recoverable in a fresh-session test,
auditable through relay records, and able to escalate an unknown task reference.
CLX/2.1 demonstrated compact request envelopes but did not establish a causal
efficiency or latency advantage. The strongest lesson is methodological:
protocol implementations must be boundary-tested and invalid runs disclosed,
because an off-by-one guard can look like an agent-quality failure. Future work
should use larger expert-adjudicated workloads, identical condition templates,
provider token measurement, multiple models, independent replication, and
fault injection across transport and protocol versions.
