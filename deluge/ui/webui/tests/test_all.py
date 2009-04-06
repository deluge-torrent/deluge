#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) Martijn Voncken 2008 <mvoncken@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3, or (at your option)
# any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, write to:
#     The Free Software Foundation, Inc.,
#     51 Franklin Street, Fifth Floor
#     Boston, MA  02110-1301, USA.
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

#

"""
Testing the REST api, not the units.
unittest the right way feels so unpythonic :(
!! BIG FAT WARNING !!: this test deletes active torrents .
!! BIG FAT WARNING 2!!: this test hammers the tracker that is tested against.
"""
import unittest
import cookielib, urllib2 , urllib
from WebUi.webserver_common import ws,TORRENT_KEYS, proxy
import operator

ws.init_06()
print 'test-env=',ws.env

#CONFIG:
BASE_URL = 'http://localhost:8112'
PWD = 'deluge'

def get_status(id):
    return proxy.get_torrent_status(id,TORRENT_KEYS)

#BASE:
#303 = see other
#404 = not found
#500 = server error
#200 = OK, page exists.
class TestWebUiBase(unittest.TestCase):
    def setUp(self):
        #cookie aware-opener that DOES NOT use redirects.
        opener = urllib2.OpenerDirector()
        self.cj = cookielib.CookieJar()
        for handler in [urllib2.HTTPHandler(),urllib2.HTTPDefaultErrorHandler(),
                urllib2.FileHandler(),urllib2.HTTPErrorProcessor(),
                urllib2.HTTPCookieProcessor(self.cj)]:
            opener.add_handler(handler)
        #/opener
        self.opener = opener

    def open_url(self, page, post=None):
        url = BASE_URL + page

        if post == 1:
            post = {'Force_a_post' : 'spam'}
        if post:
            post = urllib.urlencode(post)
        r = self.opener.open(url , data = post)


        #BUG: error-page does not return status 500, but status 200
        #workaround...
        data = r.read()
        if '<!--ERROR-MARKER-->' in data:
            error = IOError()
            error.code = 500
            #print data
            raise error
        if r.code <> 200:
            fail('no code 200, error-code=%s' % r.code)
        return r

    def get_cookies(self):
        return dict((c.name,c.value) for  c in self.cj)
    cookies = property(get_cookies)

    def assert_status(self,status, page, post):
        try :
            r = self.open_url(page, post)
        except IOError,e:
            self.assertEqual(e.code, status)
        else:
            self.fail('page was found "%s" (%s)' % (page, r.code ))

    def assert_404(self, page, post = None):
        self.assert_status(404, page, post)

    def assert_500(self, page, post = None):
        self.assert_status(500, page, post)

    def assert_303(self, page, redirect_to, post=None):
        try :
            r = self.open_url(page, post)
        except IOError,e:
            self.assertEqual(e.code, 303)
            self.assertEqual(e.headers['Location'], redirect_to)
        else:
            #print r
            self.fail('No 303!')

    def assert_exists(self, page, post = None):
        try :
            r = self.open_url(page, post)
        except IOError,e:
            self.fail('page was not found "%s" (%s)' % (page, e.code))
        else:
            pass

    first_torrent_id = property(lambda self: proxy.get_session_state()[0])
    first_torrent = property(lambda self: get_status(self.first_torrent_id))


class TestNoAuth(TestWebUiBase):
    def test303(self):
        self.assert_303('/','/login')
        self.assert_303('','/login')
        self.assert_303('/index','/login')
        #self.assert_303('/torrent/pause/','/login')
        #self.assert_303('/config','/login')
        self.assert_303('/torrent/info/','/login')

    def test404(self):
        self.assert_404('/torrent/info')
        self.assert_404('/garbage')
        #self.assert_404('/static/garbage')
        #self.assert_404('/template/static/garbage')
        self.assert_404('/torrent/pause/', post=1)

    def testOpen(self):
        self.assert_exists('/login')
        self.assert_exists('/about')

    def testStatic(self):
        self.assert_exists('/static/images/simple_line.jpg')
        self.assert_exists('/static/images/16/up.png')
        #test 404

    #test template-static



class TestSession(TestWebUiBase):
    def testLogin(self):
        self.assert_303('/home','/login')
        #invalid pwd:
        self.assert_303('/login','/login?error=1',{'pwd':'invalid'})
        #login
        self.assert_303('/login','/index',{'pwd':PWD})
        #now i'm logged-in!
        #there are no sort-coockies yet so the default page is /index.
        self.assert_303('/home','/index')
        self.assert_exists('/index')
        #self.assert_exists('/config')
        self.assert_exists('/torrent/add')
        self.assert_303('/','/index')
        self.assert_303('','/index')

        #logout
        self.assert_303('/logout','/login', post=1)
        #really logged out?
        self.assert_303('/','/login')
        self.assert_303('','/login')
        self.assert_303('/index','/login')
        self.assert_303('/torrent/add','/login')
        self.assert_exists('/about')


    def testRefresh(self):
        #starting pos
        self.assert_303('/login','/index',{'pwd':PWD})
        r = self.open_url('/index')
        assert not 'auto_refresh' in self.cookies
        assert not 'auto_refresh_secs' in self.cookies
        assert not r.headers.has_key('Refresh')

        #on:
        self.assert_303('/refresh/on','/index', post=1)

        assert 'auto_refresh' in self.cookies
        assert 'auto_refresh_secs' in self.cookies
        self.assertEqual(self.cookies['auto_refresh'],'1')
        self.assertEqual(self.cookies['auto_refresh_secs'],'10')

        r = self.open_url('/index')
        assert r.headers['Refresh'] == '10 ; url=/index'

        #set:
        self.assert_303('/refresh/set','/index',{'refresh':'5'})
        self.assertEqual(self.cookies['auto_refresh_secs'],'5')

        r = self.open_url('/index')
        assert r.headers['Refresh'] == '5 ; url=/index'
        self.assert_500('/refresh/set',{'refresh':'a string'})

        #off:
        self.assert_303('/refresh/off','/index', post=1)
        self.assertEqual(self.cookies['auto_refresh'],'0')
        self.assertEqual(self.cookies['auto_refresh_secs'],'5')

        r = self.open_url('/index')
        assert not 'Refresh' in r.headers

class TestIntegration(TestWebUiBase):
    initialized = False
    def setUp(self):
        TestWebUiBase.setUp(self)

        self.assert_303('/login','/index',{'pwd':PWD})
        self.urls = sorted([
        'http://torrents.aelitis.com:88/torrents/azplatform2_1.13.zip.torrent',
        'http://torrents.aelitis.com:88/torrents/azplugins_2.1.4.jar.torrent',
        'http://torrents.aelitis.com:88/torrents/azautoseeder_0.1.1.jar.torrent'
        ])

        torrent_ids = proxy.get_session_state()

        #avoid hammering, investigate current torrent-list and do not re-add.
        #correct means : 3 torrent's in list (for now)
        if len(torrent_ids) <> 3:
            #delete all, nice use case for refactoring delete..
            torrent_ids = proxy.get_session_state()
            for torrent in torrent_ids:
                proxy.remove_torrent([torrent], False)

            torrent_ids = proxy.get_session_state()
            self.assertEqual(torrent_ids, [])

            #add 3 using url.
            for url in self.urls:
                self.assert_303('/torrent/add','/index',{'url':url,'torrent':None})

            #added?
            self.torrent_ids = proxy.get_session_state()
            self.assertEqual(len(self.torrent_ids), 3)

        else:
            if ws.env <> '0.6':
                #test correctness of existing-list
                for url in self.urls:
                    self.assert_500('/torrent/add',{'url':url,'torrent':None})

    def testPauseResume(self):
        #pause all
        self.assert_303('/pause_all','/index', post=1)
        #pause worked?
        pause_status = [get_status(id)["user_paused"] for id in proxy.get_session_state()]
        for paused in pause_status:
            self.assertEqual(paused, True)

        #resume all
        self.assert_303('/resume_all','/index', post=1)
        #resume worked?
        pause_status = [get_status(id)["user_paused"] for id in proxy.get_session_state()]
        for paused in pause_status:
            self.assertEqual(paused,False)
        #pause again.
        self.assert_303('/pause_all','/index', post=1)

        torrent_id = self.first_torrent_id
        #single resume.
        self.assert_303('/torrent/start/%s' % torrent_id ,'/index', post=1)
        self.assertEqual(get_status(torrent_id)["user_paused"] ,False)
        #single pause
        self.assert_303('/torrent/stop/%s' % torrent_id,'/index', post=1)
        self.assertEqual(get_status(torrent_id)["user_paused"] , True)

    def testQueue(self):
        #find last:
        torrent_id = [id for id in proxy.get_session_state()
            if (get_status(id)['queue_pos'] ==3 )][0]

        #queue
        torrent = get_status(torrent_id)
        self.assertEqual(torrent['queue_pos'], 3)
        #up:
        self.assert_303('/torrent/queue/up/%s' % torrent_id,'/index', post=1)
        torrent = get_status(torrent_id)
        self.assertEqual(torrent['queue_pos'], 2)
        self.assert_303('/torrent/queue/up/%s' % torrent_id,'/index', post=1)
        torrent = get_status(torrent_id)
        self.assertEqual(torrent['queue_pos'], 1)
        self.assert_303('/torrent/queue/up/%s' % torrent_id,'/index', post=1)
        #upper limit
        torrent = get_status(torrent_id)
        self.assertEqual(torrent['queue_pos'], 1)
        #down:
        self.assert_303('/torrent/queue/down/%s' % torrent_id,'/index', post=1)
        torrent = get_status(torrent_id)
        self.assertEqual(torrent['queue_pos'], 2)
        self.assert_303('/torrent/queue/down/%s' % torrent_id,'/index', post=1)
        torrent = get_status(torrent_id)
        self.assertEqual(torrent['queue_pos'], 3)
        self.assert_303('/torrent/queue/down/%s' % torrent_id,'/index', post=1)
        #down limit
        torrent = get_status(torrent_id)
        self.assertEqual(torrent['queue_pos'], 3)

    def testMeta(self):
        #info available?
        for torrent_id in proxy.get_session_state():
            self.assert_exists('/torrent/info/%s' % torrent_id)
            self.assert_exists('/torrent/delete/%s' % torrent_id)

        #no info:
        self.assert_500('/torrent/info/99999999')
        self.assert_500('/torrent/delete/99999999')

    def testAddRemove(self):
        #add a duplicate:
        self.assert_500('/torrent/add', post={'url':self.urls[0],'torrent':None})

        #add a 4th using url

        #delete

        #add torrrent-file
        #./test01.torrent


    def test_do_redirect(self):
        self.assert_303('/home','/index')
        #1
        self.assert_exists('/index?sort=download_rate&order=down')
        self.assert_303('/home','/index?sort=download_rate&order=down')
        assert self.cookies['sort'] == 'download_rate'
        assert self.cookies['order'] == 'down'
        #2
        self.assert_exists('/index?sort=progress&order=up')
        self.assert_303('/home','/index?sort=progress&order=up')
        assert self.cookies['sort'] == 'progress'
        assert self.cookies['order'] == 'up'
        #redir after pause-POST? in /index.
        self.assert_exists('/index?sort=name&order=down')
        torrent_id = self.first_torrent_id
        self.assert_303('/torrent/stop/%s' % torrent_id,
            '/index?sort=name&order=down', post=1)
        #redir in details 1
        self.assert_303('/torrent/stop/%s?redir=/torrent/info/%s' %(torrent_id,torrent_id)
            ,'/torrent/info/' + torrent_id, post = 1)
        #redir in details 2
        self.assert_303('/torrent/stop/%s' % torrent_id
            ,'/torrent/info/' + torrent_id ,
            post={'redir': '/torrent/info/' + torrent_id})

    def testRemote(self):
        pass

    def test_redir_after_login(self):
        pass

    def testReannounce(self):
        torrent_id = self.first_torrent_id
        self.assert_303(
            '/torrent/reannounce/%(id)s?redir=/torrent/info/%(id)s'
            %  {'id':torrent_id}
            ,'/torrent/info/' + torrent_id, post = 1)

    def testRecheck(self):
        #add test before writing code..
        #RELEASE-->disable
        """
        torrent_id = self.first_torrent_id
        self.assert_303(
            '/torrent/recheck/%(id)s?redir=/torrent/info/%(id)s'
            %  {'id':torrent_id}
            ,'/torrent/info/' + torrent_id, post = 1)
        """

    def testConfig(self):
        #0.6 only
        if ws.env <> '0.6':
            return
        #
        import WebUi.config_tabs_webui #auto registers
        import WebUi.config_tabs_deluge #auto registers
        import WebUi.config as config

        for name in config.blocks:
            self.assert_exists("/config/%s" % name)

            #todo->post page with current values.








if False:
    suiteFew = unittest.TestSuite()

    suiteFew.addTest(TestSession("testRefresh"))

    unittest.TextTestRunner(verbosity=2).run(suiteFew)

elif False:
    suiteFew = unittest.TestSuite()
    suiteFew.addTest(TestIntegration("testDoRedirect"))
    unittest.TextTestRunner(verbosity=2).run(suiteFew)

else:
    unittest.main()
