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

    sudo apt install git intltool closure-compiler python3-pip
    pip3 install --user tox

You might need to add `~/.local/bin` to your PATH.

#### Runtime libraries and tools

    sudo apt install python3-libtorrent python3-geoip python3-dbus  python3-gi \
    python3-gi-cairo gir1.2-gtk-3.0 gir1.2-ayatanaappindicator3-0.1 python3-pygame libnotify4 \
    librsvg2-common xdg-utils

## Setup development environment

### Clone Deluge git repository

Download the latest git code to local folder.

    git clone git://deluge-torrent.org/deluge.git
    cd deluge

### Using Docker for development (Optional)

As an alternative to setting up a local development environment, you can use Docker to develop Deluge. This approach isolates the development environment and ensures consistency across different systems.

#### Prerequisites

- [Docker](https://docs.docker.com/get-docker/)
- [Docker Compose](https://docs.docker.com/compose/install/)

#### Setup with Docker

Deluge provides Docker configuration files in the repository to make development easier. The setup includes:

1. **Dockerfile**: Defines the development environment with all necessary dependencies
2. **docker-compose.yml**: Configures services for development and testing

To start development using docker compose first we will need to build the image from `Dockerfile`

    docker compose build

There are two services present in docker compose, one for devlopment and another for running tests/linting. Exeuting `docker compose up` will run both at once

If you just want run tests:

    docker compose up test

Otherwise, run and jump into dev container and continue to the next step

    docker compose up dev -d
    docker exec -it deluge-dev-1 bash

### Create Python virtual environment

Creation of a [Python virtual environment] keeps the development isolated
and easier to maintain and Tox has an option to make this process easier:

    tox -e denv

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
