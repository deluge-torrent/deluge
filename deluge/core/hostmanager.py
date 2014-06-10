import socket
import threading

import deluge.component as component
from deluge.log import LOG as log

class HostManager(component.Component):
    def __init__(self):
        component.Component.__init__(self, "HostManager")
        self.cache_size = 2000 #remove rarely updated enrties over this limit
        self.cache = {}

    def add_item(self, ip):
        #if .cache_size reached, remove one element with smallest update .counter
        if len(self.cache) >= self.cache_size:
            min_key = min(self.cache.values(), key=attrgetter('counter')).ip
            del self.cache[min_key]
        
        self.cache[ip] = IPContainer(ip)
        log.debug("IP cached: %s, cache size: %s (limit: %s)" % (ip, len(self.cache), self.cache_size))

            
    def get_hostname(self, ip):
        if not self.cache.has_key(ip):
            #IP isn't cached. Cache it without resolving hostname. Resolve later, on .update()
            self.add_item(ip)
        else:
            #IP is already cached, update and resolve hostname if needed (see IPContainer.resolve_hostname())
            self.cache[ip].update()
            
        return self.cache[ip].hostname
        
        
class IPContainer(object):
    def __init__(self, ipaddr):
        self.ip = ipaddr
        self.hostname = ''
        self.resolve_error = False
        self.error_string = ''
        self.resolving_in_progress = False
        self.counter = 1
        self.resolve_retries_limit = 4
        self.resolve_retries = -1

    def update(self):
        self.counter += 1
        if not self.hostname and not self.resolving_in_progress and not self.resolve_retries >= self.resolve_retries_limit:
            thread = threading.Thread(target=self.resolve_hostname)
            thread.start()

    def resolve_hostname(self):
        self.resolving_in_progress = True
        self.resolve_retries += 1
        hostname = self.hostname
        try:
            hostname = socket.gethostbyaddr(self.ip)[0]
        except Exception, e:
            self.resolve_error = True
            self.error_string = e

        if hostname:
            log.debug("Got hostname %s for %s" % (hostname, self.ip))
        else:
            log.debug("Failed to resolve hostname for %s: %s in %s retries" % (self.ip, self.error_string, self.resolve_retries))

        self.hostname = hostname
        self.resolving_in_progress = False



