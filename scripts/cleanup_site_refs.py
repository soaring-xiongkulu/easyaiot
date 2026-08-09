#!/usr/bin/env python3
"""Strip SITE portal mentions from acme packaging READMEs / leftover install help.

Modes:
  --dry-run (default): plan + write report, no writes
  --apply: apply text patches

Does not touch: VIDEO/AI SITE_PKG (python site-packages), WEB siteSetting SITE_URL.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, List, Tuple


ROOT = Path(r"F:/acme")
REPORT_DIR = ROOT / "scripts" / "reports"


@dataclass
class Op:
    action: str
    path: str
    detail: str = ""


@dataclass
class Report:
    mode: str
    started_at: str
    ops: List[Op] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def patch_readme_module_list(text: str) -> Tuple[str, str]:
    """Remove SITE from comma/顿号 module enumerations and marketing clauses."""
    orig = text
    # Chinese顿号 list: ...、PANEL、SITE → ...、PANEL
    text = re.sub(r"(、|, )\bSITE\b", "", text)
    # English "PANEL, and SITE" / "PANEL and SITE"
    text = re.sub(r", and SITE\b", "", text)
    text = re.sub(r" and SITE\b", "", text)
    text = re.sub(r", SITE\b", "", text)
    # Russian "и SITE"
    text = re.sub(r" и SITE\b", "", text)
    # French "et SITE"
    text = re.sub(r" et SITE\b", "", text)

    # Prose marketing clauses (keep sentence grammatical)
    prose_patterns = [
        r"；另以 <strong>SITE 官方网站</strong>[^；。<]*",
        r"；另以 <strong>SITE 官方網站</strong>[^；。<]*",
        r"；並以 <strong>SITE 官方網站</strong>[^；。<]*",
        r"; plus the <strong>SITE official website</strong>[^.;<]*",
        r"; ainsi que le <strong>site officiel SITE</strong>[^.;<]*",
        # RU / KO — slightly different punctuation
        r",?\s*а также <strong>официальный сайт SITE</strong>[^.;<]*",
        r",?\s*плюс <strong>официальный сайт SITE</strong>[^.;<]*",
        r";?\s*<strong>SITE 공식 웹사이트</strong>[^.;<]*",
        r",?\s*그리고 <strong>SITE 공식 웹사이트</strong>[^.;<]*",
    ]
    prose_n = 0
    for pat in prose_patterns:
        text, n = re.subn(pat, "", text)
        prose_n += n

    # Remove HTML table rows whose first cell mentions SITE module
    text2, n = re.subn(
        r"<tr>\s*<td[^>]*>\s*<strong>\s*(?:Module\s+)?SITE[^<]*</strong>\s*</td>[\s\S]*?</tr>\s*",
        "",
        text,
        flags=re.IGNORECASE,
    )
    detail = []
    if text2 != orig and ("stripped" or True):
        if any(x in orig and x not in text2 for x in ["、SITE", ", SITE", " and SITE", " et SITE", " и SITE"]):
            detail.append("stripped SITE from module lists")
        elif text2 != orig:
            detail.append("updated README SITE mentions")
    if prose_n:
        detail.append(f"removed {prose_n} SITE prose clause(s)")
    if n:
        detail.append(f"removed {n} SITE table row(s)")
    if not detail and text2 == orig:
        return text2, "no change"
    if not detail:
        detail.append("patched")
    return text2, "; ".join(detail)


def patch_install_help_leftovers(text: str) -> Tuple[str, str]:
    orig = text
    text = text.replace(
        'echo "  也可直接: cd SITE && ./install_linux.sh <子命令>"',
        'echo "  # SITE 目录已移除，勿再 cd SITE"',
    )
    text = re.sub(
        r'echo "SITE 子命令（[^"]+）:"',
        'echo "site 子命令（已禁用）:"',
        text,
    )
    text = text.replace(
        "#   site [子命令] - 官方网站 SITE 独立部署",
        "#   site [子命令] - 已移除（acme 不含 SITE）",
    )
    return text, "cleaned SITE help leftovers" if text != orig else "no change"


def patch_foundation_status(text: str) -> Tuple[str, str]:
    if "ADR-0002" in text and "SITE 官方门户已从产品树移除" in text:
        return text, "no change"
    note = (
        "\n\n## 产品范围（2026-08-09）\n\n"
        "- **SITE 官方门户已从产品树移除**（ADR-0002）；安装脚本 `site` 为失败桩。\n"
    )
    return text.rstrip() + note + "\n", "appended SITE-removed note"


PATCHERS: List[Tuple[Path, Callable[[str], Tuple[str, str]]]] = []


def build_patchers() -> None:
    PATCHERS.clear()
    for name in [
        "README.md",
        "README_zh.md",
        "README_zh_tw.md",
        "README_ru.md",
        "README_ko.md",
        "README_fr.md",
    ]:
        p = ROOT / name
        if p.exists():
            PATCHERS.append((p, patch_readme_module_list))
    for name in [
        "install_linux.sh",
        "install_linux_arm.sh",
        "install_linux_kylin.sh",
    ]:
        p = ROOT / ".scripts" / "docker" / name
        if p.exists():
            PATCHERS.append((p, patch_install_help_leftovers))
    foundation = ROOT / "docs" / "status" / "foundation.md"
    if foundation.exists():
        PATCHERS.append((foundation, patch_foundation_status))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--dry-run", action="store_true", default=True)
    g.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    mode = "apply" if args.apply else "dry-run"

    build_patchers()
    report = Report(mode=mode, started_at=utc_now())
    planned: List[Tuple[Path, Callable, str, str]] = []

    for path, fn in PATCHERS:
        text = path.read_text(encoding="utf-8", errors="replace")
        new, detail = fn(text)
        if new == text:
            report.notes.append(f"skip {path.relative_to(ROOT)} ({detail})")
            continue
        report.ops.append(Op("patch_file", str(path), detail))
        planned.append((path, fn, text, new))

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "mode": mode,
        "started_at": report.started_at,
        "notes": report.notes,
        "errors": report.errors,
        "ops": [asdict(o) for o in report.ops],
    }
    out = REPORT_DIR / f"cleanup_site_refs_{mode}.json"
    out.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    print(f"\n[report] {out}")

    if mode == "dry-run":
        print("\nDRY-RUN only. Review, then --apply.")
        return 0

    for path, fn, _old, new in planned:
        # re-read + recompute for safety
        cur = path.read_text(encoding="utf-8", errors="replace")
        new2, detail = fn(cur)
        if new2 != cur:
            path.write_text(new2, encoding="utf-8", newline="\n")
            print(f"[apply] {path} ({detail})")
        else:
            print(f"[apply] noop {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
