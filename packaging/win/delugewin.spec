# -*- mode: python -*-
import os

from PyInstaller.utils.hooks import (
    collect_data_files,
    collect_submodules,
    copy_metadata,
)

datas = []
binaries = []
hiddenimports = ['pygame', 'ifaddr']

# Collect Meta Data
datas += copy_metadata('deluge', recursive=True)
datas += copy_metadata('service-identity', recursive=True)

# Add Deluge Hidden Imports
hiddenimports += collect_submodules('deluge')

# Add stdlib as Hidden Imports.
# This is filtered list that excludes some common examples or stuff not useful in
# plugins (such as tty, mailbox, turtledemo etc.).
# It is safe to assume that 90% of that list would already be included anyway.
stdlib = [
    'string',
    're',
    'unicodedata',
    'struct',
    'codecs',
    'datetime',
    'zoneinfo',
    'calendar',
    'collections',
    'array',
    'weakref',
    'types',
    'copy',
    'enum',
    'numbers',
    'math',
    'cmath',
    'decimal',
    'fractions',
    'random',
    'statistics',
    'itertools',
    'functools',
    'operator',
    'pathlib',
    'fileinput',
    'stat',
    'tempfile',
    'glob',
    'fnmatch',
    'shutil',
    'pickle',
    'copyreg',
    'shelve',
    'marshal',
    'dom',
    'sqlite3',
    'zlib',
    'gzip',
    'bz2',
    'lzma',
    'csv',
    'hashlib',
    'hmac',
    'secrets',
    'os',
    'io',
    'time',
    'logging',
    'platform',
    'errno',
    'queue',
    'socket',
    'ssl',
    'email',
    'json',
    'mimetypes',
    'base64',
    'binhex',
    'binascii',
    'quopri',
    'uu',
    'html',
    'xml',
    'urllib',
    'http',
    'ftplib',
    'smtplib',
    'uuid',
    'xmlrpc.client',
    'ipaddress',
    'locale',
    'sys',
]
for module in stdlib:
    hiddenimports += collect_submodules(module, filter=lambda name: 'test' not in name)

# Add Hidden Imports for Plugins
hiddenimports += collect_submodules('twisted', filter=lambda name: 'test' not in name)
datas += copy_metadata('twisted', recursive=True)

# Copy UI/Plugin and translation files to where pyinstaller expects
package_data = collect_data_files('deluge')
datas += package_data

icon = [src for src, dest in package_data if src.endswith('deluge.ico')][0]

# List of executables to produce
executables = {
    'deluge-script.pyw': {'name': 'deluge', 'console': False, 'gtk': True},
    'deluge-gtk-script.pyw': {'name': 'deluge-gtk', 'console': False, 'gtk': True},
    'deluge-debug-script.py': {'name': 'deluge-debug', 'console': True, 'gtk': True},
    'deluge-console-script.py': {
        'name': 'deluge-console',
        'console': True,
        'gtk': False,
    },
    'deluged-script.pyw': {'name': 'deluged', 'console': False, 'gtk': False},
    'deluged-debug-script.py': {'name': 'deluged-debug', 'console': True, 'gtk': False},
    'deluge-web-debug-script.py': {
        'name': 'deluge-web-debug',
        'console': True,
        'gtk': False,
    },
    'deluge-web-script.pyw': {'name': 'deluge-web', 'console': False, 'gtk': False},
}

analysis = {}
exe = {}
coll = []

# Perform analysis
for e, d in executables.items():
    runtime_hooks = []
    if d['gtk']:
        runtime_hooks += [os.path.join(SPECPATH, 'pyi_rth_gtk_csd.py')]

    analysis[e] = Analysis(
        [os.path.abspath(os.path.join(HOMEPATH, os.pardir, os.pardir, 'Scripts', e))],
        pathex=[],
        binaries=binaries,
        datas=datas,
        hiddenimports=hiddenimports,
        hookspath=[],
        hooksconfig={},
        runtime_hooks=runtime_hooks,
        excludes=[],
        win_no_prefer_redirects=False,
        win_private_assemblies=False,
        cipher=None,
        noarchive=False,
    )

# Executable
for e, d in executables.items():
    exe[e] = EXE(
        PYZ(analysis[e].pure, analysis[e].zipped_data, cipher=None),
        analysis[e].scripts,
        [],
        exclude_binaries=True,
        name=d['name'],
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=True,
        icon=icon,
        console=d['console'],
        disable_windowed_traceback=False,
        target_arch=None,
        codesign_identity=None,
        entitlements_file=None,
    )

# Collect
for e, d in executables.items():
    coll += exe[e], analysis[e].binaries, analysis[e].zipfiles, analysis[e].datas

COLLECT(*coll, strip=False, upx=True, upx_exclude=[], name='Deluge')
