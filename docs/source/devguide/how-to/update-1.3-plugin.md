# How to update a Deluge 1.3 plugin for 2.0

With the new code in Deluge 2.0 there are changes that require authors of
existing plugins to update their plugins to work on Deluge 2.0.

The main changes are with Python 3 support and the new GTK3 user interface with
the dropping of GTK2. However it is still possible for a 1.3 plugin to be made
compatible with 2.0 and this guide aims to helps with that process.

Note that the Deluge 2.0 plugins now use namespace packaging which is not
compatible with Deluge 1.3.

## Python

### Python version matching

Ensure your code is both Python 2.7 and Python >=3.5 compatible.

In `1.3-stable` the plugins that were built with a specfific version of Python
could on be loaded if the system Python also matched.

This has change in Deluge 2.0 and it will load any Python version of plugin
eggs so compatibility is essential for end-users not to encounter issues.

### Six

Use [six] to assist with compatibility.

[six]: https://pythonhosted.org/six/

### Unicode literals

Add this to files to ensure strings and bytes separatation so there are no
surprises when running on Python 3.

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

https://developer.gnome.org/gtk2/stable/gtk-migrating-GtkBuilder.html

#### gtk-builder-convert

Install the `gtk-builder-convert` converter on Ubuntu with:

    sudo apt install libgtk2.0-dev

To convert your GTK run it like so:

    gtk-builder-convert data/config.glade data/config.ui

#### Glade UI designer for GTK2

The above conversion can be done in Glade UI designer (version <=3.8), ensuring
that the minimum Gtk version is set to 2.24 and any deprecated widgets are
fixed. The updated file should be saved with file extension `.ui`.

#### Python code changes

The code needs to replace `gtk.glade` references with `gtk.Builder` and the
first step is updating how the files are loaded:

```diff
- self.glade = gtk.glade.XML(get_resource("config.glade"))
+ self.builder = gtk.Builder()
+ self.builder.add_from_file(get_resource("config.ui"))
```

The next stage is to replace every occurange of these `glade` methods with
the `builder` equivalents:

    glade.signal_autoconnect -> builder.connect_signals
    glade.get_widget -> builder.get_object

### Migrate XML files to GTK3

If you open and save the file it will update with the new requirement header:

    <!-- Generated with glade 3.18.3 -->
    <interface>
      <requires lib="gtk+" version="3.0"/>

You can fix deprecated widgets but keep the minimum GTK version to <= 3.10 for
desktop compatiblity.

An example of migrating a Deluge plugin to GtkBuilder: [AutoAdd GtkBuilder]

### Gtk import rename

Move from PyGTK to GTK3 using Python bindings.

https://pygobject.readthedocs.io/en/latest/guide/porting.html

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

Imports will need updated from `deluge.ui.gtkui` to `deluge.ui.gtk3`.

### PluginBase

```diff
-from deluge.plugins.pluginbase import GtkPluginBase
+from deluge.plugins.pluginbase import Gtk3PluginBase
-class GtkUI(GtkPluginBase):
+class Gtk3UI(Gtk3PluginBase):
```

[autoadd gtkbuilder]: https://git.deluge-torrent.org/deluge/commit/?h=develop&id=510a8b50b213cab804d693a5f122f9c0d9dd1fb3
