#
# deluge/ui/web/common.py
#
# Copyright (C) 2009 Damien Churchill <damoxc@gmail.com>
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
#   The Free Software Foundation, Inc.,
#   51 Franklin Street, Fifth Floor
#   Boston, MA  02110-1301, USA.
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
#

import zlib
import gettext
from mako.template import Template as MakoTemplate
from deluge import common

_ = lambda x: gettext.gettext(x).decode("utf-8")

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
    compress = zlib.compressobj(6, zlib.DEFLATED, zlib.MAX_WBITS + 16,
        zlib.DEF_MEM_LEVEL,0)
    contents = compress.compress(contents)
    contents += compress.flush()
    return contents

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
