build_version = "1.3.0"
python_path = "C:\\Python26\\"

import shutil
shutil.copy(python_path + "Scripts\deluge-script.py", python_path + "Scripts\deluge.py")
shutil.copy(python_path + "Scripts\deluge-script.py", python_path + "Scripts\deluge-debug.py")
shutil.copy(python_path + "Scripts\deluged-script.py", python_path + "Scripts\deluged.py")
shutil.copy(python_path + "Scripts\deluge-web-script.py", python_path + "Scripts\deluge-web.py")
shutil.copy(python_path + "Scripts\deluge-gtk-script.py", python_path + "Scripts\deluge-gtk.py")
shutil.copy(python_path + "Scripts\deluge-console-script.py", python_path + "Scripts\deluge-console.py")

includes=("libtorrent", "gzip", "zipfile", "re", "socket", "struct", "cairo", "pangocairo", "atk", "pango", "wsgiref.handlers", "twisted.internet.utils", "gio", "gtk.glade")
excludes=("numpy", "OpenGL", "psyco")

dst = "..\\build-win32\\deluge-bbfreeze-" + build_version

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


import icon
icon.CopyIcons(dst+"\\deluge.exe", "deluge.ico")  
icon.CopyIcons(dst+"\\deluge-debug.exe", "deluge.ico")
icon.CopyIcons(dst+"\\deluged.exe", "deluge.ico")  
icon.CopyIcons(dst+"\\deluge-web.exe", "deluge.ico")  
icon.CopyIcons(dst+"\\deluge-gtk.exe", "deluge.ico")  
icon.CopyIcons(dst+"\\deluge-console.exe", "deluge.ico")  
