# Installing Deluge

Instructions for installing Deluge server and the GTK client.


## <i class="icon-ubuntu"></i> Ubuntu

Deluge is available from Ubuntu's Universe repository.

```
sudo add-apt-repository universe
sudo apt install deluge deluge-gtk
```


## <i class="icon-fedora"></i> Fedora

```
sudo dnf install deluge deluge-gtk
```


## <i class="fa fa-windows"></i> Windows

Unfortunately due to move to GTK3 and Python 3 there is no installer package currently
available for Windows.

Intrepid users can install Deluge from separate packages as detailed in [issue #3201].


## <i class="fa fa-apple"></i> macOS

There is no `.app` package currently for macOS, but can install Deluge with [Homebrew].

1.  Install [Homebrew]
2.  Open a terminal.
3.  Run the following to install required packages:

        brew install pygobject3 gtk+3 adwaita-icon-theme
        brew install libtorrent-rasterbar

4.  To fix translations:

        brew link gettext --force

5.  Install Deluge:

        pip3 install deluge


## Alternative Installs

### <i class="icon-python"></i> PyPi

To install from Python PyPi, Deluge requires the following system installed packages:

    sudo apt install python3-pip python3-libtorrent python3-gi python3-gi-cairo gir1.2-gtk-3.0 gir1.2-appindicator3

Install with pip:

    pip3 install deluge

### Developer PPA

Deluge also has a [development ppa]

    sudo add-apt-repository -u ppa:deluge-team/stable
    sudo apt install deluge

[development ppa]: https://launchpad.net/~deluge-team/+archive/ubuntu/develop/
[homebrew]: https://brew.sh/
[issue #3201]: https://dev.deluge-torrent.org/ticket/3201#comment:9
