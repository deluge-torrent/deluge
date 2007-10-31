# Copyright (c) 2006 Zach Tibbitts ('zachtib') <zach@collegegeek.org>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2, or (at your option)
# any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, write to:
#     The Free Software Foundation, Inc.,
#     51 Franklin Street, Fifth Floor
#     Boston, MA  02110-1301, USA.
#
#  In addition, as a special exception, the copyright holders give
#  permission to link the code of portions of this program with the OpenSSL
#  library.
#  You must obey the GNU General Public License in all respects for all of
#  the code used other than OpenSSL. If you modify file(s) with this
#  exception, you may extend this exception to your version of the file(s),
#  but you are not obligated to do so. If you do not wish to do so, delete
#  this exception statement from your version. If you delete this exception
#  statement from all source files in the program, then also delete it here.

NAME = "deluge"
FULLNAME = "Deluge BitTorrent Client"
VERSION    = "0.5.6.25"
AUTHOR = "Zach Tibbitts, Alon Zakai, Marcos Pinto, Andrew Resch, Alex Dedul"
EMAIL = "zach@collegegeek.org, kripkensteiner@gmail.com, marcospinto@dipconsultants.com, alonzakai@gmail.com, rotmer@gmail.com"
DESCRIPTION    = "A bittorrent client written in PyGTK"
URL = "http://deluge-torrent.org"
LICENSE    = "GPLv2"

import os, platform
print "Attempting to detect your system information"
if platform.machine() == "i386" or platform.machine() == "i686":
    print "32bit x86 system detected"
    ARCH = "x86"
elif platform.machine() == "x86_64" or platform.machine() == "amd64":
    print "64bit x86_64 system detected"
    ARCH = "x64"
elif platform.machine() == "ppc":
    print "PowerPC system detected"
    ARCH = "ppc"
else:
    print "Couldn't detect CPU architecture"
    ARCH = ""
if platform.system() == "Linux":
    print "Linux operating system detected"
    OS = "linux"
elif platform.system() == "Darwin" :
    print "Darwin / OS X system detected"
    OS = "osx"
elif platform.system() == "FreeBSD" :
    print "FreeBSD operating system detected"
    OS = "freebsd"
elif platform.system() in ('Windows', 'Microsoft'): 
    print "Windows system detected"
    OS = "win"
elif os.name == "posix":
    print "Unix system detected"
    OS = "nix"
else:
    print "Couldn't detect operating system"
    OS = ""
import os.path, glob
from distutils.core import setup, Extension
from distutils import sysconfig
import shutil
from distutils import cmd
from distutils.command.install import install as _install
from distutils.command.install_data import install_data as _install_data
from distutils.command.build import build as _build
if OS == "win":
    from distutils.command.build_ext import build_ext as _build_ext
import msgfmt

python_version = platform.python_version()[0:3]


# NOTE: The following "hack" removes the -g and -Wstrict-prototypes
# build options from the command that will compile the C++ module,
# deluge_core.  While we understand that you aren't generally
# encouraged to do this, we have done so for the following reasons:
# 1) The -g compiler option produces debugging information about
#    the compiled module.  However, this option increases the 
#    size of deluge_core.so from ~1.9MB to 13.6MB and slows down
#    the program's execution without offering any benefits 
#    whatsoever.
# 2) -Wstrict-prototypes is not a valid C++ build option, and the
#    compiler will throw a number of warnings at compile time.
#    While this does not really impact anything, it makes it
#    seem as if something is going wrong with the compile, and
#    it has been removed to prevent confusion.

if not OS == "win":
    EXTRA_COMPILE_ARGS = ["-Wno-missing-braces", 
                "-DHAVE_INCLUDE_LIBTORRENT_ASIO____ASIO_HPP=1", 
                "-DHAVE_INCLUDE_LIBTORRENT_ASIO_SSL_STREAM_HPP=1", 
                "-DHAVE_INCLUDE_LIBTORRENT_ASIO_IP_TCP_HPP=1", 
                "-DHAVE_PTHREAD=1", "-DTORRENT_USE_OPENSSL=1", "-DHAVE_SSL=1", 
                "-DNDEBUG=1", "-O2"]
    if ARCH == "x64":
        EXTRA_COMPILE_ARGS.append("-DAMD64")

    includedirs = ['./libtorrent', './libtorrent/include', 
                     './libtorrent/include/libtorrent', 
                     '/usr/include/python' + python_version]

    if OS == "linux":
        if os.WEXITSTATUS(os.system('grep -iq "Debian GNU/Linux 4.0\|Ubuntu 7.04\|Ubuntu 6.06\|Ubuntu 6.10\|Fedora Core release 6\|openSUSE 10.2\|Mandriva Linux release 2007.1\|Fedora release 7\|BLAG release 60001\|Yellow Dog Linux release 5.0 (Phoenix)\|CentOS release 5 (Final)" /etc/issue')) == 0:
            boosttype = 'nomt'
        else:
            boosttype = 'mt'
    elif OS == "freebsd":
        boosttype = 'nomt'
    else:
        boosttype = 'mt'
    
    removals = ['-g', '-Wstrict-prototypes']

    if python_version == '2.5':
        cv_opt = sysconfig.get_config_vars()["CFLAGS"]
        for removal in removals:
            cv_opt = cv_opt.replace(removal, " ")
        sysconfig.get_config_vars()["CFLAGS"] = ' '.join(cv_opt.split())
    else:
        cv_opt = sysconfig.get_config_vars()["OPT"]
        for removal in removals:
            cv_opt = cv_opt.replace(removal, " ")
        sysconfig.get_config_vars()["OPT"] = ' '.join(cv_opt.split())
else:
    boosttype = 'mt'
    EXTRA_COMPILE_ARGS = [  '-DBOOST_WINDOWS',
                            '-Wno-missing-braces',
                            '-DWIN32_LEAN_AND_MEAN',
                            '-D_WIN32_WINNT=0x0500',
                            '-D__USE_W32_SOCKETS',
                            '-D_WIN32',
                            '-DWIN32',
                            '-DBOOST_ALL_NO_LIB',
                            '-D_FILE_OFFSET_BITS=64',
                            '-DBOOST_THREAD_USE_LIB',
                            '-DTORRENT_USE_OPENSSL=1',
                            '-DNDEBUG=1']
                             
    EXTRA_LINK_ARGS = ['-L.\win32\lib']
    includedirs = ['./libtorrent', './libtorrent/include', './libtorrent/include/libtorrent', './win32/include']

# NOTE: The Rasterbar Libtorrent source code is in the libtorrent/ directory
# inside of Deluge's source tarball.  On several occasions, it has been 
# pointed out to us that we should build against the system's installed 
# libtorrent rather than our internal copy, and a few people even submitted
# patches to do just that. However, as of now, this version
# of libtorrent is not available in Debian, and as a result, Ubuntu. Once
# libtorrent-rasterbar is available in the repositories of these distributions,
# we will probably begin to build against a system libtorrent, but at the
# moment, we are including the source code to make packaging on Debian and
# Ubuntu possible.
if not OS == "win":
    if boosttype == "nomt":
        librariestype = ['boost_filesystem', 'boost_date_time',
            'boost_thread', 'z', 'pthread', 'ssl']
        print 'Libraries nomt' 
    elif boosttype == "mt":
        librariestype = ['boost_filesystem-mt', 'boost_date_time-mt',
            'boost_thread-mt', 'z', 'pthread', 'ssl']
        print 'Libraries mt'
else:
        librariestype = ['boost_filesystem-mt', 'boost_date_time-mt',
            'boost_thread-mt', 'z', 'ssl' ,'wsock32' ,'crypto' ,'gdi32' ,'ws2_32']
        print 'Libraries mt'

def fetchCpp():
    for root,dirs,files in os.walk('libtorrent'):
        if '.svn' in dirs:
            dirs.remove('.svn')
        for file in files:
            if file.endswith('.cpp'):
                yield os.path.join(root,file)

sources=list(fetchCpp())
sources.append(os.path.join('src','deluge_core.cpp'))
if not OS == "win":
    sources.remove('libtorrent/src/file_win.cpp')
    deluge_core = Extension('deluge_core',
                    include_dirs = includedirs,
                    libraries = librariestype,
                    extra_compile_args = EXTRA_COMPILE_ARGS,
                    sources = sources)
else:
    sources.remove('libtorrent\\src\\file.cpp')
    deluge_core = Extension('deluge_core',
                    include_dirs = includedirs,
                    libraries = librariestype,
                    extra_compile_args = EXTRA_COMPILE_ARGS,
                    extra_link_args = EXTRA_LINK_ARGS,
                    sources = sources)

# Thanks to Iain Nicol for code to save the location for installed prefix
# At runtime, we need to know where we installed the data to.

class write_data_install_path(cmd.Command):
    description = 'saves the data installation path for access at runtime'
    
    def initialize_options(self):
        self.prefix = None
        self.lib_build_dir = None

    def finalize_options(self):
        self.set_undefined_options('install',
            ('prefix', 'prefix')
        )
        self.set_undefined_options('build',
            ('build_lib', 'lib_build_dir')
        )

    def run(self):
        conf_filename = os.path.join(self.lib_build_dir,
            'deluge', 'common.py')

        conf_file = open(conf_filename, 'r')
        data = conf_file.read()
        conf_file.close()
        data = data.replace('@datadir@', self.prefix)
        conf_file = open(conf_filename, 'w')
        conf_file.write(data)
        conf_file.close()

    def get_outputs(self): return []

class unwrite_data_install_path(cmd.Command):
    description = 'undoes write_data_install_path'

    def initialize_options(self):
        self.lib_build_dir = None

    def finalize_options(self):        
        self.set_undefined_options('build',
            ('build_lib', 'lib_build_dir')
        )

    def run(self):
        dest = os.path.join(self.lib_build_dir,
            'deluge', 'common.py')
        shutil.copyfile('src/common.py', dest)

    def get_outputs(self): return []

class build_trans(cmd.Command):
    description = 'Compile .po files into .mo files'
    
    def initialize_options(self):
        pass

    def finalize_options(self):        
        pass

    def run(self):
        po_dir = os.path.join(os.path.dirname(os.curdir), 'po')
        for path, names, filenames in os.walk(po_dir):
            for f in filenames:
                if f.endswith('.po'):
                    lang = f[:len(f) - 3]
                    src = os.path.join(path, f)
                    dest_path = os.path.join('build', 'locale', lang, 'LC_MESSAGES')
                    dest = os.path.join(dest_path, 'deluge.mo')
                    if not os.path.exists(dest_path):
                        os.makedirs(dest_path)
                    if not os.path.exists(dest):
                        print 'Compiling %s' % src
                        msgfmt.make(src, dest)
                    else:
                        src_mtime = os.stat(src)[8]
                        dest_mtime = os.stat(dest)[8]
                        if src_mtime > dest_mtime:
                            print 'Compiling %s' % src
                            msgfmt.make(src, dest)

class build(_build):
    sub_commands = _build.sub_commands + [('build_trans', None)]
    def run(self):
        _build.run(self)

class install(_install):
    sub_commands = [('write_data_install_path', None)] + \
        _install.sub_commands + [('unwrite_data_install_path', None)]
    def run(self):
        _install.run(self)

class install_data(_install_data):
    def run(self):
        for lang in os.listdir('build/locale/'):
            lang_dir = os.path.join('share', 'locale', lang, 'LC_MESSAGES')
            lang_file = os.path.join('build', 'locale', lang, 'LC_MESSAGES', 'deluge.mo')
            self.data_files.append( (lang_dir, [lang_file]) )
        _install_data.run(self)
if OS == "win":
    class build_ext(_build_ext):
        def build_extensions(self):
        # Linking against this library causes deluge_core.pyd to crash 
        # on Python >= 2.4. Maybe related to strdup calls, cfr.
        # http://mail.python.org/pipermail/distutils-sig/2005-April/004433.html
            if 'msvcr71' in self.compiler.dll_libraries:
                self.compiler.dll_libraries.remove('msvcr71')
            _build_ext.build_extensions(self)

if not OS == "win":
    cmdclass = {
        'build': build,
        'install': install,
        'build_trans': build_trans,
        'install_data': install_data,
        'write_data_install_path': write_data_install_path,
        'unwrite_data_install_path': unwrite_data_install_path,
    }
else:
    cmdclass = {
        'build': build,
        'build_ext' : build_ext,
        'install': install,
        'build_trans': build_trans,
        'install_data': install_data,
        'write_data_install_path': write_data_install_path,
        'unwrite_data_install_path': unwrite_data_install_path,
    }


data = [('share/deluge/glade',  glob.glob('glade/*.glade')),
        ('share/deluge/pixmaps', glob.glob('pixmaps/*.png')),
        ('share/deluge/pixmaps', glob.glob('pixmaps/*.svg')),
        ('share/deluge/icons/scalable/apps', glob.glob('icons/scalable/apps/*.svg')),
        ('share/deluge/icons/hicolor', glob.glob('icons/hicolor/*.png')),
        ('share/icons/hicolor/128x128', glob.glob('icons/hicolor/128x128/*.png')),
        ('share/icons/hicolor/128x128/apps', glob.glob('icons/hicolor/128x128/apps/*.png')),
        ('share/icons/hicolor/16x16', glob.glob('icons/hicolor/16x16/*.png')),
        ('share/icons/hicolor/16x16/apps', glob.glob('icons/hicolor/16x16/apps/*.png')),
        ('share/icons/hicolor/192x192', glob.glob('icons/hicolor/192x192/*.png')),
        ('share/icons/hicolor/192x192/apps', glob.glob('icons/hicolor/192x192/apps/*.png')),
        ('share/icons/hicolor/22x22', glob.glob('icons/hicolor/22x22/*.png')),
        ('share/icons/hicolor/22x22/apps', glob.glob('icons/hicolor/22x22/apps/*.png')),
        ('share/icons/hicolor/24x24', glob.glob('icons/hicolor/24x24/*.png')),
        ('share/icons/hicolor/24x24/apps', glob.glob('icons/hicolor/24x24/apps/*.png')),
        ('share/icons/hicolor/256x256', glob.glob('icons/hicolor/256x256/*.png')),
        ('share/icons/hicolor/256x256/apps', glob.glob('icons/hicolor/256x256/apps/*.png')),
        ('share/icons/hicolor/32x32', glob.glob('icons/hicolor/32x32/*.png')),
        ('share/icons/hicolor/32x32/apps', glob.glob('icons/hicolor/32x32/apps/*.png')),
        ('share/icons/hicolor/36x36', glob.glob('icons/hicolor/36x36/*.png')),
        ('share/icons/hicolor/36x36/apps', glob.glob('icons/hicolor/36x36/apps/*.png')),
        ('share/icons/hicolor/48x48', glob.glob('icons/hicolor/48x48/*.png')),
        ('share/icons/hicolor/48x48/apps', glob.glob('icons/hicolor/48x48/apps/*.png')),
        ('share/icons/hicolor/64x64', glob.glob('icons/hicolor/64x64/*.png')),
        ('share/icons/hicolor/64x64/apps', glob.glob('icons/hicolor/64x64/apps/*.png')),
        ('share/icons/hicolor/72x72', glob.glob('icons/hicolor/72x72/*.png')),
        ('share/icons/hicolor/72x72/apps', glob.glob('icons/hicolor/72x72/apps/*.png')),
        ('share/icons/hicolor/96x96', glob.glob('icons/hicolor/96x96/*.png')),
        ('share/icons/hicolor/96x96/apps', glob.glob('icons/hicolor/96x96/apps/*.png')),
        ('share/deluge/pixmaps/flags18x12', glob.glob('pixmaps/flags18x12/*.png')),
        ('share/deluge/pixmaps/flags25x15', glob.glob('pixmaps/flags25x15/*.png')),
        ('share/applications' , ['deluge.desktop']),
        ('share/pixmaps' , ['deluge.png'])]

# New code to glob plugins and include subdirs:
for o in os.walk('plugins'):
    path = o[0]
    if not path.count('/.') and not path.count('\\.'):
        items = o[2]
        for x in range(len(items)):
            items[x] = path + '/' + items[x]
        data.append( ('share/deluge/' + path, items))

setup(name=NAME, fullname=FULLNAME, version=VERSION,
    author=AUTHOR, author_email=EMAIL, description=DESCRIPTION,
    url=URL, license=LICENSE,
    scripts=["scripts/deluge"],
    packages=['deluge'],
    package_dir = {'deluge': 'src'},
    data_files=data,
    ext_package='deluge',
    ext_modules=[deluge_core],
    cmdclass=cmdclass
)
