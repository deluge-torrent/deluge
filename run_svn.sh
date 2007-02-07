#!/bin/sh
#
# This file is public domain
# 
# run_svn.sh
#
# This is a small shell script to build and run
# a working copy of Deluge-SVN
#

if [ -d ./working/ ]
then
	echo "  Removing old files:  "
	rm -rvf working
fi
echo "  Creating new working directory:  "
mkdir -v working/ working/glade/ working/pixmaps/
echo "  Updating to latest SVN version:  "
svn update
echo "  Copy source to working directory:  "
for file in $(echo src/*)
do
	cp -v $file working/
done
echo "  Copying data to working directory:  "
for file in $(echo glade/*)
do
	cp -v $file working/glade/
done
for file in $(echo pixmaps/*)
do
	cp -v $file working/pixmaps/
done
echo "  Building Deluge-SVN:  "
python setup.py build
echo "  Copying C++ module to current directory:  "
for file in $(echo build/*)
do
	if [ -e $file/deluge/deluge_core.so ]
	then
		cp -v $file/deluge/deluge_core.so working/
	fi
done
echo "  Launching Deluge-SVN:  "
python working/delugegtk.py
