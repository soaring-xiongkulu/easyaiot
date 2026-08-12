#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VIDEO cutover filesystem batch ops — dry-run first, execute only with confirm token.

Policy (docs/video-java/REPO_CUTOVER_PLAN.md + user 2-phase rule):
  1) dry-run: plan every copy/move/delete/ensure_dir, self-check for path drift, write manifest+token
  2) human/agent reviews manifest (no execute yet)
  3) --execute --confirm-token --dryrun-manifest applies the *same* plan

Editing file *contents* (yaml/java) does NOT go through this tool.
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


TOOL_VERSION = 1
DEFAULT_LOG_DIR = "logs"


@dataclass
class PlannedAction:
    op: str  # copy_file | move | delete_file | ensure_dir
    src: Optional[str] = None
    dst: Optional[str] = None
    bytes_hint: Optional[int] = None
    sha256: Optional[str] = None
    rel_dst: Optional[str] = None
    note: str = ""


@dataclass
class SelfCheck:
    ok: bool
    checks: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class DryRunManifest:
    tool_version: int
    token: str
    created_at: str
    mode: str
    allow_roots: List[str]
    plan_id: str
    actions: List[Dict[str, Any]] = field(default_factory=list)
    self_check: Dict[str, Any] = field(default_factory=dict)
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


def _sha256_file(path: Path, *, max_bytes: Optional[int] = None) -> str:
    h = hashlib.sha256()
    size = 0
    with path.open("rb") as f:
        while True:
            chunk = f.read(1024 * 1024)
            if not chunk:
                break
            size += len(chunk)
            if max_bytes is not None and size > max_bytes:
                raise SystemExit(f"REFUSED: file exceeds hash budget: {path}")
            h.update(chunk)
    return h.hexdigest()


def _plan_hash(payload: Dict[str, Any]) -> str:
    blob = json.dumps(payload, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def _make_token(plan_hash: str) -> str:
    raw = f"{plan_hash}:{time.time_ns()}:{os.getpid()}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:32]


def _assert_in_roots(path: Path, roots: Sequence[Path], *, what: str) -> None:
    if not any(_is_under(path, r) for r in roots):
        raise SystemExit(
            f"REFUSED: {what} not under allow-roots: {path}\n"
            f"allow-roots={', '.join(str(r) for r in roots)}"
        )
    s = str(path).replace("\\", "/").lower()
    if "/.git/" in s + "/" or s.endswith("/.git"):
        raise SystemExit(f"REFUSED: refusing .git path: {path}")


def _rel_under(path: Path, roots: Sequence[Path]) -> str:
    for root in roots:
        if _is_under(path, root):
            return path.relative_to(root).as_posix()
    raise SystemExit(f"REFUSED: cannot relativize {path}")


def _print_actions(actions: Sequence[PlannedAction], check: SelfCheck) -> None:
    print("=== cutover_fs_batch PLAN ===")
    for i, a in enumerate(actions, 1):
        print(f"{i:3d}. {a.op}")
        if a.src:
            print(f"     src: {a.src}")
        if a.dst:
            print(f"     dst: {a.dst}")
        if a.rel_dst:
            print(f"     rel_dst: {a.rel_dst}")
        if a.bytes_hint is not None:
            print(f"     bytes: {a.bytes_hint}")
        if a.sha256:
            print(f"     sha256: {a.sha256}")
        if a.note:
            print(f"     note: {a.note}")
    print(f"TOTAL actions: {len(actions)}")
    print("\n=== SELF-CHECK ===")
    for c in check.checks:
        status = "PASS" if c.get("ok") else "FAIL"
        print(f"  [{status}] {c.get('name')}: {c.get('detail')}")
    print(f"SELF-CHECK OVERALL: {'PASS' if check.ok else 'FAIL'}")


def phase1_models_plan(repo: Path, roots: Sequence[Path]) -> tuple[List[PlannedAction], SelfCheck]:
    """Copy commercial ONNX weights VIDEO/ -> DEVICE/iot-video/models/ (no delete)."""
    names = [
        "face_rec.onnx",
        "face_det.onnx",
        "plate_detect.onnx",
        "plate_rec.onnx",
        "yolo26n-pose.onnx",
    ]
    src_dir = repo / "VIDEO"
    dst_dir = repo / "DEVICE" / "iot-video" / "models"
    actions: List[PlannedAction] = [
        PlannedAction(
            op="ensure_dir",
            dst=str(_norm(dst_dir)),
            rel_dst=_rel_under(_norm(dst_dir), roots),
            note="create models directory if missing",
        )
    ]
    checks: List[Dict[str, Any]] = []
    ok = True

    # Expected relative destinations — drift if anything else appears
    expected_rels = {f"DEVICE/iot-video/models/{n}" for n in names}
    expected_rels.add("DEVICE/iot-video/models")

    for name in names:
        src = _norm(src_dir / name)
        dst = _norm(dst_dir / name)
        _assert_in_roots(src, roots, what="src")
        _assert_in_roots(dst.parent, roots, what="dst parent")
        if not src.is_file():
            ok = False
            checks.append({"ok": False, "name": f"src_exists:{name}", "detail": f"missing {src}"})
            continue
        if src.name != name or dst.name != name:
            ok = False
            checks.append(
                {
                    "ok": False,
                    "name": f"basename_match:{name}",
                    "detail": f"src={src.name} dst={dst.name}",
                }
            )
            continue
        rel = _rel_under(dst, roots)
        if rel != f"DEVICE/iot-video/models/{name}":
            ok = False
            checks.append(
                {
                    "ok": False,
                    "name": f"rel_dst_drift:{name}",
                    "detail": f"got {rel}, expected DEVICE/iot-video/models/{name}",
                }
            )
            continue
        # reject sneaky path segments
        if ".." in Path(rel).parts:
            ok = False
            checks.append({"ok": False, "name": f"traversal:{name}", "detail": rel})
            continue
        digest = _sha256_file(src)
        size = src.stat().st_size
        if size < 1024:
            ok = False
            checks.append({"ok": False, "name": f"min_size:{name}", "detail": f"size={size}"})
            continue
        if dst.exists():
            if dst.is_file() and dst.stat().st_size == size:
                checks.append(
                    {
                        "ok": True,
                        "name": f"dst_already_same_size:{name}",
                        "detail": "will overwrite with identical size (copy2)",
                    }
                )
            else:
                checks.append(
                    {
                        "ok": True,
                        "name": f"dst_exists_different:{name}",
                        "detail": f"existing size={dst.stat().st_size if dst.is_file() else 'n/a'}; will overwrite",
                    }
                )
        actions.append(
            PlannedAction(
                op="copy_file",
                src=str(src),
                dst=str(dst),
                bytes_hint=size,
                sha256=digest,
                rel_dst=rel,
                note="Phase1 copy (VIDEO retained until Phase4/5)",
            )
        )
        checks.append(
            {
                "ok": True,
                "name": f"planned:{name}",
                "detail": f"{rel} sha256={digest[:12]}… bytes={size}",
            }
        )

    planned_rels = {a.rel_dst for a in actions if a.rel_dst}
    if planned_rels != expected_rels:
        # ensure_dir + 5 files
        missing = expected_rels - planned_rels
        extra = planned_rels - expected_rels
        if missing or extra:
            ok = False
            checks.append(
                {
                    "ok": False,
                    "name": "rel_set_exact",
                    "detail": f"missing={sorted(missing)} extra={sorted(extra)}",
                }
            )
        else:
            checks.append({"ok": True, "name": "rel_set_exact", "detail": "matches expected set"})
    else:
        checks.append({"ok": True, "name": "rel_set_exact", "detail": "matches expected set"})

    # Source and dest must not be the same path (no no-op drift)
    for a in actions:
        if a.op == "copy_file" and a.src and a.dst and _norm(Path(a.src)) == _norm(Path(a.dst)):
            ok = False
            checks.append({"ok": False, "name": "src_eq_dst", "detail": a.src})

    checks.append(
        {
            "ok": ok,
            "name": "phase1_models_gate",
            "detail": "all model copy self-checks" if ok else "one or more checks failed",
        }
    )
    return actions, SelfCheck(ok=ok, checks=checks)


def phase1_alert_images_plan(repo: Path, roots: Sequence[Path]) -> tuple[List[PlannedAction], SelfCheck]:
    """Ensure neutral data/alert_images dir (compose will point here). No VIDEO delete."""
    dst = _norm(repo / "data" / "alert_images")
    _assert_in_roots(dst.parent if not dst.exists() else dst, roots, what="alert_images")
    rel = _rel_under(dst, roots)
    checks: List[Dict[str, Any]] = []
    ok = rel == "data/alert_images"
    checks.append(
        {
            "ok": ok,
            "name": "rel_dst_alert_images",
            "detail": f"got {rel}, expected data/alert_images",
        }
    )
    actions = [
        PlannedAction(
            op="ensure_dir",
            dst=str(dst),
            rel_dst=rel,
            note="neutral alert_images mount root (Phase1)",
        )
    ]
    return actions, SelfCheck(ok=ok, checks=checks)


def _execute(actions: Sequence[PlannedAction]) -> None:
    for a in actions:
        if a.op == "ensure_dir":
            assert a.dst
            Path(a.dst).mkdir(parents=True, exist_ok=True)
        elif a.op == "copy_file":
            assert a.src and a.dst
            Path(a.dst).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(a.src, a.dst)
            # post-copy integrity
            if a.sha256:
                got = _sha256_file(Path(a.dst))
                if got != a.sha256:
                    raise SystemExit(
                        f"REFUSED post-copy: sha256 mismatch for {a.dst}\n"
                        f"  expected={a.sha256}\n  got={got}"
                    )
            if a.bytes_hint is not None and Path(a.dst).stat().st_size != a.bytes_hint:
                raise SystemExit(f"REFUSED post-copy: size mismatch for {a.dst}")
        elif a.op == "move":
            assert a.src and a.dst
            Path(a.dst).parent.mkdir(parents=True, exist_ok=True)
            shutil.move(a.src, a.dst)
        elif a.op == "delete_file":
            assert a.src
            p = Path(a.src)
            if p.exists():
                p.unlink()
        else:
            raise SystemExit(f"unknown op: {a.op}")


def _finish(
    args: argparse.Namespace,
    roots: Sequence[Path],
    plan_id: str,
    actions: Sequence[PlannedAction],
    check: SelfCheck,
) -> int:
    _print_actions(actions, check)
    if not check.ok:
        raise SystemExit("REFUSED: self-check FAILED — fix plan before execute")

    action_dicts = [asdict(a) for a in actions]
    allow_root_strs = [str(r) for r in roots]
    payload = {
        "plan_id": plan_id,
        "actions": action_dicts,
        "allow_roots": allow_root_strs,
        "self_check_ok": check.ok,
    }
    ph = _plan_hash(payload)

    log_dir = roots[0] / DEFAULT_LOG_DIR
    log_dir.mkdir(parents=True, exist_ok=True)

    if not args.execute:
        token = _make_token(ph)
        manifest = DryRunManifest(
            tool_version=TOOL_VERSION,
            token=token,
            created_at=time.strftime("%Y-%m-%dT%H:%M:%S"),
            mode="dry-run",
            allow_roots=allow_root_strs,
            plan_id=plan_id,
            actions=action_dicts,
            self_check={"ok": check.ok, "checks": check.checks},
            plan_hash=ph,
        )
        out = log_dir / f"cutover_fs_batch_dryrun_{plan_id}_{time.strftime('%Y%m%d_%H%M%S')}.json"
        out.write_text(json.dumps(asdict(manifest), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"\nDRY-RUN ONLY. Wrote: {out}")
        print(f"confirm-token: {token}")
        print("Review self-check PASS, then re-run with --execute --confirm-token --dryrun-manifest")
        return 0

    if not args.confirm_token or not args.dryrun_manifest:
        raise SystemExit("REFUSED execute: need --confirm-token and --dryrun-manifest")
    man_path = _norm(Path(args.dryrun_manifest))
    data = json.loads(man_path.read_text(encoding="utf-8"))
    if data.get("token") != args.confirm_token:
        raise SystemExit("REFUSED execute: confirm-token mismatch")
    if data.get("plan_hash") != ph:
        raise SystemExit(
            "REFUSED execute: plan_hash mismatch vs current command.\n"
            f"  dryrun={data.get('plan_hash')}\n  current={ph}\n"
            "Re-run dry-run and re-review."
        )
    if data.get("plan_id") != plan_id:
        raise SystemExit("REFUSED execute: plan_id mismatch")
    if data.get("allow_roots") != allow_root_strs:
        raise SystemExit("REFUSED execute: allow_roots changed since dry-run")

    print("\nEXECUTE: applying planned actions...")
    _execute(actions)
    print("EXECUTE: done.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Cutover FS batch with dry-run + confirm-token execute")
    p.add_argument(
        "--allow-root",
        action="append",
        default=[],
        help="Allowed root (repeatable). Default: ACME_CANDIDATE_ROOT or cwd.",
    )
    p.add_argument("--execute", action="store_true")
    p.add_argument("--confirm-token", default="")
    p.add_argument("--dryrun-manifest", default="")
    sp = p.add_subparsers(dest="plan", required=True)

    m = sp.add_parser("phase1-models", help="Copy VIDEO/*.onnx -> DEVICE/iot-video/models/")
    m.set_defaults(plan_id="phase1-models")

    a = sp.add_parser("phase1-alert-images", help="Ensure data/alert_images directory")
    a.set_defaults(plan_id="phase1-alert-images")
    return p


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    roots: List[Path] = []
    for r in args.allow_root:
        roots.append(_norm(Path(r)))
    env = os.environ.get("ACME_CANDIDATE_ROOT", "").strip()
    if env:
        roots.append(_norm(Path(env)))
    if not roots:
        roots.append(_norm(Path.cwd()))
    # de-dupe
    uniq: List[Path] = []
    seen = set()
    for r in roots:
        k = str(r)
        if k not in seen:
            seen.add(k)
            uniq.append(r)
    roots = uniq
    repo = roots[0]

    if args.plan_id == "phase1-models":
        actions, check = phase1_models_plan(repo, roots)
    elif args.plan_id == "phase1-alert-images":
        actions, check = phase1_alert_images_plan(repo, roots)
    else:
        raise SystemExit(f"unknown plan: {args.plan_id}")

    return _finish(args, roots, args.plan_id, actions, check)


if __name__ == "__main__":
    sys.exit(main())
