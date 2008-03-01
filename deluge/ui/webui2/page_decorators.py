"""
decorators for html-pages.
"""
#relative imports
from render import render
from webserver_common import ws, log, proxy
from utils import *
#/relative

from lib.webpy022.webapi import cookies, setcookie as w_setcookie
from lib.webpy022.http import seeother, url
from lib.webpy022 import changequery as self_url

#deco's:
def deluge_page_noauth(func):
    """
    add http headers;print result of func
    """
    def deco(self, name = None):
            web.header("Content-Type", "text/html; charset=utf-8")
            web.header("Cache-Control", "no-cache, must-revalidate")
            res = func(self, name) #deluge_page_noauth
            print res
    deco.__name__ = func.__name__
    return deco

def check_session(func):
    """
    return func if session is valid, else redirect to login page.
    mostly used for POST-pages.
    """
    def deco(self, name = None):
        log.debug('%s.%s(name=%s)'  % (self.__class__.__name__, func.__name__,
            name))
        vars = web.input(redir_after_login = None)
        ck = cookies()
        if ck.has_key("session_id") and ck["session_id"] in ws.SESSIONS:
            return func(self, name) #check_session:ok
        elif vars.redir_after_login:
            seeother(url("/login",redir=self_url()))
        else:
            seeother("/login") #do not continue, and redirect to login page
    deco.__name__ = func.__name__
    return deco

def check_connected(func):
    def deco(self, name = None):
        connected = False
        try:
            proxy.ping()
            connected = True
        except Exception, e:
            log.debug("not_connected: %s" % e)
        if connected:
            return func(self, name) #check_connected:ok
        else:
            seeother("/connect")


    deco.__name__ = func.__name__
    return deco

def deluge_page(func):
    "deluge_page_noauth+check_session+check connected"
    return check_session(check_connected(deluge_page_noauth(func)))

#combi-deco's:
#decorators to use in combination with the ones above.
def torrent_ids(func):
    """
    change page(self, name) to page(self, torrent_ids)
    for pages that allow a list of torrents.
    """
    def deco(self, name):
        return func (self, name.split(',')) #torrent_ids
    deco.__name__ = func.__name__
    return deco

def torrent_list(func):
    """
    change page(self, name) to page(self, torrent_ids)
    for pages that allow a list of torrents.
    """
    def deco(self, name):
        torrent_list = [get_torrent_status(id) for id in name.split(',')]
        return func (self, torrent_list) #torrent_list
    deco.__name__ = func.__name__
    return deco

def torrent(func):
    """
    change page(self, name) to page(self, get_torrent_status(torrent_id))
    """
    def deco(self, name):
        torrent_id = name.split(',')[0]
        torrent =get_torrent_status(torrent_id)
        return func (self, torrent) #torrent
    deco.__name__ = func.__name__
    return deco

def auto_refreshed(func):
    "adds a refresh header"
    def deco(self, name = None):
        if getcookie('auto_refresh') == '1':
            web.header("Refresh", "%i ; url=%s" %
                (int(getcookie('auto_refresh_secs',10)),self_url()))
        return func(self, name) #auto_refreshed
    deco.__name__ = func.__name__
    return deco

def remote(func):
    "decorator for remote (string) api's"
    def deco(self, name = None):
        try:
            log.debug('%s.%s(%s)' ,self.__class__.__name__, func.__name__,name )
            print func(self, name) #remote
        except Exception, e:
            print 'error:%s' % e.message
            print '-'*20
            print  traceback.format_exc()
    deco.__name__ = func.__name__
    return deco
