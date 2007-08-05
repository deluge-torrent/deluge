plugin_name = _("Network Activity Graph")
plugin_author = "Alon Zakai, Zach Tibbitts"
plugin_version = "0.2"
plugin_description = _("Network Activity Graph plugin\n\nWritten by Kripkenstein")


def deluge_init(deluge_path):
    global path
    path = deluge_path

def enable(core, interface):
    global path
    return NetworkGraph(path, core, interface)

from NetworkGraph.tab_graph import GraphTabManager

class NetworkGraph:
    def __init__(self, path, core, interface):
        import gtk
        self.parent   = interface
        self.location = path
        self.manager = core
        scrolledWindow = gtk.ScrolledWindow()
        scrolledWindow.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        image  = gtk.Image()

        viewport = gtk.Viewport()
        viewport.add(image)
        scrolledWindow.add(viewport)

        image.show()
        viewport.show()
        self.topWidget = scrolledWindow

        self.parentNotebook = self.parent.notebook
#        print "Parent NOTEBOOK:", self.parentNotebook
        self.parentNotebook.append_page(self.topWidget, gtk.Label(_("Graph")))
#        print "My INDEX in parentNoteBook:", self.index
        self.bootupRuns = 3  # This ensures that we pass the resizing phase, with scrollbars, etc.
                                    # So the first time it is viewed, we are all ready
        scrolledWindow.show()
        import pango
        pangoContext = self.parent.window.get_pango_context()
        pangoLayout = pango.Layout(pangoContext)
        self.tab_graph = GraphTabManager(scrolledWindow, image, pangoLayout, self.manager)

    def unload(self): # Shutdown is called when the plugin is deactivated
        numPages = self.parentNotebook.get_n_pages()
        for page in range(numPages):
            if self.parentNotebook.get_nth_page(page) == self.topWidget:
                self.parentNotebook.remove_page(page)
                break

    def update(self):
        if (not self.parentNotebook.get_nth_page(self.parentNotebook.get_current_page()) == \
                 self.topWidget\
                 or not self.parent.update_interface)\
                 and not self.bootupRuns > 0:
            return
        self.bootupRuns = max(self.bootupRuns - 1, 0)
        self.tab_graph.update_graph_store()
        self.tab_graph.update_graph_view()
