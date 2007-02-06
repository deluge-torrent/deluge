#!/bin/sh
echo "*******************************************"
echo "  Updating to latest SVN version  "
echo "*******************************************"
svn update
echo "*******************************************"
echo "  Building Deluge-SVN  "
echo "*******************************************"
python setup.py build
echo "*******************************************"
echo "  Linking C++ module to current directory  "
echo "*******************************************"
rm deluge_core.so
ln -s build/lib*/deluge_core.so .
echo "*******************************************"
echo "  Launching Deluge-SVN  "
echo "*******************************************"
python delugegtk.py