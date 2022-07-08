# Installing Deluge

Instructions for installing Deluge.

## <i class="fa fa-linux"></i> Linux

### <i class="icon-ubuntu"></i> Ubuntu

One-click [**Install**](https://tinyurl.com/installdeluge)

```
sudo apt install deluge
```

[Package Details](https://packages.ubuntu.com/deluge)

### <i class="icon-fedora"></i> Fedora

```
sudo dnf install deluge
```

[Package Details](https://src.fedoraproject.org/rpms/deluge)

### <i class="icon-archlinux"></i> Arch

```
pacman -S deluge-gtk
```

[Arch Wiki](https://wiki.archlinux.org/title/Deluge)

### <i class="icon-suse"></i> OpenSUSE

[**1 Click Install**](http://packman.links2linux.org/install/deluge)

[Package Details](https://software.opensuse.org/package/deluge)

### <i class="icon-gentoo"></i> Gentoo

[Package Details](https://packages.gentoo.org/packages/net-p2p/deluge)

### Flatpak

One-click [**Install**](https://dl.flathub.org/repo/appstream/org.deluge_torrent.deluge.flatpakref)

[Package Details](https://flathub.org/apps/details/org.deluge_torrent.deluge)

## <i class="fa fa-windows"></i> Windows

Download [installer](https://ftp.osuosl.org/pub/deluge/windows/?C=M;O=D)

Availble for Windows 7, 8 & 10 for both 32-bit and 64-bit OSes.

## <i class="fa fa-apple"></i> macOS

Unfortunately no official installer package currently available.

See [Alternative Installs](#alternative-installs)

## <i class="icon-freebsd"></i> FreeBSD

```
pkg add deluge
```

[Package details](https://www.freshports.org/net-p2p/deluge/)

## <i class="icon-python"></i> PyPi

Install with pip:

    pip install deluge

Install with all [optional dependencies][depends]:

    pip install deluge[all]

Will require system installed packages such as libtorent and GTK3. See [DEPENDS]

e.g. on Ubuntu/Debian install these packages:

    sudo apt install python3-pip python3-libtorrent python3-gi python3-gi-cairo gir1.2-gtk-3.0 gir1.2-appindicator3

## Alternative Installs

### Ubuntu PPA

The [stable PPA] contains the latest releases.

    sudo add-apt-repository -u ppa:deluge-team/stable
    sudo apt install deluge

The [development PPA] contains daily builds from the `develop` branch.

    sudo add-apt-repository -u ppa:deluge-team/develop
    sudo apt install deluge

### macOS Community

#### Unofficial `.app` packages

Check sticky topics in [MacOS Forum]

#### Macports

```
sudo port install deluge
```

[Package Details](https://ports.macports.org/port/deluge/)

#### Homebrew

1.  Install [Homebrew]
1.  Open a terminal to install required packages:

        brew install pygobject3 gtk+3 adwaita-icon-theme
        brew install libtorrent-rasterbar

1.  To fix translations:

        brew link gettext --force

1.  Install Deluge:

        pip install deluge

[development ppa]: https://launchpad.net/~deluge-team/+archive/ubuntu/develop/
[stable ppa]: https://launchpad.net/~deluge-team/+archive/ubuntu/stable/
[homebrew]: https://brew.sh/
[macos forum]: https://forum.deluge-torrent.org/viewforum.php?f=13
[depends]: ../depends.md
