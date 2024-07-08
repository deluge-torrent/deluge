# Build libtorrent from source

Check libtorrent [documentation](http://www.libtorrent.org/building.html) for any updates to build procedures.

## Ubuntu / Debian

1. Install dependencies for libtorrent build automatically using `build-dep`:

 ```
 sudo apt-get build-dep libtorrent-rasterbar
 sudo apt-get install checkinstall
```

 **OR** if that fails manually install them:

 ```
 sudo apt-get install build-essential checkinstall libboost-system-dev libboost-python-dev libboost-chrono-dev libboost-random-dev libssl-dev
 ```

2. Download [libtorrent](https://github.com/arvidn/libtorrent/releases) and extract:

```
tar xf libtorrent-rasterbar.tar.gz
cd libtorrent-rasterbar
```
3. Configure:

 ```
 ./configure --enable-python-binding --with-libiconv
```
- Missing `configure` script: (e.g. source code from git) create it with `./autotool.sh` (requires extra packages: `sudo apt-get install autoconf automake libtool`).
- *Logging:* Add `--enable-logging=default` to get logs in the current working directory. `verbose` and `error` can also be used.
- *Debug:* To create a debug build add `--enable-debug=yes`.
- ARM architecture (Raspberry Pi, etc): add `--with-boost-libdir=/usr/lib/arm-linux-gnueabihf` at the end to avoid boost library error.

4. Build:

```
make -j$(nproc)
```
- *CPU Cores:* The `make` option `-j$(nproc)` will utilize all available cpu cores.
- *Non-specific errors:* e.g. `g++: internal compiler error: Killed (program cc1plus)` try using a [#TemporarySwapFileforRasperryPiorlowmemorysystems temporary swap file]

5. Install library and python bindings:

```
sudo checkinstall
sudo ldconfig
```
 *Substituted `make install` for `checkinstall` as it creates a deb package for easier removal/re-install by `dpkg`.*

 *Running `ldconfig` avoids an `ImportError` for `libtorrent-rasterbar.so`, a result of Python being unable to find the main library.*

6. Verify libtorrent and the python bindings are installed correctly:

```
python3 -c "import libtorrent; print (libtorrent.version)"
>> 1.0.6.0
```


### Temporary Swap File for Rasperry Pi or low memory systems

Compiling libtorrent requires a lot of memory/swap during the `make` process ~1-2GB.

If you get an internal error during the make phase on a computer with low memory and/or no swap partition (verify with `free -m` ) you can try the below procedure.

1. Create a 1GB empty swap file, (use a drive location that has enough free space):

```
dd if=/dev/zero of=/.swapfile bs=1M count=1024
```
2. Format swap file:

```
mkswap /.swapfile
```
3. Activate swap file:

```
sudo swapon /.swapfile
```
4. Verify swap file is recognized:

```
swapon -s
```
5. Start/restart your libtorrent build.
6. Disable swap file:

```
swapoff /.swapfile
```
7. Delete swap file:

```
rm -f /.swapfile
```



## Windows

1. Download and install/extract these packages:
   * [MS VC++ Compiler for Python](http://www.microsoft.com/en-us/download/details.aspx?id=44266)
   * [OpenSSL](https://openssl.org/source/) requirement needs [building from source](http://dev.deluge-torrent.org/wiki/Building/openssl#BuildingOpenSSLforWindows).
   * [Python 2.7](http://www.python.org/)
   * [MSVC 2008 SP1 Redist Package (x86)](http://www.microsoft.com/en-us/download/details.aspx?id=5582)
   * [.NET Framework 3.5](https://www.microsoft.com/en-gb/download/details.aspx?id=21)
   * [Boost](http://sourceforge.net/projects/boost/files/boost/)
   * [libtorrent](https://github.com/arvidn/libtorrent/releases)

   *Note: Install or extract to a path without spaces e.g. `C:\` drive.*

1. Setup the Windows Command Prompt by executing `VC for Python` `vcvarsall.bat`, e.g.:

    ```
    "%USERPROFILE%\AppData\Local\Programs\Common\Microsoft\Visual C++ for Python\9.0\vcvarsall.bat"
    ```

    *Note: If using Visual Studio simple open a `Visual Studio 2008 Command Prompt`.*

3. Boost Build Steps:

    In the boost directory run the following:

    ```
    bootstrap.bat
    ```
    Due to a [boost bug](https://svn.boost.org/trac/boosthttps://dev.deluge-torrent.org/ticket/10817) with `VC for Python`, need to edit `project-config.jam` in boost folder to the following:

    ```
    using msvc : : : <setup>"%USERPROFILE%\\AppData\\Local\\Programs\\Common\\Microsoft\\Visual C++ for Python\\9.0\\vcvarsall.bat" ;
    ```

    Then run:

    ```
     b2 --with-system --with-date_time --with-python --with-chrono --with-random
    ```

5. Create a Boost `user-config.jam` file in the toplevel folder (e.g. `C:\boost`) with the following to force `msvc` version:

    ```
    using msvc : 9.0 : : <setup>"%USERPROFILE%\\AppData\\Local\\Programs\\Common\\Microsoft\\Visual C++ for Python\\9.0\\vcvarsall.bat" ;
    ```

    Note: For Visual Studio, simply `using msvc : 9.0 ;` is required.

6. libtorrent Build Steps:

    a. Setup the Environmental Variables:

    ```
    set BOOST_BUILD_PATH=C:\boost
    set PATH=%BOOST_BUILD_PATH%;%PATH%
    ```
      b. Navigate to libtorrent Python bindings folder:

    ```
    cd C:\libtorrent-rasterbar\bindings\python
    ```

    c. Build libtorrent with Python bindings:

    ```
    b2 boost=source libtorrent-link=static geoip=static boost-link=static release optimization=space encryption=openssl include=C:\OpenSSL-Win32\include linkflags=/LIBPATH:C:\OpenSSL-Win32\lib -j%NUMBER_OF_PROCESSORS% --hash
    ```
    *Note1: Modify the paths for OpenSSL if installed to a different location.*

    *Note2: For libtorrent versions <=1.0.6 rename `libtorrent-link` to `link`.*

    For libtorrent versions >=1.1:

    ```
    b2 libtorrent-link=static boost-link=static release optimization=space encryption=on crypto=openssl include=C:\OpenSSL-Win32\include linkflags=/LIBPATH:C:\OpenSSL-Win32\lib -j%NUMBER_OF_PROCESSORS% --hash
    ```

    Upon a successful build the library file named `libtorrent.pyd` is created in the current `bindings/python` directory.


### Debugging libtorrent on Windows

* Download and install just the `debug tools`:
  * [Standalone Debugging Tools for Windows (WinDbg)](http://msdn.microsoft.com/en-us/windows/hardware/hh852365.aspx)
* Build libtorrent with debug enabled by changing `release` to `debug` in the `b2` build line.
* Open `windbg` *(C:\Program Files\Debugging Tools for Windows (x86)\windbg.exe)*:
  * `File|Open Executable` and tick `Debug child processes`
  * Hit `F5` or `Go` a few times to get the program running
  * After the crash execute: `!analyze -v -f`.
* Symbols for libtorrent will be in the build output path:

  ```
  C:\libtorrent-rasterbar\bindings\python\bin\msvc-9.0\debug\boost-source\geoip-static\link-static\optimization-space\threading-multi
```
  So the full symbols line should look something like this:

  ```
  srv*;C:\libtorrent-rasterbar\bindings\python\bin\msvc-9.0\debug\boost-source\geoip-static\link-static\optimization-space\threading-multi;C:\Python27\symbols;srv*c:\Symbols*http://msdl.microsoft.com/download/symbols
```

Debug References:
* [Mozilla WinDbg stacktrace](https://developer.mozilla.org/en/docs/How_to_get_a_stacktrace_with_WinDbg)
* [Windbg for Beginners](http://gui-at.blogspot.co.uk/2010/01/windbg-for-beginners.html)

## Further Resources

* [libtorrent](http://libtorrent.org/building.html)
* [Leechcraft](http://leechcraft.org/development-building-from-source-win32#Building_libtorrent)
* [QBittorrent](https://github.com/qbittorrent/qBittorrent/wiki/Compiling-with-MSVC-2008%28static-linkage%29)
