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
#   Boston, MA    02110-1301, USA.
#

import gettext
from mako.template import Template as MakoTemplate
from deluge import common

class Template(MakoTemplate):
    
    builtins = {
        "_": lambda x: gettext.gettext(x).decode("utf-8"),
        "version": common.get_version()
    }
    
    def render(self, *args, **data):
        data.update(self.builtins)
        rendered = MakoTemplate.render_unicode(self, *args, **data)
        return rendered.encode('utf-8', 'replace')
