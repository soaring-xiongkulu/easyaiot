# -*- mode: python ; coding: utf-8 -*-
# Windows PyInstaller spec for EasyAIoT PANEL

import os

PANEL_DIR = os.environ.get('PANEL_SRC')
if not PANEL_DIR:
    raise SystemExit('PANEL_SRC is required')

UI_DIST = os.path.join(PANEL_DIR, 'ui', 'dist')
if not os.path.isfile(os.path.join(UI_DIST, 'index.html')):
    raise SystemExit(f'UI dist missing: {UI_DIST}/index.html')

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
    noarchive=False,
)

a.datas += Tree(UI_DIST, prefix='ui/dist')

pyz = PYZ(a.pure)

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
    console=True,
)
