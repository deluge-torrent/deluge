# Development/Plugins



## Intro
Plugins consist of a core part and ui parts for the various user-interfaces.

They are distributed using python eggs http://peak.telecommunity.com/DevCenter/PythonEggs

## Creating a new plugin
A script is available to create a new plugin here (may not work with older versions of deluge): http://dev.deluge-torrent.org/browser/trunk/deluge/scripts/create_plugin.py?format=raw

**Note**: You may need to install the *python-setuptools* package if you don't have it.

Go to an empty directory, and run:

```
python create_plugin.py --name MyPlugin2 --basepath . --author-name "Your Name" --author-email "yourname@example.com"
```

This will create a new directory <plugin-name> , contaning a basic plugin template.
And it will link it from ~/.config/deluge/plugins

Restart deluge and deluged.

## Distributing a plugin
Go to the plugin-name directory, and type

`python setup.py bdist_egg`

This will build an egg.

Rename the egg to <plugin-name>.egg and share it,

# Various random facts
* any "export_*" method in the core plugin is exposed as "plugin-name_*" in deluge.ui.client
* the deluge.ui.client api is available to core plugins as "from deluge.plugins.coreclient import client"

## Adding a status-field to core
* define a callback-function http://dev.deluge-torrent.org/browser/trunk/deluge/plugins/label/label/core.py?rev=3607#L356
* register that callback http://dev.deluge-torrent.org/browser/trunk/deluge/plugins/label/label/core.py?rev=3607#L74
* now the field is available in ui.client..get_torrent_status

## Adding a column to gtk-ui
* callback for cell : http://dev.deluge-torrent.org/browser/trunk/deluge/plugins/label/label/gtkui/__init__.py#L51
* register that callback  :  http://dev.deluge-torrent.org/browser/trunk/deluge/plugins/label/label/gtkui/__init__.py#L115

## alerts
* registering for a "torrent_finished" alert : http://forum.deluge-torrent.org/viewtopic.php?f=9&t=8155#p37775
* [Plugin Alerts](/development/plugins/alerts)

## signals
* [Plugin Signals](/development/plugins/signals)

# Examples
* [Plugin WebUI Examples](/development/plugins/webui/examples)


