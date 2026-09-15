#!/usr/bin/env python3
"""Run the negotiated CLX/2.1 20-case benchmark with checkpoints."""
from __future__ import annotations
import json, os, re, time, urllib.request
from pathlib import Path

ROOT = Path(os.environ.get('CLX_ROOT', Path(__file__).resolve().parents[1]))
CASES = json.loads((ROOT / 'benchmark/cases.json').read_text())
OUT = ROOT / 'benchmark/clx21_full_r2_results.jsonl'
SUMMARY = ROOT / 'benchmark/clx21_full_r2_summary.json'
RUN = 'clx21-full-20-r2'
CODE = {'benign':'B','suspicious':'S','malicious':'M'}

def post(envelope):
    data=json.dumps(envelope,separators=(',',':')).encode(); start=time.monotonic()
    req=urllib.request.Request('http://127.0.0.1:19101/v1/messages',data=data,headers={'Content-Type':'application/json'})
    raw=urllib.request.urlopen(req,timeout=190).read().decode()
    return json.loads(raw), len(data), len(raw), round(time.monotonic()-start,2)

def save(row):
    with OUT.open('a') as f:
        f.write(json.dumps(row,ensure_ascii=False)+'\n'); f.flush(); os.fsync(f.fileno())

OUT.unlink(missing_ok=True)
n=1
proposal={"v":"CLX/1","r":RUN,"n":n,"f":"coordinator","t":"worker","k":"PRP","q":"open","c":0.97,
          "p":"G=adopt CLX/2.1 for 20 approved cases;A=use task references and checkpoint after four tasks;O=ACK or ESC;N=begin only after ACK",
          "x":"Proposal: apply the documented CLX/2.1 dictionary to the 20 approved benchmark cases. Routine compact messages omit English only for approved tasks. A full-English checkpoint occurs after every four compact tasks; the relay retains deterministic decoding. Acknowledge only if this remains safe and auditable.",
          "e":["CLAWLINK_PROTOCOL.md","benchmark/cases.json"]}
response, bi, bo, elapsed=post(proposal); save({'type':'proposal','request':proposal,'response':response,'bytes_in':bi,'bytes_out':bo,'elapsed_s':elapsed})
if response.get('k')!='ACK': raise SystemExit('proposal not acknowledged')
n=3
for index, case in enumerate(CASES,1):
    task={"v":"CLX/2","r":RUN,"n":n,"f":"coordinator","t":"worker","k":"ASK","q":"open","c":0.95,
          "p":f"T={case['id']};G=C;I=F;O=C/E/U/N","e":["benchmark/cases.json"]}
    response, bi, bo, elapsed=post(task)
    match=re.search(r'(?:^|;)C=([BSM])(?:;|$)',response.get('p',''))
    got=match.group(1) if match else None
    save({'type':'task','id':case['id'],'expected':CODE[case['expected']],'got':got,'ok':got==CODE[case['expected']],
          'request':task,'response':response,'bytes_in':bi,'bytes_out':bo,'elapsed_s':elapsed})
    n += 2
    if index % 4 == 0 and index < len(CASES):
        checkpoint={"v":"CLX/2","r":RUN,"n":n,"f":"coordinator","t":"worker","k":"CHK","q":"done","c":1.0,
                    "p":f"F=tasks through {case['id']} completed;N=resume next approved task",
                    "x":f"Checkpoint: compact tasks through {case['id']} completed. The audit log contains the decoded records. Resume the next approved benchmark task under CLX/2.1.",
                    "e":["relay/logs/messages.jsonl","benchmark/cases.json"]}
        response, bi, bo, elapsed=post(checkpoint)
        save({'type':'checkpoint','request':checkpoint,'response':response,'bytes_in':bi,'bytes_out':bo,'elapsed_s':elapsed})
        n += 2

rows=[json.loads(x) for x in OUT.read_text().splitlines()]
tasks=[x for x in rows if x['type']=='task']
SUMMARY.write_text(json.dumps({'run':RUN,'tasks':len(tasks),'correct':sum(x['ok'] for x in tasks),'checkpoints':sum(x['type']=='checkpoint' for x in rows),'mean_elapsed_s':round(sum(x['elapsed_s'] for x in tasks)/len(tasks),2),'mean_bytes_in':round(sum(x['bytes_in'] for x in tasks)/len(tasks),1),'mean_bytes_out':round(sum(x['bytes_out'] for x in tasks)/len(tasks),1)},indent=2)+'\n')
