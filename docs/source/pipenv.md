# Using pipenv

For a quick summary read: https://docs.pipenv.org/basics/

## Prerequisites

- python-libtorrent
- pip
- pipenv

## Install pipenv and packages

Install Pipenv and upgrade pip:

    pip install -U pip pipenv

On Ubuntu:

    sudo -H pip install -U pip pipenv

In order to have access to system libtorrent we use `--site-packages` and
enable `PIP_IGNORE_INSTALLED`. Hopefully libtorrent will be available as a
pypi package at somepoint.

See: https://docs.pipenv.org/advanced/#working-with-platform-provided-python-components

Note you can `export PIP_IGNORE_INSTALLED=1` to save prefixing each time. It
has been included in commands below to denote requirement.

### Users

    PIP_IGNORE_INSTALLED=1 pipenv --site-packages install

### Developers

    PIP_IGNORE_INSTALLED=1 pipenv --site-packages install --dev

### Test libtorrent installed

    pipenv run python -c 'import libtorrent as lt; print(lt.version)'

### Bash shell completion

To enable Pipenv shell completion for commands:

    eval "$(pipenv --completion)"

## Running commands

You can either enter the Pipenv virtualenv shell:

    pipenv shell --fancy
    ./setup.py build

Note: To check whether you are in a venv use `which python`.

or prefix commands with the `pipenv run` option:

    pipenv run ./setup.py build

## Developing Deluge

This is the equivalent to `setup.py develop` but uses the pipenv environment:

    pipenv install --dev -e .
