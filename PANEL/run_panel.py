#!/usr/bin/env python3
"""
EasyAIoT PANEL Agent
- 界面化封装统一安装脚本（Linux / macOS / Windows）
- Docker 容器管理 / 拓扑 / 资源概览
默认监听 :9200
"""
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
    # 源码模式把 PANEL 目录加入 path；frozen 时模块已打进二进制
    if not getattr(sys, 'frozen', False) and here not in sys.path:
        sys.path.insert(0, here)

    env_file = os.environ.get('PANEL_ENV_FILE') or os.path.join(here, 'panel.env')
    _load_env_file(env_file)

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
    )
    logger = logging.getLogger('easyaiot-panel')

    from panel_server import PANEL_LISTEN_HOST, PANEL_LISTEN_PORT, PROJECT_ROOT, app

    logger.info('EasyAIoT PANEL 启动于 http://%s:%s', PANEL_LISTEN_HOST, PANEL_LISTEN_PORT)
    logger.info('环境文件: %s', env_file if os.path.isfile(env_file) else '(未找到，使用默认)')
    logger.info('仓库根: %s', PROJECT_ROOT)
    app.run(host=PANEL_LISTEN_HOST, port=PANEL_LISTEN_PORT, threaded=True)


if __name__ == '__main__':
    main()
