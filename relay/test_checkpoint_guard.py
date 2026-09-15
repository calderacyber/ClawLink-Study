#!/usr/bin/env python3
"""Deterministic boundary tests for the CLX/2.1 checkpoint guard."""
import importlib.util
import json
import tempfile
from pathlib import Path

MODULE = Path(__file__).with_name("clx_relay.py")
SPEC = importlib.util.spec_from_file_location("relay", MODULE)
relay = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(relay)

RUN = "checkpoint-unit"


def envelope(kind: str, number: int, **extra: object) -> dict:
    return {"v": "CLX/2", "r": RUN, "n": number, "k": kind, **extra}


def record(handle, item: dict) -> None:
    handle.write(json.dumps({"envelope": item}) + "\n")


with tempfile.TemporaryDirectory() as directory:
    log = Path(directory) / "messages.jsonl"
    with log.open("w") as handle:
        # Four successful initial exchanges fill the first cadence window.
        for number in (1, 3, 5, 7):
            record(handle, envelope("ASK", number))
            record(handle, envelope("RES", number + 1))
    candidate = envelope("ASK", 9)
    assert relay.completed_compact_tasks(candidate, log) == 4

    with log.open("a") as handle:
        # A checkpoint resets the count. Three successful exchanges are allowed.
        record(handle, envelope("CHK", 9, x="English checkpoint"))
        for number in (11, 13, 15):
            record(handle, envelope("ASK", number))
            record(handle, envelope("RES", number + 1))
        # A failed/blocked attempt does not consume a compact slot.
        record(handle, envelope("ASK", 17))
        record(handle, envelope("ESC", 18, x="blocked"))
    assert relay.completed_compact_tasks(candidate, log) == 3

    with log.open("a") as handle:
        record(handle, envelope("ASK", 19))
        record(handle, envelope("RES", 20))
    assert relay.completed_compact_tasks(candidate, log) == 4

print("checkpoint guard boundary tests passed")
