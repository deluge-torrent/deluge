build_version = "1.2.0_rc1"
python_path = "C:\\Python26\\"

import shutil
shutil.copy(python_path + "Scripts\deluge-script.py", python_path + "Scripts\deluge.py")
shutil.copy(python_path + "Scripts\deluged-script.py", python_path + "Scripts\deluged.py")

from bbfreeze import Freezer
f = Freezer("..\\build-win32\\deluge-bbfreeze-" + build_version, includes=("libtorrent", "gzip", "zipfile", "re", "socket", "struct", "cairo", "pangocairo", "atk", "pango"))
f.addScript(python_path + "Scripts\deluge.py", gui_only=False)
f.addScript(python_path + "Scripts\deluged.py", gui_only=False)
f()    # starts the freezing process
