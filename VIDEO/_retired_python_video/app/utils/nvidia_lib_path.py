"""将 pip 安装的 nvidia/* 库目录加入 LD_LIBRARY_PATH，供 ONNX Runtime CUDA EP 加载。"""
from __future__ import annotations

import glob
import logging
import os
import site


def prepend_nvidia_lib_paths() -> None:
    if os.environ.get('_ONNX_NVIDIA_LD_PATH_DONE') == '1':
        return
    try:
        search_roots = list(site.getsitepackages())
        user_site = site.getusersitepackages()
        if user_site:
            search_roots.append(user_site)
        extra: list[str] = []
        for root in search_roots:
            if not root or not os.path.isdir(root):
                continue
            for lib_dir in glob.glob(os.path.join(root, 'nvidia', '*', 'lib')):
                if os.path.isdir(lib_dir) and lib_dir not in extra:
                    extra.append(lib_dir)
        if extra:
            current = os.environ.get('LD_LIBRARY_PATH', '')
            os.environ['LD_LIBRARY_PATH'] = ':'.join(extra) + (':' + current if current else '')
        os.environ['_ONNX_NVIDIA_LD_PATH_DONE'] = '1'
    except Exception as e:
        logging.debug('无法补全 NVIDIA 库路径: %s', e)


# 模块导入时即生效，供非 Docker 直跑 python 的场景使用（须在 import onnxruntime 之前）
prepend_nvidia_lib_paths()
