import os, glob, sys
import shutil
import deluge.common

# Get build_version from installed deluge
build_version = deluge.common.get_version()
print "Deluge Version: %s" % build_version
python_path = os.path.dirname(sys.executable) + "\\"
print "Python Path: %s" % python_path
gtk_root = python_path + "Lib\\site-packages\\gtk-2.0\\runtime\\"

# Copy entry scripts with new name, which represents final .exe filename
shutil.copy(python_path + "Scripts\deluge-script.pyw", python_path + "Scripts\deluge.py")
shutil.copy(python_path + "Scripts\deluge-script.pyw", python_path + "Scripts\deluge-debug.py")
shutil.copy(python_path + "Scripts\deluged-script.py", python_path + "Scripts\deluged.py")
shutil.copy(python_path + "Scripts\deluged-script.py", python_path + "Scripts\deluged-debug.py")
shutil.copy(python_path + "Scripts\deluge-web-script.py", python_path + "Scripts\deluge-web.py")
shutil.copy(python_path + "Scripts\deluge-web-script.py", python_path + "Scripts\deluge-web-debug.py")
shutil.copy(python_path + "Scripts\deluge-gtk-script.pyw", python_path + "Scripts\deluge-gtk.py")
shutil.copy(python_path + "Scripts\deluge-console-script.py", python_path + "Scripts\deluge-console.py")

# Include python modules not picked up automatically by bbfreeze
includes=(
            "libtorrent", "cairo", "pangocairo", "atk", "pango", "twisted.internet.utils",
            "gio", "gzip", "email.mime.multipart", "email.mime.text"
         )
excludes=("numpy", "OpenGL", "psyco", "win32ui")

dst = "..\\build-win32\\deluge-bbfreeze-" + build_version + "\\"

# Need to override bbfreeze function so that it includes all gtk libraries
# in the installer so users don't require a separate GTK+ installation.
import bbfreeze.recipes
def recipe_gtk_override(mf):
    return True
bbfreeze.recipes.recipe_gtk_and_friends = recipe_gtk_override

from bbfreeze import Freezer
f = Freezer(dst, includes=includes, excludes=excludes)
f.include_py = False
f.addScript(python_path + "Scripts\deluge.py", gui_only=True)
f.addScript(python_path + "Scripts\deluge-debug.py", gui_only=False)
f.addScript(python_path + "Scripts\deluged.py", gui_only=True)
f.addScript(python_path + "Scripts\deluged-debug.py", gui_only=False)
f.addScript(python_path + "Scripts\deluge-web.py", gui_only=True)
f.addScript(python_path + "Scripts\deluge-web-debug.py", gui_only=False)
f.addScript(python_path + "Scripts\deluge-gtk.py", gui_only=True)
f.addScript(python_path + "Scripts\deluge-console.py", gui_only=False)
f()    # starts the freezing process

# add icons to the exe files
import icon
icon_path = os.path.join(os.path.dirname(__file__), "deluge.ico")
icon.CopyIcons(dst+"deluge.exe", icon_path)
icon.CopyIcons(dst+"deluge-debug.exe", icon_path)
icon.CopyIcons(dst+"deluged.exe", icon_path)
icon.CopyIcons(dst+"deluged-debug.exe", icon_path)
icon.CopyIcons(dst+"deluge-web.exe", icon_path)
icon.CopyIcons(dst+"deluge-web-debug.exe", icon_path)
icon.CopyIcons(dst+"deluge-gtk.exe", icon_path)
icon.CopyIcons(dst+"deluge-console.exe", icon_path)

# exclude files which are already included in GTK or Windows
excludeDlls = ("MSIMG32.dll", "MSVCR90.dll", "MSVCP90.dll", "POWRPROF.dll", "DNSAPI.dll", "USP10.dll")
for file in excludeDlls:
    for filename in glob.glob(dst + file):
        print "removing file:", filename
        os.remove(filename)

# copy gtk locale files
gtk_locale = os.path.join(gtk_root, 'share/locale')
locale_include_list = ['gtk20.mo', 'locale.alias']
def ignored_files(adir,filenames):
    return [
        filename for filename in filenames
        if not os.path.isdir(os.path.join(adir, filename))
        and filename not in locale_include_list
        ]
shutil.copytree(gtk_locale, os.path.join(dst, 'share/locale'), ignore=ignored_files)

# copy gtk theme files
theme_include_list = [
    "share/icons/hicolor/index.theme",
    "lib/gtk-2.0/2.10.0/engines",
    "share/themes/MS-Windows",
    "etc/gtk-2.0/gtkrc"]
for path in theme_include_list:
    full_path = os.path.join(gtk_root, path)
    if os.path.isdir(full_path):
        shutil.copytree(full_path, os.path.join(dst, path))
    else:
        dst_dir = os.path.join(dst, os.path.dirname(path))
        try:
            os.makedirs(dst_dir)
        except:
            pass
        shutil.copy(full_path, dst_dir)

file = open('VERSION.tmp', 'w')
file.write("build_version = \"%s\"" % build_version)
file.close()
