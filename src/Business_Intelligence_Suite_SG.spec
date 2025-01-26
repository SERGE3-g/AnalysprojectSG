# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['mainG.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        ('./backup', 'backup'),
        ('./build', 'build'),
        ('./data', 'data'),
        ('./dist', 'dist'),
        ('./qrcodes', 'qrcodes'),
        ('./report_output', 'report_output'),
        ('./reports', 'reports'),
        ('./config.json', '.'),
        ('./login_manager.py', '.'),
        ('./registration_window.py', '.'),
        ('./login_window.py', '.'),
        ('./sla_analyzer.py', '.'),
        ('./file_analyzer.py', '.'),
        ('./fiscal_analyzer.py', '.'),
        ('./inventory_manager.py', '.'),
        ('./user_management.py', '.'),
        ('./mainG.py', '.'),
        ('./test_analyzer_tab.py', '.'),
        ('./init_db.py', '.'),
        ('./user_utils.py', '.'),
        ('./user_management.py', '.'),
        ('./utils.py', '.'),
        ('./login_manager.py', '.')

    ],
    hiddenimports=[
        'tkinter',
        'PIL',
        'login_manager',
        'registration_window',
        'login_window',
        'sla_analyzer',
        'file_analyzer',
        'fiscal_analyzer',
        'inventory_manager',
        'user_management',
        'mainG',
        'test_analyzer_tab',
        'init_db',
        'user_utils',
        'user_management',
        'utils',
        'login_manager',
        # 'reportlab',
        #
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='Business_Intelligence_Suite_SG',
    debug=True,
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
)

app = BUNDLE(
    exe,
    name='Business_Intelligence_Suite_SG.app',
    icon=None,
    bundle_identifier=None,
)