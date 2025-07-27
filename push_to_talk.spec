# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['main_gui.py'],  # Changed from main.py to main_gui.py
    pathex=[],
    binaries=[],
    datas=[
        ('src', 'src'),
        ('.env.example', '.'),
        ('icon.ico', '.'),  # Include icon in data files
    ],
    hiddenimports=[
        'pywin32',
        'pywintypes',
        'tkinter',  # Added tkinter for GUI
        'tkinter.ttk',  # Added ttk for modern widgets
        'tkinter.messagebox',  # Added messagebox for dialogs
        'tkinter.filedialog',  # Added filedialog for file operations
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

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='PushToTalk',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Changed from True to False for GUI application
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.ico',
)
