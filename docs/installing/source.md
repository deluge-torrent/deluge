
<h1 style="text-align: left;">Installing Deluge From Source</h1>


This is build manual for Deluge 1.3.x. Build manual for 2.0.x version is here: https://deluge.readthedocs.io/en/latest/devguide/tutorials/01-setup.html

# Dependencies
Deluge has a number of dependencies that are required for it to run properly.  Most of them are runtime only deps, but a few are required for successfully building Deluge.

The 1.3.x dependencies are listed below. You will also need to install the appropriate build tools provided by your OS.


## Debian & Ubuntu Dependencies
Apt-get line to install all above dependencies:

```
sudo apt-get install python python-twisted python-openssl python-setuptools intltool python-xdg python-chardet geoip-database python-libtorrent python-notify python-pygame python-glade2 librsvg2-common xdg-utils python-mako
```

## Windows Dependencies

Python dependencies should be **py2.7** and **win32** (32-bit)''

* **[Python 2.7](http://www.python.org/download/)** *(Select `Add python.exe to path` when Installing)*
* **[python-libtorrent](http://sourceforge.net/projects/libtorrent/files/py-libtorrent/)**
* **[openssl-1.0.*-i386-win32](https://indy.fulgan.com/SSL/?C=M;O=D)** *(`copy to system32`)*
* **[PyGTK All-in-one](http://www.pygtk.org/downloads.html)**

After *Python* is installed, use *pip* to install the following from console:

```
pip install twisted[tls] chardet mako pyxdg pillow slimit pypiwin32 pygame certifi
```

## libtorrent (rasterbar)

For those advanced cases where you need to build and install [libtorrent](http://libtorrent.org/) from source, follow this guide: [Building/libtorrent](/building/libtorrent)

# Download Source
You can either get the source from a tarball on our [ftp](http://download.deluge-torrent.org/source/?C=M;O=D) or from our [GitRepo](/gitrepo).

# Building and Installing
Extract the source tarball and in the extracted folder run the build command:

```
python setup.py build
```

Install the package to your system:

```
sudo python setup.py install
```
* *Debian & Ubuntu: Append `--install-layout=deb` to use `/usr/bin/` prefix instead of Debian default `/usr/bin/local/`.*
* *Microsoft Windows: Omit `sudo` prefix.*

For Linux Desktop systems an extra step is required due to an installer [bug](http://dev.deluge-torrent.org/ticket/1389) not copying data files, such as `deluge.desktop`:

```
sudo python setup.py install_data
```

If you have run the build before, ensure you have a clean build environment:

```
python setup.py clean -a
```

## Developer Install

Installing Deluge with `develop` mode creates binaries that link back to source code. Therefore changes will be reflected immediately with no need to repeatedly install.

```
python setup.py develop
```

If you wish to use a specific development directory, the following will create a Deluge install in ~/delugeDev:

```
export PYTHONPATH=${HOME}/delugeDev
python setup.py develop --install-dir ~/delugeDev
```

Do have the included plugins available, build them with

```
python setup.py build_plugins develop
```

Another alternative for a separate Deluge development environment is to use Python [Virtualenv](http://pypi.python.org/pypi/virtualenv)

# Removing From System
In the unlikely event you want to remove Deluge installed by the previous method, you will have to manually delete the Deluge related files on your system. The main files are normally installed in one of the following places:

```
/usr/lib/python2.x/site-packages
/usr/local/lib/python2.x/site-packages
/usr/lib/python2.x/dist-packages
/usr/local/lib/python2.x/dist-packages
```

Example:

```
sudo rm -r /usr/lib/python2.7/dist-packages/deluge*
```

To find and remove the remaining files use the `locate` command and to ensure up-to date information also run `updatedb`:

```
sudo updatedb
locate deluge
```