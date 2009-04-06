#
# webuipluginbase.py
#
# Copyright (C) 2008 Andrew Resch <andrewresch@gmail.com>
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
# 	Boston, MA  02110-1301, USA.
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



from deluge.log import LOG as log
from deluge import component
import os
api = component.get("WebPluginApi")


class WebUIPluginBase:
    """
    convenience class, you don't have to use this, but it does make things easyer to setup.
    * static files: /data is automatically served on http as as /safe-plugin-name/data
    * templates: /template are added to api.render.plugin-name.
    * pages: urls attribute registers pages : urls = [(url, class), ..]
    """
    include_javascript = []
    ajax_javascript = []
    urls = []

    def __init__(self, plugin_api, plugin_name):
        log.debug("%s plugin : start initalize.." % plugin_name)

        self.plugin = plugin_api
        self.plugin_name = plugin_name
        self.clean_plugin_name = plugin_name.lower().replace(" ","_")


    def base_enable(self):
        """
        enable plugin.
        """
        for url , klass in self.urls:
            api.page_manager.register_page(url, klass)

        for js in self.include_javascript:
            api.page_manager.include_javascript.append(js)

        class egg_data_static(api.egg_handler): #serves files in /data from egg
            resource = self.clean_plugin_name
            base_path = "data"

        #use as : api.render.plugin-name.template-name[excluding.html](parameters)
        setattr(api.render, self.clean_plugin_name, api.egg_render(self.clean_plugin_name, "template"))

        api.page_manager.register_page("/%s/data/(.*)" % self.clean_plugin_name , egg_data_static, use_module=False)

        log.debug("%s plugin : end base_enable().." % self.plugin_name)

    def base_disable(self):
        """
        disable plugin.
        """
        for url , klass in self.urls:
            api.page_manager.deregister_page(url, klass)

        for js in self.include_javascript:
            api.page_manager.include_javascript.remove(js)

        log.debug("%s plugin : end base_disable().." % self.plugin_name)



