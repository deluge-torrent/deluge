= Deluge Installer for Windows =

Instructions for building the Deluge NSIS Installer for Windows Vista/7/8/8.1/10/11.

== Dependencies ==

- Deluge build: https://deluge.readthedocs.io/en/latest/depends.html
- PyInstaller: https://pypi.org/project/pyinstaller/
- NSIS: http://nsis.sourceforge.net/Download

== Build Steps ==

1.  Build and Install Deluge on Windows.
2.  Run pyinstaller from the deluge\packaging\win directory:

    `pyinstaller --clean delugewin.spec --distpath freeze`

    The result is a PyInstaller version of Deluge in `packaging\win\freeze`.

3.  Run the NSIS scripts:

    `python setup_nsis.py`

    64-bit python:

    `makensis /Darch=x64 deluge-win-installer.nsi`

    32-bit python:

    `makensis /Darch=x86 deluge-win-installer.nsi`

    Note: If you don't specify arch defaults to trying x64

The result is a standalone installer in the `packaging\win` directory.
