
# -*- mode: python ; coding: utf-8 -*-
import os
import sys
from PyInstaller.utils.hooks import collect_submodules, copy_metadata

datas = []
binaries = []
hiddenimports = ['pygame']

# Collect Meta Data
datas += copy_metadata('deluge', recursive=True)
datas += copy_metadata('service-identity', recursive=True)

# Add Deluge Hidden Imports
hiddenimports += collect_submodules('deluge')

# Add Hidden Imports for Plugins
# Add stdlib as Hidden Imports.
# This is filtered list that excludes some common examples or stuff not useful in plugins (such as tty, mailbox, tutledemo etc.).
# It is safe to assume that 90% of that list would already be included anyway.
if sys.version_info.major >= 3 and sys.version_info.minor < 10:
    stdlib = [ 'string', 're', 'unicodedata', 'struct', 'codecs', 'datetime', 'zoneinfo', 'calendar', 'collections', 'array', 'weakref',
    'types', 'copy', 'enum', 'numbers', 'math', 'cmath', 'decimal', 'fractions', 'random', 'statistics', 'itertools', 'functools',
    'operator', 'pathlib', 'fileinput', 'stat', 'tempfile', 'glob', 'fnmatch', 'shutil', 'pickle', 'copyreg', 'shelve', 'marshal',
    'dom', 'sqlite3', 'zlib', 'gzip', 'bz2', 'lzma', 'csv', 'hashlib', 'hmac', 'secrets', 'os', 'io', 'time', 'logging', 'platform',
    'errno', 'queue', 'socket', 'ssl', 'email', 'json', 'mimetypes', 'base64', 'binhex', 'binascii', 'quopri', 'uu', 'html', 'xml',
    'urllib', 'http', 'ftplib', 'smtplib', 'uuid', 'xmlrpc.client', 'ipaddress', 'locale', 'sys' ]
    for module in stdlib:
        hiddenimports += collect_submodules(module, filter=lambda name: 'test' not in name)
if sys.version_info.major >= 3 and sys.version_info.minor >= 10:
    for module in sys.stdlib_module_names:
        hiddenimports += collect_submodules(module, filter=lambda name: 'test' not in name)
hiddenimports += collect_submodules('twisted', filter=lambda name: 'test' not in name)
datas += copy_metadata('twisted', recursive=True)

#Copy UI/Plugin files to where pyinstaller expects
datas += [ ('../../deluge/ui', 'deluge/ui'),
           ('../../deluge/plugins', 'deluge/plugins') ]


block_cipher = None


a = Analysis([os.path.abspath(os.path.join(HOMEPATH,os.pardir,os.pardir)) + '\Scripts\deluge-console-script.py'],
             pathex=[],
             binaries=binaries,
             datas=datas,
             hiddenimports=hiddenimports,
             hookspath=[],
             hooksconfig={},
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          [],
          exclude_binaries=True,
          name='deluge-console',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          icon='../../deluge/ui/data/pixmaps/deluge.ico',
          console=True,
          disable_windowed_traceback=False,
          target_arch=None,
          codesign_identity=None,
          entitlements_file=None )

b = Analysis([os.path.abspath(os.path.join(HOMEPATH,os.pardir,os.pardir)) + '\Scripts\deluge-gtk-script.pyw'],
             pathex=[],
             binaries=binaries,
             datas=datas,
             hiddenimports=hiddenimports,
             hookspath=[],
             hooksconfig={},
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyzb = PYZ(b.pure, b.zipped_data,
             cipher=block_cipher)
exeb = EXE(pyzb,
          b.scripts,
          [],
          exclude_binaries=True,
          name='deluge-gtk',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          icon='../../deluge/ui/data/pixmaps/deluge.ico',
          console=False,
          disable_windowed_traceback=False,
          target_arch=None,
          codesign_identity=None,
          entitlements_file=None )

c = Analysis([os.path.abspath(os.path.join(HOMEPATH,os.pardir,os.pardir)) + '\Scripts\deluged-script.py'],
             pathex=[],
             binaries=binaries,
             datas=datas,
             hiddenimports=hiddenimports,
             hookspath=[],
             hooksconfig={},
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyzc = PYZ(c.pure, c.zipped_data,
             cipher=block_cipher)

exec = EXE(pyzc,
          c.scripts,
          [],
          exclude_binaries=True,
          name='deluged',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          icon='../../deluge/ui/data/pixmaps/deluge.ico',
          console=False,
          disable_windowed_traceback=False,
          target_arch=None,
          codesign_identity=None,
          entitlements_file=None )

d = Analysis([os.path.abspath(os.path.join(HOMEPATH,os.pardir,os.pardir)) + '\Scripts\deluged-debug-script.py'],
             pathex=[],
             binaries=binaries,
             datas=datas,
             hiddenimports=hiddenimports,
             hookspath=[],
             hooksconfig={},
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyzd = PYZ(d.pure, d.zipped_data,
             cipher=block_cipher)
exed = EXE(pyzd,
          d.scripts,
          [],
          exclude_binaries=True,
          name='deluged-debug',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          icon='../../deluge/ui/data/pixmaps/deluge.ico',
          console=True,
          disable_windowed_traceback=False,
          target_arch=None,
          codesign_identity=None,
          entitlements_file=None )

e = Analysis([os.path.abspath(os.path.join(HOMEPATH,os.pardir,os.pardir)) + '\Scripts\deluge-debug-script.py'],
             pathex=[],
             binaries=binaries,
             datas=datas,
             hiddenimports=hiddenimports,
             hookspath=[],
             hooksconfig={},
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyze = PYZ(e.pure, e.zipped_data,
             cipher=block_cipher)
exee = EXE(pyze,
          e.scripts,
          [],
          exclude_binaries=True,
          name='deluge-debug',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          icon='../../deluge/ui/data/pixmaps/deluge.ico',
          console=True,
          disable_windowed_traceback=False,
          target_arch=None,
          codesign_identity=None,
          entitlements_file=None )

f = Analysis([os.path.abspath(os.path.join(HOMEPATH,os.pardir,os.pardir)) + '\Scripts\deluge-script.pyw'],
             pathex=[],
             binaries=binaries,
             datas=datas,
             hiddenimports=hiddenimports,
             hookspath=[],
             hooksconfig={},
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyzf = PYZ(f.pure, f.zipped_data,
             cipher=block_cipher)
exef = EXE(pyzf,
          f.scripts,
          [],
          exclude_binaries=True,
          name='deluge',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          icon='../../deluge/ui/data/pixmaps/deluge.ico',
          console=False,
          disable_windowed_traceback=False,
          target_arch=None,
          codesign_identity=None,
          entitlements_file=None )

g = Analysis([os.path.abspath(os.path.join(HOMEPATH,os.pardir,os.pardir)) + '\Scripts\deluge-web-debug-script.py'],
             pathex=[],
             binaries=binaries,
             datas=datas,
             hiddenimports=hiddenimports,
             hookspath=[],
             hooksconfig={},
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyzg = PYZ(g.pure, g.zipped_data,
             cipher=block_cipher)
exeg = EXE(pyzg,
          g.scripts,
          [],
          exclude_binaries=True,
          name='deluge-web-debug',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          icon='../../deluge/ui/data/pixmaps/deluge.ico',
          console=True,
          disable_windowed_traceback=False,
          target_arch=None,
          codesign_identity=None,
          entitlements_file=None )

h = Analysis([os.path.abspath(os.path.join(HOMEPATH,os.pardir,os.pardir)) + '\Scripts\deluge-web-script.py'],
             pathex=[],
             binaries=binaries,
             datas=datas,
             hiddenimports=hiddenimports,
             hookspath=[],
             hooksconfig={},
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyzh = PYZ(h.pure, h.zipped_data,
             cipher=block_cipher)
exeh = EXE(pyzh,
          h.scripts,
          [],
          exclude_binaries=True,
          name='deluge-web',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          icon='../../deluge/ui/data/pixmaps/deluge.ico',
          console=False,
          disable_windowed_traceback=False,
          target_arch=None,
          codesign_identity=None,
          entitlements_file=None )

coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               exeb,
               b.binaries,
               b.zipfiles,
               b.datas,
               exec,
               c.binaries,
               c.zipfiles,
               c.datas,
               exed,
               d.binaries,
               d.zipfiles,
               d.datas,
               exee,
               e.binaries,
               e.zipfiles,
               e.datas,
               exef,
               f.binaries,
               f.zipfiles,
               f.datas,
               exeg,
               g.binaries,
               g.zipfiles,
               g.datas,
               exeh,
               h.binaries,
               h.zipfiles,
               h.datas,
               strip=False,
               upx=True,
               upx_exclude=[],
               name='Deluge')
