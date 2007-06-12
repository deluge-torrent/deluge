AC_INIT([deluge], [0.5.2], [zach@collegegeek.org])
AM_INIT_AUTOMAKE([-Wall -Werror foreign])

m4_define(required_pygtk_version, 2.8.0)
m4_define(required_python_abi, 2.4)

AM_PATH_PYTHON_VERSION(2.4, 2.4.0, 2.5, 2.5.0)

dnl Check for correctly installed pygtk
AC_MSG_CHECKING(for pygtk required_pygtk_version installed for python required_python_abi)
prog="
import pygtk; pygtk.require('2.0')
import gtk
assert gtk.pygtk_version >= tuple(map(int, 'required_pygtk_version'.split('.')))
"
if $PYTHON -c "$prog" 1>&AC_FD_CC 2>&AC_FD_CC; then
    AC_MSG_RESULT(found)
else
    AC_MSG_RESULT(not found)
    AC_MSG_ERROR(required pygtk version not found)
fi

AC_PROG_CC
AC_CONFIG_HEADERS([config.h])
AC_CONFIG_FILES([
 Makefile
 src/Makefile
])
AC_OUTPUT
