#!/usr/bin/env python3
"""EasyAIoT IDEA Portal — 社区贡献者在线 IDE 门户。"""
from __future__ import annotations

import logging
import os
import sys


def _load_env_file(path: str) -> None:
    if not path or not os.path.isfile(path):
        return
    try:
        with open(path, encoding='utf-8') as f:
            for raw in f:
                line = raw.strip()
                if not line or line.startswith('#') or '=' not in line:
                    continue
                key, val = line.split('=', 1)
                key = key.strip()
                val = val.strip().strip('"').strip("'")
                if key and key not in os.environ:
                    os.environ[key] = val
    except OSError:
        pass


def _runtime_dir() -> str:
    if getattr(sys, 'frozen', False):
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.dirname(os.path.abspath(__file__))


def main() -> None:
    here = _runtime_dir()
    _load_env_file(os.path.join(here, 'idea.env'))
    _load_env_file(os.environ.get('IDEA_ENV_FILE', ''))

    logging.basicConfig(
        level=os.environ.get('IDEA_LOG_LEVEL', 'INFO'),
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    )

    from idea_server import create_app, run_server

    app = create_app()
    run_server(app)


if __name__ == '__main__':
    main()
