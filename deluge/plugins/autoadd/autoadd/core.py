#
# core.py
#
# Copyright (C) 2009 GazpachoKing <chase.sterling@gmail.com>
#
# Basic plugin template created by:
# Copyright (C) 2008 Martijn Voncken <mvoncken@gmail.com>
# Copyright (C) 2007-2009 Andrew Resch <andrewresch@gmail.com>
# Copyright (C) 2009 Damien Churchill <damoxc@gmail.com>
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

from deluge._libtorrent import lt
import os
from deluge.common import is_magnet
from deluge.log import LOG as log
from deluge.plugins.pluginbase import CorePluginBase
import deluge.component as component
import deluge.configmanager
from deluge.core.rpcserver import export
from twisted.internet.task import LoopingCall, deferLater
from twisted.internet import reactor
from deluge.event import DelugeEvent

DEFAULT_PREFS = {
    "watchdirs":{},
    "next_id":1
}

OPTIONS_AVAILABLE = { #option: builtin
    "enabled":False,
    "path":False,
    "append_extension":False,
    "abspath":False,
    "download_location":True,
    "max_download_speed":True,
    "max_upload_speed":True,
    "max_connections":True,
    "max_upload_slots":True,
    "prioritize_first_last":True,
    "auto_managed":True,
    "stop_at_ratio":True,
    "stop_ratio":True,
    "remove_at_ratio":True,
    "move_completed":True,
    "move_completed_path":True,
    "label":False,
    "add_paused":True,
    "queue_to_top":False
}

MAX_NUM_ATTEMPTS = 10

class AutoaddOptionsChangedEvent(DelugeEvent):
    """Emitted when the options for the plugin are changed."""
    def __init__(self):
        pass

def CheckInput(cond, message):
    if not cond:
        raise Exception(message)

class Core(CorePluginBase):
    def enable(self):

        #reduce typing, assigning some values to self...
        self.config = deluge.configmanager.ConfigManager("autoadd.conf", DEFAULT_PREFS)
        self.watchdirs = self.config["watchdirs"]
        self.core_cfg = deluge.configmanager.ConfigManager("core.conf")

        # Dict of Filename:Attempts
        self.invalid_torrents = {}
        # Loopingcall timers for each enabled watchdir
        self.update_timers = {}
        # If core autoadd folder is enabled, move it to the plugin
        if self.core_cfg.config.get('autoadd_enable'):
            # Disable core autoadd
            self.core_cfg['autoadd_enable'] = False
            self.core_cfg.save()
            # Check if core autoadd folder is already added in plugin
            for watchdir in self.watchdirs.itervalues():
                if os.path.abspath(self.core_cfg['autoadd_location']) == watchdir['abspath']:
                    watchdir['enabled'] = True
                    break
            else:
                # didn't find core watchdir, add it
                self.add({'path':self.core_cfg['autoadd_location'], 'enabled':True})
        deferLater(reactor, 5, self.enable_looping)

    def enable_looping(self):
        #Enable all looping calls for enabled watchdirs here
        for watchdir_id, watchdir in self.watchdirs.iteritems():
            if watchdir['enabled']:
                self.enable_watchdir(watchdir_id)

    def disable(self):
        #disable all running looping calls
        for loopingcall in self.update_timers.itervalues():
            loopingcall.stop()
        self.config.save()

    def update(self):
        pass

    @export()
    def set_options(self, watchdir_id, options):
        """Update the options for a watch folder."""
        watchdir_id = str(watchdir_id)
        options = self._make_unicode(options)
        CheckInput(watchdir_id in self.watchdirs , _("Watch folder does not exist."))
        if options.has_key('path'):
            options['abspath'] = os.path.abspath(options['path'])
            CheckInput(os.path.isdir(options['abspath']), _("Path does not exist."))
            for w_id, w in self.watchdirs.iteritems():
                if options['abspath'] == w['abspath'] and watchdir_id != w_id:
                    raise Exception("Path is already being watched.")
        for key in options.keys():
            if not key in OPTIONS_AVAILABLE:
                if not key in [key2+'_toggle' for key2 in OPTIONS_AVAILABLE.iterkeys()]:
                    raise Exception("autoadd: Invalid options key:%s" % key)
        #disable the watch loop if it was active
        if watchdir_id in self.update_timers:
            self.disable_watchdir(watchdir_id)

        self.watchdirs[watchdir_id].update(options)
        #re-enable watch loop if appropriate
        if self.watchdirs[watchdir_id]['enabled']:
            self.enable_watchdir(watchdir_id)
        self.config.save()
        component.get("EventManager").emit(AutoaddOptionsChangedEvent())

    def load_torrent(self, filename, magnet):
        try:
            log.debug("Attempting to open %s for add.", filename)
            if magnet == False:
                _file = open(filename, "rb")
            elif magnet == True:
                _file = open(filename, "r")
            filedump = _file.read().strip()
            if not filedump:
                raise RuntimeError, "Torrent is 0 bytes!"
            _file.close()
        except IOError, e:
            log.warning("Unable to open %s: %s", filename, e)
            raise e

        # Get the info to see if any exceptions are raised
        if magnet == False:
            lt.torrent_info(lt.bdecode(filedump))

        return filedump

    def split_magnets(self, filename):
        log.debug("Attempting to open %s for splitting magnets.", filename)
        try:
            _file = open(filename, "r")
        except IOError, e:
            log.warning("Unable to open %s: %s", filename, e)
            raise e
        else:
            magnets = list(filter(len, _file.read().splitlines()))
            _file.close()
            if len(magnets) < 2:
                return
            path = filename.rsplit(os.sep, 1)[0]
            for magnet in magnets:
                if not is_magnet(magnet):
                    log.warning("Found line which is not a magnet: %s", magnet)
                    continue

                for part in magnet.split('&'):
                    if part.startswith("dn="):
                        name = part[3:].strip()
                        if name:
                            mname = os.sep.join([path, name + ".magnet"])
                            break
                else:
                    short_hash = magnet.split("btih:")[1][:8]
                    mname = '.'.join([os.path.splitext(filename)[0], short_hash, "magnet"])
                try:
                    _mfile = open(mname, "w")
                except IOError, e:
                    log.warning("Unable to open %s: %s", mname, e)
                else:
                    _mfile.write(magnet)
                    _mfile.close()
            return magnets

    def update_watchdir(self, watchdir_id):
        """Check the watch folder for new torrents to add."""
        watchdir_id = str(watchdir_id)
        watchdir = self.watchdirs[watchdir_id]
        if not watchdir['enabled']:
            # We shouldn't be updating because this watchdir is not enabled
            self.disable_watchdir(watchdir_id)
            return

        if not os.path.isdir(watchdir["abspath"]):
            log.warning("Invalid AutoAdd folder: %s", watchdir["abspath"])
            self.disable_watchdir(watchdir_id)
            return

        # Generate options dict for watchdir
        opts = {}
        if 'stop_at_ratio_toggle' in watchdir:
            watchdir['stop_ratio_toggle'] = watchdir['stop_at_ratio_toggle']
        # We default to True wher reading _toggle values, so a config
        # without them is valid, and applies all its settings.
        for option, value in watchdir.iteritems():
            if OPTIONS_AVAILABLE.get(option):
                if watchdir.get(option+'_toggle', True):
                    opts[option] = value

        # Check for .magnet files containing multiple magnet links and
        # create a new .magnet file for each of them.
        for filename in os.listdir(watchdir["abspath"]):
            try:
                filepath = os.path.join(watchdir["abspath"], filename)
            except UnicodeDecodeError, e:
                log.error("Unable to auto add torrent due to improper "
                          "filename encoding: %s", e)
                continue
            if os.path.isdir(filepath):
                # Skip directories
                continue
            elif os.path.splitext(filename)[1] == ".magnet" and \
                    self.split_magnets(filepath):
                os.remove(filepath)

        for filename in os.listdir(watchdir["abspath"]):
            try:
                filepath = os.path.join(watchdir["abspath"], filename)
            except UnicodeDecodeError, e:
                log.error("Unable to auto add torrent due to improper "
                          "filename encoding: %s", e)
                continue
            if os.path.isdir(filepath):
                # Skip directories
                continue
            else:
                ext = os.path.splitext(filename)[1].lower()
                if ext == ".torrent":
                    magnet = False
                elif ext == ".magnet":
                    magnet = True
                else:
                    log.debug("File checked for auto-loading is invalid: %s", filename)
                    continue
                try:
                    filedump = self.load_torrent(filepath, magnet)
                except (RuntimeError, Exception), e:
                    # If the torrent is invalid, we keep track of it so that we
                    # can try again on the next pass.  This is because some
                    # torrents may not be fully saved during the pass.
                    log.debug("Torrent is invalid: %s", e)
                    if filename in self.invalid_torrents:
                        self.invalid_torrents[filename] += 1
                        if self.invalid_torrents[filename] >= MAX_NUM_ATTEMPTS:
                            os.rename(filepath, filepath + ".invalid")
                            del self.invalid_torrents[filename]
                    else:
                        self.invalid_torrents[filename] = 1
                    continue

                # The torrent looks good, so lets add it to the session.
                if magnet == False:
                    torrent_id = component.get("TorrentManager").add(
                        filedump=filedump, filename=filename, options=opts)
                elif magnet == True:
                    torrent_id = component.get("TorrentManager").add(
                        magnet=filedump, options=opts)
                # If the torrent added successfully, set the extra options.
                if torrent_id:
                    if 'Label' in component.get("CorePluginManager").get_enabled_plugins():
                        if watchdir.get('label_toggle', True) and watchdir.get('label'):
                            label = component.get("CorePlugin.Label")
                            if not watchdir['label'] in label.get_labels():
                                label.add(watchdir['label'])
                            label.set_torrent(torrent_id, watchdir['label'])
                    if watchdir.get('queue_to_top_toggle', True) and 'queue_to_top' in watchdir:
                        if watchdir['queue_to_top']:
                            component.get("TorrentManager").queue_top(torrent_id)
                        else:
                            component.get("TorrentManager").queue_bottom(torrent_id)
                else:
                    # torrent handle is invalid and so is the magnet link
                    if magnet == True:
                        log.debug("invalid magnet link")
                        os.rename(filepath, filepath + ".invalid")
                        continue

                # Rename, copy or delete the torrent once added to deluge.
                if watchdir.get('append_extension_toggle'):
                    if not watchdir.get('append_extension'):
                        watchdir['append_extension'] = ".added"
                    os.rename(filepath, filepath + watchdir['append_extension'])
                else:
                    os.remove(filepath)

    def on_update_watchdir_error(self, failure, watchdir_id):
        """Disables any watch folders with unhandled exceptions."""
        self.disable_watchdir(watchdir_id)
        log.error("Disabling '%s', error during update: %s" % (self.watchdirs[watchdir_id]["path"], failure))

    @export
    def enable_watchdir(self, watchdir_id):
        watchdir_id = str(watchdir_id)
        # Enable the looping call
        if watchdir_id not in self.update_timers or not self.update_timers[watchdir_id].running:
            self.update_timers[watchdir_id] = LoopingCall(self.update_watchdir, watchdir_id)
            self.update_timers[watchdir_id].start(5).addErrback(self.on_update_watchdir_error, watchdir_id)
        # Update the config
        if not self.watchdirs[watchdir_id]['enabled']:
            self.watchdirs[watchdir_id]['enabled'] = True
            self.config.save()
            component.get("EventManager").emit(AutoaddOptionsChangedEvent())

    @export
    def disable_watchdir(self, watchdir_id):
        watchdir_id = str(watchdir_id)
        # Disable the looping call
        if watchdir_id in self.update_timers:
            if self.update_timers[watchdir_id].running:
                self.update_timers[watchdir_id].stop()
            del self.update_timers[watchdir_id]
        # Update the config
        if self.watchdirs[watchdir_id]['enabled']:
            self.watchdirs[watchdir_id]['enabled'] = False
            self.config.save()
            component.get("EventManager").emit(AutoaddOptionsChangedEvent())

    @export
    def set_config(self, config):
        """Sets the config dictionary."""
        config = self._make_unicode(config)
        for key in config.keys():
            self.config[key] = config[key]
        self.config.save()
        component.get("EventManager").emit(AutoaddOptionsChangedEvent())

    @export
    def get_config(self):
        """Returns the config dictionary."""
        return self.config.config

    @export()
    def get_watchdirs(self):
        return self.watchdirs.keys()

    def _make_unicode(self, options):
        opts = {}
        for key in options:
            if isinstance(options[key], str):
                options[key] = unicode(options[key], "utf8")
            opts[key] = options[key]
        return opts

    @export()
    def add(self, options={}):
        """Add a watch folder."""
        options = self._make_unicode(options)
        abswatchdir = os.path.abspath(options['path'])
        CheckInput(os.path.isdir(abswatchdir) , _("Path does not exist."))
        CheckInput(os.access(abswatchdir, os.R_OK|os.W_OK), "You must have read and write access to watch folder.")
        if abswatchdir in [wd['abspath'] for wd in self.watchdirs.itervalues()]:
            raise Exception("Path is already being watched.")
        options.setdefault('enabled', False)
        options['abspath'] = abswatchdir
        watchdir_id = self.config['next_id']
        self.watchdirs[str(watchdir_id)] = options
        if options.get('enabled'):
            self.enable_watchdir(watchdir_id)
        self.config['next_id'] = watchdir_id + 1
        self.config.save()
        component.get("EventManager").emit(AutoaddOptionsChangedEvent())
        return watchdir_id

    @export
    def remove(self, watchdir_id):
        """Remove a watch folder."""
        watchdir_id = str(watchdir_id)
        CheckInput(watchdir_id in self.watchdirs, "Unknown Watchdir: %s" % self.watchdirs)
        if self.watchdirs[watchdir_id]['enabled']:
            self.disable_watchdir(watchdir_id)
        del self.watchdirs[watchdir_id]
        self.config.save()
        component.get("EventManager").emit(AutoaddOptionsChangedEvent())
