#!/usr/bin/env python3
"""Run a reproducible A/B/C CLX benchmark against Worker Agent."""
from __future__ import annotations

import json
import os
import re
import subprocess
import time
import urllib.request
from pathlib import Path

ROOT = Path(os.environ.get('CLX_ROOT', Path(__file__).resolve().parents[1]))
CASES = json.loads((ROOT / 'benchmark/cases.json').read_text())
OUT = ROOT / 'benchmark/results.jsonl'
OPENCLAW = os.environ.get('CLX_OPENCLAW', 'openclaw')
WORKER_AGENT_ID = os.environ.get('CLX_WORKER_AGENT_ID', 'worker')
MODEL = os.environ.get('CLX_MODEL', 'openai/gpt-5.6-sol')
USER_BIN = os.environ.get('CLX_USER_BIN', '')

def record(item):
    with OUT.open('a') as f:
        f.write(json.dumps(item, ensure_ascii=False) + '\n')
        f.flush(); os.fsync(f.fileno())

def grade(text, expected):
    matches = re.findall(r'\b(benign|suspicious|malicious)\b', text.lower())
    return bool(matches) and matches[0] == expected, matches[0] if matches else None

def baseline(case):
    facts = '\n'.join('- ' + x for x in case['facts'])
    prompt = ('Classify this synthetic security alert using only supplied facts. '
              'Choose exactly one label: benign, suspicious, or malicious. '
              'Start your response with CLASS=<label>; then a one-sentence rationale.\n' + facts)
    env = os.environ.copy()
    if USER_BIN:
        env['PATH'] = USER_BIN + ':' + env['PATH']
    if os.environ.get('CLX_XDG_RUNTIME_DIR'):
        env['XDG_RUNTIME_DIR'] = os.environ['CLX_XDG_RUNTIME_DIR']
    start = time.monotonic()
    p = subprocess.run([OPENCLAW, 'agent', '--agent', WORKER_AGENT_ID, '--model', MODEL, '-m', prompt], text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=180, env=env)
    text = p.stdout if not p.returncode else p.stderr
    ok, got = grade(text, case['expected'])
    return {'mode':'plain','elapsed_s':round(time.monotonic()-start,2),'ok':ok,'got':got,'bytes_out':len(text.encode()),'raw':text.strip()}

def relay(case, mode):
    facts = ' '.join(case['facts'])
    if mode == 'clx1':
        payload = f'G=classify {case["id"]};A=use supplied facts only;O=classification rationale uncertainty;N=return result'
    else:
        payload = f'T={case["id"]};G=C;S=F1..F3;O=C/R/U/N'
    english = ('Classify this synthetic alert using only these facts. In the CLX response, put the label '
               'benign, suspicious, or malicious first in the F clause. Facts: ' + facts)
    envelope = {'v':'CLX/1','r':f'bench-{mode}-{case["id"]}','n':1,'f':'coordinator','t':'worker','k':'ASK','q':'open','c':0.95,'p':payload,'x':english,'e':[f'benchmark/{case["id"]}']}
    data = json.dumps(envelope).encode(); start = time.monotonic()
    req = urllib.request.Request('http://127.0.0.1:19101/v1/messages', data=data, headers={'Content-Type':'application/json'})
    with urllib.request.urlopen(req, timeout=190) as response:
        text = response.read().decode()
    ok, got = grade(text, case['expected'])
    return {'mode':mode,'elapsed_s':round(time.monotonic()-start,2),'ok':ok,'got':got,'bytes_in':len(data),'bytes_out':len(text.encode()),'raw':text}

for case in CASES:
    for mode in ('plain','clx1','clxdelta'):
        try:
            result = baseline(case) if mode == 'plain' else relay(case, mode)
            record({'case':case['id'],'expected':case['expected'],**result})
        except Exception as exc:
            record({'case':case['id'],'expected':case['expected'],'mode':mode,'ok':False,'error':str(exc)})

records = [json.loads(line) for line in OUT.read_text().splitlines()]
summary = {}
for mode in ('plain','clx1','clxdelta'):
    rows = [r for r in records if r['mode'] == mode]
    summary[mode] = {'trials':len(rows),'correct':sum(bool(r.get('ok')) for r in rows),'errors':sum('error' in r for r in rows),'mean_elapsed_s':round(sum(r.get('elapsed_s',0) for r in rows)/max(1,len(rows)),2),'mean_bytes_out':round(sum(r.get('bytes_out',0) for r in rows)/max(1,len(rows)),1)}
(ROOT / 'benchmark/summary.json').write_text(json.dumps(summary, indent=2) + '\n')
