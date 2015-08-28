import glob
import os
import shutil
import sys

import bbfreeze.recipes
import deluge.common
import icon
from bbfreeze import Freezer
from gi.repository import Gtk  # NOQA

# Get build_version from installed deluge
build_version = deluge.common.get_version()
print "Deluge Version: %s" % build_version
python_path = os.path.dirname(sys.executable)
if python_path.endswith("Scripts"):
    python_path = python_path[:-8]
python_path += os.path.sep

print "Python Path: %s" % python_path
gtk_root = os.path.join(os.path.dirname(sys.executable), "\\Lib\\site-packages\\gnome")

# Include python modules not picked up automatically by bbfreeze
includes = ("libtorrent", "twisted.internet.utils",
            "gzip", "email.mime.multipart", "email.mime.text")
excludes = ("numpy", "OpenGL", "psyco", "win32ui")

dst = "..\\build-win32\\deluge-bbfreeze-" + build_version + "\\"


# Need to override bbfreeze function so that it includes all gtk libraries
# in the installer so users don't require a separate GTK+ installation.
def recipe_gtk_override(mf):
    return True
bbfreeze.recipes.recipe_gtk_and_friends = recipe_gtk_override

f = Freezer(dst, includes=includes, excludes=excludes)
f.include_py = False
# Can/should we grab this from setup.py entry_points somehow
gui_scripts = ["deluge", "deluged", "deluge-web", "deluge-gtk"]
console_scripts = ["deluge-debug", "deluged-debug", "deluge-web-debug", "deluge-console"]

# Copy the scripts to get rid of the '-script' suffix before adding to freezer
for script in gui_scripts:
    shutil.copy(python_path + "Scripts/%s-script.pyw" % script, python_path + "Scripts/%s.pyw" % script)
    f.addScript(python_path + "Scripts/%s.pyw" % script, gui_only=True)
for script in console_scripts:
    shutil.copy(python_path + "Scripts/%s-script.py" % script, python_path + "Scripts/%s.py" % script)
    f.addScript(python_path + "Scripts/%s.py" % script, gui_only=False)
f()    # starts the freezing process

# Clean up the duplicated scripts
for script in gui_scripts:
    os.remove(python_path + "Scripts/%s.pyw" % script)
for script in console_scripts:
    os.remove(python_path + "Scripts/%s.py" % script)

# add icons to the exe files
icon_path = os.path.join(os.path.dirname(__file__), "deluge.ico")
for script in console_scripts + gui_scripts:
    icon.CopyIcons(dst + script + ".exe", icon_path)

# exclude files which are already included in GTK or Windows
excludeDlls = ("MSIMG32.dll", "MSVCR90.dll", "MSVCP90.dll", "POWRPROF.dll", "DNSAPI.dll", "USP10.dll")
for file in excludeDlls:
    for filename in glob.glob(dst + file):
        print "removing file:", filename
        os.remove(filename)

# copy gtk locale files
gtk_locale = os.path.join(gtk_root, 'share/locale')
locale_include_list = ['gtk20.mo', 'locale.alias']


def ignored_files(adir, filenames):
    return [
        filename for filename in filenames
        if not os.path.isdir(os.path.join(adir, filename))
        and filename not in locale_include_list
    ]
shutil.copytree(gtk_locale, os.path.join(dst, 'share/locale'), ignore=ignored_files)

file = open('VERSION.tmp', 'w')
file.write("build_version = \"%s\"" % build_version)
file.close()
