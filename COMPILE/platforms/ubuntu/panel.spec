# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec：EasyAIoT PANEL → Ubuntu 单文件可执行程序
# 由 targets/ubuntu/Dockerfile 在容器内调用。

import os

block_cipher = None

PANEL_DIR = os.environ.get('PANEL_SRC', '/src/PANEL')
UI_DIST = os.path.join(PANEL_DIR, 'ui', 'dist')

if not os.path.isfile(os.path.join(UI_DIST, 'index.html')):
    raise SystemExit(f'UI dist missing: {UI_DIST}/index.html — build PANEL/ui first')

a = Analysis(
    [os.path.join(PANEL_DIR, 'run_panel.py')],
    pathex=[PANEL_DIR],
    binaries=[],
    datas=[],
    hiddenimports=[
        'flask',
        'jinja2',
        'jinja2.ext',
        'werkzeug',
        'werkzeug.serving',
        'itsdangerous',
        'click',
        'blinker',
        'psutil',
        'requests',
        'urllib3',
        'certifi',
        'charset_normalizer',
        'idna',
        'docker_ops',
        'stack_ops',
        'topology',
        'panel_server',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

a.datas += Tree(UI_DIST, prefix='ui/dist')

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='easyaiot-panel',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
