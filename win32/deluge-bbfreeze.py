build_version = "1.2.2"
python_path = "C:\\Python26\\"

import shutil
shutil.copy(python_path + "Scripts\deluge-script.py", python_path + "Scripts\deluge.py")
shutil.copy(python_path + "Scripts\deluged-script.py", python_path + "Scripts\deluged.py")
shutil.copy(python_path + "Scripts\deluge-web-script.py", python_path + "Scripts\deluge-web.py")
shutil.copy(python_path + "Scripts\deluge-gtk-script.py", python_path + "Scripts\deluge-gtk.py")
shutil.copy(python_path + "Scripts\deluge-console-script.py", python_path + "Scripts\deluge-console.py")


from bbfreeze import Freezer
f = Freezer("..\\build-win32\\deluge-bbfreeze-" + build_version, includes=("libtorrent", "gzip", "zipfile", "re", "socket", "struct", "cairo", "pangocairo", "atk", "pango", "wsgiref.handlers", "twisted.internet.utils", "gio", "gtk.glade"))
f.addScript(python_path + "Scripts\deluge.py", gui_only=False)
f.addScript(python_path + "Scripts\deluged.py", gui_only=False)
f.addScript(python_path + "Scripts\deluge-web.py", gui_only=False)
f.addScript(python_path + "Scripts\deluge-gtk.py", gui_only=False)
f.addScript(python_path + "Scripts\deluge-console.py", gui_only=False)
f()    # starts the freezing process
