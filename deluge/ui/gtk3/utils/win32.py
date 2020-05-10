import logging
from ctypes import c_wchar_p, windll

from gi.repository import Gtk
from win32gui import CallWindowProc, SetWindowLong

import deluge.component as component
from deluge.ui.client import client

WM_ENDSESSION = 16
WM_QUERYENDSESSION = 17
GWL_WNDPROC = -4

log = logging.getLogger(__name__)


class Win32ShutdownCheck(component):
    """Handle WM_QUERYENDSESSION, WM_ENDSESSION messages to shutdown cleanly."""

    def __init__(self, gdk_window):
        component.Component.__init__(self, 'Win32ShutdownCheck')
        self.shutdown_block = None
        # Set WndProc to self._on_wndproc and store old value.
        self.prev_wndproc = SetWindowLong(
            gdk_window.handle, GWL_WNDPROC, self._on_wndproc
        )

    def shutdown(self):
        self.remove_shutdown_block()

    def _on_wndproc(self, hwnd, msg, wparam, lparam):
        """Handles all messages sent to the window from Windows OS.

        Args:
            hwnd (ctypes.wintypes.HWND): Handle to window
            msg (ctypes.wintypes.UINT): Message identifier. We handle
                WM_ENDSESSION and WM_QUERYENDSESSION.
            wparam (ctypes.wintypes.WPARAM): End-session option. If True with
                message WM_ENDSESSION, Deluge GTK will shutdown.
            lparam (ctypes.wintypes.LPARAM): Logoff option
        Returns:
            bool: If msg is WM_QUERYENDSESSION, False to indicate to prevent
                shutdown. If msg is WM_ENDSESSION, False to indicate we handled
                the massage. Else, the original WndProc return value.
        """

        if msg == WM_QUERYENDSESSION:
            log.debug('Received WM_QUERYENDSESSION, blocking shutdown')
            log.info('Preparing to shutdown Deluge')
            retval = windll.user32.ShutdownBlockReasonCreate(
                hwnd, c_wchar_p('Shutting down Deluge')
            )
            log.debug('Shutdown block created: %s', retval != 0)
            if retval != 0:
                self.shutdown_block = hwnd
                if client.connected() and client.is_localhost():
                    client.register_event_handler(
                        'SessionPausedEvent', self.remove_shutdown_block
                    )
                    # save resume data and pause session
                    client.core.torrentmanager.save_resume_data()
                    client.core.torrentmanager.save_resume_data_file()
                    client.core.pause_all_torrents()
                else:
                    self.remove_shutdown_block()
            return True
        elif msg == WM_ENDSESSION:
            log.debug('Received WM_ENDSESSION, checking status')
            if not wparam:
                log.info('Shutdown cancelled, resuming normal operation')
                self.remove_shutdown_block()
                if client.connected():
                    client.core.resume_all_torrents()
                    client.deregister_event_handler(
                        'SessionPausedEvent', self.remove_shutdown_block
                    )
            else:
                log.info('Shutting down Deluge GTK')
                # wait for block to be destroyed
                while Gtk.events_pending() and self.shutdown_block:
                    Gtk.main_iteration()
                component.get('MainWindow')._quit_gtkui(False)
            return False
        else:
            # Pass all messages on to the original WndProc.
            return CallWindowProc(self.prev_wndproc, hwnd, msg, wparam, lparam)

    def remove_shutdown_block(self):
        """Removes the blocking shutdown reason for Windows"""
        if self.shutdown_block:
            retval = windll.user32.ShutdownBlockReasonDestroy(self.shutdown_block)
            if retval != 0:
                self.shutdown_block = None
            log.debug('Shutdown block destroyed: %s', retval != 0)
