# Deluge BitTorrent Client

[![build-status]][github-ci] [![docs-status]][rtd-deluge]

Deluge is a BitTorrent client that utilizes a daemon/client model.
It has various user interfaces available such as the GTK-UI, Web-UI and
Console-UI. It uses [libtorrent][lt] at its core to handle the BitTorrent
protocol.

## Install

From [PyPi](https://pypi.org/project/deluge):

    pip install deluge

with all optional dependencies:

    pip install deluge[all]

From source code:

    pip install .

with all optional dependencies:

    pip install .[all]

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
- [IRC Libera.Chat #deluge](irc://irc.libera.chat/deluge)

[user guide]: https://dev.deluge-torrent.org/wiki/UserGuide
[thinclient guide]: https://dev.deluge-torrent.org/wiki/UserGuide/ThinClient
[installing/source]: https://dev.deluge-torrent.org/wiki/Installing/Source
[build-status]: https://github.com/deluge-torrent/deluge/actions/workflows/ci.yml/badge.svg?branch=develop "CI"
[github-ci]: https://github.com/deluge-torrent/deluge/actions/workflows/ci.yml
[docs-status]: https://readthedocs.org/projects/deluge/badge/?version=latest
[rtd-deluge]: https://deluge.readthedocs.io/en/latest/?badge=latest "Documentation Status"
[lt]: https://libtorrent.org
