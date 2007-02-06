#!/bin/sh
#
# This file is public domain
# 
# run_svn.sh
#
# This is a small shell script to build and run
# a working copy of Deluge without installing
# it globally.  This is only intended for
# testing SVN versions of Deluge, and should 
# not be used for a final installation.
#
# I make no guarantees that this script will 
# work for you, but it does build and run
# properly on my system.
#

if [ -d ./working/ ]
then
	echo "*******************************************"
	echo "  Removing old files  "
	echo "*******************************************"
	rm -rf working/
fi
echo "*******************************************"
echo "  Updating to latest SVN version  "
echo "*******************************************"
svn update
echo "*******************************************"
echo "  Copy source to working directory  "
echo "*******************************************"
cp -r src working
echo "*******************************************"
echo "  Linking files to working directory  "
echo "*******************************************"
ln -s ../glade working/
ln -s ../pixmaps working/
echo "*******************************************"
echo "  Building Deluge-SVN  "
echo "*******************************************"
python setup.py build
echo "*******************************************"
echo "  Linking C++ module to current directory  "
echo "*******************************************"
for file in $(echo build/*)
do
	if [ -e $file/deluge/deluge_core.so ]
	then
		ln -s ../$file/deluge/deluge_core.so working/
	fi
done
echo "*******************************************"
echo "  Launching Deluge-SVN  "
echo "*******************************************"
python working/delugegtk.py
