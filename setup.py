#!/usr/bin/env python
#
# setup.py
#
# Copyright (C) 2007 Andrew Resch <andrewresch@gmail.com>
#               2009 Damien Churchill <damoxc@gmail.com>
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
#   The Free Software Foundation, Inc.,
#   51 Franklin Street, Fifth Floor
#   Boston, MA    02110-1301, USA.
#

try:
    from setuptools import setup, find_packages, Extension
except ImportError:
    import ez_setup
    ez_setup.use_setuptools()
    from setuptools import setup, find_packages, Extension

import glob
import sys

from distutils import cmd, sysconfig
from distutils.command.build import build as _build
from distutils.command.build_ext import build_ext as _build_ext
from distutils.command.clean import clean as _clean
try:
    from sphinx.setup_command import BuildDoc
except ImportError:
    class BuildDoc(object):
        pass

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
    "-DBOOST_FILESYSTEM_VERSION=2",
    "-DBOOST_ASIO_SEPARATE_COMPILATION",
    "-O2",
    ]

if windows_check():
    _extra_compile_args += [
        "-D__USE_W32_SOCKETS",
        "-D_WIN32_WINNT=0x0500",
        "-D_WIN32",
        "-DWIN32_LEAN_AND_MEAN",
        "-DBOOST_ALL_NO_LIB",
        "-DBOOST_THREAD_USE_LIB",
        "-DBOOST_WINDOWS",
        "-DBOOST_WINDOWS_API",
        "-DWIN32",
        "-DUNICODE",
        "-D_UNICODE",
        "-D_SCL_SECURE_NO_WARNINGS",
        "/O2",
        "/Ob2",
        "/W3",
        "/GR",
        "/MD",
        "/wd4675",
        "/Zc:wchar_t",
        "/Zc:forScope",
        "/EHsc",
        "-c",
        ]
else:
    _extra_compile_args += ["-Wno-missing-braces"]

def remove_from_cflags(flags):
    if not windows_check():
        keys = ["OPT", "CFLAGS"]
        if python_version == '2.5':
            keys = ["CFLAGS"]

        for key in keys:
            cv_opt = sysconfig.get_config_vars()[key]
            for flag in flags:
                cv_opt = cv_opt.replace(flag, " ")
            sysconfig.get_config_vars()[key] = " ".join(cv_opt.split())

removals = ["-Wstrict-prototypes"]
remove_from_cflags(removals)

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
        'boost_filesystem-vc-mt-1_37',
        'boost_date_time-vc-mt-1_37',
        'boost_iostreams-vc-mt-1_37',
        'boost_python-vc-mt-1_37',
        'boost_system-vc-mt-1_37',
        'boost_thread-vc-mt-1_37',
        'gdi32',
        'libeay32',
        'ssleay32',
        'ws2_32',
        'wsock32',
        'zlib'
    ]
else:
    _include_dirs += [
        '/usr/include/python' + python_version,
        sysconfig.get_config_var("INCLUDEDIR")
        ]
    for include in os.environ.get("INCLUDEDIR", "").split(":"):
        _include_dirs.append(include)

    _library_dirs += [sysconfig.get_config_var("LIBDIR"), '/opt/local/lib', '/usr/local/lib']
    if osx_check():
        _include_dirs += [
            '/opt/local/include/boost-1_35',
            '/opt/local/include/boost-1_36',
            '/usr/local/include'
            '/sw/include/boost-1_35',
            '/sw/include/boost'
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

        _lib_extensions = ['-mt', '-mt_1_39', '-mt-1_38', '-mt-1_37', '-mt-1_36', '-mt-1_35']

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
    from deluge._libtorrent import lt
except ImportError:
    build_libtorrent = True
else:
    build_libtorrent = False

if build_libtorrent:
    got_libtorrent = False
    if not os.path.exists("libtorrent"):
        import subprocess
        if subprocess.call(['./get_libtorrent.sh']) > 0:
            got_libtorrent = False
        else:
            got_libtorrent = True
    else:
        got_libtorrent = True

    if got_libtorrent:
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

desktop_data = 'deluge/data/share/applications/deluge.desktop'

class build_trans(cmd.Command):
    description = 'Compile .po files into .mo files & create .desktop file'

    user_options = [
            ('build-lib', None, "lib build folder")
    ]

    def initialize_options(self):
        self.build_lib = None

    def finalize_options(self):
        self.set_undefined_options('build', ('build_lib', 'build_lib'))

    def run(self):
        po_dir = os.path.join(os.path.dirname(__file__), 'deluge/i18n/')

        if not windows_check():
            # creates the translated desktop file
            INTLTOOL_MERGE='intltool-merge'
            INTLTOOL_MERGE_OPTS='--utf8 --quiet --desktop-style'
            desktop_in='deluge/data/share/applications/deluge.desktop.in'
            print 'Creating desktop file: %s' % desktop_data
            os.system('C_ALL=C ' + '%s '*5 % (INTLTOOL_MERGE, INTLTOOL_MERGE_OPTS, \
                        po_dir, desktop_in, desktop_data))

        print 'Compiling po files from %s...' % po_dir,
        for path, names, filenames in os.walk(po_dir):
            for f in filenames:
                uptoDate = False
                if f.endswith('.po'):
                    lang = f[:len(f) - 3]
                    src = os.path.join(path, f)
                    dest_path = os.path.join(self.build_lib, 'deluge', 'i18n', lang, \
                        'LC_MESSAGES')
                    dest = os.path.join(dest_path, 'deluge.mo')
                    if not os.path.exists(dest_path):
                        os.makedirs(dest_path)
                    if not os.path.exists(dest):
                        sys.stdout.write('%s, ' % lang)
                        sys.stdout.flush()
                        msgfmt.make(src, dest)
                    else:
                        src_mtime = os.stat(src)[8]
                        dest_mtime = os.stat(dest)[8]
                        if src_mtime > dest_mtime:
                            sys.stdout.write('%s, ' % lang)
                            sys.stdout.flush()
                            msgfmt.make(src, dest)
                        else:
                            uptoDate = True

        if uptoDate:
            sys.stdout.write(' po files already upto date.  ')
        sys.stdout.write('\b\b \nFinished compiling translation files. \n')

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

        for path in glob.glob(PLUGIN_PATH):
            if os.path.exists(os.path.join(path, "setup.py")):
                os.system("cd " + path + "&& " + sys.executable + " setup.py bdist_egg -d ..")


class develop_plugins(cmd.Command):
    description = "install plugin's in 'development mode'"

    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        # Build the plugin eggs
        PLUGIN_PATH = "deluge/plugins/*"

        for path in glob.glob(PLUGIN_PATH):
            if os.path.exists(os.path.join(path, "setup.py")):
                os.system("cd " + path + "&& " + sys.executable + " setup.py develop")


class egg_info_plugins(cmd.Command):
    description = "create a distribution's .egg-info directory"

    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        # Build the plugin eggs
        PLUGIN_PATH = "deluge/plugins/*"

        for path in glob.glob(PLUGIN_PATH):
            if os.path.exists(os.path.join(path, "setup.py")):
                os.system("cd " + path + "&& " + sys.executable + " setup.py egg_info")


class build_docs(BuildDoc):
    def run(self):
        class FakeModule(object):
            def __init__(self, *args, **kwargs): pass

            def __call__(self, *args, **kwargs):
                return FakeModule()

            def __getattr__(self, key):
                return FakeModule()

            def __setattr__(self, key, value):
                self.__dict__[key] = value

        old_import = __builtins__.__import__
        def new_import(name, globals={}, locals={}, fromlist=[], level=-1):
            try:
                return old_import(name, globals, locals, fromlist, level)
            except ImportError:
                return FakeModule()
            except Exception, e:
                print "Skipping Exception: ", e
                return FakeModule()
        __builtins__.__import__ = new_import

        BuildDoc.run(self)

class build(_build):
    sub_commands = [('build_trans', None), ('build_plugins', None)] + _build.sub_commands
    def run(self):
        # Run all sub-commands (at least those that need to be run)
        _build.run(self)

class build_debug(build):
    sub_commands = [x for x in build.sub_commands if x[0] != 'build_ext'] + [('build_ext_debug', None)]

class build_ext_debug(_build_ext):

    def run(self):
        if not self.distribution.ext_modules:
            return _build_ext.run(self)

        lt_ext = None
        for ext in self.distribution.ext_modules:
            if ext.name == 'libtorrent':
                lt_ext = ext

        if not lt_ext:
            return _build_ext.run(self)

        lt_ext.extra_compile_args.remove('-DNDEBUG')
        lt_ext.extra_compile_args.remove('-O2')
        lt_ext.extra_compile_args.append('-g')
        remove_from_cflags(["-DNDEBUG", "-O2"])
        return _build_ext.run(self)

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
        print "Cleaning the plugin's folders.."

        PLUGIN_PATH = "deluge/plugins/*"

        for path in glob.glob(PLUGIN_PATH):
            if os.path.exists(os.path.join(path, "setup.py")):
                c = "cd " + path + "&& " + sys.executable + " setup.py clean"
                if self.all:
                    c += " -a"
                os.system(c)

            # Delete the .eggs
            if path[-4:] == ".egg":
                print "Deleting %s" % path
                os.remove(path)

        EGG_INFO_DIR_PATH = "deluge/plugins/*/*.egg-info"

        for path in glob.glob(EGG_INFO_DIR_PATH):
            # Delete the .egg-info's directories
            if path[-9:] == ".egg-info":
                print "Deleting %s" % path
                for fpath in os.listdir(path):
                    os.remove(os.path.join(path, fpath))
                os.removedirs(path)

        ROOT_EGG_INFO_DIR_PATH = "deluge*.egg-info"

        for path in glob.glob(ROOT_EGG_INFO_DIR_PATH):
            print "Deleting %s" % path
            for fpath in os.listdir(path):
                os.remove(os.path.join(path, fpath))
            os.removedirs(path)

class clean(_clean):
    sub_commands = _clean.sub_commands + [('clean_plugins', None)]

    def run(self):
        # Run all sub-commands (at least those that need to be run)
        for cmd_name in self.get_sub_commands():
            self.run_command(cmd_name)
        _clean.run(self)

        if os.path.exists(desktop_data):
            print "Deleting %s" % desktop_data
            os.remove(desktop_data)

cmdclass = {
    'build': build,
    'build_trans': build_trans,
    'build_plugins': build_plugins,
    'build_docs': build_docs,
    'build_debug': build_debug,
    'build_ext_debug': build_ext_debug,
    'clean_plugins': clean_plugins,
    'clean': clean,
    'develop_plugins': develop_plugins,
    'egg_info_plugins': egg_info_plugins
}

# Data files to be installed to the system.
_data_files = []
if not windows_check() and not osx_check():
    _data_files = [
        ('share/icons/hicolor/scalable/apps', ['deluge/data/icons/scalable/apps/deluge.svg']),
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
        ('share/pixmaps', ['deluge/data/pixmaps/deluge.png', 'deluge/data/pixmaps/deluge.xpm']),
        ('share/man/man1', [
            'docs/man/deluge.1',
            'docs/man/deluged.1',
            'docs/man/deluge-gtk.1',
            'docs/man/deluge-web.1',
            'docs/man/deluge-console.1'])
    ]

    if os.path.exists(desktop_data):
        _data_files.append(('share/applications', [desktop_data]))

entry_points = {
    "console_scripts": [
        "deluge-console = deluge.ui.console:start",
        "deluge-web = deluge.ui.web:start",
        "deluged = deluge.main:start_daemon"
    ],
    "gui_scripts": [
        "deluge = deluge.main:start_ui",
        "deluge-gtk = deluge.ui.gtkui:start"
    ]
}


if windows_check():
    entry_points["console_scripts"].append("deluge-debug = deluge.main:start_ui")

# Main setup
setup(
    name = "deluge",
    version = "1.3.15",
    fullname = "Deluge Bittorrent Client",
    description = "Bittorrent Client",
    author = "Andrew Resch, Damien Churchill",
    author_email = "andrewresch@gmail.com, damoxc@gmail.com",
    keywords = "torrent bittorrent p2p fileshare filesharing",
    long_description = """Deluge is a bittorrent client that utilizes a
        daemon/client model. There are various user interfaces available for
        Deluge such as the GTKui, the webui and a console ui. Deluge uses
        libtorrent in it's backend to handle the bittorrent protocol.""",
    url = "http://deluge-torrent.org",
    license = "GPLv3",
    cmdclass = cmdclass,
    data_files = _data_files,
    ext_package = "deluge",
    ext_modules = _ext_modules,
    package_data = {"deluge": ["ui/gtkui/glade/*.glade",
                                "data/pixmaps/*.png",
                                "data/pixmaps/*.svg",
                                "data/pixmaps/*.ico",
                                "data/pixmaps/*.gif",
                                "data/pixmaps/flags/*.png",
                                "plugins/*.egg",
                                "i18n/*/LC_MESSAGES/*.mo",
                                "ui/web/gettext.js",
                                "ui/web/index.html",
                                "ui/web/css/*.css",
                                "ui/web/icons/*.png",
                                "ui/web/images/*.gif",
                                "ui/web/images/*.png",
                                "ui/web/js/*.js",
                                "ui/web/js/*/*.js",
                                "ui/web/js/*/.order",
                                "ui/web/js/*/*/*.js",
                                "ui/web/js/*/*/.order",
                                "ui/web/render/*.html",
                                "ui/web/themes/css/*.css",
                                "ui/web/themes/images/*/*.gif",
                                "ui/web/themes/images/*/*.png",
                                "ui/web/themes/images/*/*/*.gif",
                                "ui/web/themes/images/*/*/*.png"
                                ]},
    packages = find_packages(exclude=["plugins", "docs", "tests"]),
    entry_points = entry_points
)
