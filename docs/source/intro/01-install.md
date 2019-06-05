# Installing Deluge

These are the instructions for installing Deluge. Consider them a work-in-progress and
feel free to make suggestions for improvement.

## <i class="icon-ubuntu"></i> Ubuntu

### PPA

Until the stable PPA is updated, the development version of Deluge can be used:

    sudo add-apt-repository -u ppa:deluge-team/develop
    sudo apt install deluge

### <i class="icon-python"></i> PyPi

To install from Python PyPi, Deluge requires the following system installed packages:

    sudo apt install python3-pip python3-libtorrent python3-gi python3-gi-cairo gir1.2-gtk-3.0 gir1.2-appindicator3

Install with pip:

    pip install deluge

## <i class="fa fa-windows"></i> Windows

There is no installer package currently for Windows, but can try Deluge as follows.

1.  Download and install [Python 3.6].
2.  Download and extract [gvsbuild] tarball to `C:\`.
3.  Open a terminal.
4.  Run this command to add `gvsbuild` directory to `PATH`:

        set PATH=C:\gvsbuild\release;%PATH%

5.  Install `gvsbuild` Python wheels:

        pip install C:\gvsbuild\release\python\pycairo-1.18.0-cp36-cp36m-win_amd64.whl
        pip install C:\gvsbuild\release\python\PyGObject-3.32.0-cp36-cp36m-win_amd64.whl

6.  Install Deluge:

        pip install deluge deluge-libtorrent

## <i class="fa fa-apple"></i> macOS

There is no `.app` package currently for macOS, but can try Deluge with homebrew.

1. Install [Homebrew]
2. Open a terminal.
3. Run the following to install required packages:

   brew install pyobject3 gtk+3 adwaita-icon-theme
   brew install libtorrent-rasterbar

4. To fix translations:

   brew link gettext --force

5. Install Deluge:

   pip3 install deluge

[develop ppa]: https://launchpad.net/~deluge-team/+archive/ubuntu/develop/
[homebrew]: https://brew.sh/
[python 3.6]: https://www.python.org/downloads/release/python-368/
[gvsbuild]: https://ci.appveyor.com/api/buildjobs/b0y2sttcq3t1071q/artifacts/gvsbuild-vs14-x64.tar.gz
