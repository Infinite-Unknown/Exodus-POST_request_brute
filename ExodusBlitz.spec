# -*- mode: python ; coding: utf-8 -*-
import os
import certifi

conda_dir = os.path.join(SPECPATH, '.conda')

a = Analysis(
    ['blitz.py'],
    pathex=[
        os.path.join(conda_dir, 'DLLs'),
        os.path.join(conda_dir, 'Library', 'bin'),
    ],
    binaries=[
        (os.path.join(conda_dir, 'Library', 'bin', 'tcl86t.dll'), '.'),
        (os.path.join(conda_dir, 'Library', 'bin', 'tk86t.dll'), '.'),
        (os.path.join(conda_dir, 'Library', 'bin', 'ffi.dll'), '.'),
        (os.path.join(conda_dir, 'Library', 'bin', 'ffi-8.dll'), '.'),
        (os.path.join(conda_dir, 'DLLs', '_ctypes.pyd'), '.'),
        (os.path.join(conda_dir, 'DLLs', '_tkinter.pyd'), '.'),
        # SSL support
        (os.path.join(conda_dir, 'DLLs', '_ssl.pyd'), '.'),
        (os.path.join(conda_dir, 'Library', 'bin', 'libssl-3-x64.dll'), '.'),
        (os.path.join(conda_dir, 'Library', 'bin', 'libcrypto-3-x64.dll'), '.'),
    ],
    datas=[
        (os.path.join(conda_dir, 'Library', 'lib', 'tcl8.6'), 'tcl/tcl8.6'),
        (os.path.join(conda_dir, 'Library', 'lib', 'tk8.6'), 'tcl/tk8.6'),
        # SSL certificates
        (certifi.where(), '.'),
    ],
    hiddenimports=['keyboard'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='ExodusBlitz',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['Assets\\icon.png'],
)
