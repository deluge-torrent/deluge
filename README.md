# Deluge BitTorrent Client

[![build-status]][travis-deluge] [![docs-status]][rtd-deluge]

Deluge is a BitTorrent client that utilizes a
daemon/client model. There are various user interfaces available for
Deluge such as the GTK-UI, the Web-UI and a Console-UI. Deluge uses
libtorrent in it's backend to handle the BitTorrent protocol.

## Installation

Instruction for installing from source code. See [DEPENDS](DEPENDS.md) for
build and runtime dependencies. Further details on the wiki:
[Installing/Source].

    python setup.py build
    python setup.py install

## Usage

There are various user-interfaces and a daemon for Deluge that can be used as
follows:

- **Gtk**

  `deluge` or `deluge-gtk`

- **Console**

  `deluge-console`

- **Web**

  `deluge-web`

  Go to http://localhost:8112 and use default password `deluge`.

- **Daemon**

  `deluged`

  See [Thinclient guide] for connecting to the daemon from another machine.

## Contact/Support

- [Homepage](https://deluge-torrent.org)
- [Support docs][user guide]
- [Forum](https://forum.deluge-torrent.org)
- [IRC Freenode #deluge](irc://irc.freenode.net/deluge)

[user guide]: https://dev.deluge-torrent.org/wiki/UserGuide
[thinclient guide]: https://dev.deluge-torrent.org/wiki/UserGuide/ThinClient
[installing/source]: https://dev.deluge-torrent.org/wiki/Installing/Source
[build-status]: https://travis-ci.org/deluge-torrent/deluge.svg "Travis Status"
[travis-deluge]: https://travis-ci.org/deluge-torrent/deluge
[docs-status]: https://readthedocs.org/projects/deluge/badge/?version=develop
[rtd-deluge]: https://deluge.readthedocs.io/en/develop/?badge=develop "Documentation Status"
