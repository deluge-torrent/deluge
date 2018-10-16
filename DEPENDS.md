# Deluge dependencies

The following are required to install and run Deluge. They are separated into
sections to distinguish the precise requirements for each module.

All modules will require the [common](#common) section dependencies.

## Prerequisite

- [Python] _>= 2.7.7 or >= 3.5_

## Build

- [setuptools]
- [intltool] - Translation file tool
- [closure-compiler] - Minify javascript (alternative is [slimit])

## Common

- [Twisted] _>= 16.6_ - Use `TLS` extras for `service_identity` and `idna`.
- [OpenSSL] _>= 1.0.1_
- [pyOpenSSL]
- [Chardet]
- [gettext]
- [PyXDG]
- [six]
- [zope.interface]
- [xdg-utils]

#### Optional

- [setproctitle] - Support correctly naming Deluge processes.
- [Pillow] - Image library for `.ico` support.
- [rencode] _>= 1.0.2_ - Encoding library with Python port bundled.
- [dbus-python]

#### Windows OS

- [pywin32]
- [certifi]
- [py2-ipaddress] - Optional for Python 2 IPv6 lookup

## Core (deluged daemon)

- [libtorrent] _>= 1.1.1_
- [GeoIP] - Optional (_Debian: `python-geoip`_)

## GTK UI

- PyGTK
- [pycairo]
- [librsvg] _>= 2_
- [python-appindicator] - Optional

#### MacOS

- [GtkOSXApplication]

## Web UI

- [mako]

## Plugins

### Notifications

Optional dependencies for this plugin.

- [pygame] - Sound
- [python-notify] - Desktop popup

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
[pywin32]: https://github.com/mhammond/pywin32
[certifi]: https://pypi.org/project/certifi/
[py2-ipaddress]: https://pypi.org/project/py2-ipaddress/
[dbus-python]: https://pypi.org/project/dbus-python/
[setproctitle]: https://pypi.org/project/setproctitle/
[gtkosxapplication]: https://github.com/jralls/gtk-mac-integration
[chardet]: https://chardet.github.io/
[gettext]: https://www.gnu.org/software/gettext/
[rencode]: https://github.com/aresch/rencode
[pyxdg]: https://www.freedesktop.org/wiki/Software/pyxdg/
[six]: https://pythonhosted.org/six/
[xdg-utils]: https://www.freedesktop.org/wiki/Software/xdg-utils/
[pycairo]: https://cairographics.org/pycairo/
[pygobject]: https://pygobject.readthedocs.io/en/latest/
[geoip]: https://pypi.org/project/GeoIP/
[mako]: https://www.makotemplates.org/
[pygame]: https://www.pygame.org/
[python-notify]: https://packages.ubuntu.com/xenial/python-notify
[python-appindicator]: https://packages.ubuntu.com/xenial/python-appindicator
[librsvg]: https://wiki.gnome.org/action/show/Projects/LibRsvg
