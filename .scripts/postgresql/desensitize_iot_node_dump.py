#!/usr/bin/env python3
"""脱敏 iot-node pg_dump，生成可提交的样例 SQL（iot-node10.sql -> iot-node20）。"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

IP_MAP = {
    "172.16.13.220": "192.168.1.10",
    "10.200.212.54": "192.168.1.11",
    "10.200.212.51": "192.168.1.12",
}

HOSTNAME_MAP = {
    "172.16.13.220": "192.168.1.10",
    "10.200.212.54": "192.168.1.11",
    "10.200.212.51": "192.168.1.12",
}

NODE_NAME_MAP = {
    "Ceph-Storage-54": "NFS-Storage-01",
    "Ceph-Client-51": "NFS-Client-01",
}

DEMO_SSH_CRED = "ZGVtb19zc2hfcGFzc3dvcmQ="  # demo_ssh_password
DEMO_SSH_USER = "demo"

METRIC_KEEP = 30
STORAGE_LOG_KEEP = 20

COPY_HEADER = re.compile(r"^COPY public\.(\w+) \((.+)\) FROM stdin;\s*$")


def demo_token(node_id: str) -> str:
    digest = hashlib.md5(f"easyaiot-demo-node-{node_id}".encode()).hexdigest()
    return digest


def replace_ips(text: str) -> str:
    out = text
    for src, dst in IP_MAP.items():
        out = out.replace(src, dst)
    out = out.replace(":60022", ":22")
    return out


def scrub_json_ips(raw: str) -> str:
    if raw in ("\\N", "", "null"):
        return raw
    try:
        obj = json.loads(raw)
    except json.JSONDecodeError:
        return replace_ips(raw)

    def walk(value):
        if isinstance(value, dict):
            return {k: walk(v) for k, v in value.items()}
        if isinstance(value, list):
            return [walk(v) for v in value]
        if isinstance(value, str):
            v = replace_ips(value)
            if v in HOSTNAME_MAP:
                return HOSTNAME_MAP[v]
            if v == "ubuntu":
                return "demo-node"
            return v
        return value

    return json.dumps(walk(obj), ensure_ascii=False, separators=(",", ": "))


def process_compute_node(line: str) -> str:
    parts = line.split("\t")
    if len(parts) < 14:
        return replace_ips(line)
    node_id = parts[0]
    parts[1] = NODE_NAME_MAP.get(parts[1], parts[1])
    parts[2] = IP_MAP.get(parts[2], replace_ips(parts[2]))
    if parts[3] not in ("\\N", ""):
        parts[3] = "22"
    parts[13] = demo_token(node_id)
    if len(parts) > 8 and parts[8] not in ("\\N", ""):
        parts[8] = scrub_json_ips(parts[8])
    if len(parts) > 14 and parts[14] not in ("\\N", ""):
        parts[14] = replace_ips(parts[14])
    return "\t".join(parts)


def process_control_plane_peer(line: str) -> str:
    parts = line.split("\t")
    if len(parts) < 5:
        return replace_ips(line)
    parts[2] = replace_ips(parts[2])
    parts[3] = IP_MAP.get(parts[3], replace_ips(parts[3])) if parts[3] not in ("\\N", "") else parts[3]
    parts[4] = demo_token(parts[0]) if parts[4] not in ("\\N", "") else parts[4]
    return "\t".join(parts)


def process_node_ssh_credential(line: str) -> str:
    parts = line.split("\t")
    if len(parts) < 5:
        return line
    parts[3] = DEMO_SSH_USER
    parts[4] = DEMO_SSH_CRED
    if len(parts) > 5:
        parts[5] = "\\N"
    return "\t".join(parts)


def process_edge_node(line: str) -> str:
    parts = line.split("\t")
    if len(parts) < 4:
        return replace_ips(line)
    parts[2] = replace_ips(parts[2])
    parts[3] = IP_MAP.get(parts[3], replace_ips(parts[3])) if parts[3] not in ("\\N", "") else parts[3]
    if len(parts) > 6 and parts[6] not in ("\\N", ""):
        parts[6] = f"demo-mqtt-{parts[0]}"
    if len(parts) > 7 and parts[7] not in ("\\N", ""):
        parts[7] = DEMO_SSH_USER
    if len(parts) > 16 and parts[16] not in ("\\N", ""):
        parts[16] = scrub_json_ips(parts[16])
    return "\t".join(parts)


def process_device_media_binding(line: str) -> str:
    return replace_ips(line)


def process_storage_op_log(line: str) -> str:
    return replace_ips(line)


def trim_rows(lines: list[str], keep: int) -> list[str]:
    if len(lines) <= keep:
        return lines
    return lines[-keep:]


def transform_copy_block(table: str, rows: list[str]) -> list[str]:
    if not rows:
        return rows

    if table == "node_metric_snapshot":
        rows = trim_rows(rows, METRIC_KEEP)
    elif table == "node_storage_op_log":
        rows = trim_rows(rows, STORAGE_LOG_KEEP)

    out: list[str] = []
    for row in rows:
        if table == "compute_node":
            out.append(process_compute_node(row))
        elif table == "control_plane_peer":
            out.append(process_control_plane_peer(row))
        elif table == "node_ssh_credential":
            out.append(process_node_ssh_credential(row))
        elif table == "edge_node":
            out.append(process_edge_node(row))
        elif table == "device_media_binding":
            out.append(process_device_media_binding(row))
        elif table == "node_storage_op_log":
            out.append(process_storage_op_log(row))
        else:
            out.append(replace_ips(row))
    return out


def desensitize_dump(text: str) -> str:
    lines = text.splitlines()
    result: list[str] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        m = COPY_HEADER.match(line)
        if not m:
            result.append(replace_ips(line))
            i += 1
            continue

        table = m.group(1)
        result.append(line)
        i += 1
        rows: list[str] = []
        while i < len(lines):
            if lines[i] == "\\.":
                break
            if lines[i].strip():
                rows.append(lines[i])
            i += 1

        for row in transform_copy_block(table, rows):
            result.append(row)

        if i < len(lines) and lines[i] == "\\.":
            result.append("\\.")
            i += 1
        else:
            result.append("\\.")
        if i < len(lines) and lines[i] == "":
            result.append("")
            i += 1

    return "\n".join(result) + ("\n" if text.endswith("\n") else "")


def main() -> int:
    parser = argparse.ArgumentParser(description="Desensitize iot-node pg_dump SQL")
    parser.add_argument("input", type=Path, help="raw pg_dump sql")
    parser.add_argument("-o", "--output", type=Path, required=True, help="output sql path")
    args = parser.parse_args()

    raw = args.input.read_text(encoding="utf-8", errors="replace")
    cleaned = desensitize_dump(raw)
    args.output.write_text(cleaned, encoding="utf-8")
    print(f"Wrote desensitized dump: {args.output} ({args.output.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
