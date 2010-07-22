#!/bin/bash
#
# This script checks out libtorrent from subversion
#

SVN=$(which svn)
LT_URL=https://libtorrent.svn.sourceforge.net/svnroot/libtorrent
VERSION=14
[ "$1" != "" ] && VERSION=$1
BRANCH=branches/RC_0_$VERSION

if [ -d libtorrent ]; then
	$SVN up libtorrent
else
	$SVN co $LT_URL/$BRANCH libtorrent
fi
