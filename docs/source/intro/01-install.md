# Installing Deluge

These are the instructions for installer Deluge. They are a work-in-progress and feel
free to make suggestions for improvement.

## Ubuntu

### PPA

https://launchpad.net/~deluge-team/+archive/ubuntu/develop/

### PyPi

Deluge requires the following system installed packages:

    sudo apt install python3-pip python3-libtorrent python3-gi python3-gi-cairo gir1.2-gtk-3.0 gir1.2-appindicator3

Install with pip:

    pip install --user deluge

## Windows

There is no installer package currently for Windows, but can try Deluge as follows.

1. Install Python 3.6.
2. Download and extract the `gvsbuild`.
3. Open a terminal.
4. Add directory to PATH: `set PATH=C:\gvsbuild\release;%PATH%`
5. Install Python wheels from gvsbuild:
   pip install C:\gvsbuild\release\python\pycairo-1.17.1-cp36-cp36m-win_amd64.whl
   pip install C:\gvsbuild\release\python\PyGObject-3.28.3-py3.6-win-amd64.whl
6. Install Deluge
   pip install deluge deluge-libtorrent

## macOS

There is no `.app` package currently for macOS, but can try Deluge with homebrew.

1. Install [Homebrew](https://brew.sh/)
2. Open a terminal.
3. Run the following to install required packages:

   brew install pyobject3 gtk+3 adwaita-icon-theme
   brew install libtorrent-rasterbar

4. To fix translations:

   brew link gettext --force

5. Install Deluge:

   pip3 install deluge
