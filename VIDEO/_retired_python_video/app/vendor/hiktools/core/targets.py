from __future__ import annotations

import ipaddress
from pathlib import Path
from typing import Iterable

DEFAULT_PORTS: tuple[int, ...] = (80, 443, 8000, 8443)
MAX_SCAN_TASKS = 4096


def _require_dotted_ipv4(token: str, *, ctx: str = "IP") -> None:
    """拒绝 Python 将 ``11`` 解析为 ``0.0.0.11`` 等简写。"""
    if token.count(".") != 3:
        raise ValueError(
            f"请使用完整 IPv4 {ctx}（四段点分），例如 192.168.1.1；不能仅写 {token!r}"
        )


def _count_hosts_in_token(token: str) -> tuple[int, int | None]:
    """估算 token 展开后的主机数；返回 (host_count, inline_port_or_None)。"""
    inline_port: int | None = None
    if token.count(":") == 1 and "/" not in token and "-" not in token.split(":")[0]:
        host, port_s = token.rsplit(":", 1)
        inline_port = int(port_s)
        token = host

    if "/" in token:
        net_part = token.split("/", 1)[0]
        _require_dotted_ipv4(net_part, ctx="网段")
        net = ipaddress.ip_network(token, strict=False)
        if net.version != 4:
            raise ValueError(f"仅支持 IPv4 网段：{token!r}")
        if net.num_addresses <= 2:
            return 1, inline_port
        return net.num_addresses - 2, inline_port

    if "-" in token:
        lo_s, hi_s = token.split("-", 1)
        if "." in hi_s:
            _require_dotted_ipv4(lo_s.strip(), ctx="起始 IP")
            _require_dotted_ipv4(hi_s.strip(), ctx="结束 IP")
            lo = ipaddress.IPv4Address(lo_s)
            hi = ipaddress.IPv4Address(hi_s)
        else:
            _require_dotted_ipv4(lo_s.strip(), ctx="起始 IP")
            lo = ipaddress.IPv4Address(lo_s)
            base = lo_s.rsplit(".", 1)[0]
            hi = ipaddress.IPv4Address(f"{base}.{hi_s}")
        if int(hi) < int(lo):
            raise ValueError(f"invalid IP range: {token!r}")
        return int(hi) - int(lo) + 1, inline_port

    _require_dotted_ipv4(token)
    ipaddress.ip_address(token)
    return 1, inline_port


def estimate_scan_tasks(raw: str, ports_spec: str | Iterable[int] | None = None) -> int:
    """估算 (ip, port) 探测点数量，不展开大网段。"""
    default_ports = parse_ports(ports_spec)
    if not default_ports:
        raise ValueError("at least one port is required")

    total = 0
    for line in raw.splitlines():
        line = line.split("#", 1)[0].strip()
        if not line:
            continue
        for token in line.replace(";", ",").split(","):
            token = token.strip()
            if not token:
                continue
            host_count, inline_port = _count_hosts_in_token(token)
            port_count = 1 if inline_port is not None else len(default_ports)
            total += host_count * port_count
    return total


def parse_ports(spec: str | Iterable[int] | None) -> list[int]:
    if spec is None:
        return list(DEFAULT_PORTS)
    if isinstance(spec, str):
        out: list[int] = []
        for part in spec.replace(";", ",").split(","):
            part = part.strip()
            if not part:
                continue
            if "-" in part:
                lo_s, hi_s = part.split("-", 1)
                lo, hi = int(lo_s), int(hi_s)
                if lo > hi or lo < 1 or hi > 65535:
                    raise ValueError(f"invalid port range: {part!r}")
                out.extend(range(lo, hi + 1))
            else:
                p = int(part)
                if not 1 <= p <= 65535:
                    raise ValueError(f"port out of range: {p}")
                out.append(p)
        return _dedup_preserve(out)
    return _dedup_preserve(int(p) for p in spec)


def _dedup_preserve(items: Iterable[int]) -> list[int]:
    seen: set[int] = set()
    out: list[int] = []
    for it in items:
        if it not in seen:
            seen.add(it)
            out.append(it)
    return out


def _expand_ip_token(token: str) -> tuple[list[str], int | None]:
    """Return (ips, inline_port_or_None) for one token. Token may include :port."""
    inline_port: int | None = None
    if token.count(":") == 1 and "/" not in token and "-" not in token.split(":")[0]:
        host, port_s = token.rsplit(":", 1)
        inline_port = int(port_s)
        token = host

    if "/" in token:
        net_part = token.split("/", 1)[0]
        _require_dotted_ipv4(net_part, ctx="网段")
        net = ipaddress.ip_network(token, strict=False)
        if net.num_addresses > MAX_SCAN_TASKS + 2:
            raise ValueError(
                f"网段 {token} 主机数量过多（约 {net.num_addresses - 2}），"
                f"请缩小范围（单次上限 {MAX_SCAN_TASKS} 个探测点）"
            )
        return [str(h) for h in net.hosts()] or [str(net.network_address)], inline_port

    if "-" in token:
        lo_s, hi_s = token.split("-", 1)
        if "." in hi_s:
            _require_dotted_ipv4(lo_s.strip(), ctx="起始 IP")
            _require_dotted_ipv4(hi_s.strip(), ctx="结束 IP")
            lo = ipaddress.IPv4Address(lo_s)
            hi = ipaddress.IPv4Address(hi_s)
        else:
            _require_dotted_ipv4(lo_s.strip(), ctx="起始 IP")
            lo = ipaddress.IPv4Address(lo_s)
            base = lo_s.rsplit(".", 1)[0]
            hi = ipaddress.IPv4Address(f"{base}.{hi_s}")
        if int(hi) < int(lo):
            raise ValueError(f"invalid IP range: {token!r}")
        span = int(hi) - int(lo) + 1
        if span > MAX_SCAN_TASKS:
            raise ValueError(
                f"IP 范围 {token} 包含 {span} 个地址，超过单次上限 {MAX_SCAN_TASKS}"
            )
        return [str(ipaddress.IPv4Address(i)) for i in range(int(lo), int(hi) + 1)], inline_port

    _require_dotted_ipv4(token)
    ipaddress.ip_address(token)
    return [token], inline_port


def parse_targets(
    raw: str,
    ports: Iterable[int] | None = None,
) -> list[tuple[str, int]]:
    """Parse multi-line/comma-separated target spec into (ip, port) tuples.

    Tokens supported per line:
      - 192.168.1.0/24
      - 10.0.0.1-10.0.0.50  or  10.0.0.1-50
      - 1.2.3.4
      - 1.2.3.4:8080  (inline port overrides ports arg for this token)
    """
    default_ports = list(ports) if ports is not None else list(DEFAULT_PORTS)
    if not default_ports:
        raise ValueError("at least one port is required")

    tasks: list[tuple[str, int]] = []
    seen: set[tuple[str, int]] = set()

    for line in raw.splitlines():
        line = line.split("#", 1)[0].strip()
        if not line:
            continue
        for token in line.replace(";", ",").split(","):
            token = token.strip()
            if not token:
                continue
            ips, inline_port = _expand_ip_token(token)
            port_list = [inline_port] if inline_port is not None else default_ports
            for ip in ips:
                for p in port_list:
                    key = (ip, p)
                    if key not in seen:
                        seen.add(key)
                        tasks.append(key)
    return tasks


def load_targets_from_file(path: str | Path) -> str:
    return Path(path).read_text(encoding="utf-8")
