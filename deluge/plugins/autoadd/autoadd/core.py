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
    """
    Emitted when a new command is added.
    """
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
        
        
        # A list of filenames
        self.invalid_torrents = []
        # Filename:Attempts
        self.attempts = {}
        # Loopingcall timers for each enabled watchdir
        self.update_timers = {}
        # If core autoadd folder is enabled, move it to the plugin
        if self.core_cfg.config.get('autoadd_enable'):
            # Disable core autoadd
            self.core_cfg['autoadd_enable'] = False
            # Check if core autoadd folder is already added in plugin
            for watchdir in self.watchdirs:
                if os.path.abspath(self.core_cfg['autoadd_location']) == watchdir['abspath']:
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
        pass

    def update(self):
        pass
        
    @export()
    def set_options(self, watchdir_id, options):
        """
        update the options for a watch folder
        """
        watchdir_id = str(watchdir_id)
        options = self._clean_unicode(options)
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
        
    def load_torrent(self, filename):
        try:
            log.debug("Attempting to open %s for add.", filename)
            _file = open(filename, "rb")
            filedump = _file.read()
            if not filedump:
                raise RuntimeError, "Torrent is 0 bytes!"
            _file.close()
        except IOError, e:
            log.warning("Unable to open %s: %s", filename, e)
            raise e

        # Get the info to see if any exceptions are raised
        info = lt.torrent_info(lt.bdecode(filedump))

        return filedump
        
    def update_watchdir(self, watchdir_id):
        watchdir_id = str(watchdir_id)
        watchdir = self.watchdirs[watchdir_id]
        if not watchdir['enabled']:
            # We shouldn't be updating because this watchdir is not enabled
            #disable the looping call
            self.update_timers[watchdir_id].stop()
            del self.update_timers[watchdir_id]
            return

        # Check the auto add folder for new torrents to add
        if not os.path.isdir(watchdir["abspath"]):
            log.warning("Invalid AutoAdd folder: %s", watchdir["abspath"])
            #disable the looping call
            watchdir['enabled'] = False
            self.update_timers[watchdir_id].stop()
            del self.update_timers[watchdir_id]
            return
        
        #Generate options dict for watchdir
        opts={}
        if watchdir.get('stop_at_ratio_toggle'):
            watchdir['stop_ratio_toggle'] = True
        for option, value in watchdir.iteritems():
            if OPTIONS_AVAILABLE.get(option):
                if watchdir.get(option+'_toggle', True):
                    opts[option] = value
        opts = self._clean_unicode(opts)
        for filename in os.listdir(watchdir["abspath"]):
            if filename.split(".")[-1] == "torrent":
                try:
                    filepath = os.path.join(watchdir["abspath"], filename)
                except UnicodeDecodeError, e:
                    log.error("Unable to auto add torrent due to inproper filename encoding: %s", e)
                    continue
                try:
                    filedump = self.load_torrent(filepath)
                except (RuntimeError, Exception), e:
                    # If the torrent is invalid, we keep track of it so that we
                    # can try again on the next pass.  This is because some
                    # torrents may not be fully saved during the pass.
                    log.debug("Torrent is invalid: %s", e)
                    if filename in self.invalid_torrents:
                        self.attempts[filename] += 1
                        if self.attempts[filename] >= MAX_NUM_ATTEMPTS:
                            os.rename(filepath, filepath + ".invalid")
                            del self.attempts[filename]
                            self.invalid_torrents.remove(filename)
                    else:
                        self.invalid_torrents.append(filename)
                        self.attempts[filename] = 1
                    continue

                # The torrent looks good, so lets add it to the session
                torrent_id = component.get("TorrentManager").add(filedump=filedump, filename=filename, options=opts)
                if torrent_id:
                    if 'Label' in component.get("CorePluginManager").get_enabled_plugins():
                        if watchdir.get('label_toggle', True) and watchdir.get('label'):
                            label = component.get("CorePlugin.Label")
                            if not watchdir['label'] in label.get_labels():
                                label.add(watchdir['label'])
                            label.set_torrent(torrent_id, watchdir['label'])
                    if watchdir.get('queue_to_top_toggle'):
                        if watchdir.get('queue_to_top', True):
                            component.get("TorrentManager").queue_top(torrent_id)
                        else:
                            component.get("TorrentManager").queue_bottom(torrent_id)
                if watchdir.get('append_extension_toggle', False):
                    if not watchdir.get('append_extension'):
                        watchdir['append_extension'] = ".added"
                    os.rename(filepath, filepath + watchdir['append_extension'])
                else:
                    os.remove(filepath)
        
    @export
    def enable_watchdir(self, watchdir_id):
        watchdir_id = str(watchdir_id)
        self.watchdirs[watchdir_id]['enabled'] = True
        #Enable the looping call
        self.update_timers[watchdir_id] = LoopingCall(self.update_watchdir, watchdir_id)
        self.update_timers[watchdir_id].start(5)
        self.config.save()
        component.get("EventManager").emit(AutoaddOptionsChangedEvent())
        
    @export
    def disable_watchdir(self, watchdir_id):
        watchdir_id = str(watchdir_id)
        self.watchdirs[watchdir_id]['enabled'] = False
        #disable the looping call here
        self.update_timers[watchdir_id].stop()
        del self.update_timers[watchdir_id]
        self.config.save()
        component.get("EventManager").emit(AutoaddOptionsChangedEvent())

    @export
    def set_config(self, config):
        """sets the config dictionary"""
        for key in config.keys():
            self.config[key] = config[key]
        self.config.save()
        component.get("EventManager").emit(AutoaddOptionsChangedEvent())

    @export
    def get_config(self):
        """returns the config dictionary"""
        return self.config.config
        
    @export()
    def get_watchdirs(self):
        return self.watchdirs.keys()
    
    def _clean_unicode(self, options):
        opts = {}
        for key, value in options.iteritems():
            if isinstance(key, unicode):
                key = str(key)
            if isinstance(value, unicode):
                value = str(value)
            opts[key] = value
        return opts
        
    #Labels:
    @export()
    def add(self, options={}):
        """add a watchdir
        """
        options = self._clean_unicode(options)
        abswatchdir = os.path.abspath(options['path'])
        CheckInput(os.path.isdir(abswatchdir) , _("Path does not exist."))
        CheckInput(os.access(abswatchdir, os.R_OK|os.W_OK), "You must have read and write access to watch folder.")
        for watchdir_id, watchdir in self.watchdirs.iteritems():
            if watchdir['abspath'] == abswatchdir:
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
        """remove a label"""
        watchdir_id = str(watchdir_id)
        CheckInput(watchdir_id in self.watchdirs, "Unknown Watchdir: %s" % self.watchdirs)
        if self.watchdirs[watchdir_id]['enabled']:
            self.disable_watchdir(watchdir_id)
        del self.watchdirs[watchdir_id]
        self.config.save()
        component.get("EventManager").emit(AutoaddOptionsChangedEvent())
