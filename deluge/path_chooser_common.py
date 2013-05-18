#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# path_chooser_common.py
#
# Copyright (C) 2013 Bro <bro.development@gmail.com>
#
# Deluge is free software.
#
# You may redistribute it and/or modify it under the terms of the
# GNU General Public License, as published by the Free Software
# Foundation; either version 3 of the License, or (at your option)
# any later version.
#
# deluge is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with deluge.    If not, write to:
#       The Free Software Foundation, Inc.,
#       51 Franklin Street, Fifth Floor
#       Boston, MA  02110-1301, USA.
#
#    In addition, as a special exception, the copyright holders give
#    permission to link the code of portions of this program with the OpenSSL
#    library.
#    You must obey the GNU General Public License in all respects for all of
#    the code used other than OpenSSL. If you modify file(s) with this
#    exception, you may extend this exception to your version of the file(s),
#    but you are not obligated to do so. If you do not wish to do so, delete
#    this exception statement from your version. If you delete this exception
#    statement from all source files in the program, then also delete it here.
#

import os

def get_resource(filename):
    import deluge
    return deluge.common.resource_filename("deluge.ui.gtkui", os.path.join("glade", filename))

def is_hidden(filepath):
    def has_hidden_attribute(filepath):
        import win32api, win32con
        try:
            attribute = win32api.GetFileAttributes(filepath)
            return attribute & (win32con.FILE_ATTRIBUTE_HIDDEN | win32con.FILE_ATTRIBUTE_SYSTEM)
        except (AttributeError, AssertionError):
            return False

    name = os.path.basename(os.path.abspath(filepath))
    # Windows
    if os.name== 'nt':
        return has_hidden_attribute(filepath)
    return name.startswith('.')

def get_completion_paths(args):
    """
    Takes a path value and returns the available completions.
    If the path_value is a valid path, return all sub-directories.
    If the path_value is not a valid path, remove the basename from the
    path and return all sub-directories of path that start with basename.

    :param args: options
    :type args: dict
    :returns: the args argument containing the available completions for the completion_text
    :rtype: list

    """
    args["paths"] = []
    path_value = args["completion_text"]
    hidden_files = args["show_hidden_files"]

    def get_subdirs(dirname):
        try:
            return os.walk(dirname).next()[1]
        except StopIteration:
            # Invalid dirname
            return []

    dirname = os.path.dirname(path_value)
    basename = os.path.basename(path_value)

    dirs = get_subdirs(dirname)
    # No completions available
    if not dirs:
        return args

    # path_value ends with path separator so
    # we only want all the subdirectories
    if not basename:
        # Lets remove hidden files
        if not hidden_files:
            old_dirs = dirs
            dirs = []
            for d in old_dirs:
                if not is_hidden(os.path.join(dirname, d)):
                    dirs.append(d)
    matching_dirs = []
    for s in dirs:
        if s.startswith(basename):
            p = os.path.join(dirname, s)
            if not p.endswith(os.path.sep):
                p += os.path.sep
            matching_dirs.append(p)

    args["paths"] = sorted(matching_dirs)
    return args
