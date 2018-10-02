from __future__ import unicode_literals


class ACTION(object):
    PAUSE = 'pause'
    RESUME = 'resume'
    REANNOUNCE = 'update_tracker'
    EDIT_TRACKERS = 3
    RECHECK = 'force_recheck'
    REMOVE = 'remove_torrent'
    REMOVE_DATA = 6
    REMOVE_NODATA = 7
    DETAILS = 'torrent_details'
    MOVE_STORAGE = 'move_download_folder'
    QUEUE = 'queue'
    QUEUE_TOP = 'queue_top'
    QUEUE_UP = 'queue_up'
    QUEUE_DOWN = 'queue_down'
    QUEUE_BOTTOM = 'queue_bottom'
    TORRENT_OPTIONS = 'torrent_options'
