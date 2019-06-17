# Setup tutorial for Deluge development

The aim of this tutorial is to download the source code and setup an
environment to enable development work on Deluge.

## Pre-requisites

To build and run the Deluge applications they depends on tools and libraries as
listed in DEPENDS.md.

Almost all of the Python packages dependencies will be installed using pip but
there are some packages or libraries that are required to be installed to the
system.

### Ubuntu

#### Build tools

    sudo apt install git intltool closure-compiler
    pip install --user tox tox-venv

#### Runtime libraries and tools

    sudo apt install python3-libtorrent python3-geoip python3-dbus  python3-gi \
    python3-gi-cairo gir1.2-gtk-3.0 gir1.2-appindicator3 python3-pygame libnotify4 \
    librsvg2-common xdg-utils

## Setup development environment

### Clone Deluge git repository

Download the latest git code to local folder.

    git clone git://deluge-torrent.org/deluge.git
    cd deluge

### Create Python virtual environment

Creation of a [Python virtual environment] keeps the development isolated
and easier to maintain and Tox has an option to make this process easier:

    tox -e denv3

Activate virtual environment:

    source .venv/bin/activate

Deluge will be installed by Tox in _develop_ mode which creates links back
to source code so that changes will be reflected immediately without repeated
installation. Check it is installed with:

    (.venv) $ deluge --version
    deluge-gtk 2.0.0b2.dev149
    libtorrent: 1.1.9.0
    Python: 2.7.12
    OS: Linux Ubuntu 16.04 xenial

### Setup pre-commit hook

Using [pre-commit] ensures submitted code is checked for quality when
creating git commits.

    (.venv) $ pre-commit install

You are now ready to start playing with the source code.

### Reference

- [Contributing]
- [Key requirements concepts]

<!--
## How-to guides

- How to install plugins in develop mode?
- How to setup and test translations?
- How to run tests?
- How to create a plugin?
-->

[pre-commit]: https://pre-commit.com
[contributing]: https://dev.deluge-torrent.org/wiki/Contributing
[requirements topic]: ../topics/requirements.md
