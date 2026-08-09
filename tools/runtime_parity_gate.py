#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Runtime parity gate CLI — Phase 0 MVP.

Subcommands:
  doctor          — validate testbed skeleton (G-0.1)
  record-python   — write oracle golden skeleton under golden/python/
  run             — sample cpp executor (golden/cpp/); not_sampled if no RUNTIME
  certify         — layered diff report (ok=false in MVP)

See docs/runtime-parity/testbed/README.md
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Optional, Sequence

# Allow `python tools/runtime_parity_gate.py` from repo root
_TOOLS_DIR = Path(__file__).resolve().parent
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))

from runtime_parity.certify import run_certify
from runtime_parity.doctor import run_doctor
from runtime_parity.record import run_record_python
from runtime_parity.record_oracle_smoke import run_record_oracle_smoke
from runtime_parity.run_cpp import run_cpp


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="runtime_parity_gate.py",
        description="Runtime parity testbed gate (Phase 0 MVP)",
    )
    sp = p.add_subparsers(dest="command", required=True)

    dp = sp.add_parser("doctor", help="Check manifest, thresholds, directories")
    dp.add_argument(
        "--strict-golden",
        action="store_true",
        help="Fail if golden/python has status=placeholder (G-0.3)",
    )

    rp = sp.add_parser("record-python", help="Record python oracle golden (MVP skeleton)")
    rp.add_argument("--case", required=True, help="Case id from manifest.json")

    ros = sp.add_parser(
        "record-oracle-smoke",
        help="Write non-placeholder python golden via local media smoke path",
    )
    ros.add_argument(
        "--case",
        default=None,
        help="Case id (default: all P0 cases in manifest)",
    )
    ros.add_argument(
        "--engine",
        default="auto",
        choices=["auto", "onnx", "ultralytics"],
        help="Detection engine for smoke golden (onnx aligns with cpp RUNTIME)",
    )

    runp = sp.add_parser("run", help="Run candidate executor sampling")
    runp.add_argument("--executor", choices=["cpp"], required=True)
    runp.add_argument("--case", required=True)

    cp = sp.add_parser("certify", help="Layered diff python vs cpp")
    cp.add_argument("--case", default=None, help="Single case (default: profile P0 set)")
    cp.add_argument(
        "--profile",
        default=None,
        choices=["linux_full", "win_default", "win_cpp"],
        help="Certify all cases in profile filter",
    )
    return p


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "doctor":
        return run_doctor(strict_golden=args.strict_golden)
    if args.command == "record-python":
        return run_record_python(args.case)
    if args.command == "record-oracle-smoke":
        return run_record_oracle_smoke(args.case, engine=args.engine)
    if args.command == "run":
        if args.executor != "cpp":
            print("Only --executor cpp is supported in Phase 0", file=sys.stderr)
            return 2
        return run_cpp(args.case)
    if args.command == "certify":
        return run_certify(case_id=args.case, profile=args.profile)
    return 2


if __name__ == "__main__":
    sys.exit(main())
