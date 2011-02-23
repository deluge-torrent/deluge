#
# preferences.py
#
# Copyright (C) 2007-2010 Andrew Resch <andrewresch@gmail.com>
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
#     The Free Software Foundation, Inc.,
#     51 Franklin Street, Fifth Floor
#     Boston, MA  02110-1301, USA.
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

import os
import gtk

import logging
import pkg_resources
from twisted.internet.defer import maybeDeferred

import deluge.component as component
import dialogs
from deluge.ui.client import client
import deluge.common
import deluge.error
import common

log = logging.getLogger(__name__)

class PreferencePage(object):
    """
    Must set a name and widget prior to adding to them Preferences dialog.
    """
    def __init__(self):
        self.name = ""
        self.widget = None
        self.builder = None

        # Set the core widgets and their config keys
        # {widget: (accessor, core_key, non_localhost_widget), ...}
        self.core_widgets = {}
        # Likewise for local widgets
        self.local_widgets = {}

    def show(self):
        """
        Called when the page needs to have it's values updated.
        """
        raise NotImplementedError

    def apply(self):
        """
        Called when the settings need to be saved.  This method needs to be
        defined by the subclass.
        """
        raise NotImplementedError

    def set_widget(self, widget):
        """
        Creates a scrolled window with a proper header for the widget.  The
        widget is likely a gtk.VBox or similar container.

        :param widget: the container widget for all the pref widgets
        :type widget: gtk.Widget

        """
        # Create a header and scrolled window for the preferences tab
        parent = widget.get_parent()
        if parent:
            parent.remove(widget)
        vbox = gtk.VBox()
        label = gtk.Label()
        label.set_use_markup(True)
        label.set_markup("<b><i><big>" + self.name + "</big></i></b>")
        label.set_alignment(0.00, 0.50)
        label.set_padding(10, 10)
        vbox.pack_start(label, False, True, 0)
        sep = gtk.HSeparator()
        vbox.pack_start(sep, False, True, 0)
        align = gtk.Alignment()
        align.set_padding(5, 0, 0, 0)
        align.set(0, 0, 1, 1)
        align.add(widget)
        vbox.pack_start(align, True, True, 0)
        scrolled = gtk.ScrolledWindow()
        viewport = gtk.Viewport()
        viewport.set_shadow_type(gtk.SHADOW_NONE)
        viewport.add(vbox)
        scrolled.add(viewport)
        scrolled.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.widget = scrolled

    def set_widget_from_file(self, xmlfile, obj):
        """
        Sets the widget from an object in a gtkBuilder xml file.

        :param xmlfile: the path to the xml file
        :type xmlfile: string
        :param obj: the object name to use
        :type obj: string

        """
        if not os.path.isfile(xmlfile):
            xmlfile = os.path.join(os.path.dirname(__file__), xmlfile)
        self.builder = gtk.Builder()
        self.builder.add_from_file(xmlfile)
        self.set_widget(self.builder.get_object(obj))
        
        
class GtkUIPreferencePage(PreferencePage):
    def __init__(self, name, xml, widget):
        super(GtkUIPreferencePage, self).__init__()
        self.name = name
        self.set_widget_from_file(xml, widget)

    def show(self):
        """
        Called when the page needs to have it's values updated.
        """
        if self.core_widgets:
            coreconfig = component.get("CoreConfig")
            for name, (accessor, key, non_localhost) in self.core_widgets.items():
                widget = self.builder.get_object(name)
                getattr(widget, "set_" + accessor)(coreconfig[key])
                if client.is_localhost():
                    # Hide any non_localhost widgets
                    if non_localhost:
                        self.builder.get_object(non_localhost).hide()
                        widget.show()
                else:
                    if non_localhost:
                        # Hide this widget because it should only be shown
                        # if core is a localhost, but show its non_localhost widget
                        self.builder.get_object(non_localhost).show()
                        widget.hide()


class DownloadsPreferencePage(GtkUIPreferencePage):
    def __init__(self, name, xml, widget):
        super(DownloadsPreferencePage, self).__init__(name, xml, widget)
        self.core_widgets = {
            "download_path_button": ("current_folder", "download_location", "entry_download_path"),
            "entry_download_path": ("text", "download_location", ""),
            "chk_move_completed": ("active", "move_completed", ""),
            "move_completed_path_button": ("current_folder", "move_completed_path", "entry_move_completed_path"),
            "entry_move_completed_path": ("text", "move_completed_path", ""),
            "chk_autoadd": ("active", "autoadd_enable", ""),
            "folder_autoadd": ("current_folder", "autoadd_location", "entry_autoadd"),
            "entry_autoadd": ("text", "autoadd_location", ""),
            "chk_copy_torrent_file": ("active", "copy_torrent_file", ""),
            "torrent_files_button": ("current_folder", "torrentfiles_location", "entry_torrents_path"),
            "entry_torrents_path": ("text", "torrentfiles_location", ""),
            "chk_del_copy_torrent_file": ("active", "del_copy_torrent_file", ""),
            "radio_compact_allocation": ("active", "compact_allocation", ""),
            "radio_full_allocation": ("active", "compact_allocation", ""),
            "chk_prioritize_first_last_pieces": ("active", "prioritize_first_last_pieces", ""),
            "chk_add_paused": ("active", "add_paused", "")
        }

class NetworkPreferencePage(PreferencePage):
    pass

class BandwidthPreferencePage(PreferencePage):
    def __init__(self):
        self.name = _("Bandwidth")
        #xml = pkg_resources.resource_filename("deluge.ui.gtkui",
        #                                "glade/preferences/bandwidth.glade")
        xml = "glade/preferences/bandwidth.glade"
        self.set_widget_from_file(xml, "bandwidth_prefs_page")

    def update(self):
        pass

class InterfacePreferencePage(PreferencePage):
    def __init__(self):
        self.name = _("Interface")
        #xml = pkg_resources.resource_filename("deluge.ui.gtkui",
        #                                "glade/preferences/interface.glade")
        xml = "glade/preferences/interface.glade"
        self.set_widget_from_file(xml, "interface_prefs_page")

    def update(self):
        pass

class OtherPreferencePage(PreferencePage):
    def __init__(self):
        self.name = _("Other")
        #xml = pkg_resources.resource_filename("deluge.ui.gtkui",
        #                                "glade/preferences/other.glade")
        xml = "glade/preferences/other.glade"
        self.set_widget_from_file(xml, "other_prefs_page")

    def update(self):
        pass

class DaemonPreferencePage(PreferencePage):
    def __init__(self):
        self.name = _("Daemon")
        #xml = pkg_resources.resource_filename("deluge.ui.gtkui",
        #                                "glade/preferences/daemon.glade")
        xml = "glade/preferences/daemon.glade"
        self.set_widget_from_file(xml, "daemon_prefs_page")

    def update(self):
        pass

class QueuePreferencePage(PreferencePage):
    def __init__(self):
        self.name = _("Queue")
        #xml = pkg_resources.resource_filename("deluge.ui.gtkui",
        #                                "glade/preferences/queue.glade")
        xml = "glade/preferences/queue.glade"
        self.set_widget_from_file(xml, "queue_prefs_page")

    def update(self):
        pass

class ProxyPreferencePage(PreferencePage):
    def __init__(self):
        self.name = _("Proxy")
        #xml = pkg_resources.resource_filename("deluge.ui.gtkui",
        #                                "glade/preferences/proxy.glade")
        xml = "glade/preferences/proxy.glade"
        self.set_widget_from_file(xml, "proxy_prefs_page")

    def update(self):
        pass

class CachePreferencePage(PreferencePage):
    def __init__(self):
        self.name = _("Cache")
        #xml = pkg_resources.resource_filename("deluge.ui.gtkui",
        #                                "glade/preferences/cache.glade")
        xml = "glade/preferences/cache.glade"
        self.set_widget_from_file(xml, "cache_prefs_page")

    def update(self):
        pass

class PluginsPreferencePage(PreferencePage):
    def __init__(self):
        self.name = _("Plugins")
        #xml = pkg_resources.resource_filename("deluge.ui.gtkui",
        #                                "glade/preferences/plugins.glade")
        xml = "glade/preferences/plugins.glade"
        self.set_widget_from_file(xml, "plugins_prefs_page")

    def update(self):
        pass

class Preferences(component.Component):
    def __init__(self):
        component.Component.__init__(self, "Preferences")

        self.dialog = gtk.Dialog(_("Preferences"))
        self.dialog.set_default_size(560, 530)
        #self.dialog.set_transient_for(component.get("MainWindow").window)

        # Set the buttons for the dialog
        self.button_cancel = self.dialog.add_button(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL)
        self.button_apply = self.dialog.add_button(gtk.STOCK_APPLY, gtk.RESPONSE_APPLY)
        self.button_ok = self.dialog.add_button(gtk.STOCK_OK, gtk.RESPONSE_OK)

        # Setup the content area
        self.dialog_hpaned = gtk.HPaned()
        vp = gtk.Viewport()
        self.listview = gtk.TreeView()
        vp.add(self.listview)
        self.dialog_hpaned.pack1(vp)

        self.notebook = gtk.Notebook()
        self.notebook.set_show_tabs(False)
        self.dialog_hpaned.pack2(self.notebook)
        self.dialog.get_content_area().pack_start(self.dialog_hpaned)

        # Setup the listview for the preference categories
        self.liststore = gtk.ListStore(str)
        render = gtk.CellRendererText()
        column = gtk.TreeViewColumn(_("Categories"), render, text=0)
        self.listview.append_column(column)
        self.listview.set_model(self.liststore)

        self.listview.get_selection().connect("changed", self._on_selection_changed)

        # Store the PreferencePages currently in the Preferences dialog
        self.pages = {}

        self.add_page(DownloadsPreferencePage(_("Downloads"), "glade/preferences/downloads.glade", "downloads_prefs_page"))


    def add_page(self, page):
        """
        Add a Preference page.

        :param page: the preference page to add
        :type page: PreferencePage

        """
        if not isinstance(page, PreferencePage):
            raise ValueError("Must be a PreferencePage!")

        # Add this page to the notebook
        index = self.notebook.append_page(page.widget)
        self.liststore.append([page.name])
        self.pages[index] = page
        return page.name

    def remove_page(self, name):
        """
        Removes a Preference page.

        :param name: the name of the preference page
        :type name: string
        """
        index = self.get_page_index(name)
        if index:
            del self.liststore[index]
            self.notebook.remove_page(index)

    def get_page_index(self, page):
        """
        Returns the index for the page.

        :param page: the name of the preference page
        :type page: string

        :returns: the index
        :rtype: int

        """
        for index, row in enumerate(self.liststore):
            if page == row[0]:
                return index

        return None

        # We need to re-adjust the index values for the remaining pages
        for i, (index, name) in enumerate(self.liststore):
            self.liststore[i][0] = i

    def show(self, page=None):
        """
        Shows the Preferences dialog.

        :param page: the name of the page to show initially
        :type page: string

        """
        if page:
            index = self.get_page_index(page)
            if index:
                self.pages[index].show()
                self.listview.get_selection().select_path(index)
        else:
            self.listview.get_selection().select_path(0)

        self.dialog.show_all()

    def _on_selection_changed(self, treeselection):
        """
        This is called when the preference page changes or when it's initially
        showed.  We must call the page's update() method prior to showing the
        page.
        """
        (model, row) = treeselection.get_selected()
        index = self.get_page_index(model[row][0])
        if index is None:
            return

        def on_page_show(result):
            self.notebook.set_current_page(index)
        try:
            maybeDeferred(self.pages[index].show).addCallback(on_page_show)
        except Exception, e:
            dialogs.ErrorDialog(
                _("Error with preference page"),
                _("Could not show preference page correctly."),
                self.dialog,
                traceback=True).run()

if __name__ == "__main__":
    p = Preferences()
    d = DownloadsPreferencePage(_("Downloads"), "glade/preferences/downloads.glade", "downloads_prefs_page")
    p.add_page(d)
    #d2 = NetworkPreferencePage(_("Network"), "glade/preferences/network.glade", "network_prefs_page")
    #p.add_page(d2)
    ##d3 = BandwidthPreferencePage()
    ##p.add_page(d3)
    ##d4 = InterfacePreferencePage()
    ##p.add_page(d4)
    ##d5 = OtherPreferencePage()
    ##p.add_page(d5)
    ##d6 = DaemonPreferencePage()
    ##p.add_page(d6)
    ##d7 = QueuePreferencePage()
    ##p.add_page(d7)
    ##d8 = ProxyPreferencePage()
    ##p.add_page(d8)
    ##d9 = CachePreferencePage()
    ##p.add_page(d9)
    ##d10 = PluginsPreferencePage()
    ##p.add_page(d10)
    p.show()
    gtk.main()

