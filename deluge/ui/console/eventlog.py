import time

import deluge.component as component
from deluge.decorators import maybe_coroutine
from deluge.ui.client import client
from deluge.ui.console.utils import colors


class EventLog(component.Component):
    """
    Prints out certain events as they are received from the core.
    """

    def __init__(self):
        component.Component.__init__(self, 'EventLog')
        self.console = component.get('ConsoleUI')
        self.prefix = '{!event!}* [%H:%M:%S] '
        self.date_change_format = 'On {!yellow!}%a, %d %b %Y{!input!} %Z:'

        event_callbacks = {
            'TorrentAddedEvent': self.on_torrent_added,
            'PreTorrentRemovedEvent': self.on_torrent_removed,
            'TorrentStateChangedEvent': self.on_torrent_state_changed,
            'TorrentFinishedEvent': self.on_torrent_finished,
            'NewVersionAvailableEvent': self.on_new_version_available,
            'SessionPausedEvent': self.on_session_paused,
            'SessionResumedEvent': self.on_session_resumed,
            'ConfigValueChangedEvent': self.on_config_value_changed,
            'PluginEnabledEvent': self.on_plugin_enabled,
            'PluginDisabledEvent': self.on_plugin_disabled,
        }

        for event, callback in event_callbacks.items():
            client.register_event_handler(event, callback)

        self.previous_time = time.localtime(0)

    @maybe_coroutine
    async def on_torrent_added(self, torrent_id, from_state):
        if from_state:
            return

        status = await client.core.get_torrent_status(torrent_id, ['name', 'state'])
        self.write(
            '{!green!}Torrent Added: {!info!}%s ({!cyan!}%s{!info!})'
            % (status['name'], torrent_id)
        )
        # Write out what state the added torrent took
        self.on_torrent_state_changed(torrent_id, status['state'])

    def on_torrent_removed(self, torrent_id):
        self.write(
            '{!red!}Torrent Removed: {!info!}%s ({!cyan!}%s{!info!})'
            % (self.console.get_torrent_name(torrent_id), torrent_id)
        )

    def on_torrent_state_changed(self, torrent_id, state):
        # It's probably a new torrent, ignore it
        if not state:
            return
        # Modify the state string color
        if state in colors.state_color:
            state = colors.state_color[state] + state

        t_name = self.console.get_torrent_name(torrent_id)

        # Again, it's most likely a new torrent
        if not t_name:
            return

        self.write(f'{state}: {{!info!}}{t_name} ({{!cyan!}}{torrent_id}{{!info!}})')

    def on_torrent_finished(self, torrent_id):
        if component.get('TorrentList').config['ring_bell']:
            import curses.beep

            curses.beep()
        self.write(
            '{!info!}Torrent Finished: %s ({!cyan!}%s{!info!})'
            % (self.console.get_torrent_name(torrent_id), torrent_id)
        )

    def on_new_version_available(self, version):
        self.write('{!input!}New Deluge version available: {!info!}%s' % (version))

    def on_session_paused(self):
        self.write('{!input!}Session Paused')

    def on_session_resumed(self):
        self.write('{!green!}Session Resumed')

    def on_config_value_changed(self, key, value):
        color = '{!white,black,bold!}'
        try:
            color = colors.type_color[type(value)]
        except KeyError:
            pass

        self.write(f'ConfigValueChanged: {{!input!}}{key}: {color}{value}')

    def write(self, s):
        current_time = time.localtime()

        date_different = False
        for field in ['tm_mday', 'tm_mon', 'tm_year']:
            c = getattr(current_time, field)
            p = getattr(self.previous_time, field)
            if c != p:
                date_different = True

        if date_different:
            string = time.strftime(self.date_change_format)
            self.console.write_event(' ')
            self.console.write_event(string)

        p = time.strftime(self.prefix)

        self.console.write_event(p + s)
        self.previous_time = current_time

    def on_plugin_enabled(self, name):
        self.write('PluginEnabled: {!info!}%s' % name)

    def on_plugin_disabled(self, name):
        self.write('PluginDisabled: {!info!}%s' % name)
