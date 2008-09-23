#
# webuipluginbase.py
#
# Copyright (C) 2008 Andrew Resch ('andar') <andrewresch@gmail.com>
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
# 	The Free Software Foundation, Inc.,
# 	51 Franklin Street, Fifth Floor
# 	Boston, MA    02110-1301, USA.
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


from deluge.log import LOG as log
from deluge import component
import os
api = component.get("WebPluginApi")


"""
def plugin_render_template(*args , **kwargs):
    return "plugin-render"

class plugin_render():
    def __getattr__(self, attr):
        return plugin_render_template
"""


class WebUIPluginBase:
    """
    convenience class, you don't have to use this, but it does make things easyer to setup.
    * static files: /data is automatically served on http as as /safe-plugin-name/data
    * templates: /template are added to api.render.plugin-name.
    * pages: urls attribute registers pages : urls = [(url, class), ..]
    """
    urls= []
    def __init__(self, plugin_api, plugin_name):
        log.debug("%s plugin : start initalize.." % plugin_name)
        self.plugin = plugin_api
        self.plugin_name = plugin_name
        clean_plugin_name = plugin_name.lower().replace(" ","_")

        for url , klass in self.urls:
                api.page_manager.register_page(url, klass)

        class egg_data_static(api.egg_handler): #serves files in /data from egg
            resource = clean_plugin_name
            base_path = "data"

        setattr(api.render, clean_plugin_name, api.egg_render(clean_plugin_name, "template"))

        api.page_manager.register_page("/%s/data/(.*)" % clean_plugin_name , egg_data_static)

        log.debug("%s plugin : end initalize.." % plugin_name)
