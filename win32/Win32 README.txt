=  Deluge Installer for Windows =

Instructions for building the Deluge NSIS Installer for Windows XP/Vista/7.

== Dependencies ==
 * Deluge build: http://dev.deluge-torrent.org/wiki/Installing/Source#WindowsDependencies
 * Bbfreeze: http://pypi.python.org/pypi/bbfreeze
 * NSIS: http://nsis.sourceforge.net/Download

== Build Steps ==

 1.  Build Deluge on Windows.

 2.  Verify/update the Deluge version in the win32 packaging scripts.

    bbfreeze script - Edit 'build_version' variable in:

        win32/deluge-bbfreeze.py

    NSIS script - Edit 'PROGRAM_VERSION' variable in:

        win32/deluge-win32-installer.nsi

 3.  Modify bbfreeze program.

    We want to include all the gtk libraries in the installer so that users don't
    require a separate GTK+ installation so we need to slightly modify bbfreeze.

    The modification is to add a line to bbfreeze\recipes.py, usually located here:

        C:\Python26\Lib\site-packages\bbfreeze-*-py2.6-win32.egg\bbfreeze\recipes.py

    Find the line containing 'def recipe_gtk_and_friends' and after it add:

        return True

 4.  Run the bbfreeze script from the win32 directory:

        python deluge-bbfreeze.py

    The script places the bbfreeze'd version of Deluge in

        build-win32/deluge-bbfreeze-build_version

    Note: The assumption for this script is that Python 2.6 is installed
    in 'C:\Python26' otherwise the 'python_path' variable should be changed.

 5.  Run the NSIS script (right-click and choose `Compile with NSIS`)

    The result is a standalone installer in the `build-win32` directory.

The Uninstaller will remove everything from the installation directory. The file
association for '.torrent' will also be removed but only if it's associated with Deluge

