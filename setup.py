#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2007 Andrew Resch <andrewresch@gmail.com>
# Copyright (C) 2009 Damien Churchill <damoxc@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

import glob
import os
import platform
import sys
from distutils import cmd
from distutils.command.build import build as _build
from distutils.command.clean import clean as _clean

from setuptools import find_packages, setup
from setuptools.command.test import test as _test

import msgfmt
from version import get_version

try:
    from sphinx.setup_command import BuildDoc
except ImportError:
    class BuildDoc(object):
        pass


def windows_check():
    return platform.system() in ('Windows', 'Microsoft')

desktop_data = 'deluge/ui/data/share/applications/deluge.desktop'


class PyTest(_test):

    def initialize_options(self):
        _test.initialize_options(self)
        self.pytest_args = []

    def finalize_options(self):
        _test.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        import pytest
        errcode = pytest.main(self.test_args)
        sys.exit(errcode)


class BuildTranslations(cmd.Command):
    description = 'Compile .po files into .mo files & create .desktop file'

    user_options = [
        ('build-lib', None, "lib build folder"),
        ('develop', 'D', 'Compile translations in develop mode (deluge/i18n)')
    ]
    boolean_options = ['develop']

    def initialize_options(self):
        self.build_lib = None
        self.develop = False

    def finalize_options(self):
        self.set_undefined_options('build', ('build_lib', 'build_lib'))

    def run(self):
        po_dir = os.path.join(os.path.dirname(__file__), 'deluge/i18n/')

        if self.develop:
            basedir = po_dir
        else:
            basedir = os.path.join(self.build_lib, 'deluge', 'i18n')

        if not windows_check():
            # creates the translated desktop file
            intltool_merge = 'intltool-merge'
            intltool_merge_opts = '--utf8 --quiet --desktop-style'
            desktop_in = 'deluge/ui/data/share/applications/deluge.desktop.in'
            print('Creating desktop file: %s' % desktop_data)
            os.system('C_ALL=C ' + '%s ' * 5 % (intltool_merge, intltool_merge_opts,
                                                po_dir, desktop_in, desktop_data))

        print('Compiling po files from %s...' % po_dir),
        for path, names, filenames in os.walk(po_dir):
            for f in filenames:
                upto_date = False
                if f.endswith('.po'):
                    lang = f[:len(f) - 3]
                    src = os.path.join(path, f)
                    dest_path = os.path.join(basedir, lang, 'LC_MESSAGES')
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
                            upto_date = True

        if upto_date:
            sys.stdout.write(' po files already upto date.  ')
        sys.stdout.write('\b\b \nFinished compiling translation files. \n')


class BuildPlugins(cmd.Command):
    description = "Build plugins into .eggs"

    user_options = [
        ('install-dir=', None, "develop install folder"),
        ('develop', 'D', 'Compile plugins in develop mode')
    ]
    boolean_options = ['develop']

    def initialize_options(self):
        self.install_dir = None
        self.develop = False

    def finalize_options(self):
        pass

    def run(self):
        # Build the plugin eggs
        plugin_path = "deluge/plugins/*"

        for path in glob.glob(plugin_path):
            if os.path.exists(os.path.join(path, "setup.py")):
                if self.develop and self.install_dir:
                    os.system("cd " + path + "&& " + sys.executable +
                              " setup.py develop --install-dir=%s" % self.install_dir)
                elif self.develop:
                    os.system("cd " + path + "&& " + sys.executable + " setup.py develop")
                else:
                    os.system("cd " + path + "&& " + sys.executable + " setup.py bdist_egg -d ..")


class EggInfoPlugins(cmd.Command):
    description = "create a distribution's .egg-info directory"

    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        # Build the plugin eggs
        plugin_path = "deluge/plugins/*"

        for path in glob.glob(plugin_path):
            if os.path.exists(os.path.join(path, "setup.py")):
                os.system("cd " + path + "&& " + sys.executable + " setup.py egg_info")


class Build(_build):
    sub_commands = [('build_trans', None), ('build_plugins', None)] + _build.sub_commands

    def run(self):
        # Run all sub-commands (at least those that need to be run)
        _build.run(self)
        try:
            from deluge._libtorrent import lt
            print "Found libtorrent version: %s" % lt.version
        except ImportError, e:
            print "Warning libtorrent not found: %s" % e


class CleanPlugins(cmd.Command):
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
        print("Cleaning the plugin's folders..")

        plugin_path = "deluge/plugins/*"

        for path in glob.glob(plugin_path):
            if os.path.exists(os.path.join(path, "setup.py")):
                c = "cd " + path + " && " + sys.executable + " setup.py clean"
                if self.all:
                    c += " -a"
                print("Calling '%s'" % c)
                os.system(c)

            # Delete the .eggs
            if path[-4:] == ".egg":
                print("Deleting %s" % path)
                os.remove(path)

        egg_info_dir_path = "deluge/plugins/*/*.egg-info"

        for path in glob.glob(egg_info_dir_path):
            # Delete the .egg-info's directories
            if path[-9:] == ".egg-info":
                print("Deleting %s" % path)
                for fpath in os.listdir(path):
                    os.remove(os.path.join(path, fpath))
                os.removedirs(path)

        root_egg_info_dir_path = "deluge*.egg-info"

        for path in glob.glob(root_egg_info_dir_path):
            print("Deleting %s" % path)
            for fpath in os.listdir(path):
                os.remove(os.path.join(path, fpath))
            os.removedirs(path)


class Clean(_clean):
    sub_commands = _clean.sub_commands + [('clean_plugins', None)]

    def run(self):
        # Run all sub-commands (at least those that need to be run)
        for cmd_name in self.get_sub_commands():
            self.run_command(cmd_name)
        _clean.run(self)

        if os.path.exists(desktop_data):
            print("Deleting %s" % desktop_data)
            os.remove(desktop_data)

cmdclass = {
    'build': Build,
    'build_trans': BuildTranslations,
    'build_plugins': BuildPlugins,
    'build_docs': BuildDoc,
    'clean_plugins': CleanPlugins,
    'clean': Clean,
    'egg_info_plugins': EggInfoPlugins,
    'test': PyTest,
}

# Data files to be installed to the system
_data_files = [
    ('share/icons/hicolor/scalable/apps', ['deluge/ui/data/icons/hicolor/scalable/apps/deluge.svg']),
    ('share/icons/hicolor/128x128/apps', ['deluge/ui/data/icons/hicolor/128x128/apps/deluge.png']),
    ('share/icons/hicolor/16x16/apps', ['deluge/ui/data/icons/hicolor/16x16/apps/deluge.png']),
    ('share/icons/hicolor/192x192/apps', ['deluge/ui/data/icons/hicolor/192x192/apps/deluge.png']),
    ('share/icons/hicolor/22x22/apps', ['deluge/ui/data/icons/hicolor/22x22/apps/deluge.png']),
    ('share/icons/hicolor/24x24/apps', ['deluge/ui/data/icons/hicolor/24x24/apps/deluge.png']),
    ('share/icons/hicolor/256x256/apps', ['deluge/ui/data/icons/hicolor/256x256/apps/deluge.png']),
    ('share/icons/hicolor/32x32/apps', ['deluge/ui/data/icons/hicolor/32x32/apps/deluge.png']),
    ('share/icons/hicolor/36x36/apps', ['deluge/ui/data/icons/hicolor/36x36/apps/deluge.png']),
    ('share/icons/hicolor/48x48/apps', ['deluge/ui/data/icons/hicolor/48x48/apps/deluge.png']),
    ('share/icons/hicolor/64x64/apps', ['deluge/ui/data/icons/hicolor/64x64/apps/deluge.png']),
    ('share/icons/hicolor/72x72/apps', ['deluge/ui/data/icons/hicolor/72x72/apps/deluge.png']),
    ('share/icons/hicolor/96x96/apps', ['deluge/ui/data/icons/hicolor/96x96/apps/deluge.png']),
    ('share/pixmaps', ['deluge/ui/data/pixmaps/deluge.png', 'deluge/ui/data/pixmaps/deluge.xpm']),
    ('share/man/man1', [
        'docs/man/deluge.1',
        'docs/man/deluged.1',
        'docs/man/deluge-gtk.1',
        'docs/man/deluge-web.1',
        'docs/man/deluge-console.1'])
]

if not windows_check() and os.path.exists(desktop_data):
    _data_files.append(('share/applications', [desktop_data]))

entry_points = {
    "console_scripts": [
        "deluge-console = deluge.ui.console:start"
    ],
    "gui_scripts": [
        "deluge = deluge.main:start_ui",
        "deluge-gtk = deluge.ui.gtkui:start",
        "deluge-web = deluge.ui.web:start",
        "deluged = deluge.main:start_daemon"
    ]
}

if windows_check():
    entry_points["console_scripts"].extend([
        "deluge-debug = deluge.main:start_ui",
        "deluge-web-debug = deluge.ui.web:start",
        "deluged-debug = deluge.main:start_daemon"])

# Main setup
setup(
    name="deluge",
    version=get_version(prefix='deluge-', suffix='.dev0'),
    fullname="Deluge Bittorrent Client",
    description="Bittorrent Client",
    author="Andrew Resch, Damien Churchill",
    author_email="andrewresch@gmail.com, damoxc@gmail.com",
    keywords="torrent bittorrent p2p fileshare filesharing",
    long_description="""Deluge is a bittorrent client that utilizes a
        daemon/client model. There are various user interfaces available for
        Deluge such as the GTKui, the webui and a console ui. Deluge uses
        libtorrent in it's backend to handle the bittorrent protocol.""",
    url="http://deluge-torrent.org",
    license="GPLv3",
    cmdclass=cmdclass,
    tests_require=['pytest'],
    data_files=_data_files,
    package_data={"deluge": ["ui/gtkui/glade/*.glade",
                             "ui/gtkui/glade/*.ui",
                             "ui/data/pixmaps/*.png",
                             "ui/data/pixmaps/*.svg",
                             "ui/data/pixmaps/*.ico",
                             "ui/data/pixmaps/*.gif",
                             "ui/data/pixmaps/flags/*.png",
                             "plugins/*.egg",
                             "i18n/*/LC_MESSAGES/*.mo",
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
                             "ui/web/js/*/*/*/*.js",
                             "ui/web/render/*.html",
                             "ui/web/themes/css/*.css",
                             "ui/web/themes/images/*/*.gif",
                             "ui/web/themes/images/*/*.png",
                             "ui/web/themes/images/*/*/*.gif",
                             "ui/web/themes/images/*/*/*.png"
                             ]},
    packages=find_packages(exclude=["plugins", "docs", "tests"]),
    namespace_packages=["deluge", "deluge.plugins"],
    entry_points=entry_points
)
