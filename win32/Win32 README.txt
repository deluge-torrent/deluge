Instructions for building the Win32 installer
---------------------------------------------

Dependencies:
- Deluge build: http://dev.deluge-torrent.org/wiki/Installing/Source
- Bbfreeze: http://pypi.python.org/pypi/bbfreeze
- StartX: http://www.naughter.com/startx.html
- NSIS: http://nsis.sourceforge.net/Main_Page

The assumption in the following is that Python 2.6 is installed in C:\Python26.
The GTK+ runtime libraries are installed separately (anywhere, in the Windows PATH).

1)  Build Deluge on Windows

2)  Use a slightly hacked bbfreeze to create a standalone "executable" which does not need the the Python libs
    
    The modification is to add these lines to:
    
        C:\Python26\Lib\site-packages\bbfreeze-0.96.5-py2.6-win32.egg\bbfreeze\recipes.py

    Right at the top of the Python function 'recipe_gtk_and_friends':
        return True
        
    We want to include all the gtk libraries in the installer so that users don't
    require a separate GTK+ installation.

3)  Edit the 'build_version' variable in the Python script:

        win32/build-bbfreeze.py

    and run the script from the win32 directory:
  
        python build-bbfreeze.py
  
    The script places the bbfreeze'd version of deluge in

        build-win32/deluge-bbfreeze-build_version

    Note: the build-bbfreeze.py script assumes that Python 2.6 is installed in C:\Python26,
    otherwise the 'python_path' variable should be changed.


4)  Edit the variable 'PROGRAM_VERSION' in the NSIS script

        win32/deluge-win32-installer.nsi

    and run the NSIS script.

    The result is a standalone installer. The only dependency for the installer is the GTK+ runtime, 
    which is downloaded by the Deluge installer if it isn't installed in the system.

    The GTK+ installer is downloaded from http://download.deluge-torrent.org/windows/deps/
    and placed in the user temp directory (not deleted after installation).

    The post install script creates the deluge.cmd file using startX.exe with the correct path 
    and sets up the file association for .torrent.


5)  The Uninstaller will remove everything from the installation directory. Also the file
    association for '.torrent' will be removed but only if it's associated with Deluge

