#
# blocklist/blocklist.py
#
# Copyright (C) 2007 Andrew Resch ('andar') <andrewresch@gmail.com>
# Copyright (C) 2008 Mark Stahler ('kramed') <markstahler@gmail.com>

# a snip or two used from johhnyg

# 
# Deluge is free software.
# 
# You may redistribute it and/or modify it under the terms of the
# GNU General Public License, as published by the Free Software
# Foundation; either version 2 of the License, or (at your option)
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
#     Boston, MA    02110-1301, USA.
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

# TODO:
#    - ZERO connections until after import
#    - download timeouts / retries

import urllib2, httplib, socket, os, datetime, sys
import deluge.common
import deluge.component # for libtorrent session reference to change connection number
from deluge.log import LOG as log
import ui # added by Mark for pausing torrents
from peerguardian import PGReader, PGException
from text import TextReader, GZMuleReader, PGZip

BLOCKLIST_PREFS = {
        "url": "http://www.bluetack.co.uk/config/pipfilter.dat.gz",
        "load_on_start": "True",
        "check_after_days": 2,
        "listtype": "gzmule",
        "timeout": 180,
        "try_times": 3
}

BACKUP_PREFS = {
        "url": "http://www.bluetack.co.uk/config/pipfilter.dat.gz",
        "listtype": "gzmule",
}

FORMATS =  {
       'gzmule': ["Emule IP list (GZip)", GZMuleReader, None],
       'spzip': ["SafePeer Text (Zipped)", PGZip, None],
       'pgtext': ["PeerGuardian Text (Uncompressed)", TextReader, None],
       'p2bgz': ["PeerGuardian P2B (GZip)", PGReader, None]
} 

class HTTPConnection(httplib.HTTPConnection):
    """A customized HTTPConnection allowing a per-connection timeout, specified at construction."""

    def __init__(self, host, port=None, strict=None, timeout=None):
        httplib.HTTPConnection.__init__(self, host, port, strict)
        self.timeout = timeout

    def connect(self):
        """Override HTTPConnection.connect to connect to
        host/port specified in __init__."""

        msg = "getaddrinfo returns an empty list"
        for res in socket.getaddrinfo(self.host, self.port, 0, socket.SOCK_STREAM):
            af, socktype, proto, canonname, sa = res
            try:
                self.sock = socket.socket(af, socktype, proto)
                if self.timeout:
                    self.sock.settimeout(self.timeout)
                self.sock.connect(sa)
            except socket.error, msg:
                if self.sock:
                    self.sock.close()
                self.sock = None
                continue
            break
        if not self.sock:
            raise socket.error, msg


class HTTPHandler(urllib2.HTTPHandler):
    """A customized HTTPHandler which times out connection after the duration specified at construction."""

    def __init__(self, timeout=None):
        urllib2.HTTPHandler.__init__(self)
        self.timeout = timeout

    def http_open(self, req):
        """Override http_open."""

        def makeConnection(host, port=None, strict=None):
            return HTTPConnection(host, port, strict, timeout = self.timeout)

        #print "HTTPHandler opening", req.get_full_url()
        return self.do_open(makeConnection, req)


class TorrentBlockList:    
    def __init__(self, coreplugin):       
        self.plugin = coreplugin    # reference from plugin core
        log.info('Blocklist: TorrentBlockList instantiated')
        deluge.component.get("Core").session.set_max_connections(0)
        self.config = deluge.configmanager.ConfigManager("blocklist.conf", BLOCKLIST_PREFS)
        self.curr = 0
        self.load_options()
        
        # Make sure we have a current block list file locally
        self.fetch = False
        self.local_blocklist = deluge.common.get_config_dir("blocklist.cache")                   

        # Check list for modifications from online version
        self.check_update()
        
        # Initialize download attempt
        self.attempt = 0
        
        if self.fetch == True:
            self.download()
                        
        log.debug('Blocklist: TorrentBlockList Constructor finished')
        
                    
    def load_options(self):
        #self.config.load()
        # Fill variables with settings from block list configuration file
        self.url = self.config['url']
        self.listtype = self.config['listtype']
        self.check_after_days = self.config['check_after_days']    
        self.load_on_start = self.config['load_on_start']
        self.timeout = self.config['timeout']
        self.try_times = self.config['try_times']
        
        self.old_url = self.url
        self.old_listtype = self.listtype
        
        socket.setdefaulttimeout(self.timeout)
        
    def set_options(self, options):
        log.info('Blocklist: Options saved...')
        self.config.set('url', options['url'])
        self.config.set('check_after_days', options['check_after_days'])
        self.config.set('load_on_start', options['load_on_start'])
        self.config.set('listtype', options['listtype'])
        self.config.set('timeout', options['timeout'])
        self.config.set('try_times', options['try_times'])
        # Save settings to disk
        self.config.save()
        # Load newly set options to core plugin
        self.load_options()
        
    def check_update(self):
        log.info('Blocklist: Checking for updates')  
        
        try:
            # Check current block lists time stamp and decide if it needs to be replaced
            list_stats = os.stat(self.local_blocklist)
            list_time = datetime.datetime.fromtimestamp(list_stats.st_mtime)
            list_size = list_stats.st_size
            current_time = datetime.datetime.today()
        
        except:
            self.fetch = True
            return
        
        # If local blocklist file exists but nothing is in it
        if list_size == 0:
            self.fetch = True
            return           
        
        if current_time >= (list_time + datetime.timedelta(self.check_after_days)):
            check_newer = True
            log.debug('Blocklist: List may need to be replaced')
        else:
            check_newer = False
                
        # If the program decides it is time to get a new list
        if check_newer == True:
            log.debug('Blocklist: Attempting check')
    
            j = 0    # counter for loop
            
            while j < self.try_times:
                # Get current online block lists time stamp and compare it with current
                try:                    
                    http_handler = HTTPHandler(timeout = 15)
                    opener = urllib2.build_opener(http_handler)
                    request = urllib2.Request(self.url)
                    
                    try:
                        new_listinfo = opener.open(request)    # Can Raise URLError
                        header = new_listinfo.info()
                        remote_size = int(header['content-length'])
                        remote_time = datetime.datetime.strptime(header['last-modified'],"%a, %d %b %Y %H:%M:%S GMT")
                        remote_type = header['content-type']
                    
                    except Exception, e:
                        log.warning(e)
                        # HANDLE EXCEPTOIN
                    
                    log.debug(self.listtype)
          
                    # check expected list type
                    if self.listtype == "spzip":
                        list_type = "application/zip"
                    elif self.listtype == "gzmule" or self.listtype == "p2bgz":
                        list_type = "application/x-gzip"
                    else:
                        list_type = "text/html"
                    
                    # Print remote file information and local
                    log.debug('Blocklist: remote')
                    log.debug(remote_type)
                    log.debug(remote_time)
                    log.debug(remote_size)
                    log.debug('Blocklist: local')
                    log.debug(list_type)
                    log.debug(list_time)
                    log.debug(list_size)
                        
                    # Compare MIME types of local and remote list
                    if list_type == remote_type:
                        log.info('Blocklist: Remote and Local have the same list type')
                        # Compare last modified times and decide to download a new list or not
                        if list_time < remote_time or list_size != remote_size:
                            self.fetch = True
                            log.info('Blocklist: Local blocklist list is out of date')
                        
                        else:
                            self.fetch = False
                            log.info('Blocklist: Local block list is up to date')
                        
                        return
                            
                    j+=1
                    log.debug('Blocklist: 6 TRY AGAIN FOO')
                    
                # Connection can't be made to check remote time stamps
                except: # && urllib2.URLError
                    log.debug('Blocklist: Connection to remote server timed out')
                    self.fetch = False
                    j+=1
                
        else:
            log.info('Blocklist: Not enough time has passed to check for a new list')
            return
        
    def download(self):
        log.info('Blocklist: Beginning download')
        self.attempt += 1
        
        i = 0
        while i < self.try_times:
            # Download a new block list    
            try:
                log.info('Blocklist: Downloading new list...')
                http_handler = HTTPHandler(timeout = 15)
                opener = urllib2.build_opener(http_handler)
                request = urllib2.Request(self.url)
            	new_list = opener.open(request)
                file = open(deluge.common.get_config_dir("blocklist.cache"), 'w')
                while 1:
                    data = new_list.read()
                    if not len(data):
                        break
                    file.write(data)
                file.close()   
                            
            except OSError, e:
                log.debug('Blocklist: Unable to write blocklist file')
                return
                        
            except:
                if self.attempt > self.try_times:
                    log.warning('Blocklist: All download attempts failed')
                    return
                
                else:
                    log.warning('Blocklist: Try list download again')
                    i += 1    
                    
            # CHECKSUM 
            
            log.info('Blocklist: List downloaded sucessfully')
               
                
    def import_list(self):
        log.info('Blocklist: Importing list...')        
        try:
            self.plugin.reset_ip_filter()
            self.curr = 0
            log.info('Blocklist: IP Filter reset')
        except:
            log.debug('Blocklist: Reset filter failed')
            pass
        
        # Instantiate format class that will read the lists file format
        try:
            log.info('Blocklist: ' + str(self.listtype))
            read_list = FORMATS[self.listtype][1](self.local_blocklist)
            
        except:
            log.warning('Blocklist: Error: Format read error')
            self.reset_critical_settings()
            
        try:
            ips = read_list.next()
            print ips
            
            while ips:
                self.plugin.block_ip_range(ips)
                ips = read_list.next()
                self.curr += 1
                # Progress measurement here
                
            log.info(self.curr)
                
        except IOError, e:
            log.debug('Blocklist: Problem with list, re-download')
            return
        
        # Throw exception if curr = 0 reset critical settings
        if self.curr == 0:
            log.warning("Blocklist: Improper list read")
            self.reset_critical_settings()
        else:
            deluge.component.get("Core").session.set_max_connections(deluge.configmanager.ConfigManager("core.conf")["max_connections_global"])
            log.info('Blocklist: Import completed sucessfully')
        
    def reset_critical_settings(self):
        log.info('Blocklist: URL and List type reset')
        reset_url = BACKUP_PREFS["url"]
        reset_listtype = BACKUP_PREFS["listtype"]
        
        log.info(reset_url)
        log.info(reset_listtype)
        
        self.config.set('url', reset_url)
        self.config.set('listtype', reset_listtype)
        self.config.save()
        
        self.load_options()
        log.info(self.url)
        log.info(self.listtype)
        self.download()
        self.import_list()
        
    def return_count(self):
        return self.curr
    
    def get_config_value(self, key): # url, check_after_days, listtype
        val = self.config[key]
        log.debug('Blocklist: Get_config_val')
        return val
