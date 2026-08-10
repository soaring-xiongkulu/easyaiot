#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Runtime-parity safe filesystem body operations.

Policy (docs/runtime-parity/EXECUTION.md §4):
  - Default is dry-run: plan actions, write manifest+token, change nothing.
  - --execute requires --confirm-token matching the dry-run token.
  - All paths must stay under declared allow-roots.
  - Destructive ops additionally require path prefix whitelist.

This module is the ONLY approved entry for copy/move/delete of file trees
by agents. Editing file *contents* does not go through this tool.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence


DEFAULT_LOG_DIR_NAME = "logs"
TOOL_VERSION = 1

# Deletion whitelist relative segments (posix). Matched after resolving under allow-root.
DEFAULT_DELETE_PREFIXES = (
    "VIDEO/services/realtime_algorithm_service",
    "VIDEO/services/snapshot_algorithm_service",
    "VIDEO/services/patrol_algorithm_service",
    "VIDEO/services/_retired",
    # P3-S3: archive Python VIDEO serving surface into VIDEO/_retired_python_video/
    "VIDEO/app",
    "VIDEO/run.py",
    "VIDEO/models.py",
    "VIDEO/start_prod.sh",
    "VIDEO/docker-entrypoint.sh",
    "VIDEO/services/frame_extractor_service",
    "VIDEO/services/media_janitor",
    "VIDEO/services/media_upload_worker",
    "VIDEO/services/post_process_worker",
    "VIDEO/services/pusher_service",
    "VIDEO/services/sorter_service",
    "VIDEO/services/stream_forward_service",
    "VIDEO/services",
    "testdata/runtime-parity/golden",
    "logs/safe_fsops_dryrun",
)


@dataclass
class PlannedAction:
    op: str  # copy_file | copy_tree | move | delete_file | delete_tree
    src: Optional[str] = None
    dst: Optional[str] = None
    bytes_hint: Optional[int] = None
    note: str = ""


@dataclass
class DryRunManifest:
    tool_version: int
    token: str
    created_at: str
    mode: str
    allow_roots: List[str]
    delete_prefixes: List[str]
    actions: List[Dict[str, Any]] = field(default_factory=list)
    plan_hash: str = ""


def _eprint(msg: str) -> None:
    print(msg, file=sys.stderr)


def _norm(p: Path) -> Path:
    return p.expanduser().resolve(strict=False)


def _is_under(child: Path, root: Path) -> bool:
    try:
        child.relative_to(root)
        return True
    except ValueError:
        return False


def _path_bytes(p: Path) -> int:
    if not p.exists():
        return 0
    if p.is_file():
        return p.stat().st_size
    total = 0
    for root, _dirs, files in os.walk(p):
        for name in files:
            fp = Path(root) / name
            try:
                total += fp.stat().st_size
            except OSError:
                pass
    return total


def _forbidden_target(path: Path) -> Optional[str]:
    """Return reason if path is globally forbidden to touch destructively."""
    s = str(path).replace("\\", "/").rstrip("/")
    lowered = s.lower()
    if path.anchor and path == Path(path.anchor):
        return "refusing filesystem root"
    if lowered.endswith("/.git") or "/.git/" in lowered + "/":
        return "refusing .git"
    # entire worktrees container
    if lowered.endswith("/.worktrees") or lowered.endswith("/.worktrees/"):
        return "refusing entire .worktrees directory"
    return None


def _rel_posix_under_root(path: Path, roots: Sequence[Path]) -> Optional[str]:
    for root in roots:
        if _is_under(path, root):
            rel = path.relative_to(root).as_posix()
            return rel
    return None


def _assert_in_allow_roots(path: Path, roots: Sequence[Path], *, what: str) -> None:
    if not any(_is_under(path, r) for r in roots):
        raise SystemExit(
            f"REFUSED: {what} not under allow-roots: {path}\n"
            f"allow-roots={', '.join(str(r) for r in roots)}"
        )
    bad = _forbidden_target(path)
    if bad:
        raise SystemExit(f"REFUSED: {bad}: {path}")


def _assert_delete_whitelisted(path: Path, roots: Sequence[Path], prefixes: Sequence[str]) -> None:
    rel = _rel_posix_under_root(path, roots)
    if rel is None:
        raise SystemExit(f"REFUSED delete: not under allow-roots: {path}")
    ok = False
    for pref in prefixes:
        pref = pref.replace("\\", "/").rstrip("/")
        if rel == pref or rel.startswith(pref + "/"):
            ok = True
            break
    if not ok:
        raise SystemExit(
            f"REFUSED delete: path not in delete whitelist.\n"
            f"  rel={rel}\n"
            f"  whitelist={list(prefixes)}"
        )


def _plan_hash(actions: Sequence[Dict[str, Any]], allow_roots: Sequence[str], prefixes: Sequence[str]) -> str:
    blob = json.dumps(
        {"actions": actions, "allow_roots": list(allow_roots), "delete_prefixes": list(prefixes)},
        sort_keys=True,
        ensure_ascii=False,
    )
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def _make_token(plan_hash: str) -> str:
    raw = f"{plan_hash}:{time.time_ns()}:{os.getpid()}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:32]


def _logs_dir(candidate_hint: Optional[Path]) -> Path:
    base = candidate_hint or Path.cwd()
    # Prefer repo logs/ under an allow root if present
    for p in (base, base / "logs", Path.cwd() / "logs"):
        pass
    d = base / DEFAULT_LOG_DIR_NAME
    d.mkdir(parents=True, exist_ok=True)
    return d


def _write_manifest(manifest: DryRunManifest, log_dir: Path) -> Path:
    ts = time.strftime("%Y%m%d_%H%M%S")
    path = log_dir / f"safe_fsops_dryrun_{ts}.json"
    path.write_text(json.dumps(asdict(manifest), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


def _load_manifest(path: Path) -> DryRunManifest:
    data = json.loads(path.read_text(encoding="utf-8"))
    return DryRunManifest(**data)


def _print_actions(actions: Sequence[PlannedAction]) -> None:
    print("=== safe_fsops PLAN (dry-run unless --execute) ===")
    if not actions:
        print("(no actions)")
        return
    for i, a in enumerate(actions, 1):
        print(f"{i:3d}. {a.op}")
        if a.src:
            print(f"     src: {a.src}")
        if a.dst:
            print(f"     dst: {a.dst}")
        if a.bytes_hint is not None:
            print(f"     bytes_hint: {a.bytes_hint}")
        if a.note:
            print(f"     note: {a.note}")
    print(f"TOTAL actions: {len(actions)}")


def _resolve_allow_roots(args: argparse.Namespace) -> List[Path]:
    roots: List[Path] = []
    for env_name in ("ACME_ORACLE_ROOT", "ACME_CANDIDATE_ROOT"):
        v = os.environ.get(env_name, "").strip()
        if v:
            roots.append(_norm(Path(v)))
    for r in args.allow_root or []:
        roots.append(_norm(Path(r)))
    if not roots:
        # Fail closed: require explicit roots for safety
        raise SystemExit(
            "REFUSED: no allow-roots. Set ACME_ORACLE_ROOT / ACME_CANDIDATE_ROOT "
            "or pass --allow-root (repeatable)."
        )
    # de-dupe
    uniq: List[Path] = []
    seen = set()
    for r in roots:
        key = str(r)
        if key not in seen:
            seen.add(key)
            uniq.append(r)
    return uniq


def _delete_prefixes(args: argparse.Namespace) -> List[str]:
    prefs = list(DEFAULT_DELETE_PREFIXES)
    for p in args.allow_delete_prefix or []:
        prefs.append(p.replace("\\", "/").rstrip("/"))
    return prefs


def cmd_copy(args: argparse.Namespace) -> int:
    roots = _resolve_allow_roots(args)
    src = _norm(Path(args.src))
    dst = _norm(Path(args.dst))
    _assert_in_allow_roots(src, roots, what="src")
    _assert_in_allow_roots(dst.parent if not dst.exists() else dst, roots, what="dst")

    actions: List[PlannedAction] = []
    if src.is_dir():
        actions.append(
            PlannedAction(
                op="copy_tree",
                src=str(src),
                dst=str(dst),
                bytes_hint=_path_bytes(src),
                note="shutil.copytree",
            )
        )
    else:
        actions.append(
            PlannedAction(
                op="copy_file",
                src=str(src),
                dst=str(dst),
                bytes_hint=_path_bytes(src),
                note="shutil.copy2",
            )
        )
    return _finish(args, roots, actions, delete_prefixes=_delete_prefixes(args))


def cmd_move(args: argparse.Namespace) -> int:
    roots = _resolve_allow_roots(args)
    src = _norm(Path(args.src))
    dst = _norm(Path(args.dst))
    _assert_in_allow_roots(src, roots, what="src")
    _assert_in_allow_roots(dst.parent if not dst.exists() else dst, roots, what="dst")
    # move implies delete of src — must be whitelisted
    _assert_delete_whitelisted(src, roots, _delete_prefixes(args))

    actions = [
        PlannedAction(
            op="move",
            src=str(src),
            dst=str(dst),
            bytes_hint=_path_bytes(src),
            note="shutil.move (src must be delete-whitelisted)",
        )
    ]
    return _finish(args, roots, actions, delete_prefixes=_delete_prefixes(args))


def cmd_delete_tree(args: argparse.Namespace) -> int:
    roots = _resolve_allow_roots(args)
    path = _norm(Path(args.path))
    _assert_in_allow_roots(path, roots, what="path")
    _assert_delete_whitelisted(path, roots, _delete_prefixes(args))
    if not path.exists():
        actions = [
            PlannedAction(op="delete_tree", src=str(path), note="path does not exist (no-op)")
        ]
    elif path.is_file():
        actions = [
            PlannedAction(
                op="delete_file",
                src=str(path),
                bytes_hint=_path_bytes(path),
                note="single file",
            )
        ]
    else:
        actions = [
            PlannedAction(
                op="delete_tree",
                src=str(path),
                bytes_hint=_path_bytes(path),
                note="shutil.rmtree",
            )
        ]
    return _finish(args, roots, actions, delete_prefixes=_delete_prefixes(args))


def _execute_actions(actions: Sequence[PlannedAction]) -> None:
    for a in actions:
        if a.op == "copy_file":
            assert a.src and a.dst
            Path(a.dst).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(a.src, a.dst)
        elif a.op == "copy_tree":
            assert a.src and a.dst
            if Path(a.dst).exists():
                raise SystemExit(f"REFUSED execute: dst exists for copy_tree: {a.dst}")
            shutil.copytree(a.src, a.dst)
        elif a.op == "move":
            assert a.src and a.dst
            Path(a.dst).parent.mkdir(parents=True, exist_ok=True)
            shutil.move(a.src, a.dst)
        elif a.op == "delete_file":
            assert a.src
            p = Path(a.src)
            if p.exists():
                p.unlink()
        elif a.op == "delete_tree":
            assert a.src
            p = Path(a.src)
            if not p.exists():
                continue
            if p.is_file():
                p.unlink()
            else:
                shutil.rmtree(p)
        else:
            raise SystemExit(f"unknown op: {a.op}")


def _finish(
    args: argparse.Namespace,
    roots: Sequence[Path],
    actions: Sequence[PlannedAction],
    *,
    delete_prefixes: Sequence[str],
) -> int:
    _print_actions(actions)
    action_dicts = [asdict(a) for a in actions]
    allow_root_strs = [str(r) for r in roots]
    ph = _plan_hash(action_dicts, allow_root_strs, delete_prefixes)

    log_base = roots[-1] if roots else Path.cwd()
    # Prefer candidate root for logs if present in env
    cand = os.environ.get("ACME_CANDIDATE_ROOT", "").strip()
    if cand:
        log_base = _norm(Path(cand))
    log_dir = _logs_dir(log_base)

    if not args.execute:
        token = _make_token(ph)
        manifest = DryRunManifest(
            tool_version=TOOL_VERSION,
            token=token,
            created_at=time.strftime("%Y-%m-%dT%H:%M:%S"),
            mode="dry-run",
            allow_roots=allow_root_strs,
            delete_prefixes=list(delete_prefixes),
            actions=action_dicts,
            plan_hash=ph,
        )
        out = _write_manifest(manifest, log_dir)
        print(f"\nDRY-RUN ONLY. Wrote: {out}")
        print(f"confirm-token: {token}")
        print("Re-run with --execute --confirm-token <token> after orchestrator review.")
        return 0

    # execute path
    if not args.confirm_token:
        raise SystemExit("REFUSED execute: missing --confirm-token")
    if not args.dryrun_manifest:
        # try find latest matching token in log_dir
        raise SystemExit(
            "REFUSED execute: pass --dryrun-manifest path to the reviewed dry-run JSON"
        )

    man_path = _norm(Path(args.dryrun_manifest))
    if not man_path.is_file():
        raise SystemExit(f"REFUSED execute: dryrun manifest not found: {man_path}")
    man = _load_manifest(man_path)
    if man.token != args.confirm_token:
        raise SystemExit("REFUSED execute: confirm-token mismatch")
    if man.plan_hash != ph:
        raise SystemExit(
            "REFUSED execute: plan_hash mismatch vs current command.\n"
            f"  dryrun={man.plan_hash}\n  current={ph}\n"
            "Re-run dry-run and re-review."
        )
    if man.allow_roots != allow_root_strs:
        raise SystemExit("REFUSED execute: allow_roots changed since dry-run")

    print("\nEXECUTE: applying planned actions...")
    _execute_actions(actions)
    print("EXECUTE: done.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="safe_fsops.py",
        description="Dry-run-first copy/move/delete for runtime-parity (EXECUTION.md §4).",
    )
    p.add_argument(
        "--allow-root",
        action="append",
        default=[],
        help="Allowed root directory (repeatable). Also reads ACME_*_ROOT env.",
    )
    p.add_argument(
        "--allow-delete-prefix",
        action="append",
        default=[],
        help="Extra relative delete whitelist prefix under an allow-root (repeatable).",
    )
    p.add_argument(
        "--execute",
        action="store_true",
        help="Actually apply actions (requires --confirm-token and --dryrun-manifest).",
    )
    p.add_argument("--confirm-token", default="", help="Token from reviewed dry-run JSON.")
    p.add_argument(
        "--dryrun-manifest",
        default="",
        help="Path to reviewed logs/safe_fsops_dryrun_*.json",
    )

    sp = p.add_subparsers(dest="cmd", required=True)

    c = sp.add_parser("copy", help="Copy file or directory tree")
    c.add_argument("--src", required=True)
    c.add_argument("--dst", required=True)
    c.set_defaults(func=cmd_copy)

    m = sp.add_parser("move", help="Move file or directory (src must be delete-whitelisted)")
    m.add_argument("--src", required=True)
    m.add_argument("--dst", required=True)
    m.set_defaults(func=cmd_move)

    d = sp.add_parser("delete-tree", help="Delete file or directory tree (whitelist only)")
    d.add_argument("--path", required=True)
    d.set_defaults(func=cmd_delete_tree)

    return p


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.func(args))
    except BrokenPipeError:
        return 0


if __name__ == "__main__":
    sys.exit(main())
