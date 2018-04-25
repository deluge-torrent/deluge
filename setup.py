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

from __future__ import print_function

import glob
import os
import platform
import sys
from distutils import cmd
from distutils.command.build import build as _build
from distutils.command.clean import clean as _clean
from distutils.command.install_data import install_data as _install_data
from shutil import rmtree

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


def osx_check():
    return platform.system() == 'Darwin'


desktop_data = 'deluge/ui/data/share/applications/deluge.desktop'
appdata_data = 'deluge/ui/data/share/appdata/deluge.appdata.xml'

# Variables for setuptools.setup
_package_data = {}
_exclude_package_data = {}
_entry_points = {'console_scripts': [], 'gui_scripts': [], 'deluge.ui': []}
_data_files = []
_version = get_version(prefix='deluge-', suffix='.dev0')


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


class BuildDocs(BuildDoc):
    description = 'Build the documentation'

    def run(self):
        print('Generating module documentation...')
        os.system('sphinx-apidoc --force -o docs/source/modules/ deluge deluge/plugins')
        BuildDoc.run(self)


class CleanDocs(cmd.Command):
    description = 'Clean the documentation build and rst files'
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        for docs_dir in ('docs/build', 'docs/source/modules'):
            try:
                print('Deleting {}'.format(docs_dir))
                rmtree(docs_dir)
            except OSError:
                pass


class BuildWebUI(cmd.Command):
    description = 'Minify WebUI files'
    user_options = []

    JS_DIR = os.path.join('deluge', 'ui', 'web', 'js')
    JS_SRC_DIRS = ('deluge-all', os.path.join('extjs', 'ext-extensions'))

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        js_basedir = os.path.join(os.path.dirname(__file__), self.JS_DIR)

        try:
            from minify_web_js import minify_js_dir
            import_error = ''
        except ImportError as err:
            import_error = err

        for js_src_dir in self.JS_SRC_DIRS:
            source_dir = os.path.join(js_basedir, js_src_dir)
            try:
                minify_js_dir(source_dir)
            except NameError:
                js_file = source_dir + '.js'
                if os.path.isfile(js_file):
                    print('Unable to minify but found existing minified: {}'.format(js_file))
                else:
                    # Unable to minify and no existing minified file found so exiting.
                    print('Import error: %s' % import_error)
                    sys.exit(1)

        # Create the gettext.js file for translations.
        try:
            from gen_web_gettext import create_gettext_js
        except ImportError:
            pass
        else:
            deluge_all_path = os.path.join(js_basedir, self.JS_SRC_DIRS[0])
            print('Creating WebUI translation file: %s/gettext.js' % deluge_all_path)
            create_gettext_js(deluge_all_path)


class CleanWebUI(cmd.Command):
    description = 'Clean the documentation build and rst files'
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        js_basedir = os.path.join(os.path.dirname(__file__), BuildWebUI.JS_DIR)
        for js_src_dir in BuildWebUI.JS_SRC_DIRS:
            for file_type in ('.js', '-debug.js'):
                js_file = os.path.join(js_basedir, js_src_dir + file_type)
                print('Deleting {}'.format(js_file))
                try:
                    os.remove(js_file)
                except OSError:
                    pass


class BuildTranslations(cmd.Command):
    description = 'Compile .po files into .mo files & create .desktop file'

    user_options = [
        ('build-lib', None, 'lib build folder'),
        ('develop', 'D', 'Compile translations in develop mode (deluge/i18n)')
    ]
    boolean_options = ['develop']

    def initialize_options(self):
        self.build_lib = None
        self.develop = False

    def finalize_options(self):
        self.set_undefined_options('build', ('build_lib', 'build_lib'))

    def run(self):
        po_dir = os.path.join(os.path.dirname(__file__), 'deluge', 'i18n')

        if self.develop:
            basedir = po_dir
        else:
            basedir = os.path.join(self.build_lib, 'deluge', 'i18n')

        if not windows_check():
            intltool_merge = 'intltool-merge'
            intltool_merge_opts = '--utf8 --quiet'
            for data_file in (desktop_data, appdata_data):
                # creates the translated file from .in file.
                in_file = data_file + '.in'
                if 'xml' in data_file:
                    intltool_merge_opts += ' --xml-style'
                elif 'desktop' in data_file:
                    intltool_merge_opts += ' --desktop-style'

                print('Creating file: %s' % data_file)
                os.system('C_ALL=C ' + '%s ' * 5 % (
                    intltool_merge, intltool_merge_opts, po_dir, in_file, data_file))

        print('Compiling po files from %s...' % po_dir)
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


class CleanTranslations(cmd.Command):
    description = 'Cleans translations files.'
    user_options = [('all', 'a', 'Remove all build output, not just temporary by-products')]
    boolean_options = ['all']

    def initialize_options(self):
        self.all = None

    def finalize_options(self):
        self.set_undefined_options('clean', ('all', 'all'))

    def run(self):
        for path in (desktop_data, appdata_data):
            if os.path.isfile(path):
                print('Deleting %s' % path)
                os.remove(path)


class BuildPlugins(cmd.Command):
    description = 'Build plugins into .eggs'

    user_options = [
        ('install-dir=', None, 'develop install folder'),
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
        plugin_path = 'deluge/plugins/*'

        for path in glob.glob(plugin_path):
            if os.path.exists(os.path.join(path, 'setup.py')):
                if self.develop and self.install_dir:
                    os.system('cd ' + path + '&& ' + sys.executable +
                              ' setup.py develop --install-dir=%s' % self.install_dir)
                elif self.develop:
                    os.system('cd ' + path + '&& ' + sys.executable + ' setup.py develop')
                else:
                    os.system('cd ' + path + '&& ' + sys.executable + ' setup.py bdist_egg -d ..')


class CleanPlugins(cmd.Command):
    description = 'Cleans the plugin folders'
    user_options = [('all', 'a', 'Remove all build output, not just temporary by-products')]
    boolean_options = ['all']

    def initialize_options(self):
        self.all = None

    def finalize_options(self):
        self.set_undefined_options('clean', ('all', 'all'))

    def run(self):
        print('Cleaning the plugin\'s folders...')

        plugin_path = 'deluge/plugins/*'

        for path in glob.glob(plugin_path):
            if os.path.exists(os.path.join(path, 'setup.py')):
                c = 'cd ' + path + ' && ' + sys.executable + ' setup.py clean'
                if self.all:
                    c += ' -a'
                print('Calling \'%s\'' % c)
                os.system(c)

            # Delete the .eggs
            if path[-4:] == '.egg':
                print('Deleting egg file "%s"' % path)
                os.remove(path)

            # Delete the .egg-link
            if path[-9:] == '.egg-link':
                print('Deleting egg link "%s"' % path)
                os.remove(path)

        egg_info_dir_path = 'deluge/plugins/*/*.egg-info'

        for path in glob.glob(egg_info_dir_path):
            # Delete the .egg-info's directories
            if path[-9:] == '.egg-info':
                print('Deleting %s' % path)
                for fpath in os.listdir(path):
                    os.remove(os.path.join(path, fpath))
                os.removedirs(path)


class EggInfoPlugins(cmd.Command):
    description = 'Create .egg-info directories for plugins'

    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        # Build the plugin eggs
        plugin_path = 'deluge/plugins/*'

        for path in glob.glob(plugin_path):
            if os.path.exists(os.path.join(path, 'setup.py')):
                os.system('cd ' + path + '&& ' + sys.executable + ' setup.py egg_info')


class Build(_build):
    sub_commands = [
        ('build_webui', None),
        ('build_trans', None),
        ('build_plugins', None)
    ] + _build.sub_commands

    def run(self):
        # Run all sub-commands (at least those that need to be run).
        _build.run(self)
        try:
            from deluge._libtorrent import LT_VERSION
            print('Info: Found libtorrent ({}) installed.'.format(LT_VERSION))
        except ImportError as ex:
            print('Warning: libtorrent (libtorrent-rasterbar) not found: %s' % ex)


class InstallData(_install_data):
    """Custom class to fix `setup install` copying data files to incorrect location. (Bug #1389)"""

    def finalize_options(self):
        self.install_dir = None
        self.set_undefined_options('install', ('install_data', 'install_dir'),
                                   ('root', 'root'), ('force', 'force'),)

    def run(self):
        _install_data.run(self)


class Clean(_clean):
    sub_commands = _clean.sub_commands + [
        ('clean_plugins', None),
        ('clean_trans', None),
        ('clean_webui', None)]

    def run(self):
        # Remove deluge egg-info.
        root_egg_info_dir_path = 'deluge*.egg-info'
        for path in glob.glob(root_egg_info_dir_path):
            print('Deleting %s' % path)
            for fpath in os.listdir(path):
                os.remove(os.path.join(path, fpath))
            os.removedirs(path)

        # Run all sub-commands (at least those that need to be run)
        for cmd_name in self.get_sub_commands():
            self.run_command(cmd_name)
        _clean.run(self)


cmdclass = {
    'build': Build,
    'build_webui': BuildWebUI,
    'build_trans': BuildTranslations,
    'build_plugins': BuildPlugins,
    'build_docs': BuildDocs,
    'install_data': InstallData,
    'clean_plugins': CleanPlugins,
    'clean_trans': CleanTranslations,
    'clean_docs': CleanDocs,
    'clean_webui': CleanWebUI,
    'clean': Clean,
    'egg_info_plugins': EggInfoPlugins,
    'test': PyTest,
}


if not windows_check() and not osx_check():
    for icon_path in glob.glob('deluge/ui/data/icons/hicolor/*x*'):
        size = os.path.basename(icon_path)
        _data_files.append(
            ('share/icons/hicolor/{}/apps'.format(size), ['{}/apps/deluge.png'.format(icon_path)]))
    _data_files.extend([
        ('share/icons/hicolor/scalable/apps', ['deluge/ui/data/icons/hicolor/scalable/apps/deluge.svg']),
        ('share/pixmaps', ['deluge/ui/data/pixmaps/deluge.png']),
        ('share/man/man1', [
            'docs/man/deluge.1',
            'docs/man/deluged.1',
            'docs/man/deluge-gtk.1',
            'docs/man/deluge-web.1',
            'docs/man/deluge-console.1'])])
    if os.path.isfile(desktop_data):
        _data_files.append(('share/applications', [desktop_data]))
    if os.path.isfile(appdata_data):
        _data_files.append(('share/appdata', [appdata_data]))

_entry_points['console_scripts'] = [
    'deluge-console = deluge.ui.console:start',
    'deluge-web = deluge.ui.web:start',
    'deluged = deluge.core.daemon_entry:start_daemon']
if windows_check():
    _entry_points['console_scripts'].extend([
        'deluge-debug = deluge.ui.ui_entry:start_ui',
        'deluge-web-debug = deluge.ui.web:start',
        'deluged-debug = deluge.core.daemon_entry:start_daemon'])
_entry_points['gui_scripts'] = [
    'deluge = deluge.ui.ui_entry:start_ui',
    'deluge-gtk = deluge.ui.gtkui:start']
_entry_points['deluge.ui'] = [
    'console = deluge.ui.console:Console',
    'web = deluge.ui.web:Web',
    'gtk = deluge.ui.gtkui:Gtk']


_package_data['deluge'] = [
    'ui/data/pixmaps/*.png',
    'ui/data/pixmaps/*.svg',
    'ui/data/pixmaps/*.ico',
    'ui/data/pixmaps/*.gif',
    'ui/data/pixmaps/flags/*.png',
    'plugins/*.egg',
    'i18n/*/LC_MESSAGES/*.mo']
_package_data['deluge.ui.web'] = [
    'index.html',
    'css/*.css',
    'icons/*.png',
    'images/*.gif',
    'images/*.png',
    'js/*.js',
    'js/extjs/*.js',
    'render/*.html',
    'themes/css/*.css',
    'themes/images/*/*.gif',
    'themes/images/*/*.png',
    'themes/images/*/*/*.gif',
    'themes/images/*/*/*.png']
_package_data['deluge.ui.gtkui'] = ['glade/*.ui']

if 'dev' not in _version:
    _exclude_package_data['deluge.ui.web'] = ['*-debug.js', '*-debug.css']

docs_require = [
    'Sphinx',
    'recommonmark',
    'sphinx-rtd-theme',
    'sphinxcontrib-spelling',
]
tests_require = [
    'coverage',
    'flake8',
    'flake8-blind-except',
    'flake8-builtins',
    'flake8-commas',
    'flake8-comprehensions',
    'flake8-debugger',
    'flake8-isort',
    'flake8-mock',
    'flake8-mutable',
    'flake8-quotes',
    'pre-commit',
    'pre-commit-hooks',
    'pytest',
    'detox',
    'tox',
]

# Main setup
setup(
    name='deluge',
    version=_version,
    fullname='Deluge BitTorrent Client',
    description='BitTorrent Client',
    author='Deluge Team',
    maintainer='Calum Lind',
    maintainer_email='calumlind+deluge@gmail.com',
    keywords='torrent bittorrent p2p fileshare filesharing',
    long_description="""Deluge is a BitTorrent client that utilizes a
        daemon/client model. There are various user interfaces available for
        Deluge such as the GTK-UI, the Web-UI and a Console-UI. Deluge uses
        libtorrent in it's backend to handle the BitTorrent protocol.""",
    url='https://deluge-torrent.org',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Environment :: Web Environment',
        'Environment :: X11 Applications :: GTK',
        'Framework :: Twisted',
        'Intended Audience :: End Users/Desktop',
        ('License :: OSI Approved :: '
            'GNU General Public License v3 or later (GPLv3+)'),
        'Programming Language :: Python',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: POSIX',
        'Topic :: Internet'],
    license='GPLv3',
    cmdclass=cmdclass,
    python_requires='~=2.7',
    extras_require={
        'docs': docs_require,
        'tests': tests_require,
        'dev': docs_require + tests_require,
    },
    tests_require=tests_require,
    data_files=_data_files,
    package_data=_package_data,
    exclude_package_data=_exclude_package_data,
    packages=find_packages(exclude=['deluge.plugins.*', 'deluge.tests']),
    namespace_packages=['deluge', 'deluge.plugins'],
    entry_points=_entry_points
)
