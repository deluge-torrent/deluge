Instructions for building the Win32 installer
---------------------------------------------

Dependencies:
- Python dependencies for building deluge, see
  http://dev.deluge-torrent.org/wiki/Installing/Windows
- Bbfreeze
- StartX, get it here: http://www.naughter.com/startx.html
- NSIS, get it here: http://nsis.sourceforge.net/Main_Page

The assumption in the following is that Python is installed in C:\Python25.
The GTK+ 2.12 runtime libraries are installed separately (anywhere, in the Windows PATH).
The instructions below also work with GTK+ 2.14 from a recent Pidgin version.


1) Build Deluge on Windows


2) Use a slightly hacked bbfreeze to create a standalone "executable" which does not need the the Python libs
The modification is to add these lines to 

   C:\Python25\Lib\site-packages\bbfreeze-0.96.5-py2.5-win32.egg\bbfreeze\recipes.py

right after the "prefixes" part of the Python function recipe_gtk_and_friends

        # Exclude DLL files in the GTK+ 2.12 or GTK+ 2.14 runtime bin dir
        # The GTK+ runtime must be in the PATH or copied to the application dir, so
        # so there is point in including these DLLs with the bbfreeze output
        #
        prefixes2 = ["iconv", "intl", "zlib1", "libpng12", "libatk", "libcairo", "libfont", "libfree", "libtiff", "libgio"]

        for p in prefixes2:        
            if x.identifier.startswith(p):
                print "SKIPPING:", x
                x.__class__ = ExcludedModule
                retval = True                
                break

The purpose is to avoid that bbfreeze copies DLLs from the GTK+ runtime bin directory.
Bbfreeze only copies a subset of the necessary DLLs (for some reason?). The cleanest 
solution is to have the GTK+ runtime in a separate dir. 


3) Edit the build_version variable in the Python script

  /branches/deluge-1.1.0_RC/win32/build-bbfreeze.py

and run the script from the win32 directory
  
  python build-bbfreeze.py
  
The script places the bbfreeze'd version of deluge in

  /branches/deluge-1.1.0_RC/build-win32/deluge-bbfreeze-build_version

Note: the build-bbfreeze.py script assumes that Python 2.5 is installed in C:\Python25,
otherwise the python_path variable should be changed.


4) Edit the variable PROGRAM_VERSION in the NSIS script

   /branches/deluge-1.1.0_RC/win32/deluge-win32-installer.nsi

and run the NSIS script.

The result is a standalone installer. The only dependency for the installer is the GTK+ runtime, 
which is downloaded by the Deluge installer if it isn't installed in the system.

The GTK+ installer is downloaded from 
http://download.deluge-torrent.org/windows/deps/gtk-2.12.9-win32-2.exe
and placed in the user temp directory (not deleted after installation).

The post install script creates the deluge.cmd file using startX.exe with the correct path 
and sets up the file association for .torrent.


5) The Uninstaller will remove everything from the installation directory. 
Also the file association for .torrent will be removed but only if it's associated with Deluge

