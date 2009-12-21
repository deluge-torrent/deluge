import gtk
import gobject

_ = lambda x: x

class Client(object):
    def is_localhost(self):
        return True
client = Client()

class MainWindow(object):
    def __init__(self):
        # {(PreferenceItem, widget_number): (widget, method), ...}
        self.widgets = {}

        self.renderers = {
            FolderSelect: self.render_folder_select,
        }

        self.window = gtk.Window()
        self.window.set_default_size(510, 530)
        self.window.set_border_width(5)
        vbox = gtk.VBox()
        hpaned = gtk.HPaned()
        button_box = gtk.HButtonBox()
        button_box.set_layout(gtk.BUTTONBOX_END)
        self.button_ok = gtk.Button(stock=gtk.STOCK_OK)
        self.button_apply = gtk.Button(stock=gtk.STOCK_APPLY)
        self.button_cancel = gtk.Button(stock=gtk.STOCK_CANCEL)
        button_box.pack_start(self.button_cancel)
        button_box.pack_start(self.button_apply)
        button_box.pack_start(self.button_ok)

        vbox.pack_start(hpaned, True)
        vbox.pack_start(button_box, False)

        self.cat_listview = gtk.TreeView()
        sw = gtk.ScrolledWindow()
        sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        sw.add_with_viewport(self.cat_listview)
        hpaned.pack1(sw)
        self.notebook = gtk.Notebook()
        self.notebook.set_show_tabs(False)
        hpaned.pack2(self.notebook)

        # Setup the liststore for the categories (tab pages)
        self.cat_liststore = gtk.ListStore(int, str)
        self.cat_listview.set_model(self.cat_liststore)
        render = gtk.CellRendererText()
        column = gtk.TreeViewColumn("Categories", render, text=1)
        self.cat_listview.append_column(column)


        # Add the default categories
#        i = 0
#        for category in [_("Downloads"), _("Network"), _("Bandwidth"), _("Interface"),
#            _("Other"), _("Daemon"), _("Queue"), _("Proxy"), _("Notification"),
#            _("Cache"), _("Plugins")]:
#            self.cat_liststore.append([i, category])
#            i += 1

        self.window.add(vbox)
        self.window.show_all()

    def add_page(self, page):
        """Add a another page to the notebook"""
        # Create a header and scrolled window for the preferences tab
        vbox = gtk.VBox()
        scrolled = gtk.ScrolledWindow()
        viewport = gtk.Viewport()
        viewport.set_shadow_type(gtk.SHADOW_NONE)
        viewport.add(vbox)
        scrolled.add(viewport)
        scrolled.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)

        # Create the top header
        label = gtk.Label()
        label.set_use_markup(True)
        label.set_markup("<b><i><big>" + page.name + "</big></i></b>")
        label.set_alignment(0.00, 0.50)
        label.set_padding(10, 10)
        vbox.pack_start(label, False, True, 0)
        vbox.pack_start(gtk.HSeparator(), False, True, 0)

        # All the page widgets will be added to the alignment widget via the pvbox
        align = gtk.Alignment()
        align.set_padding(5, 0, 0, 0)
        pvbox = gtk.VBox()
        align.add(pvbox)
        # Add in the page widgets here..
        for section in page.items:
            # Setup section frame
            frame = gtk.Frame("<b>"+section+"</b>")
            frame.get_label_widget().set_use_markup(True)
            frame.set_shadow_type(gtk.SHADOW_NONE)
            pvbox.pack_start(frame)
            frame_align = gtk.Alignment()
            frame_align.set_padding(2, 2, 12, 0)
            frame.add(frame_align)
            frame_vbox = gtk.VBox()
            frame_align.add(frame_vbox)

            # Now we add the section items to the vbox
            for item in page.items[section]:
                frame_vbox.pack_start(self.renderers[type(item)](item))

        print self.widgets
        # Add them to the vbox which is in the scrolled window
        vbox.pack_start(align, True, True, 0)

        # Show all the widgets
        scrolled.show_all()

        # Add this page to the notebook
        index = self.notebook.append_page(scrolled)
        self.cat_liststore.append([index, page.name])

    def render_folder_select(self, item):
        """
        Returns a folder select widget.
        """
        hbox = gtk.HBox()
        hbox.set_spacing(5)
        hbox.set_homogeneous(True)
        if item.toggleable:
            label = gtk.CheckButton(item.label)
            self.widgets[(item, 1)] = (label, "get_active")
        else:
            label = gtk.Label(item.label)
            label.set_alignment(0.0, 0.5)
        if client.is_localhost():
            entry = gtk.FileChooserButton(_("Select a folder"))
            entry.set_action(gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER)
        else:
            entry = gtk.Entry()

        # Add this widget to the widgets dict so
        self.widgets[(item, 0)] = (entry, "get_text")

        hbox.pack_start(label, False)
        hbox.pack_end(entry)
        return hbox

class PreferenceItem(object):
    pass

class FolderSelect(PreferenceItem):
    def __init__(self, config, label, toggleable=False):
        """
        :param config: the config dict and key to use
        :type config: a tuple (dict, key), eg, ("ui", "key") or ("core", "key1", "key2")
        :param label: the text to display
        :type label: string
        :param toggleable: if a checkbox is needed. this param uses config key2.
        :type toggleable: bool

        """
        self.config = config
        self.label = label
        self.toggleable = toggleable

class RadioButton(PreferenceItem):
    def __init__(self, config, label, group=0):
        """
        :param config: the config dict and key to use
        :type config: a tuple (dict, key), eg, ("ui", "key") or ("core", "key")
        :param label: the text to display
        :type label: string
        :param group: the group number to assign this radio button to
        :type group: int

        """
        self.config = config
        self.label = label
        self.group = group

class CheckButton(PreferenceItem):
    def __init__(self, config, label):
        """
        :param config: the config dict and key to use
        :type config: a tuple (dict, key), eg, ("ui", "key") or ("core", "key")
        :param label: the text to display
        :type label: string

        """
        self.config = config
        self.label = label

class PreferencePage(object):
    def __init__(self, name):
        self.name = name
        self.section = "General"
        self.items = {}

    def set_section(self, section):
        self.section = section
        if self.section not in self.items:
            self.items[self.section] = []

    def add(self, item):
        """
        Adds a PreferenceItem to the page.

        :param item: the item to add
        :type item: PreferenceItem

        """
        if not isinstance(item, PreferenceItem):
            raise ValueError("item is not a PreferenceItem!")

        self.items[self.section].append(item)


p = PreferencePage(_("Downloads"))
p.set_section(_("Folders"))
p.add(FolderSelect(("core", "download_location"), _("Download to:")))
p.add(FolderSelect(("core", "move_completed_path", "move_completed"), _("Move completed to:"), True))
p.add(FolderSelect(("core", "torrentfiles_location", "copy_torrent_file"), _("Copy of .torrent files to:"), True))
p.add(FolderSelect(("core", "autoadd_location", "autoadd_enable"), _("Auto add .torrents from:"), True))
m = MainWindow()
m.add_page(p)
gtk.main()
