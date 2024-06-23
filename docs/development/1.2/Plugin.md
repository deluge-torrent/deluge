
## Introduction

When considering to write a plugin for Deluge, one must first understand the basic design of Deluge.  Deluge is split in two, the core and the user-interface of which there could be many.  When writing your plugin you will be writing a Core portion and, perhaps, many different UI portions.  This may sound complicated and at times it can be, but once you get the hang of it, it becomes second-hand.

### Skill Checklist

This is a list of recommended skills or knowledge that you may need to successfully write a plugin.  This is by no means required, but can serve as a starting point if you're not sure what you need to know.  It may also be a good idea to read [How To Write a Client](http://dev.deluge-torrent.org/wiki/Development/UiClient1.2) first, to give you some idea of how a UI would interact with the Core.

* Python
* Twisted, specifically Deferreds
* GTK and possibly Glade
* Javascript for the WebUI portions

### Designing Your Plugin

Deluge has the ability to function in a headless environment with only the daemon (Core) portion running.  Various user-interfaces will connect from time to time and view or modify the session, but may not be connected all the time, so the "smarts" of your plugin should reside in the core.  You should also be aware that multiple UIs may be connected at the same time and they will need to behave correctly in terms of your plugin.  Typically, the best place to start writing your plugin is in the Core portion since it will contain most of the plugin logic, with the UI portions typically responsible for displaying and modifying plugin configuration or providing the user with status updates.

Conceptually you'll want to view your plugin as a collection of separate programs with your UI programs interfacing with your Core program through an RPC interface.  They do not share the same space in memory and may in fact be run on different computers, so information from the Core will need to be accessible to the clients through it's RPC exported functions -- and you can't send any object over this interface, only the basic types.

## Getting Started

The easiest way to get started is to use the [create_plugin.py](http://git.deluge-torrent.org/deluge/plain/deluge/scripts/create_plugin.py?h=1.3-stable) script in the appropriate branch in our [GitRepo](/gitrepo).  Alternatively, you can use other plugins as a template if you prefer.

Running the script:

```
$ python create_plugin.py --name MyPlugin --basepath . --author-name "Your Name" --author-email "yourname@example.com"
```

This should create a directory called `myplugin` under which should be a collection of directories and files which will form the base of your plugin.

The file structure should look like this (perhaps a bit more since it does a build right away):

```
myplugin/
|-- create_dev_link.sh
|-- myplugin
|   |-- __init__.py
|   |-- common.py
|   |-- core.py
|   |-- data
|   |   `-- config.glade
|   |-- gtkui.py
|   |-- template
|   |   `-- default.html
|   `-- webui.py
`-- setup.py
```

### Modifying Metadata

You may want to change or add some stuff to your plugin's metadata, such as the description or perhaps a URL for your project.  To do this, navigate to your `myplugin` directory and open up the `setup.py` file.  You will see a few different properties and modifying them should be self-explanatory, but you should refrain from changing the plugin name.

### Building The Plugin

Whenever you want to test out your plugin in Deluge, you will need to build it into an egg.

First off, navigate to your `myplugin` base directory, you should see a `setup.py` file in there.  Next, run the following command:

```
$ python setup.py bdist_egg
```

It's as simple as that.  You can also use this method to create an egg for distribution to other Deluge users.  The egg will be located in the `dist` directory.

## Core Plugin

### Introduction

We'll start off by writing the Core portion of our plugin.  In this example, we'll do some pretty trivial things to demonstrate some of the ideas and components associated with the plugin development process.  We'll look at configuration, exporting rpc functions, interacting with Core components and timers.

### Hello Wo...UI!

Let's start with a look at what our `create_plugin.py` script created for us in the `core.py` file.

```python

from deluge.log import LOG as log
from deluge.plugins.pluginbase import CorePluginBase
import deluge.component as component
import deluge.configmanager
from deluge.core.rpcserver import export

DEFAULT_PREFS = {
    "test":"NiNiNi"
}

class Core(CorePluginBase):
    def enable(self):
        self.config = deluge.configmanager.ConfigManager("myplugin.conf", DEFAULT_PREFS)

    def disable(self):
        pass

    def update(self):
        pass

    @export
    def set_config(self, config):
        "sets the config dictionary"
        for key in config.keys():
            self.config[key] = config[key]
        self.config.save()

    @export
    def get_config(self):
        "returns the config dictionary"
        return self.config.config
```

#### Imports

There are a number of imports at the top of this file and you may not end up using all of them.  I will describe what they are for.

* log - This is the Deluge logging object.  It can be handy for logging debug information or anything else you want printed to the log.  It has a few methods: log.debug("Message"), log.error("Message"), log.info("Message"), etc..  You can see the rest defined in the python logging module documentation.
* CorePluginBase - This is the base class we use for our Core plugin.
* component - This provides access to the component registry where you can reference any of the Deluge components for use in your plugin.
* configmanager - This allows access to the Deluge ConfigManager which is how you will access config files.
* export - This is a decorator function we use to *export* RPC methods.

#### Special Methods

You may notice that we have a few methods at the top of this class: `enable()`, `disable()`, `update()`.  These methods are overloaded from the base class and are called at different times.
* enable() - This method is called when the plugin is enabled, either by the user or when the program starts.
* disable() - This method is called when the plugin is disabled, either by the user or by exiting the program.
* update() - This method is called every second while the plugin is enabled.

You don't need to necessarily *do* anything in these methods, but you should at least define them and put a `pass` statement in.


#### Configuration

We'll get started by examining what is already going on in this plugin template and that is a basic setup to handle configuration setting and getting.

The first thing that is done, is creating the Config object when the plugin is enabled.

```python
self.config = deluge.configmanager.ConfigManager("myplugin.conf", DEFAULT_PREFS)
```

We see here that we're using Deluge's ConfigManager to handle loading our config with some default preferences.  All you really need to know is that this `config` object will act much like a dictionary object, but has some special methods like `save()` for writing the config to disk.  You don't need to necessarily call `save()` yourself, as the config object will handle this on it's own when the config values change.

You can read here: http://deluge-torrent.org/docs/current/modules/config.html for more information on the Config class.

```python

    @export
    def set_config(self, config):
        "sets the config dictionary"
        for key in config.keys():
            self.config[key] = config[key]
        self.config.save()

    @export
    def get_config(self):
        "returns the config dictionary"
        return self.config.config
```

Whoa, what's this?  It's our first two RPC exported methods of course!  You may be asking yourself, "What does that mean?", it means that the UI portions of our plugins will be able to call these methods over RPC.  This is the primary method for your plugin portions to communicate.

You'll notice that we use a decorator function (@export) to mark methods as being exportable, this makes it very easy to export functions.

To get back to what we're looking at, you'll see that `set_config()` takes an argument `config` and in this case it is a dictionary object.  The UI portion will be *sending* this dictionary to the Core portion to update it's Config object.  This is important because many config options you'll want to have available for the Core to use -- you don't want to be saving config options on the UI side that the Core portion needs because they may not be on the same computer and cannot access the same config file.

The `get_config()` method will simply return a dict object representing all the key/value pairs in our Config object back to the requestor.

A example of how calling these methods would look like from the UI perspective:

```python

def on_get_config(result):
    result["test"] = "i want to change this value"
    client.myplugin.set_config(result)

client.myplugin.get_config().addCallback(on_get_config)
```

Don't worry if you don't quite understand this example, we'll get to that when we start working on our UI portions of the plugin.

#### Functionality

Now that we have configuration covered, it's time to start expanding our plugin so that it does something useful.  In this tutorial, we will have our plugin keep track of our overall downloaded and uploaded byte totals and make this information available to the UI portions of the plugin.  We will also be using the configuration system we just examined to save the totals during restarts and shutdowns of the daemon so that our values will remain persistent between sessions.

First off, since we're going to be storing values we want to be persistent, let's add these to our config dictionary.

```python

DEFAULT_PREFS = {
    "total_download": 0,
    "total_upload": 0
}
```

Great!  Now we have a place to store our data that will be persistent between sessions.

Let's modify our `enable()` method to initialize some object members to the values contained in the config file.

```python

    def enable(self):
        self.config = deluge.configmanager.ConfigManager("myplugin.conf", DEFAULT_PREFS)
        self.total_download = self.config["total_download"]
        self.total_upload = self.config["total_upload"]
```

Now, every time the plugin is enabled, it will initialize these member variables to what was saved in the config file.  This means that we need to make sure we're saving this data when then plugin is disabled or shutdown!

```python

    def disable(self):
        self.config["total_upload"] = self.total_upload
        self.config["total_download"] = self.total_download
```

Ok, now our stats should be persistent and we can now move on to updating our `total_upload` and `total_download` member variables based on the session status from the Core.

We'll want to poll the core every few seconds to get the latest byte count.  What we'll do is setup a timer function to get the latest data and update our member variables.

Let's start by creating the method that will be called by the timer.

```python

    def update_stats(self):
        status = component.get("Core").get_session_status(["total_download", "total_upload"])
        self.total_upload = self.config["total_upload"] + status["total_upload"]
        self.total_download = self.config["total_download"] + status["total_download"]
```

The first thing you'll notice about this method is that it's using the `component` module to access the Core object.  You can view the documentation for the Core object here: http://deluge-torrent.org/docs/current/modules/core/core.html

You'll see that we're updating our member variables `total_upload` and `total_download` with the values in our config dictionary plus the session byte count.  This will give us a total download/upload count over all our sessions.

At this point the function isn't doing anything because it isn't called anywhere! So it's time to add our `LoopingCall` to take care of this for us.

We need to import the `LoopingCall` class first.  Since we use Twisted for our mainloop, we import this class from there.  You will want to put this import with the rest at the top of the file.

```python

from twisted.internet.task import LoopingCall
```

Now, we want to setup and start the `LoopingCall` when the plugin is enabled, so lets modify `enable()` again.

```python

    def enable(self):
        self.config = deluge.configmanager.ConfigManager("myplugin.conf", DEFAULT_PREFS)
        self.total_download = self.config["total_download"]
        self.total_upload = self.config["total_upload"]

        self.update_status_timer = LoopingCall(self.update_stats)
        self.update_status_timer.start(2)

    def disable(self):
        self.update_status_timer.stop()

        self.config["total_upload"] = self.total_upload
        self.config["total_download"] = self.total_download
```

The syntax for the `LoopingCall` is simple, it just takes function you wish to call in the timer.  Next, we simply `start()` the timer with a value in seconds that determines it's frequency, in this case the function will be called every 2 seconds.  In our `disable()` method we `stop()` the timer.

