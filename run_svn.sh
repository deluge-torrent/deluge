#!/bin/sh
echo "*******************************************"
echo "  Updating to latest SVN version  "
echo "*******************************************"
svn update
echo "*******************************************"
echo "  Linking modules to working directory  "
echo "*******************************************"
ln -s src/*.py .
echo "*******************************************"
echo "  Building Deluge-SVN  "
echo "*******************************************"
python setup.py build
echo "*******************************************"
echo "  Linking C++ module to current directory  "
echo "*******************************************"
ln -s build/lib*/deluge_core.so .
echo "*******************************************"
echo "  Launching Deluge-SVN  "
echo "*******************************************"
python delugegtk.py
