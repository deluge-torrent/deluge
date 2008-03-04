"""
torrent-organize core plugin.

adds a status field for tracker.
"""

from deluge.log import LOG as log
from deluge.plugins.corepluginbase import CorePluginBase

from urlparse import urlparse

STATE_FILTERS =   {
    'Allocating': lambda t: (t.state == 'Allocating'),
    'Checking': lambda t: (t.state == 'Checking'),
    'Downloading': lambda t: (t.state == 'Downloadig'),
    'Seeding':lambda t: (t.state == 'Seeding'),
    'Paused':lambda t: (t.state == 'Paused'),
    'Error':lambda t: (t.state == 'Error'),
    'Queued':lambda t: (t.state == 'Queued')
    #'Traffic':lambda t: (t.download_payload_rate > 0 or  t.upload_payload_rate  > 0)
}

class Core(CorePluginBase):
    def enable(self):
        log.info("*** START Organize plugin***")

        self.plugin.register_status_field("tracker_name", self._status_get_tracker)
        log.debug("Organize plugin enabled..")

        #__init__....
        core = self.plugin.get_core()
        self.torrents = core.torrents.torrents

    def disable(self):
        # De-register the label field

        self.plugin.deregister_status_field("tracker_name")

    def update(self):
        pass


    ## Utils ##
    def get_tracker(self, torrent):
        "returns 1st tracker."
        log.debug(torrent)
        log.debug(torrent.trackers)
        if not torrent.trackers:
            return 'tracker-less'
        url = urlparse(torrent.trackers[0]['url'])
        if hasattr(url,'hostname'):
            return (url.hostname or 'unknown?')
        return 'No-tracker?'

    ## Filters ##
    def filter_state(self, torrents, state):
        "in/out: a list of torrent objects."
        filter_func = STATE_FILTERS[state]
        return [t for t in torrents if filter_func(t)]

    def filter_tracker(self, torrents, tracker):
        "in/out: a list of torrent objects."
        return [t for t in torrents if self.get_tracker(t) == tracker]

    def filter_keyword(self, torrents, keyword):
        "in/out: a list of torrent objects."
        return [t for t in torrents if keyword in t.filename.lower()]

    ## Public  ##
    def export_state_filter_items(self):
        """
        returns a sorted list of tuples:
        [(state, count), ...]
        """
        #maybe I should explain this.. ..
        #or just fix it to be less generic, and more readable.
        return  [("All", len(self.torrents))] + [
            (state, len(self.filter_state(self.torrents.values(), state)))
            for state in STATE_FILTERS]

    def export_tracker_filter_items(self):
        """
        returns a sorted list of tuples:
        [(tracker_name, count), ...]
        """
        trackers = [self.get_tracker(t) for t in self.torrents.values()]
        tcounter = {}
        for tracker in trackers:
            tcounter[tracker] = tcounter.get(tracker,0) + 1
        #tcounter= {'tracker-name':count, ...}
        return sorted([x for x in tcounter.iteritems()])

    def export_all_filter_items(self):
            """
            for sclient, returns:{
                'tracker':<tracker_items>,
                'state':<state_items>}
            """
            return {
                'tracker':self.export_tracker_filter_items(),
                'state':self.export_state_filter_items()
            }

    def export_get_session_state(self,filter_dict):
        """
        in: a dict of filters:
        {
        'keyword':'a keyword',
        'state':'Seeding',
        'tracker':'tracker.aelitis.com'
        }
        returns a list of torrent_id's
        """
        torrents = self.torrents.values()

        if 'keyword' in filter_dict:
            filter_dict['keyword'] = filter_dict['keyword'].lower()
            torrents = self.filter_keyword(torrents, filter_dict['keyword'])

        if 'state' in filter_dict and filter_dict['state'] <> "All":
            torrents = self.filter_state(torrents, filter_dict['state'])

        if 'tracker' in filter_dict:
            torrents = self.filter_tracker(torrents, filter_dict['tracker'])

        return [t.torrent_id for t in torrents]


    ## Status fields ##
    def _status_get_tracker(self, torrent_id):
        return self.get_tracker(self.torrents[torrent_id])

if __name__ == "__main__":
    import test

