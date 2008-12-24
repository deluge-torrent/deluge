#
# setup.py
#
# Copyright (C) 2007 Andrew Resch <andrewresch@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3, or (at your option)
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

import ez_setup
ez_setup.use_setuptools()
import glob

from setuptools import setup, find_packages, Extension
from distutils import cmd, sysconfig
from distutils.command.build import build as _build
from distutils.command.clean import clean as _clean
from setuptools.command.install import install as _install

import msgfmt
import os
import platform

python_version = platform.python_version()[0:3]

def windows_check():
    return platform.system() in ('Windows', 'Microsoft')

def osx_check():
    return platform.system() == "Darwin"

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
        "-DBOOST_ALL_DYN_LINK",
        "-DBOOST_THREAD_USE_LIB",
        "-DBOOST_WINDOWS",
        "-DBOOST_WINDOWS_API",
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
    './libtorrent/include/libtorrent'
]

if windows_check():
    _include_dirs += ['./win32/include','./win32/include/openssl', './win32/include/zlib']
    _library_dirs += ['./win32/lib']
    _libraries = [
        'advapi32',
        'boost_filesystem-vc71-mt-1_36',
        'boost_date_time-vc71-mt-1_36',
        'boost_iostreams-vc71-mt-1_36',
        'boost_python-vc71-mt-1_36',
        'boost_system-vc71-mt-1_36',
        'boost_thread-vc71-mt-1_36',
        'gdi32',
        'libeay32MT',
        'ssleay32MT',
        'ws2_32',
        'wsock32',
        'zlib'
    ]
else:
    _include_dirs += [
        '/usr/include/python' + python_version,
        sysconfig.get_config_var("INCLUDEDIR")
        ]
    _library_dirs += [sysconfig.get_config_var("LIBDIR"), '/opt/local/lib']
    if osx_check():
        _include_dirs += [
            '/opt/local/include/boost-1_35',
            '/opt/local/include/boost-1_36'
        ]
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

    if not windows_check():
        dynamic_lib_extension = ".so"
        if osx_check():
            dynamic_lib_extension = ".dylib"

        _lib_extensions = ['-mt-1_36', '-mt-1_35', '-mt']

        # Modify the libs if necessary for systems with only -mt boost libs
        for lib in _libraries:
            if lib[:6] == "boost_":
                for lib_prefix in _library_dirs:
                    for lib_suffix in _lib_extensions:
                        # If there is a -mt version use that
                        if os.path.exists(os.path.join(lib_prefix, "lib" + lib + lib_suffix + dynamic_lib_extension)):
                            _libraries[_libraries.index(lib)] = lib + lib_suffix
                            lib = lib + lib_suffix
                            break

_sources = glob.glob("./libtorrent/src/*.cpp") + \
                        glob.glob("./libtorrent/src/*.c") + \
                        glob.glob("./libtorrent/src/kademlia/*.cpp") + \
                        glob.glob("./libtorrent/bindings/python/src/*.cpp")

# Remove some files from the source that aren't needed
_source_removals = ["mapped_storage.cpp", "memdebug.cpp"]
to_remove = []
for source in _sources:
    for rem in _source_removals:
        if rem in source:
            to_remove.append(source)

for rem in to_remove:
    _sources.remove(rem)

_ext_modules = []

# Check for a system libtorrent and if found, then do not build the libtorrent extension
build_libtorrent = True
try:
    import libtorrent
except ImportError:
    build_libtorrent = True
else:
    if libtorrent.version_major == 0 and libtorrent.version_minor == 14:
        build_libtorrent = False

if build_libtorrent:
    # There isn't a system libtorrent library, so let's build the one included with deluge
    libtorrent = Extension(
        'libtorrent',
        extra_compile_args = _extra_compile_args,
        include_dirs = _include_dirs,
        libraries = _libraries,
        library_dirs = _library_dirs,
        sources = _sources
    )

    _ext_modules = [libtorrent]

class build_trans(cmd.Command):
    description = 'Compile .po files into .mo files'

    user_options = [
            ('build-lib', None, "lib build folder")
    ]

    def initialize_options(self):
        self.build_lib = None

    def finalize_options(self):
        self.set_undefined_options('build', ('build_lib', 'build_lib'))

    def run(self):
        po_dir = os.path.join(os.path.dirname(__file__), 'deluge/i18n/')
        for path, names, filenames in os.walk(po_dir):
            for f in filenames:
                if f.endswith('.po'):
                    lang = f[:len(f) - 3]
                    src = os.path.join(path, f)
                    dest_path = os.path.join(self.build_lib, 'deluge', 'i18n', lang, \
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

class build_plugins(cmd.Command):
    description = "Build plugins into .eggs"

    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        # Build the plugin eggs
        PLUGIN_PATH = "deluge/plugins/*"
        if windows_check():
            PLUGIN_PATH = "deluge\\plugins\\"

        for path in glob.glob(PLUGIN_PATH):
            if os.path.exists(os.path.join(path, "setup.py")):
                os.system("cd " + path + "&& python setup.py bdist_egg -d ..")

class build(_build):
    sub_commands = [('build_trans', None), ('build_plugins', None)] + _build.sub_commands
    def run(self):
        # Run all sub-commands (at least those that need to be run)
        _build.run(self)

class clean_plugins(cmd.Command):
    description = "Cleans the plugin folders"
    user_options = [
         ('all', 'a', "remove all build output, not just temporary by-products")
    ]
    boolean_options = ['all']

    def initialize_options(self):
        self.all = None

    def finalize_options(self):
        self.set_undefined_options('clean', ('all', 'all'))

    def run(self):
        print("Cleaning the plugin folders..")

        PLUGIN_PATH = "deluge/plugins/*"
        if windows_check():
            PLUGIN_PATH = "deluge\\plugins\\"

        for path in glob.glob(PLUGIN_PATH):
            if os.path.exists(os.path.join(path, "setup.py")):
                c = "cd " + path + "&& python setup.py clean"
                if self.all:
                    c += " -a"
                os.system(c)

            # Delete the .eggs
            if path[-4:] == ".egg":
                print("Deleting %s" % path)
                os.remove(path)

class clean(_clean):
    sub_commands = _clean.sub_commands + [('clean_plugins', None)]

    def run(self):
        # Run all sub-commands (at least those that need to be run)
        for cmd_name in self.get_sub_commands():
            self.run_command(cmd_name)
        _clean.run(self)

class install(_install):
    def run(self):
        for cmd_name in self.get_sub_commands():
            self.run_command(cmd_name)
        _install.run(self)
        if not self.root:
            self.do_egg_install()

cmdclass = {
    'build': build,
    'build_trans': build_trans,
    'build_plugins': build_plugins,
    'clean_plugins': clean_plugins,
    'clean': clean,
    'install': install
}

# Data files to be installed to the system
_data_files = [
    ('share/icons/scalable/apps', ['deluge/data/icons/scalable/apps/deluge.svg']),
    ('share/icons/hicolor/128x128/apps', ['deluge/data/icons/hicolor/128x128/apps/deluge.png']),
    ('share/icons/hicolor/16x16/apps', ['deluge/data/icons/hicolor/16x16/apps/deluge.png']),
    ('share/icons/hicolor/192x192/apps', ['deluge/data/icons/hicolor/192x192/apps/deluge.png']),
    ('share/icons/hicolor/22x22/apps', ['deluge/data/icons/hicolor/22x22/apps/deluge.png']),
    ('share/icons/hicolor/24x24/apps', ['deluge/data/icons/hicolor/24x24/apps/deluge.png']),
    ('share/icons/hicolor/256x256/apps', ['deluge/data/icons/hicolor/256x256/apps/deluge.png']),
    ('share/icons/hicolor/32x32/apps', ['deluge/data/icons/hicolor/32x32/apps/deluge.png']),
    ('share/icons/hicolor/36x36/apps', ['deluge/data/icons/hicolor/36x36/apps/deluge.png']),
    ('share/icons/hicolor/48x48/apps', ['deluge/data/icons/hicolor/48x48/apps/deluge.png']),
    ('share/icons/hicolor/64x64/apps', ['deluge/data/icons/hicolor/64x64/apps/deluge.png']),
    ('share/icons/hicolor/72x72/apps', ['deluge/data/icons/hicolor/72x72/apps/deluge.png']),
    ('share/icons/hicolor/96x96/apps', ['deluge/data/icons/hicolor/96x96/apps/deluge.png']),
    ('share/applications', ['deluge/data/share/applications/deluge.desktop']),
    ('share/pixmaps', ['deluge/data/pixmaps/deluge.png', 'deluge/data/pixmaps/deluge.xpm']),
    ('share/man/man1', ['deluge/docs/man/deluge.1', 'deluge/docs/man/deluged.1'])
]

# Main setup
setup(
    author = "Andrew Resch, Marcos Pinto, Martijn Voncken, Sadrul Habib Chowdhury",
    author_email = "andrewresch@gmail.com, markybob@dipconsultants.com, mvoncken@gmail.com, sadrul@users.sourceforge.net",
    cmdclass = cmdclass,
    data_files = _data_files,
    description = "Bittorrent Client",
    long_description = """Deluge is a bittorrent client that utilizes a
        daemon/client model.  There are various user interfaces available for
        Deluge such as the GTKui, the webui and a console ui.  Deluge uses
        libtorrent in it's backend to handle the bittorrent protocol.""",
    keywords = "torrent bittorrent p2p fileshare filesharing",
    entry_points = """
        [console_scripts]
            deluge = deluge.main:start_ui
            deluged = deluge.main:start_daemon
    """,
    ext_package = "deluge",
    ext_modules = _ext_modules,
    fullname = "Deluge Bittorrent Client",
    include_package_data = True,
    license = "GPLv3",
    name = "deluge",
    package_data = {"deluge": ["ui/gtkui/glade/*.glade",
                                "data/pixmaps/*.png",
                                "data/pixmaps/*.svg",
                                "data/pixmaps/*.ico",
                                "data/pixmaps/flags/*.png",
                                "data/revision",
                                "data/GeoIP.dat",
                                "plugins/*.egg",
                                "i18n/*.pot",
                                "i18n/*/LC_MESSAGES/*.mo",
                                "ui/webui/scripts/*",
                                "ui/webui/ssl/*",
                                "ui/webui/static/*.css",
                                "ui/webui/static/*.js",
                                "ui/webui/static/images/*.png",
                                "ui/webui/static/images/*.jpg",
                                "ui/webui/static/images/*.gif",
                                "ui/webui/static/images/16/*.png",
                                "ui/webui/templates/deluge/*",
                                "ui/webui/templates/classic/*",
                                "ui/webui/templates/white/*",
                                "ui/webui/templates/ajax/*.cfg",
                                "ui/webui/templates/ajax/*.js",
                                "ui/webui/templates/ajax/*.html",
                                "ui/webui/templates/ajax/*.css",
                                "ui/webui/templates/ajax/render/html/*.html",
                                "ui/webui/templates/ajax/render/js/*",
                                "ui/webui/templates/ajax/static/css/*.css",
                                "ui/webui/templates/ajax/static/icons/16/*.png",
                                "ui/webui/templates/ajax/static/icons/32/*.png",
                                "ui/webui/templates/ajax/static/images/*.gif",
                                "ui/webui/templates/ajax/static/js/*.js",
                                "ui/webui/templates/ajax/static/themes/classic/*",
                                "ui/webui/templates/ajax/static/themes/white/*"
                                ]},
    packages = find_packages(exclude=["plugins"]),
    url = "http://deluge-torrent.org",
    version = "1.1.0_RC1",
)
