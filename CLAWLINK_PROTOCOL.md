# ClawLink Protocol (CLX/1)

CLX/1 is a compact, versioned experiment protocol. It is compression, not a
private language: every message carries a human-readable canonical expansion.

## Envelope

Each relay record is JSONL:

```json
{"v":"CLX/1","r":"run-id","n":1,"f":"coordinator","t":"worker","k":"ASK","q":"open","c":0.95,"p":"G=...;A=...;O=...;N=...","x":"Plain-English canonical expansion.","e":["artifact-or-source"],"ts":"RFC3339"}
```

| Field | Meaning |
|---|---|
| `v` | protocol version |
| `r`, `n` | run ID and monotonically increasing sequence |
| `f`, `t` | sender and recipient identity |
| `k` | message kind |
| `q` | state |
| `c` | calibrated confidence from `0.00` to `1.00` |
| `p` | compressed payload using the grammar below |
| `x` | complete English rendering of `p` |
| `e` | evidence/artifact references, never secret values |

## Kinds

`ASK` assignment · `ACK` receipt · `EVD` evidence · `RES` result · `ESC`
escalation · `PRP` protocol proposal · `CHK` checkpoint · `STOP` stop.

## States

`open` · `active` · `blocked` · `done` · `rejected`.

## Payload grammar

Payload clauses are separated by semicolons. Values may not contain semicolons.

`G` goal · `A` action · `F` finding · `O` output · `E` evidence summary ·
`U` uncertainty · `N` next action · `Q` question · `B` blocker · `R` risk.

Example:

```text
G=classify alert A-03;A=compare indicators against task facts;F=benign admin activity;E=src=case/A-03.json;U=no host telemetry;N=request process tree
```

Canonical English expansion:

```text
Classify alert A-03. I compared its indicators against the supplied task facts.
My preliminary finding is benign administrative activity, supported by
case/A-03.json. I lack host telemetry, so request the process tree next.
```

## Evolution and safety

- Any new shorthand requires a `PRP` record containing its definition, an
  example, and an English decoder.
- It takes effect only after an explicit `ACK` from the other agent.
- A fresh worker must be able to continue from the log and glossary alone.
- `ESC` and `STOP` are always written in ordinary English as well as CLX/1.

## CLX/2 pilot: negotiated task references

CLX/2 is a narrow compression experiment for repeated, local benchmark work.
It is valid only after a `CLX/1 PRP` receives a worker-generated `ACK`.

Routine CLX/2.1 envelopes omit `x` only when all of these conditions hold:

1. The task is in the approved local task library.
2. Both agents acknowledged this dictionary for the current run.
3. The relay writes its deterministic dictionary decoding to the append-only
   audit log.
4. A full-English `CHK` is exchanged after at most four completed compact
   task-response exchanges, and every
   `ESC` or `STOP` remains full English.

CLX/2 dictionary for this pilot:

| Code | Meaning |
|---|---|
| `T=A01` | Task A01 in `benchmark/cases.json` |
| `G=C` | Goal: classify |
| `I=F` | Input: task facts only |
| `O=C/E/U/N` | Output: classification, evidence, uncertainty, next action |
| `C=B|S|M` | Classification: benign, suspicious, or malicious |
| `E=...`, `U=...`, `N=...` | Evidence, uncertainty, and next action |

Example task payload: `T=A01;G=C;I=F;O=C/E/U/N`.

The relay retains the outer identity, run, confidence, kind, state, and
evidence fields. The dictionary is not authority: task scope and the worker
charter still govern every action.

The four-task cadence is an empirical safety amendment: the initial pilot
showed the worker conservatively refusing a fifth compact task until it could
verify a checkpoint. Any change to this cadence requires a new `PRP`/`ACK`.
