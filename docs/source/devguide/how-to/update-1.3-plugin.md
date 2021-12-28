# How to update a Deluge 1.3 plugin for 2.0

With the new code in Deluge 2.0 there are changes that require authors of
existing plugins to update their plugins to work on Deluge 2.0.

The main changes are with Python 3 support and the new GTK3 user interface with
the dropping of GTK2. However it is still possible for a 1.3 plugin to be made
compatible with 2.0 and this guide aims to helps with that process.

## Python

### Python version matching

Ensure your code is Python >=3.6 compatible.

In `1.3-stable` the plugins that were built with a specific version of Python
would only be loaded if the system Python also matched.

This has change in Deluge 2.0 and it will load any Python version of plugin
eggs so compatibility is essential for end-users not to encounter issues.

## GTK 3 addition

In order to support both Deluge 1.3 and 2.0 all existing plugin GTK UI files
must be copied and then converted to contain only GTK3 code with the old files
still using PyGTK e.g.:

    cp gtkui.py gtk3ui.py

### Convert from libglade to GtkBuilder

With PyGTK there were two library options for creating the user interface from
XML files by default Deluge plugins used libglade but that has been deprecated
and removed in GTK3. So the libglade `.glade` files will need converted to
GtkBuilder `.ui` files and the Python code updated.

See the official [Migrating to GtkBuilder][migrate-gtkbuilder] document for more details.

#### GtkBuilder conversion script

Install the `gtk-builder-convert` converter on Ubuntu with:

    sudo apt install libgtk2.0-dev

To convert your GTK run it like so:

    gtk-builder-convert data/config.glade data/config.ui

#### Glade UI designer for GTK2

The above conversion can also be done in Glade UI designer (version <=3.8).

In the preferences select `GtkBuilder` as the project file format. Ensure
that the minimum Gtk version is set to 2.24 and fix any deprecated widgets.

The updated file should be saved with file extension `.ui`.

#### Python code changes

The code needs to replace `gtk.glade` references with `gtk.Builder` and the
first step is updating how the files are loaded:

```diff
- glade = gtk.glade.XML(get_resource("config.glade"))
+ builder = Gtk.Builder.new_from_file(get_resource("config.ui"))
```

Replace signals method:

```diff
- glade.signal_autoconnect(self)
+ builder.connect_signals(self)
```

Replace `get_widget` with `get_object`:

```diff
- glade.get_widget
+ builder.get_object
```

Check for any remaining `glade` methods and replace with the `builder` equivalents.

### Migrate XML files to GTK3

If you open and save the file it will update with the new requirement header:

    <!-- Generated with glade 3.18.3 -->
    <interface>
      <requires lib="gtk+" version="3.10"/>

You can fix deprecated widgets but keep the minimum GTK version to <= 3.10 for
desktop compatibility.

An example of migrating a Deluge plugin to GtkBuilder: [AutoAdd GtkBuilder]

### Gtk import rename

Move from PyGTK to GTK3 using Python bindings.

<https://pygobject.readthedocs.io/en/latest/guide/porting.html>

    wget https://gitlab.gnome.org/GNOME/pygobject/raw/master/tools/pygi-convert.sh
    cp gtkui.py gtk3ui.py
    sh pygi-convert.sh gtk3ui.py

```diff
-import gtk
+from gi.repository import Gtk
```

```diff
- self.builder = gtk.Builder()
+ self.builder = Gtk.Builder()
```

### Deluge GTK3

#### Imports

Imports will need renamed from `deluge.ui.gtkui` to `deluge.ui.gtk3`.

There is also a new PluginBase for Gtk3 UI:

```diff
-from deluge.plugins.pluginbase import GtkPluginBase
+from deluge.plugins.pluginbase import Gtk3PluginBase
-class GtkUI(GtkPluginBase):
+class Gtk3UI(Gtk3PluginBase):
```

#### Entry points

To enable the GTK3 UI to find the plugin the entry points requires updating too.

In the plugin `__init__.py` file add a new `Gtk3UIPlugin` class:

```
class Gtk3UIPlugin(PluginInitBase):
    def __init__(self, plugin_name):
        from .gtk3ui import Gtk3UI as _plugin_cls
        self._plugin_cls = _plugin_cls
        super(Gtk3UIPlugin, self).__init__(plugin_name)
```

A new entry for GTK3 UI can then be added to `setup.py`:

```diff
     [deluge.plugin.gtkui]
     %s = %s:GtkUIPlugin
+    [deluge.plugin.gtk3ui]
+    %s = deluge_%s:Gtk3UIPlugin
     [deluge.plugin.webui]
     %s = %s:WebUIPlugin
-    """ % ((__plugin_name__, __plugin_name__.lower())*3)
+    """ % ((__plugin_name__, __plugin_name__.lower())*4)
```

[migrate-gtkbuilder]: https://developer.gnome.org/gtk2/stable/gtk-migrating-GtkBuilder.html
[autoadd gtkbuilder]: https://git.deluge-torrent.org/deluge/commit/?h=develop&id=510a8b50b213cab804d693a5f122f9c0d9dd1fb3
