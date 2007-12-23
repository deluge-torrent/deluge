# -*- coding: utf-8 -*-
#
# browser.py
#
# Copyright (C) Marcos Pinto 2007 <markybob@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2, or (at your option)
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
#  In addition, as a special exception, the copyright holders give
#  permission to link the code of portions of this program with the OpenSSL
#  library.
#  You must obey the GNU General Public License in all respects for all of
#  the code used other than OpenSSL. If you modify file(s) with this
#  exception, you may extend this exception to your version of the file(s),
#  but you are not obligated to do so. If you do not wish to do so, delete
#  this exception statement from your version. If you delete this exception
#  statement from all source files in the program, then also delete it here.

import os
import common

if common.windows_check():
    import win32con
    from ctypes import *
    from ctypes.wintypes import *
    from comtypes import IUnknown, GUID, COMMETHOD, COMObject
    from comtypes.automation import IDispatch, VARIANT
    from comtypes.hresult import *
    from comtypes.client import CreateObject, GetModule
    CreateObject("InternetExplorer.Application").Quit()
    from comtypes.gen.SHDocVw import IWebBrowser2
    kernel32 = windll.kernel32
    user32 = windll.user32
    atl = windll.atl
else:
    import gtkmozembed

import pygtk
pygtk.require("2.0")
import gtk, gtk.keysyms, gtk.glade
import gobject
import common

class Browser:
    """class builds and displays our internal browser"""
    def __init__(self, launch_site=None):
        if common.windows_check():
            self.widgets = gtk.glade.XML(common.get_glade_file("browserwin.glade"), domain='deluge')
        else:
            self.widgets = gtk.glade.XML(common.get_glade_file("browser.glade"), domain='deluge')
        self.txt_url = self.widgets.get_widget("entry1")
        self.widgets.get_widget("window1").set_title("Deluge Web Browser")
        self.txt_google = self.widgets.get_widget("entry2")
        self.window = self.widgets.get_widget("window1")
        self.window.set_default_size(940, 700)
        self.window.set_position(gtk.WIN_POS_CENTER_ALWAYS)
        self.window.set_focus(self.txt_url)
        self.window.connect("key_press_event", self.key_pressed)
        self.window.connect("delete_event", self.hide)
        self.window.realize()
        self.signal_dic = { "load_url" : self.load_url,
                            "search" : self.search,
                            "reload" : self.reload_url,
                            "go_back" : self.go_back,
                            "go_forward" : self.go_forward,
                            "go_back2" : self.go_back2,
                            "go_forward2" : self.go_forward2,
                            "stop_load" : self.stop_load,
                            "list_bookmarks" : self.bookmark_manager }
        self.widgets.signal_autoconnect(self.signal_dic)

        if not common.windows_check():
            """do all the work nessecary setup the mozilla environment."""
            self.window.set_icon(common.get_logo(48))
            self.create_profile_directory()
            self.create_prefs_js()
            self.create_mime()
            gtkmozembed.set_profile_path(common.CONFIG_DIR, "mozilla")
            self.gtkmoz = gtkmozembed.MozEmbed()
            self.gtkmoz2 = gtkmozembed.MozEmbed()
            if launch_site:
                self.gtkmoz.load_url(launch_site.strip())
            else:
                self.gtkmoz.load_url("http://deluge-torrent.org/google_search.htm")
            self.gtkmoz2.load_url("http://deluge-torrent.org/google.php")
            self.widgets.get_widget("frame1").add(self.gtkmoz)
            self.widgets.get_widget("frame2").add(self.gtkmoz2)
            self.txt_url.set_text(self.gtkmoz.get_location())
    
        else:
            #
            # here begins all the COM nonsense necessary for IE to use a different
            # user-agent string.  we need to implement IOleClientSite, from which
            # IE will ask for the user-agent string via IDispatch.  to make it ask,
            # we need to prod it via IOleControl.OnAmbientPropertyChange()
            #
            USER_AGENT = "Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1) Deluge BitTorrent/0.5.8"
            PROXY = "147932-web1.dipconsultants.com:3128"
            class INTERNET_PROXY_INFO(Structure):
                 _fields_ = [
                 ('dwAccessType', c_long),
                 ('lpszProxy', c_char_p),
                 ('lpszProxyBypass', c_char_p)
                ]
            INTERNET_OPEN_TYPE_PROXY = 3
            INTERNET_OPTION_PROXY = 38
            InternetSetOption = windll.wininet.InternetSetOptionA
            ProxyInfo = INTERNET_PROXY_INFO()
            ProxyInfo.dwAccessType = INTERNET_OPEN_TYPE_PROXY
            ProxyInfo.lpszProxy = "http=" + PROXY
            ProxyInfo.lpszProxyBypass = "<local>" # Any address with no dots isn't proxied
            InternetSetOption(0, INTERNET_OPTION_PROXY, byref(ProxyInfo), sizeof(ProxyInfo))

            class IOleClientSite(IUnknown):
                _case_insensitive_ = True
                _iid_ = GUID('{00000118-0000-0000-C000-000000000046}')
                _idlflags_ = []
    
            IOleClientSite._methods_ = [
                COMMETHOD([], HRESULT, 'SaveObject'),
                COMMETHOD([], HRESULT, 'GetMoniker',
                    ( ['in'], c_ulong, 'dwAssign' ),
                    ( ['in'], c_ulong, 'dwWhichMoniker' ),
                    ( ['out'], POINTER(POINTER(DWORD)), 'ppmk' )),  # should be IMoniker but we don't use it
                COMMETHOD([], HRESULT, 'GetContainer',
                    ( ['out'], POINTER(POINTER(DWORD)), 'ppContainer' )),  # should be IOleContainer but we don't use it
                COMMETHOD([], HRESULT, 'ShowObject'),
                COMMETHOD([], HRESULT, 'OnShowWindow',
                    ( ['in'], c_int, 'fShow' )),
                COMMETHOD([], HRESULT, 'RequestNewObjectLayout'),
                ]

            class IOleObject(IUnknown):
                _case_insensitive_ = True
                _iid_ = GUID('{00000112-0000-0000-C000-000000000046}')
                _idlflags_ = []

            IOleObject._methods_ = [
                COMMETHOD([], HRESULT, 'SetClientSite',
                  ( ['in'], POINTER(IOleClientSite), 'pClientSite' )),
                # ...
                ]

            class IOleControl(IUnknown):
                _case_insensitive_ = True
                _iid_ = GUID('{B196B288-BAB4-101A-B69C-00AA00341D07}')

            IOleControl._methods_ = [
                COMMETHOD([], HRESULT, 'GetControlInfo',
                          (['out'], POINTER(DWORD), 'pCI')),  # should be CONTROLINFO but we don't use it
                COMMETHOD([], HRESULT, 'OnMnemonic',
                          (['in'], POINTER(DWORD), 'pMsg')),  # should be MSG but we don't use it
                COMMETHOD([], HRESULT, 'OnAmbientPropertyChange',
                          (['in'], DWORD, 'dispID')),         # should be DISPID but we don't use it
                # ...
                ]

            DISPID_AMBIENT_USERAGENT = -5513

            class IESite(COMObject):
                _com_interfaces_ = [IDispatch, IOleClientSite]
                def IDispatch_Invoke(self, this, memid, riid, lcid, wFlags, pDispParams,
                                     pVarResult, pExcepInfo, puArgErr):
                    if memid == DISPID_AMBIENT_USERAGENT and pVarResult:
                        pVarResult[0].value = USER_AGENT
                    return S_OK

            _ieSite = IESite()

            #
            # here ends the COM nonsense for user-agent.
            #

            self.container = self.widgets.get_widget('drawingarea1')
            self.container2 = self.widgets.get_widget('drawingarea2')
            self.container.realize()
            self.container2.realize()
            self.container.show()
            self.container2.show()
            self.container.set_property("can-focus", True)
            self.widgets.get_widget('vpaned1').set_position(600)
            self.container.connect("focus", self.on_container_focus)
            self.container.connect("size-allocate", self.on_container_size)
            self.container2.connect("size-allocate", self.on_container_size)

            def makeBrowser(container, num):
                """Create and return an instance of IE via AtlAxWin.
                'container' should be a gtk.DrawingArea which acts as IE's parent."""
                # Create the IE control instance.
                atl.AtlAxWinInit()
                hInstance = kernel32.GetModuleHandleA(None)
                parentHwnd = container.window.handle
                self.atlAxWinHwnd = \
                    user32.CreateWindowExA(0, "AtlAxWin",
                            "{EAB22AC1-30C1-11CF-A7EB-0000C05BAE0B}", # IWebBrowser2
                            win32con.WS_VISIBLE | win32con.WS_CHILD |
                            win32con.WS_HSCROLL | win32con.WS_VSCROLL,
                            0, 0, 100, 100, parentHwnd, None, hInstance, 0)
        
                # Get the IWebBrowser2 interface for the IE control.
                pBrowserUnk = POINTER(IUnknown)()
                atl.AtlAxGetControl(self.atlAxWinHwnd, byref(pBrowserUnk))
                # Wire up our client site, which provides the User-Agent as an ambient property.
                oleObject = pBrowserUnk.QueryInterface(IOleObject)
                oleObject.SetClientSite(_ieSite);
                oleControl = pBrowserUnk.QueryInterface(IOleControl)
                oleControl.OnAmbientPropertyChange(DISPID_AMBIENT_USERAGENT);

                if num == 1:
                    self.pBrowser = pBrowserUnk.QueryInterface(IWebBrowser2)
                    self.pBrowser.Navigate("about:blank")
                    if launch_site:
                        self.pBrowser.Navigate(launch_site.strip())
                    else:   
                        self.pBrowser.Navigate("http://deluge-torrent.org/google_search.htm")
    
                elif num == 2:
                    self.pBrowser2 = pBrowserUnk.QueryInterface(IWebBrowser2)
                    self.pBrowser2.Navigate("about:blank")
                    self.pBrowser2.Navigate("http://deluge-torrent.org/google.php")
                return gtk.gdk.window_foreign_new(long(self.atlAxWinHwnd))
            # Create the IE controls.
            self.ieParents = {
                self.container: makeBrowser(self.container, 1),
                self.container2: makeBrowser(self.container2, 2)
                }


        # Create the BookmarkManager
        import bookmark
        self.bookmarks = bookmark.BookmarkManager(self,
            self.widgets.get_widget("toolbutton_bookmarks"))
        self.window.show_all()
        gobject.timeout_add(int(1000), self.update)
        
    def on_widget_click(self, widget, data):
        self.main.window.focus()

    def on_container_size(self, widget, sizeAlloc):
        self.ieParents[widget].move_resize(0, 0, sizeAlloc.width, sizeAlloc.height)
        
    def on_container_focus(self, widget, data):
        rect = RECT()
        user32.GetWindowRect(self.atlAxWinHwnd, byref(rect))
        ieHwnd = user32.WindowFromPoint(POINT(rect.left, rect.top))
        user32.SetFocus(ieHwnd)

    def create_profile_directory(widget=None):
        """create the mozilla profile directory, if needed."""
        if not common.windows_check():
            path = os.path.join(common.CONFIG_DIR, "mozilla")
            if not os.path.exists(path):
                os.makedirs(path)
        else:
            pass

    def create_mime(widget=None):
        """create the mimeTypes.rdf file"""
        if not common.windows_check():
            mime_content = """\
<?xml version="1.0"?>
<RDF:RDF xmlns:NC="http://home.netscape.com/NC-rdf#"
         xmlns:RDF="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
  <RDF:Description RDF:about="urn:mimetype:handler:application/x-bittorrent"
                   NC:saveToDisk="false"
                   NC:alwaysAsk="false"
                   NC:useSystemDefault="true">
    <NC:externalApplication RDF:resource="urn:mimetype:externalApplication:application/x-bittorrent"/>
  </RDF:Description>
  <RDF:Seq RDF:about="urn:mimetypes:root">
    <RDF:li RDF:resource="urn:mimetype:application/x-bittorrent"/>
  </RDF:Seq>
  <RDF:Description RDF:about="urn:mimetypes">
    <NC:MIME-types RDF:resource="urn:mimetypes:root"/>
  </RDF:Description>
  <RDF:Description RDF:about="urn:mimetype:application/x-bittorrent"
                   NC:description="BitTorrent seed file"
                   NC:value="application/x-bittorrent"
                   NC:editable="true">
    <NC:handlerProp RDF:resource="urn:mimetype:handler:application/x-bittorrent"/>
  </RDF:Description>
  <RDF:Description RDF:about="urn:mimetype:externalApplication:application/x-bittorrent"
                   NC:prettyName=""
                   NC:path="" />
</RDF:RDF>
"""
            mime_path = os.path.join(common.CONFIG_DIR, "mozilla", "mimeTypes.rdf")
            f = open(mime_path, "wt")
            f.write(mime_content)
            f.close()
        else:
            pass

    def create_prefs_js(widget=None):
        """create the file prefs.js in the mozilla profile directory.  this
        does things like turn off the warning when navigating to https pages.
        """
        if not common.windows_check():
            prefs_content = """\
user_pref("security.warn_entering_secure", false);
user_pref("security.warn_entering_weak", false);
user_pref("security.warn_viewing_mixed", false);
user_pref("security.warn_leaving_secure", false);
user_pref("security.warn_submit_insecure", false);
user_pref("security.warn_entering_secure.show_once", false);
user_pref("security.warn_entering_weak.show_once", false);
user_pref("security.warn_viewing_mixed.show_once", false);
user_pref("security.warn_leaving_secure.show_once", false);
user_pref("security.warn_submit_insecure.show_once", false);
user_pref("security.enable_java", false);
user_pref("browser.xul.error_pages.enabled", false);
user_pref("general.useragent.vendor", %s);
user_pref("general.useragent.vendorSub", %s);
user_pref("network.proxy.http", "%s");
user_pref("network.proxy.http_port", %s);
user_pref("network.proxy.ssl", "%s");
user_pref("network.proxy.ssl_port", %s);
user_pref("network.proxy.type", 1);
""" % (repr("Deluge BitTorrent"),
       repr("0.5.8"),
       '147932-web1.dipconsultants.com',
       3128,
       '147932-web1.dipconsultants.com',
       3128)
            prefs_path = os.path.join(common.CONFIG_DIR, "mozilla", "prefs.js")
            f = open(prefs_path, "wt")
            f.write(prefs_content)
            f.close()
        else:
            pass

    def update(self):
        """updates the GUI"""
        if self.window.get_focus() != self.txt_url:
            if not common.windows_check():
                self.txt_url.set_text(self.gtkmoz.get_location())
                try:
                    self.widgets.get_widget("window1").set_title("Deluge Web Browser " \
                        + self.gtkmoz.get_title())
                except:
                    pass
                if self.gtkmoz.can_go_back():
                    self.widgets.get_widget("toolbutton_back").set_sensitive(True)
                else:
                    self.widgets.get_widget("toolbutton_back").set_sensitive(False)
                if self.gtkmoz.can_go_forward():
                    self.widgets.get_widget("toolbutton_forward").set_sensitive(True)
                else:
                    self.widgets.get_widget("toolbutton_forward").set_sensitive(False)
                if self.gtkmoz2.can_go_back():
                    self.widgets.get_widget("toolbutton_back2").set_sensitive(True)
                else:
                    self.widgets.get_widget("toolbutton_back2").set_sensitive(False)
                if self.gtkmoz2.can_go_forward():
                    self.widgets.get_widget("toolbutton_forward2").set_sensitive(True)
                else:
                    self.widgets.get_widget("toolbutton_forward2").set_sensitive(False)
            else:
                self.txt_url.set_text(self.pBrowser.LocationURL)
                try:
                    self.widgets.get_widget("window1").set_title("Deluge Web Browser " \
                    + self.pBrowser.LocationName)
                except:
                    pass
        return True

    def key_pressed(self, widget, key):
        """captures ctrl+ keys and sets focus accordingly, or quits"""
        if key.keyval in (gtk.keysyms.L, gtk.keysyms.l) and (key.state & \
            gtk.gdk.CONTROL_MASK) != 0:
            self.window.set_focus(self.txt_url)
        elif key.keyval in (gtk.keysyms.K, gtk.keysyms.k) and (key.state & \
            gtk.gdk.CONTROL_MASK) != 0:
            self.window.set_focus(self.txt_google)
        elif key.keyval in (gtk.keysyms.R, gtk.keysyms.r) and (key.state & \
            gtk.gdk.CONTROL_MASK) != 0:
            if not common.windows_check():
                self.gtkmoz.reload(0)
            else:
                self.pBrowser.refresh()
        elif key.keyval == gtk.keysyms.Return and (key.state & \
            gtk.gdk.CONTROL_MASK) != 0:
            if not common.windows_check():
                self.gtkmoz.load_url("http://www.%s.com" % (self.txt_url.get_text()))
                self.txt_url.set_text(self.gtkmoz.get_location())
            else:
                v = byref(VARIANT())
                self.pBrowser.Navigate("http://www.%s.com" % (self.txt_url.get_text()), v, v, v, v)
        elif key.keyval == gtk.keysyms.Return and (key.state & \
            gtk.gdk.SHIFT_MASK) != 0:
            if not common.windows_check():
                self.gtkmoz.load_url("http://www.%s.net" % (self.txt_url.get_text()))
                self.txt_url.set_text(self.gtkmoz.get_location())
            else:
                v = byref(VARIANT())
                self.pBrowser.Navigate("http://www.%s.net" % (self.txt_url.get_text()), v, v, v, v)                
        elif key.keyval in (gtk.keysyms.Q, gtk.keysyms.q, gtk.keysyms.W, \
            gtk.keysyms.w) and (key.state & gtk.gdk.CONTROL_MASK) != 0:
            self.hide()


    def search(self, widget=None):
        """open a new search page"""
        if not common.windows_check():
            self.gtkmoz.load_url("http://www.google.com/cse?cx=0103316019315568500"
                + "92%3Apfadwhze_jy&q=" + self.txt_google.get_text() + "&sa=Search&cof=FORID%3A1")
            try:
                self.widgets.get_widget("window1").set_title("Deluge Web Browser " \
                + self.gtkmoz.get_title())
            except:
                pass
        else:
            v = byref(VARIANT())
            self.pBrowser.Navigate("http://www.google.com/cse?cx=0103316019315568500"
                + "92%3Apfadwhze_jy&q=" + self.txt_google.get_text() + "&sa=Search&cof=FORID%3A1", v, v, v, v)

    def load_url(self, widget=None):
        """open a new url"""
        if not common.windows_check():
            self.gtkmoz.load_url(self.txt_url.get_text())
            try:
                self.widgets.get_widget("window1").set_title("Deluge Web Browser " \
                + self.gtkmoz.get_title())
            except:
                pass
        else:
            v = byref(VARIANT())
            self.pBrowser.Navigate(self.txt_url.get_text(), v, v, v, v)

    def reload_url(self, widget=None):
        """refresh the current url"""
        if not common.windows_check():
            self.gtkmoz.reload(0)
        else:
            self.pBrowser.refresh()

    def go_back(self, widget=None):
        """go a page back"""
        if not common.windows_check():
            if self.gtkmoz.can_go_back():
                self.gtkmoz.go_back()
                self.txt_url.set_text(self.gtkmoz.get_location())
            try:
                self.widgets.get_widget("window1").set_title("Deluge Web Browser " \
                    + self.gtkmoz.get_title())
            except:
                pass
        else:
            self.pBrowser.GoBack()
            self.txt_url.set_text(self.pBrowser.LocationURL)
            try:
                self.widgets.get_widget("window1").set_title("Deluge Web Browser" \
                    + self.pBrowser.LocationName)
            except:
                pass

    def go_forward(self, widget=None):
        """go a page ahead"""
        if not common.windows_check():
            if self.gtkmoz.can_go_forward():
                self.gtkmoz.go_forward()
                self.txt_url.set_text(self.gtkmoz.get_location())
            try:
                self.widgets.get_widget("window1").set_title("Deluge Web Browser " \
                + self.gtkmoz.get_title())
            except:
                pass
        else:
            self.pBrowser.GoForward()
            self.txt_url.set_text(self.pBrowser.LocationURL)
            try:
                self.widgets.get_widget("window1").set_title("Deluge Web Browser" \
                    + self.pBrowser.LocationName)
            except:
                pass

    def go_back2(self, widget=None):
        """go a page back"""
        if not common.windows_check():
            if self.gtkmoz2.can_go_back():
                self.gtkmoz2.go_back()
        else:
            self.pBrowser2.GoBack()

    def go_forward2(self, widget=None):
        """go a page ahead"""
        if not common.windows_check():
            if self.gtkmoz2.can_go_forward():
                self.gtkmoz2.go_forward()
        else:
            self.pBrowser2.GoForward()

    def stop_load(self, widget=None):
        """stop loading current page"""
        if not common.windows_check():
            self.gtkmoz.stop_load()
        else:
            self.pBrowser.Stop()

    def bookmark_manager(self, widget=None):
        """show bookmark manager"""
        self.bookmarks.show()

    def hide(self, widget=None, arg=None):
        """close browser"""
        self.window.hide()
        return True

