import pickle
import unittest.mock as mock
from unittest.mock import MagicMock

import pytest

from deluge import component
from deluge.core.authmanager import AUTH_LEVEL_ADMIN
from deluge.core.torrent import Torrent
from deluge.core.torrentmanager import TorrentOptions, TorrentState


class MockComponent(component.Component):
    def __init__(self, name):
        super().__init__(name)

    def emit(self, *args):
        pass

    def get_session_auth_level(self):
        return AUTH_LEVEL_ADMIN


class TestRenamePersistence:
    @pytest.fixture(autouse=True)
    def setup(self, tmp_path):
        self.tmpdir = tmp_path
        self.config_dir = self.tmpdir / 'config'
        self.config_dir.mkdir(exist_ok=True)

        # Mock necessary components if they are not already registered
        for name in [
            'AlertManager',
            'RPCServer',
            'AuthManager',
            'EventManager',
            'CorePluginManager',
            'Core',
        ]:
            try:
                c = component.get(name)
            except KeyError:
                c = MockComponent(name)

            if name == 'Core':
                c.session = MagicMock()
                c.session.is_paused.return_value = False

        yield

    def test_torrent_state_mapped_files_persistence(self):
        mapped_files = {0: 'renamed_file.txt', 1: 'another_renamed.txt'}
        state = TorrentState(torrent_id='abc', mapped_files=mapped_files)

        assert hasattr(state, 'mapped_files')
        assert state.mapped_files == mapped_files

        # Test pickling
        state_file = self.tmpdir / 'torrents.state'
        with open(state_file, 'wb') as f:
            pickle.dump(state, f)

        with open(state_file, 'rb') as f:
            loaded_state = pickle.load(f)

        assert hasattr(loaded_state, 'mapped_files')
        assert loaded_state.mapped_files == mapped_files

    def test_torrent_options_mapped_files_default(self):
        # This test ensures TorrentOptions still has mapped_files defaulting to {}
        # which is important for the load_state loop.

        config_dict = {
            'max_connections_per_torrent': -1,
            'max_upload_slots_per_torrent': -1,
            'max_upload_speed_per_torrent': -1.0,
            'max_download_speed_per_torrent': -1.0,
            'move_completed': False,
            'move_completed_path': '/tmp',
            'pre_allocate_storage': False,
            'prioritize_first_last_pieces': False,
            'remove_seed_at_ratio': False,
            'sequential_download': False,
            'shared': False,
            'stop_seed_at_ratio': False,
            'stop_seed_ratio': 2.0,
            'super_seeding': False,
            'add_paused': False,
            'auto_managed': True,
            'download_location': '/tmp',
        }

        with mock.patch('deluge.core.torrent.ConfigManager') as mock_cm:
            mock_cm.return_value.config = config_dict
            options = TorrentOptions()
            assert 'mapped_files' in options
            assert options['mapped_files'] == {}

    def test_torrent_rename_updates_mapped_files(self):
        mock_handle = MagicMock()
        mock_handle.info_hash.return_value = 'abc'
        mock_handle.status().has_metadata = True
        mock_handle.status().paused = False
        mock_handle.status().state = 3  # downloading

        config_dict = {
            'max_connections_per_torrent': -1,
            'max_upload_slots_per_torrent': -1,
            'max_upload_speed_per_torrent': -1.0,
            'max_download_speed_per_torrent': -1.0,
            'move_completed': False,
            'move_completed_path': '/tmp',
            'pre_allocate_storage': False,
            'prioritize_first_last_pieces': False,
            'remove_seed_at_ratio': False,
            'sequential_download': False,
            'shared': False,
            'stop_seed_at_ratio': False,
            'stop_seed_ratio': 2.0,
            'super_seeding': False,
            'add_paused': False,
            'auto_managed': True,
            'download_location': '/tmp',
        }

        with mock.patch('deluge.core.torrent.ConfigManager') as mock_cm:
            mock_cm.return_value.config = config_dict
            torrent = Torrent(mock_handle, {})

            # Test rename_files
            torrent.rename_files([(0, 'new_name.txt')])
            assert torrent.options['mapped_files'][0] == 'new_name.txt'

            # Test rename_folder
            # Mock get_files to return some files in a folder
            torrent.get_files = MagicMock(
                return_value=[
                    {'index': 1, 'path': 'folder/file1.txt'},
                    {'index': 2, 'path': 'folder/file2.txt'},
                    {'index': 3, 'path': 'other/file3.txt'},
                ]
            )
            torrent.rename_folder('folder', 'new_folder')
            # sanitize_filepath('new_folder', folder=True) returns 'new_folder/'
            # and folder is normalized to 'folder/'
            # then .replace('folder/', 'new_folder/') results in 'new_folder/file1.txt'
            assert torrent.options['mapped_files'][1] == 'new_folder/file1.txt'
            assert torrent.options['mapped_files'][2] == 'new_folder/file2.txt'
            assert 3 not in torrent.options['mapped_files']
