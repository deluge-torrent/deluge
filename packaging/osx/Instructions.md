# Packaging setup with jhbuild

These are the manual step based upon https://wiki.gnome.org/Projects/Jhbuild/Mac_OS

If you encounter curl stalling on FTP URLs try disabling `epsv` for curl:
`echo no-epsv >> ~/.curlrc`

1.  Install XCode command line developer tools:

        xcode-select --install

1.  Install jhbuild:

        curl -LO https://gitlab.gnome.org/GNOME/gtk-osx/raw/master/gtk-osx-build-setup.sh
        sh gtk-osx-build-setup.sh
        jhbuild bootstrap

1.  GTK-OSX Build

    1.  Bootstrap GTK and install PyGTK

            jhbuild build python meta-gtk-osx-bootstrap meta-gtk-osx-python

    1.  GTK OSX Themes:

            jhbuild build meta-gtk-osx-themes gtk-quartz-engine

        Note: ​[Quartz patch] if build error; `'height' is uninitialized`.

1.  Install [MacOS bundler] script

    This script is to help package GTK for Deluge.

        curl -OL http://ftp.gnome.org/pub/gnome/sources/gtk-mac-bundler/0.7/gtk-mac-bundler-0.7.4.tar.xz
        tar xf gtk-mac-bundler-0.7.4.tar.xz
        cd gtk-mac-bundler-0.7.4
        make install

1.  Build libtorrent and deps using ​libtorrent.modules:

        curl -O http://git.deluge-torrent.org/deluge/plain/osx/libtorrent.modules?h=develop
        jhbuild -m libtorrent.modules build meta_libtorrent

    - OpenSSL requires "Skip Module (2)" when install stage fails as unable to use DESTDIR path. See ​patch.
    - Note on a potential OpenSSL Error: 'libcrypto is a fat file' is due to mixing arch types (i386, x64) in build process.

[quartz patch]: https://www.xpra.org/trac/attachment/ticket/533/quartz-style-fix.patch
[macos bundler]: https://wiki.gnome.org/Projects/GTK%2B/OSX/Bundling
