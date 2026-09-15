# ClawLink Study

**Primary researcher:** Rick Myers  
**Affiliation and copyright holder:** Caldera Cybersecurity Services

This public-release workspace is isolated from operational agent state. It
contains only the worker scope, protocol glossary, synthetic test tasks, and
sanitized experiment artifacts.

## Package contents

- `ClawLink_Study_Case_Study.md` and `.docx`: the case study.
- `benchmark/cases.json`: the canonical 20-case machine-readable workload.
- `tasks/A01.json` through `tasks/A20.json`: individual human-readable views
  of the same canonical cases.
- `relay/`: the loopback-only relay implementation and boundary test.
- `INTEGRITY_MANIFEST.sha256`: file-integrity verification manifest.
- `SANITIZATION.md`: public-release pseudonymization and deployment guidance.

Initial trial:

1. Run the task in plain English.
2. Repeat it in CLX/1.
3. Compare correctness, handoff completeness, message size, and human ability
   to reconstruct the decision.

No agent-to-agent protocol is valid if it omits its English expansion or its
evidence references.

## Licensing

- Original code: [Apache License 2.0](LICENSE)
- Paper, documentation, and synthetic benchmark data: [CC BY 4.0](LICENSE-PAPER-DATA.md)
- Attribution, exclusions, and third-party notices: [NOTICE](NOTICE)

## Public-release configuration

See [SANITIZATION.md](SANITIZATION.md) for the generic role labels and the
environment variables required to run this bundle without restoring internal
accounts, paths, credentials, or host identifiers.

## Verify before use

```bash
sha256sum -c INTEGRITY_MANIFEST.sha256
python3 relay/test_checkpoint_guard.py
```

Do not commit provider credentials, SSH keys, gateway tokens, or live relay
logs. The `.gitignore` file blocks common accidental additions but is not a
substitute for review before pushing.
