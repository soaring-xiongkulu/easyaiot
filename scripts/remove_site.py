#!/usr/bin/env python3
"""Remove official SITE portal from acme (hard-fork productization).

Two modes (mutually exclusive intent; default dry-run):
  --dry-run   Plan only: list deletes + text patches, write report JSON. No writes.
  --apply     Execute deletes and patches after human review of dry-run.

Does NOT touch: WEB siteSetting.ts SITE_URL (gitee marketing link, unrelated),
geojson false positives, or mqttAuthPort 8090 in node constants.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional


ROOT = Path(r"F:/acme")
REPORT_DIR = ROOT / "scripts" / "reports"


@dataclass
class Op:
    action: str  # delete_tree | delete_file | patch_file | write_file
    path: str
    detail: str = ""
    risk: str = ""
    bytes_hint: int = 0


@dataclass
class Report:
    mode: str
    started_at: str
    root: str
    ops: List[Op] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    def add(self, op: Op) -> None:
        self.ops.append(op)


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def tree_stats(p: Path) -> tuple[int, int]:
    n, b = 0, 0
    if not p.exists():
        return 0, 0
    for f in p.rglob("*"):
        if f.is_file():
            n += 1
            try:
                b += f.stat().st_size
            except OSError:
                pass
    return n, b


def _remove_balanced_block(text: str, open_idx: int) -> Optional[str]:
    """Remove `{...}` starting at open_idx (must point at '{'). Returns new text or None."""
    if open_idx < 0 or open_idx >= len(text) or text[open_idx] != "{":
        return None
    depth = 0
    i = open_idx
    while i < len(text):
        c = text[i]
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                end = i + 1
                # also drop following newline if present
                if end < len(text) and text[end] == "\n":
                    end += 1
                return text[:open_idx] + text[end:]
        i += 1
    return None


def _find_line_start(text: str, pos: int) -> int:
    return text.rfind("\n", 0, pos) + 1


def remove_server_listen_port(text: str, port: int) -> tuple[str, int]:
    """Remove entire `server { ... }` blocks that contain `listen <port>` near the start."""
    removed = 0
    guard = 0
    while guard < 20:
        guard += 1
        m = re.search(rf"(?m)^[ \t]*server[ \t]*\{{", text)
        # find all server blocks via iterative search
        found = False
        for m in re.finditer(r"(?m)^([ \t]*)server[ \t]*\{", text):
            brace = m.end() - 1
            # peek ahead ~400 chars for listen port before nested confusion — use slice to matching close
            # Extract block first
            depth = 0
            i = brace
            end = None
            while i < len(text):
                if text[i] == "{":
                    depth += 1
                elif text[i] == "}":
                    depth -= 1
                    if depth == 0:
                        end = i + 1
                        break
                i += 1
            if end is None:
                continue
            block = text[m.start() : end]
            if re.search(rf"(?m)^[ \t]*listen[ \t]+{port}\b", block):
                # include preceding consecutive comment lines that mention SITE / 8090
                start = m.start()
                # Walk back over blank + consecutive comment lines immediately above
                # this listen-<port> server (SITE headers are not always all tagged).
                ls = _find_line_start(text, start)
                while ls > 0:
                    prev_start = _find_line_start(text, ls - 1)
                    prev = text[prev_start:ls]
                    if prev.strip() == "" or prev.lstrip().startswith("#"):
                        ls = prev_start
                        continue
                    break
                # drop trailing newline after block
                end2 = end
                if end2 < len(text) and text[end2] == "\n":
                    end2 += 1
                text = text[:ls] + text[end2:]
                removed += 1
                found = True
                break
        if not found:
            break
    return text, removed


def patch_web_compose(text: str) -> tuple[str, str]:
    orig = text
    text = re.sub(
        r'\n[ \t]*# SITE 官网.*\n[ \t]*- "\$\{SITE_PORT:-8090\}:8090"\n',
        "\n",
        text,
    )
    text = re.sub(
        r"\n[ \t]*# SITE 官网静态产物.*\n[ \t]*# - \$\{SITE_HTML:-.*\n",
        "\n",
        text,
    )
    return text, "removed SITE_PORT mapping and SITE_HTML mount comments" if text != orig else "no change"


def patch_nginx_conf(text: str) -> tuple[str, str]:
    new, n = remove_server_listen_port(text, 8090)
    # sanity: braces
    if new.count("{") != new.count("}"):
        return text, f"ABORT unbalanced braces after removing {n} listen-8090 blocks"
    return new, f"removed {n} listen-8090 SITE server block(s)" if n else "no SITE server block"


def patch_nginx_prod(text: str) -> tuple[str, str]:
    text2 = re.sub(r"(?m)^#   8090  → SITE.*\n", "", text)
    text2 = re.sub(r"(?m)^#   html/SITE.*\n", "", text2)
    new, n = remove_server_listen_port(text2, 8090)
    if new.count("{") != new.count("}"):
        return text, f"ABORT unbalanced braces after removing {n} listen-8090 blocks"
    detail = []
    if text2 != text:
        detail.append("stripped SITE header comments")
    detail.append(f"removed {n} listen-8090 server block(s)" if n else "no 8090 server block")
    return new, "; ".join(detail)


def patch_runtime_image_common(text: str) -> tuple[str, str]:
    new = re.sub(
        r"\n# SITE 官方网站：仅 site 命令使用.*\nSITE_MODULE_MAPPING=.*\n",
        "\n# SITE portal removed from acme product tree (see docs/adr/0002-remove-site.md)\n",
        text,
    )
    return new, "commented out SITE_MODULE_MAPPING" if new != text else "no change"


def patch_install_site_cmd(text: str, script_name: str) -> tuple[str, str]:
    """Replace SITE delegate function body with hard fail; soften menu labels."""
    orig = text
    # Menu line
    text = text.replace(
        'echo "  3) 官网 — SITE 官方网站独立部署"',
        'echo "  3) 官网 — 已从 acme 移除（不可用）"',
    )
    text = text.replace(
        'echo -e "${YELLOW}  【官网】SITE 独立部署${NC}"',
        'echo -e "${YELLOW}  【官网】已从 acme 移除${NC}"',
    )
    # Help lines mentioning site command
    text = re.sub(
        r'echo "  site \[子命令\]   - 官方网站 SITE 独立部署（默认 install）"',
        'echo "  site [子命令]   - 已移除：acme 不含 SITE 官网"',
        text,
    )
    text = re.sub(
        r'echo "  SITE_PORT                    - 官网宿主机端口（默认 8090）"',
        'echo "  # SITE_PORT removed with SITE portal"',
        text,
    )

    # Replace run_site_module() that delegates to SITE/install_linux.sh
    pat = re.compile(
        r"\n# 官方网站 SITE：委托 SITE/install_linux\.sh\n"
        r"run_site_module\(\) \{\n"
        r"[\s\S]*?\n\}\n",
        re.MULTILINE,
    )
    replacement = """
# SITE portal removed from acme — keep stub so old docs/CI fail clearly.
run_site_module() {
    print_error "SITE 官方网站已从 acme 产品树移除（见 docs/adr/0002-remove-site.md）"
    return 1
}

"""
    text2, n = pat.subn(replacement, text)
    if n == 0:
        text2 = text
        note = "menu/help patched; run_site_module pattern not found"
    else:
        note = f"replaced run_site_module ({n}) + menu/help labels"

    if script_name == "diagnose_tools.sh":
        pat_d = re.compile(
            r"\nrun_site_interactive_menu\(\) \{\n[\s\S]*?\n\}\n",
            re.MULTILINE,
        )
        stub_d = """
run_site_interactive_menu() {
    print_error "SITE 官方网站已从 acme 产品树移除（见 docs/adr/0002-remove-site.md）"
    return 1
}

"""
        text3, nd = pat_d.subn(stub_d, text2)
        if nd:
            text2 = text3
            note = (note + f"; stubbed run_site_interactive_menu ({nd})").lstrip("; ")
        else:
            note = (note + "; run_site_interactive_menu pattern not found").lstrip("; ")

    return text2, note if text2 != orig or n else "no change"


def plan(report: Report) -> None:
    site = ROOT / "SITE"
    n, b = tree_stats(site)
    report.notes.append(f"SITE tree files={n} bytes={b} (~{b/1e6:.1f} MB)")
    if site.exists():
        report.add(
            Op(
                "delete_tree",
                str(site),
                detail=f"remove official portal source ({n} files)",
                risk="destructive",
                bytes_hint=b,
            )
        )
    else:
        report.notes.append("SITE/ already absent")

    site_nginx = ROOT / "WEB" / "conf" / "nginx.site.conf"
    if site_nginx.exists():
        report.add(Op("delete_file", str(site_nginx), detail="SITE-only nginx conf", risk="destructive"))

    patches = [
        (ROOT / "WEB" / "docker-compose.yaml", patch_web_compose),
        (ROOT / "WEB" / "conf" / "nginx.conf", patch_nginx_conf),
        (ROOT / "WEB" / "conf" / "nginx.mini.conf", patch_nginx_conf),
        (ROOT / "WEB" / "conf" / "nginx.prod-server.conf", patch_nginx_prod),
        (ROOT / ".scripts" / "docker" / "runtime_image_common.sh", patch_runtime_image_common),
    ]
    for path, fn in patches:
        if not path.exists():
            report.errors.append(f"missing patch target: {path}")
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        new, detail = fn(text)
        if new == text:
            report.notes.append(f"skip patch (no change): {path.relative_to(ROOT)} ({detail})")
            continue
        report.add(
            Op(
                "patch_file",
                str(path),
                detail=detail,
                risk="edit",
                bytes_hint=len(text.encode("utf-8")),
            )
        )
        # stash planned content hash length only in dry-run; apply reads again

    install_scripts = [
        ROOT / ".scripts" / "docker" / "install_linux.sh",
        ROOT / ".scripts" / "docker" / "install_linux_arm.sh",
        ROOT / ".scripts" / "docker" / "install_linux_kylin.sh",
        ROOT / ".scripts" / "docker" / "diagnose_tools.sh",
    ]
    for path in install_scripts:
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        new, detail = patch_install_site_cmd(text, path.name)
        if new == text and "not found" in detail:
            report.notes.append(f"install stub weak: {path.name}: {detail}")
        if new != text:
            report.add(Op("patch_file", str(path), detail=detail, risk="edit"))

    adr = ROOT / "docs" / "adr" / "0002-remove-site.md"
    report.add(
        Op(
            "write_file",
            str(adr),
            detail="ADR: SITE removed from product",
            risk="create",
        )
    )
    report.notes.append(
        "Out of scope (intentional): WEB siteSetting.ts SITE_URL (external gitee image link); "
        "mqttAuthPort 8090; README_zh upstream marketing copy (optional later)."
    )


def _rmtree_win(path: Path) -> None:
    """shutil.rmtree with Windows read-only / lock retries."""
    import os
    import stat
    import time

    def onerror(func, p, exc_info):
        try:
            os.chmod(p, stat.S_IWRITE)
            func(p)
        except Exception:
            raise

    last = None
    for i in range(5):
        try:
            if not path.exists():
                return
            shutil.rmtree(path, onerror=onerror)
            return
        except PermissionError as e:
            last = e
            time.sleep(0.4 * (i + 1))
    # Last resort: rename away so product tree is clean of SITE name
    tomb = path.with_name(path.name + ".__removed__")
    try:
        if tomb.exists():
            shutil.rmtree(tomb, onerror=onerror)
        path.rename(tomb)
        print(f"[apply] WARN renamed locked {path} -> {tomb} (delete tombstone later)")
        return
    except Exception as e2:
        raise last from e2


def apply_patches(report: Report) -> None:
    # Recompute patches and write; do deletes last so a lock doesn't skip patches.
    mapping = {
        str(ROOT / "WEB" / "docker-compose.yaml"): patch_web_compose,
        str(ROOT / "WEB" / "conf" / "nginx.conf"): patch_nginx_conf,
        str(ROOT / "WEB" / "conf" / "nginx.mini.conf"): patch_nginx_conf,
        str(ROOT / "WEB" / "conf" / "nginx.prod-server.conf"): patch_nginx_prod,
        str(ROOT / ".scripts" / "docker" / "runtime_image_common.sh"): patch_runtime_image_common,
        str(ROOT / ".scripts" / "docker" / "install_linux.sh"): lambda t: patch_install_site_cmd(t, "install_linux.sh"),
        str(ROOT / ".scripts" / "docker" / "install_linux_arm.sh"): lambda t: patch_install_site_cmd(t, "install_linux_arm.sh"),
        str(ROOT / ".scripts" / "docker" / "install_linux_kylin.sh"): lambda t: patch_install_site_cmd(t, "install_linux_kylin.sh"),
        str(ROOT / ".scripts" / "docker" / "diagnose_tools.sh"): lambda t: patch_install_site_cmd(t, "diagnose_tools.sh"),
    }
    order = {"write_file": 0, "patch_file": 1, "delete_file": 2, "delete_tree": 3}
    ops = sorted(report.ops, key=lambda o: order.get(o.action, 9))
    for op in ops:
        p = Path(op.path)
        if op.action == "delete_tree":
            if p.exists():
                # Already emptied but dir locked → still try remove / rename
                _rmtree_win(p)
                print(f"[apply] deleted tree {p} (exists_now={p.exists()})")
            else:
                print(f"[apply] delete_tree already gone: {p}")
        elif op.action == "delete_file":
            if p.exists():
                p.unlink()
                print(f"[apply] deleted file {p}")
            else:
                print(f"[apply] delete_file already gone: {p}")
        elif op.action == "patch_file":
            fn = mapping.get(str(p))
            if not fn:
                report.errors.append(f"no patch fn for {p}")
                continue
            text = p.read_text(encoding="utf-8", errors="replace")
            new, detail = fn(text)
            if new != text:
                if "ABORT" in detail:
                    report.errors.append(f"{p}: {detail}")
                    print(f"[apply] SKIP {p} ({detail})")
                    continue
                p.write_text(new, encoding="utf-8", newline="\n")
                print(f"[apply] patched {p} ({detail})")
            else:
                print(f"[apply] patch noop {p}")
        elif op.action == "write_file" and p.name == "0002-remove-site.md":
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(ADR_BODY, encoding="utf-8", newline="\n")
            print(f"[apply] wrote {p}")


ADR_BODY = """# ADR-0002 — 从 acme 产品树移除 SITE 官网

- 日期: 2026-08-09
- 状态: Accepted

## 决策

acme 硬分叉产品 **不再包含 / 维护** EasyAIoT 官方门户模块 `SITE/`（纯前端营销站）。

## 理由

- 官网非业务管控能力；公司不负责维护该对外营销面。
- 保留会干扰本地代码分析、误入打包与认知负担。
- 上游若仍有 SITE，仅作偶发合并时跳过；不长期跟踪。

## 后果

- 删除 `SITE/` 源码树与 `WEB/conf/nginx.site.conf`。
- WEB nginx / docker-compose 去掉 8090 官网监听与映射。
- 安装脚本 `site` 子命令改为明确失败桩。
- 业务 WEB/APP/PANEL/DEVICE 不受影响。
"""


def update_company_docs_apply() -> None:
    """Light company-doc touch after SITE removal."""
    overview = ROOT / "docs" / "architecture" / "overview.md"
    if overview.exists():
        t = overview.read_text(encoding="utf-8")
        if "SITE" in t or "site" in t.lower():
            pass
        # Ensure note present
        note = "\n\n> **SITE**：已从 acme 产品树移除（ADR-0002）。\n"
        if "ADR-0002" not in t:
            overview.write_text(t.rstrip() + note, encoding="utf-8", newline="\n")
            print(f"[apply] updated {overview}")

    acme_md = ROOT / "ACME.md"
    if acme_md.exists():
        t = acme_md.read_text(encoding="utf-8")
        if "ADR-0002" not in t:
            acme_md.write_text(
                t.rstrip()
                + "\n\n## 产品范围备注\n\n- 不含官方门户 **SITE**（已移除，见 `docs/adr/0002-remove-site.md`）。\n",
                encoding="utf-8",
                newline="\n",
            )
            print(f"[apply] updated {acme_md}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--dry-run", action="store_true", default=True)
    g.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    mode = "apply" if args.apply else "dry-run"

    if not ROOT.is_dir():
        print(f"ROOT missing: {ROOT}", file=sys.stderr)
        return 2

    report = Report(mode=mode, started_at=utc_now(), root=str(ROOT))
    plan(report)

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    out = REPORT_DIR / f"remove_site_{mode}.json"
    payload = {
        "mode": mode,
        "started_at": report.started_at,
        "root": report.root,
        "notes": report.notes,
        "errors": report.errors,
        "op_counts": {},
        "ops": [asdict(o) for o in report.ops],
    }
    for o in report.ops:
        payload["op_counts"][o.action] = payload["op_counts"].get(o.action, 0) + 1
    out.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    print(f"\n[report] {out}")

    if mode == "dry-run":
        print("\nDRY-RUN only. Review ops, then re-run with --apply.")
        return 0

    apply_patches(report)
    update_company_docs_apply()
    # refresh apply report
    payload["finished_at"] = utc_now()
    out_a = REPORT_DIR / "remove_site_apply.json"
    out_a.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[report] {out_a}")
    if report.errors:
        print("ERRORS:", report.errors, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
