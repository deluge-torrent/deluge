# -*- coding: utf-8 -*-
#
# Copyright (C) 2009 Damien Churchill <damoxc@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

import gettext
import zlib

from deluge import common


def _(text):
    return gettext.gettext(text).decode("utf-8")


def escape(text):
    """
    Used by the gettext.js template to escape translated strings
    so they don't break the script.
    """
    text = text.replace("'", "\\'")
    text = text.replace('\r\n', '\\n')
    text = text.replace('\r', '\\n')
    text = text.replace('\n', '\\n')
    return text


def compress(contents, request):
    request.setHeader("content-encoding", "gzip")
    compress_zlib = zlib.compressobj(6, zlib.DEFLATED, zlib.MAX_WBITS + 16, zlib.DEF_MEM_LEVEL, 0)
    contents = compress_zlib.compress(contents)
    contents += compress_zlib.flush()
    return contents

try:
    # This is beeing done like this in order to allow tests to use the above
    # `compress` without requiring Mako to be instaled
    from mako.template import Template as MakoTemplate

    class Template(MakoTemplate):
        """
        A template that adds some built-ins to the rendering
        """

        builtins = {
            "_": _,
            "escape": escape,
            "version": common.get_version()
        }

        def render(self, *args, **data):
            data.update(self.builtins)
            rendered = MakoTemplate.render_unicode(self, *args, **data)
            return rendered.encode('utf-8', 'replace')
except ImportError:
    import warnings
    warnings.warn("The Mako library is required to run deluge.ui.web",
                  RuntimeWarning)

    class Template(object):
        def __new__(cls, *args, **kwargs):
            raise RuntimeError(
                "The Mako library is required to run deluge.ui.web"
            )
