#!/usr/bin/env python3
"""Run the repaired CLX/2.1 20-case benchmark with audited checkpoints."""
from __future__ import annotations

import json
import os
import re
import time
import urllib.request
from pathlib import Path

ROOT = Path(os.environ.get('CLX_ROOT', Path(__file__).resolve().parents[1]))
CASES = json.loads((ROOT / 'benchmark/cases.json').read_text())
OUT = ROOT / 'benchmark/clx21_full_r3_results.jsonl'
SUMMARY = ROOT / 'benchmark/clx21_full_r3_summary.json'
RUN = 'clx21-full-20-r3'
CODE = {'benign': 'B', 'suspicious': 'S', 'malicious': 'M'}


def post(envelope: dict) -> tuple[dict, int, int, float]:
    data = json.dumps(envelope, separators=(',', ':')).encode()
    started = time.monotonic()
    request = urllib.request.Request(
        'http://127.0.0.1:19101/v1/messages', data=data,
        headers={'Content-Type': 'application/json'},
    )
    raw = urllib.request.urlopen(request, timeout=190).read().decode()
    return json.loads(raw), len(data), len(raw), round(time.monotonic() - started, 2)


def save(row: dict) -> None:
    with OUT.open('a') as handle:
        handle.write(json.dumps(row, ensure_ascii=False) + '\n')
        handle.flush()
        os.fsync(handle.fileno())


OUT.unlink(missing_ok=True)
number = 1
proposal = {
    'v': 'CLX/1', 'r': RUN, 'n': number, 'f': 'coordinator', 't': 'worker',
    'k': 'PRP', 'q': 'open', 'c': 0.97,
    'p': 'G=adopt repaired CLX/2.1 for 20 approved cases;A=use task references and checkpoint after four completed exchanges;O=ACK or ESC;N=begin only after ACK',
    'x': 'Proposal: apply the documented repaired CLX/2.1 dictionary to the 20 approved benchmark cases. Routine compact messages omit English only for approved tasks. A full-English checkpoint occurs after every four completed compact task-response exchanges; the relay retains deterministic decoding. Acknowledge only if this remains safe and auditable.',
    'e': ['CLAWLINK_PROTOCOL.md', 'benchmark/cases.json'],
}
response, bytes_in, bytes_out, elapsed = post(proposal)
save({'type': 'proposal', 'request': proposal, 'response': response,
      'bytes_in': bytes_in, 'bytes_out': bytes_out, 'elapsed_s': elapsed})
if response.get('k') != 'ACK':
    raise SystemExit('proposal not acknowledged')

number = 3
for index, case in enumerate(CASES, 1):
    task = {
        'v': 'CLX/2', 'r': RUN, 'n': number, 'f': 'coordinator', 't': 'worker',
        'k': 'ASK', 'q': 'open', 'c': 0.95,
        'p': f"T={case['id']};G=C;I=F;O=C/E/U/N", 'e': ['benchmark/cases.json'],
    }
    response, bytes_in, bytes_out, elapsed = post(task)
    match = re.search(r'(?:^|;)C=([BSM])(?:;|$)', response.get('p', ''))
    got = match.group(1) if match else None
    save({'type': 'task', 'id': case['id'], 'expected': CODE[case['expected']],
          'got': got, 'ok': got == CODE[case['expected']], 'request': task,
          'response': response, 'bytes_in': bytes_in, 'bytes_out': bytes_out,
          'elapsed_s': elapsed})
    number += 2
    if index % 4 == 0 and index < len(CASES):
        checkpoint = {
            'v': 'CLX/2', 'r': RUN, 'n': number, 'f': 'coordinator', 't': 'worker',
            'k': 'CHK', 'q': 'done', 'c': 1.0,
            'p': f"F=tasks through {case['id']} completed;N=resume next approved task",
            'x': f"Checkpoint: compact tasks through {case['id']} completed. The audit log contains the decoded records. Resume the next approved benchmark task under CLX/2.1.",
            'e': ['relay/logs/messages.jsonl', 'benchmark/cases.json'],
        }
        response, bytes_in, bytes_out, elapsed = post(checkpoint)
        save({'type': 'checkpoint', 'request': checkpoint, 'response': response,
              'bytes_in': bytes_in, 'bytes_out': bytes_out, 'elapsed_s': elapsed})
        number += 2

rows = [json.loads(line) for line in OUT.read_text().splitlines()]
tasks = [row for row in rows if row['type'] == 'task']
SUMMARY.write_text(json.dumps({
    'run': RUN, 'tasks': len(tasks), 'correct': sum(row['ok'] for row in tasks),
    'checkpoints': sum(row['type'] == 'checkpoint' for row in rows),
    'mean_elapsed_s': round(sum(row['elapsed_s'] for row in tasks) / len(tasks), 2),
    'mean_bytes_in': round(sum(row['bytes_in'] for row in tasks) / len(tasks), 1),
    'mean_bytes_out': round(sum(row['bytes_out'] for row in tasks) / len(tasks), 1),
}, indent=2) + '\n')
