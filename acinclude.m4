# Copyright 1999, 2000, 2001, 2002, 2003  Free Software Foundation, Inc.

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2, or (at your option)
# any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA
# 02111-1307, USA.

# AM_PATH_PYTHON_VERSION(ABI-VERSION1, [MINIMUM-VERSION1 [, ABI-VERSION2, [MINIMUM-VERSION2 ...]]])
#
# An alternative to AM_PATH_PYTHON that checks for specific python ABI/version pairs.
# Example:
#    AM_PATH_PYTHON_VERSION(2.3, 2.3.5, 2.4, 2.4.0)
# checks for a python2.3 binary returning python version >= 2.3.5, and
# if that fails it looks for python2.4 containing version >= 2.4.0
# It aborts configure with an error if no statisfying version is found.
# Env. var. PYTHON can be used to point a specific/laternate version to configure.

AC_DEFUN([AM_PATH_PYTHON_VERSION],
 [
  m4_pattern_allow([m4_shift])
  _python_save="$PYTHON"
  dnl Find a Python interpreter with corresponding ABI version.

  m4_define(PYTHON_var, PYTHON[]m4_translit($1,[.],[_]))

  if test -z "$PYTHON"; then
    AC_PATH_PROG(PYTHON_var, python$1, [])
  else
    PYTHON_var="$PYTHON"
  fi

  PYTHON="$PYTHON_var"
  AC_SUBST(PYTHON)

  if test -n "$PYTHON"; then

  m4_if([$2],[],[
  ], [
      dnl A version check is needed.
      AC_MSG_CHECKING([whether $PYTHON version is >= $2])
      AM_PYTHON_CHECK_VERSION([$PYTHON], [$2],
			      [AC_MSG_RESULT(yes)],
			      [AC_MSG_RESULT([no]); PYTHON=""])
  ])

  fi

  if test -z "$PYTHON"; then
    dnl if more arguments, shift/recurse, else fail
    m4_if([$3],[],[
        AC_MSG_ERROR([no suitable Python interpreter found])
    ], [
        PYTHON="$_python_save"
        AM_PATH_PYTHON_VERSION(m4_shift(m4_shift($@)))
    ])

  else

  dnl Query Python for its version number.  Getting [:3] seems to be
  dnl the best way to do this; it's what "site.py" does in the standard
  dnl library.

  AC_CACHE_CHECK([for $am_display_PYTHON version], [am_cv_python_version],
    [am_cv_python_version=`$PYTHON -c "import sys; print sys.version[[:3]]"`])
  AC_SUBST([PYTHON_VERSION], [$am_cv_python_version])

  dnl Use the values of $prefix and $exec_prefix for the corresponding
  dnl values of PYTHON_PREFIX and PYTHON_EXEC_PREFIX.  These are made
  dnl distinct variables so they can be overridden if need be.  However,
  dnl general consensus is that you shouldn't need this ability.

  AC_SUBST([PYTHON_PREFIX], ['${prefix}'])
  AC_SUBST([PYTHON_EXEC_PREFIX], ['${exec_prefix}'])

  dnl At times (like when building shared libraries) you may want
  dnl to know which OS platform Python thinks this is.

  AC_CACHE_CHECK([for $am_display_PYTHON platform], [am_cv_python_platform],
    [am_cv_python_platform=`$PYTHON -c "import sys; print sys.platform"`])
  AC_SUBST([PYTHON_PLATFORM], [$am_cv_python_platform])


  dnl Set up 4 directories:

  dnl pythondir -- where to install python scripts.  This is the
  dnl   site-packages directory, not the python standard library
  dnl   directory like in previous automake betas.  This behavior
  dnl   is more consistent with lispdir.m4 for example.
  dnl Query distutils for this directory.  distutils does not exist in
  dnl Python 1.5, so we fall back to the hardcoded directory if it
  dnl doesn't work.
  AC_CACHE_CHECK([for $am_display_PYTHON script directory],
    [am_cv_python_pythondir],
    [am_cv_python_pythondir=`$PYTHON -c "from distutils import sysconfig; print sysconfig.get_python_lib(0,0,prefix='$PYTHON_PREFIX')" 2>/dev/null ||
     echo "$PYTHON_PREFIX/lib/python$PYTHON_VERSION/site-packages"`])
  AC_SUBST([pythondir], [$am_cv_python_pythondir])

  dnl pkgpythondir -- $PACKAGE directory under pythondir.  Was
  dnl   PYTHON_SITE_PACKAGE in previous betas, but this naming is
  dnl   more consistent with the rest of automake.

  AC_SUBST([pkgpythondir], [\${pythondir}/$PACKAGE])

  dnl pyexecdir -- directory for installing python extension modules
  dnl   (shared libraries)
  dnl Query distutils for this directory.  distutils does not exist in
  dnl Python 1.5, so we fall back to the hardcoded directory if it
  dnl doesn't work.
  AC_CACHE_CHECK([for $am_display_PYTHON extension module directory],
    [am_cv_python_pyexecdir],
    [am_cv_python_pyexecdir=`$PYTHON -c "from distutils import sysconfig; print sysconfig.get_python_lib(1,0,prefix='$PYTHON_EXEC_PREFIX')" 2>/dev/null ||
     echo "${PYTHON_EXEC_PREFIX}/lib/python${PYTHON_VERSION}/site-packages"`])
  AC_SUBST([pyexecdir], [$am_cv_python_pyexecdir])

  dnl pkgpyexecdir -- $(pyexecdir)/$(PACKAGE)

  AC_SUBST([pkgpyexecdir], [\${pyexecdir}/$PACKAGE])

  fi

])

