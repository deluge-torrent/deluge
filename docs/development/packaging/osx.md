# Deluge.app for OSX

## Manual Steps (Tested on Yosemite VM)

1. Install XCode
2. Jhbuild install and update Python:
    ```sh
    wget https://git.gnome.org/browse/gtk-osx/plain/gtk-osx-build-setup.sh
    sh gtk-osx-build-setup.sh
    export PATH=~/.local/bin:~/gtk/inst/bin:$PATH
    jhbuild build bootstrap
    jhbuild build python
    ```
    * Uncomment `_gtk_osx_use_jhbuild_python = True` in `.jhbuildrc-custom`.
3. [GTK OSX Build](https://wiki.gnome.org/Projects/GTK+/OSX/Building):
    ```sh
    jhbuild build meta-gtk-osx-bootstrap
    ```
4. [PyGTK](https://wiki.gnome.org/Projects/GTK+/OSX/Python) (Includes `meta-gtk-osx-core`)
    ```sh
    jhbuild build libglade
    jhbuild build meta-gtk-osx-python
    ```
    * A [pygobject patch](https://git.gnome.org/browse/pygobject/commit/?h=pygobject-2-28&id=42d01f060c5d764baa881d13c103d68897163a49) to apply to fix annoying console warnings.
5. GTK OSX Themes:
    ```
    jhbuild build meta-gtk-osx-themes
    jhbuild build gtk-quartz-engine
    ```
    * *Note:* [Quartz patch](https://www.xpra.org/trac/attachmenthttps://dev.deluge-torrent.org/ticket/533/quartz-style-fix.patch) if build error: `'height' is uninitialized`.
6. [Bundler](https://wiki.gnome.org/Projects/GTK%2B/OSX/Bundling) for Packaging Deluge.
    ```sh
    wget http://ftp.gnome.org/pub/gnome/sources/gtk-mac-bundler/0.7/gtk-mac-bundler-0.7.4.tar.xz
    tar xf gtk-mac-bundler-0.7.4.tar.xz
    cd gtk-mac-bundler-0.7.4
    make install
    ```
7. Build libtorrent and deps using [libtorrent.modules](https://gist.github.com/cas--/d1df3758d6e794c0ca4e):
    ```sh
    wget http://git.deluge-torrent.org/deluge/plain/osx/libtorrent.modules?h=1.3-stable
    jhbuild -m libtorrent.modules build meta_libtorrent
    ```
    * OpenSSL requires "Skip Module (2)" when install stage fails as unable to use DESTDIR path. See [patch](https://github.com/elelay/gpodder-osx-bundle/blob/master/modulesets/patches/openssl-respect-destdir.patch).
    * *Note on potential OpenSSL Error:* 'libcrypto is a fat file' is due to mixing arch types (i386, x64) in build process.
8. Install Deluge dependencies using [pip](https://pip.pypa.io/en/latest/installing/):
    ```sh
    jhbuild shell
    wget https://bootstrap.pypa.io/get-pip.py
    python get-pip.py
    pip install twisted[tls] chardet mako pyxdg setproctitle pillow py2app cython
    pip install rencode
    pip install setuptools==19.2
    ```
    * *Note1:* pygame for Notifications plugin need installed separately.
    * *Note2:* rencode requires cython before attempting pip install. [(rencode issue)](https://github.com/aresch/rencode/issues/11)
    * *Note3:* Due to bug in setuptools require version 19.2 [(setuptools issue)](https://github.com/pypa/setuptools/issues/517)
9. Install and package Deluge:
    1. If using release tarball download required `setup.cfg` and `osx` directory from git, run commands in deluge source directory:
        ```sh
        wget --content-disposition http://git.deluge-torrent.org/deluge/plain/setup.cfg?h=1.3-stable
        wget -rnd -np -e robots=off --reject "index.html*" --content-disposition http://git.deluge-torrent.org/deluge/plain/osx/?h=1.3-stable -P osx
        ```
        * *Note:* In setup.cfg need to remove 'dev' line and set arch to 'x86_64'.
    2. Build and install Deluge using py2app:
        ```sh
        jhbuild shell
        python setup.py py2app
        python setup.py install
        ```
      * For error `dyld_find() got an unexpected keyword argument 'loader'` either uninstall `pillow` or [patch MachOGraph.py](https://bitbucket.org/ronaldoussoren/macholib/pull-requests/10/)
    3. Package Deluge into app in `osx/app/` using gtk-mac-bundler script:
        ```sh
        jhbuild shell
        cd osx
        ./make-app
        ```
      * Fix for pango_module_version error [on github](https://github.com/jralls/gtk-mac-bundler/commit/5a348d5a9405c958ee0e85fb0af58a8dc0dd999c)
10. Optionally create dmg image:
```sh
hdiutil create -format UDBZ -srcfolder Deluge.app -volname deluge-1.3.13-osx-x64-0 deluge-1.3.13-osx-x64-0.dmg
```
