build_version = "1.3.5"
python_path = "C:\\Python26\\"

import os, glob
import shutil
shutil.copy(python_path + "Scripts\deluge-script.pyw", python_path + "Scripts\deluge.py")
shutil.copy(python_path + "Scripts\deluge-script.pyw", python_path + "Scripts\deluge-debug.py")
shutil.copy(python_path + "Scripts\deluged-script.py", python_path + "Scripts\deluged.py")
shutil.copy(python_path + "Scripts\deluge-web-script.py", python_path + "Scripts\deluge-web.py")
shutil.copy(python_path + "Scripts\deluge-gtk-script.pyw", python_path + "Scripts\deluge-gtk.py")
shutil.copy(python_path + "Scripts\deluge-console-script.py", python_path + "Scripts\deluge-console.py")

includes=("libtorrent", "gzip", "zipfile", "re", "socket", "struct", "cairo", "pangocairo", "atk", "pango", "twisted.internet.utils", "gio", "gtk.glade", "email.mime")
excludes=("numpy", "OpenGL", "psyco", "win32ui")

dst = "..\\build-win32\\deluge-bbfreeze-" + build_version + "\\"

from bbfreeze import Freezer
f = Freezer(dst, includes=includes, excludes=excludes)
f.include_py = False
f.addScript(python_path + "Scripts\deluge.py", gui_only=True)
f.addScript(python_path + "Scripts\deluge-debug.py", gui_only=False)
f.addScript(python_path + "Scripts\deluged.py", gui_only=False)
f.addScript(python_path + "Scripts\deluge-web.py", gui_only=False)
f.addScript(python_path + "Scripts\deluge-gtk.py", gui_only=True)
f.addScript(python_path + "Scripts\deluge-console.py", gui_only=False)
f()    # starts the freezing process

# add icons to the exe files
import icon

icon_path = os.path.join(os.path.dirname(__file__), "deluge.ico")
icon.CopyIcons(dst+"deluge.exe", icon_path)
icon.CopyIcons(dst+"deluge-debug.exe", icon_path)
icon.CopyIcons(dst+"deluged.exe", icon_path)  
icon.CopyIcons(dst+"deluge-web.exe", icon_path)  
icon.CopyIcons(dst+"deluge-gtk.exe", icon_path)  
icon.CopyIcons(dst+"deluge-console.exe", icon_path)  

# exclude files which are already included in GTK or Windows
excludeFiles = ("MSIMG32.dll", "MSVCR90.dll", "MSVCP90.dll", "POWRPROF.dll", "DNSAPI.dll", "USP10.dll")
for file in excludeFiles:
    for filename in glob.glob(dst + file):
        print "removing file:", filename
        os.remove(filename)
