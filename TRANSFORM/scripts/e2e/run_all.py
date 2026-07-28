#!/usr/bin/env python3
"""一键跑 TRANSFORM e2e：mock 接收端 + 01/02/03。

前置：Kafka、PostgreSQL、transform-runtime 已启动。
"""

from __future__ import annotations

import argparse
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent
PY = sys.executable


def wait_url(url: str, timeout: float = 30.0) -> None:
    deadline = time.time() + timeout
    last = None
    while time.time() < deadline:
        try:
            r = requests.get(url, timeout=2)
            if r.status_code < 500:
                return
            last = r.status_code
        except Exception as e:
            last = e
        time.sleep(0.5)
    raise RuntimeError(f"等待超时 {url}: {last}")


def run_step(script: str, extra: list[str] | None = None) -> None:
    cmd = [PY, str(ROOT / script), *(extra or [])]
    print(f"\n>>> {' '.join(cmd)}", flush=True)
    subprocess.check_call(cmd, cwd=str(ROOT))


def main() -> int:
    ap = argparse.ArgumentParser(description="TRANSFORM e2e 一键运行")
    ap.add_argument("--skip-mock", action="store_true", help="不自动启 mock（已手动启动时用）")
    ap.add_argument("--expect-members", type=int, default=1)
    ap.add_argument("--batch", type=int, default=20)
    ap.add_argument("--api", default=os.getenv("TRANSFORM_API", "http://127.0.0.1:48096"))
    ap.add_argument("--kafka", default=os.getenv("KAFKA_BOOTSTRAP", "127.0.0.1:9092"))
    ap.add_argument("--receiver-port", type=int, default=int(os.getenv("RECEIVER_PORT", "18080")))
    args = ap.parse_args()

    mock_proc = None
    try:
        if not args.skip_mock:
            mock_proc = subprocess.Popen(
                [PY, str(ROOT / "mock_receiver.py"), "--port", str(args.receiver_port)],
                cwd=str(ROOT),
            )
            wait_url(f"http://127.0.0.1:{args.receiver_port}/health")
            print(f"mock receiver pid={mock_proc.pid}", flush=True)

        wait_url(f"{args.api.rstrip('/')}/transform/overview")
        common = ["--api", args.api, "--kafka", args.kafka]
        run_step("01_channels.py", common)
        run_step(
            "02_horizontal_scale.py",
            common + ["--expect-members", str(args.expect_members), "--batch", str(args.batch)],
        )
        run_step("03_self_heal.py", common)
        print("\n=== ALL PASS ===", flush=True)
        return 0
    except Exception as e:
        print(f"\n=== FAIL: {e} ===", flush=True)
        return 1
    finally:
        if mock_proc and mock_proc.poll() is None:
            mock_proc.send_signal(signal.SIGTERM)
            try:
                mock_proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                mock_proc.kill()


if __name__ == "__main__":
    sys.exit(main())
