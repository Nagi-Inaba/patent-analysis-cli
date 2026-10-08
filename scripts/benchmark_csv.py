"""Measure fresh-process CSV time/peak RSS using generated, bounded local fixtures."""

from __future__ import annotations

import argparse
import ctypes
import hashlib
import json
import platform
import subprocess
import sys
import time
from pathlib import Path

CASES = {"rows": (100_000, 2), "cells": (99_999, 20), "wide": (1_999, 1_000),
         "bytes": (100_000, 2), "unicode": (100_000, 2)}
OPERATIONS = ("inspect", "ranking", "composition")


def peak_rss_bytes():
    if sys.platform == "win32":
        from ctypes import wintypes

        class Counters(ctypes.Structure):
            _fields_ = [("cb", wintypes.DWORD), ("faults", wintypes.DWORD)] + [
                (name, ctypes.c_size_t) for name in
                ("peak_working_set", "working_set", "peak_paged", "paged",
                 "peak_nonpaged", "nonpaged", "pagefile", "peak_pagefile", "private")]

        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel.GetCurrentProcess.restype = wintypes.HANDLE
        kernel.K32GetProcessMemoryInfo.argtypes = [
            wintypes.HANDLE, ctypes.POINTER(Counters), wintypes.DWORD]
        kernel.K32GetProcessMemoryInfo.restype = wintypes.BOOL
        counters = Counters()
        counters.cb = ctypes.sizeof(counters)
        if not kernel.K32GetProcessMemoryInfo(
                kernel.GetCurrentProcess(), ctypes.byref(counters), counters.cb):
            raise ctypes.WinError(ctypes.get_last_error())
        return counters.peak_working_set
    import resource
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return peak if sys.platform == "darwin" else peak * 1024


def measure(source, operation, rows, columns):
    from patent_analysis import api

    if operation == "ranking":
        spec = {"analysis_type": "ranking", "dimension": "group",
                "measure": {"mode": "count", "column": None}, "top_n": 20,
                "include_other": True, "multi_value_mode": "all"}
    else:
        spec = {"analysis_contract_version": "2.0.0", "analysis_id": "composition.v1",
                "normalization": {"profiles": []},
                "resolution": {"bindings": {"group": "group"}},
                "population": {"filters": [], "selection_sets": [], "family_mode": "records"},
                "parameters": {"role": "group"}}
    started = time.perf_counter()
    if operation == "inspect":
        result = api.inspect_dataset(source, allowed_root=source.parent)
        assert result["dataset"]["row_count"] == rows
        assert result["dataset"]["column_count"] == columns
    else:
        result = api.run_analysis_csv(source, json.dumps(spec).encode(), allowed_root=source.parent)
        if operation == "composition":
            assert [(x["label"], x["value"]) for x in result["data"]["items"]] == [("A", rows)]
        else:
            assert [(x["label"], x["value"]) for x in result["result"]["rows"]] == [("A", rows)]
    elapsed = time.perf_counter() - started
    return {"operation": operation, "seconds": round(elapsed, 6),
            "peak_rss_bytes": peak_rss_bytes(), "golden_passed": True}


def fixture(root, case):
    rows, columns = CASES[case]
    path = root / f"{case}.csv"
    header = (",".join(["group"] + [f"payload{i}" for i in range(columns - 1)]) + "\n").encode()
    digest = hashlib.sha256()
    target = 300 * 1024 * 1024
    width, remainder = divmod(target - len(header), rows)
    with path.open("xb") as stream:
        stream.write(header)
        digest.update(header)
        for index in range(rows):
            if case in {"bytes", "unicode"}:
                size = width + (index < remainder) - 3
                payload = (b"X" * size if case == "bytes" else
                           "特".encode() * (size // 3) + b"X" * (size % 3))
                row = b"A," + payload + b"\n"
            else:
                row = ("A," + ",".join([f"{index:06}"] * (columns - 1)) + "\n").encode()
            stream.write(row)
            digest.update(row)
    assert path.stat().st_size <= target
    return path, {"case": case, "rows": rows, "columns": columns,
                  "bytes": path.stat().st_size, "sha256": digest.hexdigest()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, required=True,
                        help="New directory for generated fixtures; never reuse existing data")
    parser.add_argument("--cases", nargs="+", choices=CASES, default=list(CASES))
    parser.add_argument("--repeat", type=int, choices=range(1, 11), default=1)
    parser.add_argument("--measure", choices=OPERATIONS, help=argparse.SUPPRESS)
    parser.add_argument("--case", choices=CASES, help=argparse.SUPPRESS)
    args = parser.parse_args()
    root = args.workspace.resolve()
    if args.measure:
        rows, columns = CASES[args.case]
        print(json.dumps(measure(root / f"{args.case}.csv", args.measure, rows, columns)))
        return
    root.mkdir()
    print(json.dumps({"python": platform.python_version(), "platform": platform.platform(),
                      "machine": platform.machine(), "repeat": args.repeat}), flush=True)
    for case in args.cases:
        path, metadata = fixture(root, case)
        for operation in OPERATIONS:
            for repetition in range(args.repeat):
                completed = subprocess.run(
                    [sys.executable, str(Path(__file__).resolve()), "--workspace", str(root),
                     "--measure", operation, "--case", case],
                    capture_output=True, text=True, encoding="utf-8", timeout=600, check=True)
                result = {**metadata, "repetition": repetition + 1, **json.loads(completed.stdout)}
                print(json.dumps(result), flush=True)
        with path.open("rb") as stream:
            assert hashlib.file_digest(stream, "sha256").hexdigest() == metadata["sha256"]


if __name__ == "__main__":
    main()
