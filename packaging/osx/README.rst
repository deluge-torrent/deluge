====================================
Instructions for building Deluge.app
====================================

1. Compiler
-----------

- To build deluge and the gtk osx modules, you must use `gcc`
- This has been successfully working with :
    - gcc 4.2.1 - Xcode 4.1 - Mac OSX Lion (10.7.2)
    - llvm-gcc 4.2.1 - Xcode 4.3.1 (With Command line utilities) - Mac OSX Lion (10.7.3)
- Check your version of gcc using `gcc -v`

2. GTK-OSX jhbuild environment
------------------------------

Quick how-to *(from the full GTK-OSX building instructions)* [1]_, [2]_

a. Create a dedicated user account and use it for all the next steps::

        sudo su - gtk
        cat << EOF > ~/.profile
        export PATH=~/.local/bin:~/bin:/bin:/usr/bin:/sbin:/usr/sbin:/usr/local/git/bin
        EOF
        . ~/.profile

  *Note*: I'm using `gtk` login with `/opt/gtk` as home an jhbuild prefix.

b. Download and run the gtk-osx-build-setup [3]_ script to install jhbuild::

        curl -O https://raw.github.com/jralls/gtk-osx-build/master/gtk-osx-build-setup.sh
        sh gtk-osx-build-setup.sh

c. Link or copy deluge osx jhbuildrc-custom::

        ln -sf deluge/osx/jhbuildrc-custom ~/.jhbuildrc-custom

  *Note*: This setup builds only for `x86_64` arch to `/opt/gtk` prefix, feel free to edit.

d. Build jhbuild and its modulesets: *(takes a while...)*::

        jhbuild bootstrap && jhbuild

  *Note*: If you encounter an error while building `glib` like::

        gconvert.c:65:2: error: #error GNU libiconv not in use but included iconv.h is from libiconv

  Start a shell from jhbuild, edit the file `vim glib/gconvert.c +65` to delete the
  section raising error, which is irrelevant. *(Lion iconv.h looks like gnu one, but it is not)*
  Then exit the shell and resume build.

5. Build the deluge moduleset: *(takes a while...)*::

        jhbuild -m deluge/osx/deluge.modules build deluge

  *Note*: This jhbuild moduleset *should* build and install all deluge dependencies not available in gtk-osx.

3. Build Deluge.app
-------------------

a. Always do your custom build operations under a jhbuild shell::

        jhbuild shell

b. Cleanup::

        python setup.py clean -a

c. Build and install::

        python setup.py py2app
        python setup.py install

d. Build app to `deluge/osx/app/Deluge.app`::

        cd osx
        ./make-app

You *should* now have a working Deluge.app

i386 Notes
----------

- Uncomment the relevant sections of :
    - jhbuildrc-custom
    - deluge.modules
    - setup.cfg
- deluge egg has to be named without the -macosx-10.6-intel suffix
- To build for i386 under a x64 arch libtorrent python bindings have to be
  patched manually to set correct arch see macports package patch

Issues
------

If Deluge.app doesn't work or crash the first thing to do is to check OSX
Console for logs and/or crash reports.

You can enable logging by passing the usual log command switches via console::

        /Applications/Deluge.app/Contents/MacOS/Deluge -L debug -l debug.log

Recent jhbuild issues:

- Some jhbuild modules fails to build, freetype and gtk-mac-integration,
  strangely configure is not called before build/install.
- If that happens, just force rebuild with something like:

        jhbuild build -cf gtk-mac-integration-python

-  Interrupt while building with Ctrl+C and wipe to start over if configure missing

Known issues
------------

- **i386**: libtorrent crash
- **i18n**: English only for now
- **Magnet URLs**: Not currently supported by GTK-OSX

Reference
---------

.. [1] http://live.gnome.org/Jhbuild
.. [2] http://live.gnome.org/GTK%2B/OSX/Building
.. [3] http://github.com/jralls/gtk-osx-build
.. [4] http://winswitch.org/dev/macosx.html
.. [5] http://mail.python.org/pipermail/pythonmac-sig/
.. [6] https://github.com/jralls/gtk-mac-integration
