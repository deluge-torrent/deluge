#
# webui.py
#
# Copyright (C) 2008 Fredrik Eriksson <feeder@winterbird.org>
#
# Basic plugin template created by:
# Copyright (C) 2008 Martijn Voncken <mvoncken@gmail.com>
# Copyright (C) 2007, 2008 Andrew Resch <andrewresch@gmail.com>
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
#         The Free Software Foundation, Inc.,
#         51 Franklin Street, Fifth Floor
#         Boston, MA    02110-1301, USA.
#
#    In addition, as a special exception, the copyright holders give
#    permission to link the code of portions of this program with the OpenSSL
#    library.
#    You must obey the GNU General Public License in all respects for all of
#    the code used other than OpenSSL. If you modify file(s) with this
#    exception, you may extend this exception to your version of the file(s),
#    but you are not obligated to do so. If you do not wish to do so, delete
#    this exception statement from your version. If you delete this exception

import logging
import feedparser # for proccessing feed entries
import os
from deluge.ui.client import sclient, aclient
from deluge.plugins.webuipluginbase import WebUIPluginBase
from deluge import component

log = logging.getLogger(__name__)

api = component.get("WebPluginApi")
forms = api.forms

class feed_page:
    "Class for showing feed items"
    @api.deco.deluge_page
    def GET(self, feedname):
        entries = sclient.feeder_get_items(feedname)
        items = ""
        for item in entries:
            items = """%(old)s
                <a href="%(link)s">
                <li>%(entry)s</li>
                </a>""" % { "old":items, "entry":item, "link":entries[item]}
        return api.render.feeder.feeds(items, feedname)

class filter_page:
    "Class for showing filters / filter settings"
    @api.deco.deluge_page
    def GET(self, args):
        new_filter = new_filter_form()
        filters = sclient.feeder_get_filters()

        # List filters
        txt = ""
        for filter in filters:
            txt = """%(old)s
                <li onclick=\"load_options('%(new)s')\">
                %(new)s
                </li>""" % {'old':txt, 'new':filter}

        return api.render.feeder.filters(txt, new_filter)

    def POST(self):
        "Saves the new filter"
        name = api.utils.get_newforms_data(new_filter_form)['name']
        sclient.feeder_add_filter(name)
        return self.GET(name)

class new_filter_form(forms.Form):
    "basic form for a new label"
    name = forms.CharField(label="")

class filter_settings_page:
    "Class for showing filter settings"
    @api.deco.deluge_page
    def GET(self, filter):
        form = filter_settings_form(filter)
        return api.render.feeder.filter_settings(form, filter)

    def POST(self, filter):
        opts = api.utils.get_newforms_data(filter_settings_form)

        # apparently the "Unlimited" options still have to be changed
        # to -1 (wtf?)
        # FIXME there is probably a very much better way to ensure that
        # all values have the right types... not to mention to convert "Unlimited"
        # to -1...
        try:
            opts['max_upload_speed'] = int(opts['max_upload_speed'])
        except:
            opts['max_upload_speed'] = int(-1)
        try:
            opts['max_download_speed'] = int(opts['max_download_speed'])
        except:
            opts['max_download_speed'] = int(-1)
        try:
            opts['max_connections'] = int(opts['max_connections'])
        except:
            opts['max_connections'] = int(-1)
        try:
            opts['max_upload_slots'] = int(opts['max_upload_slots'])
        except:
            opts['max_upload_slots'] = int(-1)
        """opts['max_upload_slots'] = long(opts['max_upload_slots'])
        opts['max_connections'] = long(opts['max_connections'])"""

        # TODO filter settings per feed not implemented.
        opts['feeds'] = []

        sclient.feeder_set_filter_config(filter, opts)
        return self.GET(filter)

class filter_settings_form(forms.Form):
    "form for filter settings"

    def __init__(self, filter, test=False):
        self.filtername = filter # We want to save our filtername
        forms.Form.__init__(self)

    def initial_data(self):
        self.conf = sclient.feeder_get_filter_config(self.filtername)
        return self.conf

    def post_html(self):
        regex = self.conf["regex"]
        hits = sclient.feeder_test_filter(regex)
        if not hits:
            return "No hits"
        list = ""
        for hit in hits:
            list = """%(old)s
            <li><a href="%(link)s" >%(name)s</a></li>
            """ % { "old":list, "link":hits[hit], "name":hit }
        return """
        <ul>
            %s
        </ul>
        """ % list

    regex = forms.CharField(_("regular_expression"))
    all_feeds = forms.CheckBox(_("all_feeds"))
    active = forms.CheckBox(_("active"))

    #maximum:
    max_download_speed = forms.DelugeFloat(_("max_download_speed"))
    max_upload_speed = forms.DelugeFloat(_("max_upload_speed"))
    max_upload_slots = forms.DelugeInt(_("max_upload_slots"))
    max_connections = forms.DelugeInt(_("max_connections"))

    stop_ratio = forms.DelugeFloat(_("stop_ratio"))
    stop_at_ratio = forms.CheckBox(_("stop_at_ratio"))
    remove_at_ratio = forms.CheckBox(_("remove_at_ratio"))

    #queue:
    auto_managed = forms.CheckBox(_("is_auto_managed"))
    prioritize_first_last_pieces = forms.CheckBox(_("prioritize_first_last_pieces"))

    download_location = forms.ServerFolder(_("download_location"))

class remove_feed_page:
    "Class for deleting feeds, redirects to setting page"
    @api.deco.deluge_page
    def GET(self, feedname):
        sclient.feeder_remove_feed(feedname)
        return """<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN" "http://www.w3.org/TR/html4/strict.dtd">
        <html>
        <head>
        <title>Redirecting back to settings</title>
        <meta http-equiv="refresh" content="0; URL=/config/feeder">
        <meta http-equiv="Content-Type" content="text/html; charset=utf-8">
        </head>
        <body>
        </body>

        </html>"""

class remove_filter_page:
    "Class for deleting filters, redirects to setting page"
    @api.deco.deluge_page
    def GET(self, name):
        sclient.feeder_remove_filter(name)
        return """<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN" "http://www.w3.org/TR/html4/strict.dtd">
        <html>
        <head>
        <title>Redirecting back to settings</title>
        <meta http-equiv="refresh" content="0; URL=/config/feeder">
        <meta http-equiv="Content-Type" content="text/html; charset=utf-8">
        </head>
        <body>
        </body>

        </html>"""


class WebUI(WebUIPluginBase):
    #map url's to classes: [(url,class), ..]
    urls = [('/feeder/filters', filter_page),
            ('/feeder/filter_settings/(.*)', filter_settings_page),
            ('/feeder/feed_remove/(.*)', remove_feed_page),
            ('/feeder/filter_remove/(.*)', remove_filter_page),
            ('/feeder/feed/(.*)', feed_page)]

    def enable(self):
        api.config_page_manager.register('plugins', 'feeder' ,ConfigForm)

    def disable(self):
        api.config_page_manager.deregister('feeder')

class ConfigForm(forms.Form):
    #meta:
    title = _("feeder")

    #load/save:
    def initial_data(self):
        return sclient.feeder_get_config()

    def save(self, data):
        cfg = dict(data)
        sclient.feeder_add_feed(cfg)

    def pre_html(self):
        feeds = sclient.feeder_get_feeds()
        filters = sclient.feeder_get_filters()
        filterlist = ""
        for filter in filters:
            filterlist = """ %(old)s <li>%(new)s
                <a href="/feeder/filter_remove/%(new)s">
                <img src="/static/images/16/list-remove.png" alt="Remove" />
                </a></li>""" % {'old':filterlist, 'new':filter}
        feedlist = ""
        for feed in feeds:
            feedlist = """%(old)s
                <li> <a href="/feeder/feed/%(new)s"> %(new)s (%(entrys)s torrents)</a>
                <a href="/feeder/feed_remove/%(new)s">
                <img src="/static/images/16/list-remove.png" alt="Remove" />
                </a></li>""" % {'old':feedlist, 'new':feed, 'entrys':len(sclient.feeder_get_items(feed))}

        return """
        <table width=100%%><tr><td>
            <h3>Feeds</h3>
        </td>
        <td>
            <h3>Filters</h3>
        </td></tr>
        <tr><td>
            <div class="info">
            <ul>
            %(feeds)s
            </ul></div>
        </td><td>
            <div class="info">
            <ul>
            %(filters)s
            </ul></div>
        <a href="/feeder/filters">Add/modify filters</a>
        </td></tr>
        </table>
        <h3>Add/change feed settings</h3>""" % {'feeds':feedlist, 'filters':filterlist}

    name = forms.CharField(label=_("Name of feed"))
    url = forms.URLField(label=_("URL of feed"))
    updatetime = forms.IntegerField(label=_("Defualt refresh time"))

