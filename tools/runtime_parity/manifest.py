"""Manifest and thresholds loading."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from .paths import manifest_path, thresholds_path


@dataclass
class CaseSpec:
    id: str
    priority: str
    task_type: str
    caps: List[str] = field(default_factory=list)
    media_id: str = ""
    fixture: str = ""
    required_layers: List[str] = field(default_factory=list)
    executor_baseline: str = "python"
    mock_hook_port: Optional[int] = None
    description: str = ""
    raw: Dict[str, Any] = field(default_factory=dict)


def load_json(path: Path) -> Dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(f"missing: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def load_manifest(root: Optional[Path] = None) -> Dict[str, Any]:
    return load_json(manifest_path(root))


def load_thresholds(root: Optional[Path] = None) -> Dict[str, Any]:
    return load_json(thresholds_path(root))


def parse_cases(manifest: Dict[str, Any]) -> List[CaseSpec]:
    cases: List[CaseSpec] = []
    for item in manifest.get("cases", []):
        cases.append(
            CaseSpec(
                id=item["id"],
                priority=item.get("priority", "P2"),
                task_type=item.get("task_type", "realtime"),
                caps=list(item.get("caps", [])),
                media_id=item.get("media_id", ""),
                fixture=item.get("fixture", ""),
                required_layers=list(item.get("required_layers", [])),
                executor_baseline=item.get("executor_baseline", "python"),
                mock_hook_port=item.get("mock_hook_port"),
                description=item.get("description", ""),
                raw=item,
            )
        )
    return cases


def find_case(manifest: Dict[str, Any], case_id: str) -> CaseSpec:
    for c in parse_cases(manifest):
        if c.id == case_id:
            return c
    raise KeyError(f"case not in manifest: {case_id}")
