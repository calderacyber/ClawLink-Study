# Public-release sanitization

This public bundle is named **ClawLink Study**. It replaces internal labels and
machine-specific paths with the following generic terms:

| Public label | Meaning |
|---|---|
| `coordinator` | The primary agent role that dispatches bounded work. |
| `worker` | The independently hosted worker-agent role. |
| `CLX_ROOT` | Environment variable pointing to the local study-bundle root. |

The transformation removed personal names, organization names, local account
names, internal host paths, and host-specific service paths. It did not change
benchmark task IDs, labels, classifications, timestamps, latency values, byte
counts, protocol semantics, or test outcomes.

For deployment, set `CLX_ROOT`, `CLX_OPENCLAW`, `CLX_WORKER_AGENT_ID`,
`CLX_MODEL`, and—only where required—`CLX_USER_BIN` and
`CLX_XDG_RUNTIME_DIR` in the local environment. Never publish credentials,
private keys, gateway tokens, host addresses, or provider authorization data.
