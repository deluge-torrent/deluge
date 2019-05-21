# Deluge BitTorrent Client

[![build-status]][travis-deluge] [![docs-status]][rtd-deluge]

Deluge is a BitTorrent client that utilizes a daemon/client model.
It has various user interfaces available such as the GTK-UI, Web-UI and
a Console-UI. It uses [libtorrent][lt] at it's core to handle the BitTorrent
protocol.

## Install

From [PyPi](https://pypi.org/project/deluge):

    pip install deluge

From source code:

    python setup.py build
    python setup.py install

See [DEPENDS](DEPENDS.md) and [Installing/Source] for dependency details.

## Usage

The various user-interfaces and Deluge daemon can be started with the following commands.

Use the `--help` option for further command options.

### Gtk UI

`deluge` or `deluge-gtk`

### Console UI

`deluge-console`

### Web UI

`deluge-web`

Open http://localhost:8112 with default password `deluge`.

### Daemon

`deluged`

See the [Thinclient guide] to connect to the daemon from another computer.

## Contact

- [Homepage](https://deluge-torrent.org)
- [User guide][user guide]
- [Forum](https://forum.deluge-torrent.org)
- [IRC Freenode #deluge](irc://irc.freenode.net/deluge)

[user guide]: https://dev.deluge-torrent.org/wiki/UserGuide
[thinclient guide]: https://dev.deluge-torrent.org/wiki/UserGuide/ThinClient
[installing/source]: https://dev.deluge-torrent.org/wiki/Installing/Source
[build-status]: https://travis-ci.org/deluge-torrent/deluge.svg "Travis Status"
[travis-deluge]: https://travis-ci.org/deluge-torrent/deluge
[docs-status]: https://readthedocs.org/projects/deluge/badge/?version=develop
[rtd-deluge]: https://deluge.readthedocs.io/en/develop/?badge=develop "Documentation Status"
[lt]: https://libtorrent.org
