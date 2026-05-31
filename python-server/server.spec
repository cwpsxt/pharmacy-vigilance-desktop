# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec - properly bundles numpy/pandas C extensions

from PyInstaller.utils.hooks import collect_all

block_cipher = None

# 收集 numpy 全部数据/二进制/隐式依赖（修复 numpy C-extension 导入失败）
numpy_datas, numpy_binaries, numpy_hidden = collect_all('numpy')
pandas_datas, pandas_binaries, pandas_hidden = collect_all('pandas')
crypto_datas, crypto_binaries, crypto_hidden = collect_all('cryptography')

a = Analysis(
    ['run.py'],
    pathex=[],
    binaries=numpy_binaries + pandas_binaries + crypto_binaries,
    datas=[
        ('static', 'static'),
        ('data', 'data'),
        ('uploads', 'uploads'),
    ] + numpy_datas + pandas_datas + crypto_datas,
    hiddenimports=[
        'flask',
        'flask_cors',
        'flask_sqlalchemy',
        'sqlalchemy',
        'sqlalchemy.dialects.sqlite',
        'bcrypt',
        'openpyxl',
        'xlrd',
        'matplotlib',
        'matplotlib.backends.backend_agg',
        'docx',
        'requests',
        'urllib3',
        'charset_normalizer',
        'idna',
        'certifi',
        'werkzeug',
        'jinja2',
        'markupsafe',
        'click',
        'itsdangerous',
        'cryptography',
        'cryptography.fernet',
        'cryptography.hazmat.primitives.serialization',
        'cryptography.hazmat.primitives.asymmetric.ed25519',
        'app.license',
        'app.license_crypto',
    ] + numpy_hidden + pandas_hidden + crypto_hidden,
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
    name='server',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='../electron/assets/icon.ico',
)
