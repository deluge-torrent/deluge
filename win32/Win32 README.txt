=  Deluge Installer for Windows =

Instructions for building the Deluge NSIS Installer for Windows XP/Vista/7.

== Dependencies ==
 * Deluge build: http://dev.deluge-torrent.org/wiki/Installing/Source#WindowsDependencies
 * Bbfreeze: http://pypi.python.org/pypi/bbfreeze
 * NSIS: http://nsis.sourceforge.net/Download

== Build Steps ==

 1.  Build and Install Deluge on Windows.

 2.  Run the bbfreeze script from the win32 directory:

        python deluge-bbfreeze.py

    The result is a bbfreeze'd version of Deluge in `build-win32/deluge-bbfreeze-build_version`.

 3.  Run the NSIS script (right-click and choose `Compile with NSIS`)

    The result is a standalone installer in the `build-win32` directory.
