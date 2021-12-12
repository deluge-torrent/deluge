# Deluge dependencies

The following are required to install and run Deluge. They are separated into
sections to distinguish the precise requirements for each module.

All modules will require the [common](#common) section dependencies.

## Prerequisite

- [Python] _>= 3.5_

## Build

- [setuptools]
- [intltool] - Optional: Desktop file translation for \*nix.
- [closure-compiler] - Minify javascript (alternative is [slimit])

## Common

- [Twisted] _>= 17.1_ - Use `TLS` extras for `service_identity` and `idna`.
- [OpenSSL] _>= 1.0.1_
- [pyOpenSSL]
- [rencode] _>= 1.0.2_ - Encoding library.
- [PyXDG] - Access freedesktop.org standards for \*nix.
- [xdg-utils] - Provides xdg-open for \*nix.
- [six]
- [zope.interface]
- [chardet] - Optional: Encoding detection.
- [setproctitle] - Optional: Renaming processes.
- [Pillow] - Optional: Support for resizing tracker icons.
- [dbus-python] - Optional: Show item location in filemanager.

### Linux and BSD

- [distro] - Optional: OS platform information.

### Windows OS

- [pywin32]
- [certifi]

## Core (deluged daemon)

- [libtorrent] _>= 1.1.1_
- [GeoIP] - Optional: IP address location lookup. (_Debian: `python-geoip`_)

## GTK UI

- [GTK+] >= 3.10
- [PyGObject]
- [Pycairo]
- [librsvg] _>= 2_
- [libappindicator3] w/GIR - Optional: Ubuntu system tray icon.

### MacOS

- [GtkOSXApplication]

## Web UI

- [mako]

## Plugins

### Notifications

- [pygame] - Optional: Play sounds
- [libnotify] w/GIR - Optional: Desktop popups.

[python]: https://www.python.org/
[setuptools]: https://setuptools.readthedocs.io/en/latest/
[intltool]: https://freedesktop.org/wiki/Software/intltool/
[closure-compiler]: https://developers.google.com/closure/compiler/
[slimit]: https://slimit.readthedocs.io/en/latest/
[openssl]: https://www.openssl.org/
[pyopenssl]: https://pyopenssl.org
[twisted]: https://twistedmatrix.com
[pillow]: https://pypi.org/project/Pillow/
[libtorrent]: https://libtorrent.org/
[zope.interface]: https://pypi.org/project/zope.interface/
[distro]: https://github.com/nir0s/distro
[pywin32]: https://github.com/mhammond/pywin32
[certifi]: https://pypi.org/project/certifi/
[py2-ipaddress]: https://pypi.org/project/py2-ipaddress/
[dbus-python]: https://pypi.org/project/dbus-python/
[setproctitle]: https://pypi.org/project/setproctitle/
[gtkosxapplication]: https://github.com/jralls/gtk-mac-integration
[chardet]: https://chardet.github.io/
[rencode]: https://github.com/aresch/rencode
[pyxdg]: https://www.freedesktop.org/wiki/Software/pyxdg/
[six]: https://pythonhosted.org/six/
[xdg-utils]: https://www.freedesktop.org/wiki/Software/xdg-utils/
[gtk+]: https://www.gtk.org/
[pycairo]: https://cairographics.org/pycairo/
[pygobject]: https://pygobject.readthedocs.io/en/latest/
[geoip]: https://pypi.org/project/GeoIP/
[mako]: https://www.makotemplates.org/
[pygame]: https://www.pygame.org/
[libnotify]: https://developer.gnome.org/libnotify/
[python-appindicator]: https://packages.ubuntu.com/xenial/python-appindicator
[librsvg]: https://wiki.gnome.org/action/show/Projects/LibRsvg
