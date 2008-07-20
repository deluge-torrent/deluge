# setup.py
#
# Copyright (C) 2007 Andrew Resch ('andar') <andrewresch@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2, or (at your option)
# any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.    See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.    If not, write to:
# 	The Free Software Foundation, Inc.,
# 	51 Franklin Street, Fifth Floor
# 	Boston, MA    02110-1301, USA.
#
#    In addition, as a special exception, the copyright holders give
#    permission to link the code of portions of this program with the OpenSSL
#    library.
#    You must obey the GNU General Public License in all respects for all of
#    the code used other than OpenSSL. If you modify file(s) with this
#    exception, you may extend this exception to your version of the file(s),
#    but you are not obligated to do so. If you do not wish to do so, delete
#    this exception statement from your version. If you delete this exception
#    statement from all source files in the program, then also delete it here.

import ez_setup
ez_setup.use_setuptools()
import glob

from setuptools import setup, find_packages, Extension
from distutils import cmd, sysconfig
from distutils.command.build import build as _build
from distutils.command.install import install as _install
from distutils.command.install_data import install_data as _install_data

import msgfmt
import os
import platform

python_version = platform.python_version()[0:3]

def windows_check():
    import platform
    if platform.system() in ('Windows', 'Microsoft'):
        return True
    else:
        return False

# Try to get SVN revision number to append to version
revision_string = ""
try:
    stdout = os.popen("svn info")
    for line in stdout:
        if line.split(" ")[0] == "Revision:":
            revision_string = line.split(" ")[1].strip()
            break
    # Try to get the SVN revision on Gentoo systems
    if revision_string == "":
        stdout = os.popen("svn info /usr/portage/distfiles/svn-src/deluge/deluge-0.6")
        for line in stdout:
            if line.split(" ")[0] == "Revision:":
                revision_string = line.split(" ")[1].strip()
                break

    f = open("deluge/data/revision", "w")
    f.write(revision_string)
    f.close()
except:
    pass


if not os.environ.has_key("CC"):
    os.environ["CC"] = "gcc"

if not os.environ.has_key("CXX"):
    os.environ["CXX"] = "gcc"

if not os.environ.has_key("CPP"):
    os.environ["CPP"] = "g++"

# The libtorrent extension
_extra_compile_args = [
    "-D_FILE_OFFSET_BITS=64",
    "-DNDEBUG",
    "-DTORRENT_USE_OPENSSL=1",
    "-O2",
    ]

if windows_check():
    _extra_compile_args += [
        "-D__USE_W32_SOCKETS",
        "-D_WIN32_WINNT=0x0500",
        "-D_WIN32",
        "-DWIN32_LEAN_AND_MEAN",
        "-DBOOST_ALL_NO_LIB",
        "-DBOOST_STATIC_LINK",
        "-DBOOST_THREAD_USE_LIB",
        "-DBOOST_WINDOWS",
        "-DBOOST_WINDOWS_API",
        "-DTORRENT_BUILDING_SHARED",
        "-DTORRENT_LINKING_SHARED",
        "-DWIN32",
        "-DUNICODE",
        "-D_UNICODE",
        "/GR",
        "/Zc:wchar_t",
        ]
else:
    _extra_compile_args += ["-Wno-missing-braces"]

removals = ["-Wstrict-prototypes"]

if not windows_check():
    if python_version == '2.5':
        cv_opt = sysconfig.get_config_vars()["CFLAGS"]
        for removal in removals:
            cv_opt = cv_opt.replace(removal, " ")
        sysconfig.get_config_vars()["CFLAGS"] = " ".join(cv_opt.split())
    else:
        cv_opt = sysconfig.get_config_vars()["OPT"]
        for removal in removals:
            cv_opt = cv_opt.replace(removal, " ")
        sysconfig.get_config_vars()["OPT"] = " ".join(cv_opt.split())

_library_dirs = [
]

_include_dirs = [
    './libtorrent',
    './libtorrent/include',
    './libtorrent/include/libtorrent',
]

if windows_check():
    _include_dirs += ['./win32/include','./win32/include/openssl', './win32/include/zlib']
    _library_dirs += ['./win32/lib']
    _libraries = [
        'advapi32',
        'boost_filesystem-vc71-mt-1_35',
        'boost_date_time-vc71-mt-1_35',
        'boost_iostreams-vc71-mt-1_35',
        'boost_python-vc71-mt-1_35',
        'boost_system-vc71-mt-1_35',
        'boost_thread-vc71-mt-1_35',
        'gdi32',
        'libeay32',
        'ssleay32',
        'ws2_32',
        'wsock32',
        'zlib'
    ]
else:
    _include_dirs += ['/usr/include/python' + python_version]
    _libraries = [
        'boost_filesystem',
        'boost_date_time',
        'boost_iostreams',
        'boost_python',
        'boost_thread',
        'pthread',
        'ssl',
        'z'
        ]

_sources = glob.glob("./libtorrent/src/*.cpp") + \
                        glob.glob("./libtorrent/src/*.c") + \
                        glob.glob("./libtorrent/src/kademlia/*.cpp") + \
                        glob.glob("./libtorrent/bindings/python/src/*.cpp")

# Remove some files from the source that aren't needed
_source_removals = ["mapped_storage.cpp"]

for source in _sources:
    for rem in _source_removals:
        if rem in source:
            _sources.remove(source)
            break

libtorrent = Extension(
    'libtorrent',
    extra_compile_args = _extra_compile_args,
    include_dirs = _include_dirs,
    libraries = _libraries,
    library_dirs = _library_dirs,
    sources = _sources
)

class build_trans(cmd.Command):
    description = 'Compile .po files into .mo files'

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        po_dir = os.path.join(os.path.dirname(__file__), 'deluge/i18n/')
        for path, names, filenames in os.walk(po_dir):
            for f in filenames:
                if f.endswith('.po'):
                    lang = f[:len(f) - 3]
                    src = os.path.join(path, f)
                    dest_path = os.path.join('deluge', 'i18n', lang, \
                        'LC_MESSAGES')
                    dest = os.path.join(dest_path, 'deluge.mo')
                    if not os.path.exists(dest_path):
                        os.makedirs(dest_path)
                    if not os.path.exists(dest):
                        print('Compiling %s' % src)
                        msgfmt.make(src, dest)
                    else:
                        src_mtime = os.stat(src)[8]
                        dest_mtime = os.stat(dest)[8]
                        if src_mtime > dest_mtime:
                            print('Compiling %s' % src)
                            msgfmt.make(src, dest)

class build(_build):
    sub_commands = _build.sub_commands + [('build_trans', None)]
    def run(self):
        _build.run(self)

class install_data(_install_data):
    def run(self):
        _install_data.run(self)

cmdclass = {
    'build': build,
    'build_trans': build_trans,
    'install_data': install_data
}

# Build the plugin eggs
PLUGIN_PATH = "deluge/plugins/*"
if windows_check():
    PLUGIN_PATH = "deluge\\plugins\\"

for path in glob.glob(PLUGIN_PATH):
    if os.path.exists(os.path.join(path, "setup.py")):
        os.system("cd " + path + "&& python setup.py bdist_egg -d ..")

# Main setup
PREFIX = "/usr/"
if windows_check():
    PREFIX = ""
_data_files = [(os.path.join(PREFIX, 'share/icons/scalable/apps'), [
                         'deluge/data/icons/scalable/apps/deluge.svg']),
                (os.path.join(PREFIX, 'share/icons/hicolor/128x128/apps'), [
                        'deluge/data/icons/hicolor/128x128/apps/deluge.png']),
                (os.path.join(PREFIX, 'share/icons/hicolor/16x16/apps'), [
                        'deluge/data/icons/hicolor/16x16/apps/deluge.png']),
                (os.path.join(PREFIX, 'share/icons/hicolor/192x192/apps'), [
                        'deluge/data/icons/hicolor/192x192/apps/deluge.png']),
                (os.path.join(PREFIX, 'share/icons/hicolor/22x22/apps'), [
                        'deluge/data/icons/hicolor/22x22/apps/deluge.png']),
                (os.path.join(PREFIX, 'share/icons/hicolor/24x24/apps'), [
                        'deluge/data/icons/hicolor/24x24/apps/deluge.png']),
                (os.path.join(PREFIX, 'share/icons/hicolor/256x256/apps'), [
                        'deluge/data/icons/hicolor/256x256/apps/deluge.png']),
                (os.path.join(PREFIX, 'share/icons/hicolor/32x32/apps'), [
                        'deluge/data/icons/hicolor/32x32/apps/deluge.png']),
                (os.path.join(PREFIX, 'share/icons/hicolor/36x36/apps'), [
                        'deluge/data/icons/hicolor/36x36/apps/deluge.png']),
                (os.path.join(PREFIX, 'share/icons/hicolor/48x48/apps'), [
                        'deluge/data/icons/hicolor/48x48/apps/deluge.png']),
                (os.path.join(PREFIX, 'share/icons/hicolor/64x64/apps'), [
                        'deluge/data/icons/hicolor/64x64/apps/deluge.png']),
                (os.path.join(PREFIX, 'share/icons/hicolor/72x72/apps'), [
                        'deluge/data/icons/hicolor/72x72/apps/deluge.png']),
                (os.path.join(PREFIX, 'share/icons/hicolor/96x96/apps'), [
                        'deluge/data/icons/hicolor/96x96/apps/deluge.png']),
                (os.path.join(PREFIX, 'share/applications'), [
                        'deluge/data/share/applications/deluge.desktop']),
                (os.path.join(PREFIX, 'share/pixmaps'), ['deluge/data/pixmaps/deluge.png'])]
setup(
    author = "Andrew Resch, Marcos Pinto, Martijn Voncken, Sadrul Habib Chowdhury",
    author_email = "andrewresch@gmail.com, markybob@dipconsultants.com, \
        mvoncken@gmail.com, sadrul@users.sourceforge.net",
    cmdclass=cmdclass,
    data_files = _data_files,
    description = "Bittorrent Client",
    entry_points = """
        [console_scripts]
            deluge = deluge.main:start_ui
            deluged = deluge.main:start_daemon
    """,
    ext_package = "deluge",
    ext_modules = [libtorrent],
    fullname = "Deluge Bittorent Client",
    include_package_data = True,
    license = "GPLv2",
    name = "deluge",
    package_data = {"deluge": ["ui/gtkui/glade/*.glade",
                                "data/pixmaps/*.png",
                                "data/pixmaps/*.svg",
                                "data/pixmaps/flags/*.png",
                                "data/revision",
                                "plugins/*.egg",
                                "i18n/*.pot",
                                "i18n/*/LC_MESSAGES/*.mo",
                                "ui/webui/LICENSE",
                                "ui/webui/scripts/*",
                                "ui/webui/ssl/*",
                                "ui/webui/static/*.css",
                                "ui/webui/static/*.js",
                                "ui/webui/static/images/*.png",
                                "ui/webui/static/images/*.jpg",
                                "ui/webui/static/images/*.gif",
                                "ui/webui/static/images/tango/*.png",
                                "ui/webui/templates/deluge/*",
                                "ui/webui/templates/classic/*",
                                "ui/webui/templates/ajax_demo/*.cfg",
                                "ui/webui/templates/ajax_demo/*.html",
                                "ui/webui/templates/ajax_demo/static/js/*",
                                "ui/webui/templates/white/*"
                                ]},
    packages = find_packages(exclude=["plugins"]),
    url = "http://deluge-torrent.org",
    version = "0.9.03",
)

try:
    f = open("deluge/data/revision", "w")
    f.write("")
    f.close()
except:
    pass
