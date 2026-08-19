"""加载 SENTINEL/registry 下的 YAML 配置。"""
from __future__ import annotations

import os
from functools import lru_cache
from typing import Any, Dict

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore


def _registry_dir() -> str:
    here = os.path.dirname(os.path.abspath(__file__))
    candidate = os.path.join(os.path.dirname(here), 'registry')
    if os.path.isdir(candidate):
        return candidate
    return os.path.join(here, '..', 'registry')


def _load_yaml(name: str) -> Dict[str, Any]:
    path = os.path.join(_registry_dir(), name)
    if not os.path.isfile(path) or yaml is None:
        return {}
    with open(path, encoding='utf-8') as f:
        data = yaml.safe_load(f) or {}
    return data if isinstance(data, dict) else {}


@lru_cache(maxsize=1)
def load_components_registry() -> Dict[str, Any]:
    return _load_yaml('components.yaml')


@lru_cache(maxsize=1)
def load_capabilities_registry() -> Dict[str, Any]:
    return _load_yaml('capabilities.yaml')


@lru_cache(maxsize=1)
def load_functions_registry() -> Dict[str, Any]:
    return _load_yaml('functions.yaml')
