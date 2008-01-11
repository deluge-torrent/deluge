"""
decorators for html-pages.
"""
#relative imports
from render import render
from webserver_common import ws
from utils import *
#/relative

from lib.webpy022.webapi import cookies, setcookie as w_setcookie
from lib.webpy022.http import seeother, url
from lib.webpy022 import changequery as self_url

#deco's:
def deluge_page_noauth(func):
    """
    add http headers
    print result of func
    """
    def deco(self, name = None):
            web.header("Content-Type", "text/html; charset=utf-8")
            web.header("Cache-Control", "no-cache, must-revalidate")
            res = func(self, name)
            print res
    deco.__name__ = func.__name__
    return deco

def check_session(func):
    """
    a decorator
    return func if session is valid, else redirect to login page.
    """
    def deco(self, name = None):
        ws.log.debug('%s.%s(name=%s)'  % (self.__class__.__name__, func.__name__,
            name))
        vars = web.input(redir_after_login = None)
        ck = cookies()
        if ck.has_key("session_id") and ck["session_id"] in ws.SESSIONS:
            return func(self, name) #ok, continue..
        elif vars.redir_after_login:
            seeother(url("/login",redir=self_url()))
        else:
            seeother("/login") #do not continue, and redirect to login page
    return deco

def deluge_page(func):
    return check_session(deluge_page_noauth(func))

#combi-deco's:
def auto_refreshed(func):
    "decorator:adds a refresh header"
    def deco(self, name = None):
        if getcookie('auto_refresh') == '1':
            web.header("Refresh", "%i ; url=%s" %
                (int(getcookie('auto_refresh_secs',10)),self_url()))
        return func(self, name)
    deco.__name__ = func.__name__
    return deco

def remote(func):
    "decorator for remote api's"
    def deco(self, name = None):
        try:
            ws.log.debug('%s.%s(%s)' ,self.__class__.__name__, func.__name__,name )
            print func(self, name)
        except Exception, e:
            print 'error:%s' % e.message
            print '-'*20
            print  traceback.format_exc()
    deco.__name__ = func.__name__
    return deco
