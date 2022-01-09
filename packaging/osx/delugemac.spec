
# -*- mode: python ; coding: utf-8 -*-
import os
import sys
import deluge.common
from PyInstaller.utils.hooks import collect_submodules, copy_metadata

datas = []
binaries = []
hiddenimports = []

# Collect Meta Data
datas += copy_metadata('deluge', recursive=True)
datas += copy_metadata('service-identity', recursive=True)

# Add Deluge Hidden Imports
hiddenimports += collect_submodules('deluge')

# Add Hidden Imports for Plugins
# Add stdlib as Hidden Imports.
# This is filtered list that excludes some common examples or stuff not useful in plugins (such as tty, mailbox, tutledemo etc.).
# It is safe to assume that 90% of that list would already be included anyway.
stdlib = [ 'pickle', 'json', 'email', 'http', 'marshal', 'uuid', 'base64', 'string', 'struct', 'glob', 'ssl', 'urllib', 'html', 'sys',
  'crypt', 'datetime', 'hmac', 'locale', 'queue', 're', 'enum', 'collections', 'tokenize', 'hashlib', 'xml', 'csb', 'ipaddress', 'os' ]
for module in stdlib:
    hiddenimports += collect_submodules('twisted', filter=lambda name: 'test' not in name)
datas += copy_metadata('twisted', recursive=True)

#Copy UI/Plugin files to where pyinstaller expects
datas += [ ('../../deluge/ui', 'deluge/ui'),
           ('../../deluge/plugins', 'deluge/plugins') ]

block_cipher = None


a = Analysis([os.path.abspath(os.path.join(HOMEPATH,os.pardir,os.pardir,os.pardir)) + '/bin/deluge-console'],
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

b = Analysis([os.path.abspath(os.path.join(HOMEPATH,os.pardir,os.pardir,os.pardir)) + '/bin/deluge-gtk'],
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

c = Analysis([os.path.abspath(os.path.join(HOMEPATH,os.pardir,os.pardir,os.pardir)) + '/bin/deluged'],
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

#f = Analysis([os.path.abspath(os.path.join(HOMEPATH,os.pardir,os.pardir,os.pardir)) + '/bin/deluge'],
#             pathex=[],
#             binaries=binaries,
#             datas=datas,
#             hiddenimports=hiddenimports,
#             hookspath=[],
#             hooksconfig={},
#             runtime_hooks=[],
#             excludes=[],
#             win_no_prefer_redirects=False,
#             win_private_assemblies=False,
#             cipher=block_cipher,
#             noarchive=False)
#pyzf = PYZ(f.pure, f.zipped_data,
#             cipher=block_cipher)
#exef = EXE(pyzf,
#          f.scripts,
#          [],
#          exclude_binaries=True,
#          name='deluge',
#          debug=False,
#          bootloader_ignore_signals=False,
#          strip=False,
#          upx=True,
#          icon='../../deluge/ui/data/pixmaps/deluge.ico',
#          console=False,
#          disable_windowed_traceback=False,
#          target_arch=None,
#          codesign_identity=None,
#          entitlements_file=None )

h = Analysis([os.path.abspath(os.path.join(HOMEPATH,os.pardir,os.pardir,os.pardir)) + '/bin/deluge-web'],
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
               #exef,
               #f.binaries,
               #f.zipfiles,
               #f.datas,
               exeh,
               h.binaries,
               h.zipfiles,
               h.datas,
               strip=False,
               upx=True,
               upx_exclude=[],
               name='Deluge')

if sys.platform == 'darwin':
  app = BUNDLE(coll,
               name='Deluge.app',
               bundle_identifier=None,
               icon='../../deluge/ui/data/pixmaps/deluge.ico',
               version=deluge.common.get_version(),
               info_plist={
                 'NSPrincipalClass': 'NSApplication',
                 'NSAppleScriptEnabled': False,
               })
