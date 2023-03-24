#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

import json
import logging
import os
from codecs import getwriter

import pytest
from twisted.internet import task

from deluge.common import JSON_FORMAT
from deluge.config import Config
from deluge.ui.hostlist import mask_hosts_password

DEFAULTS = {
    'string': 'foobar',
    'int': 1,
    'float': 0.435,
    'bool': True,
    'unicode': 'foobar',
    'password': 'abc123*\\[!]?/<>#{@}=|"+$%(^)~',
    'hosts': [
        ('host1', 'port', '', 'password1234'),
        ('host2', 'port', '', 'password5678'),
    ],
}


LOGGER = logging.getLogger(__name__)


class TestConfig:
    def test_init(self):
        config = Config('test.conf', defaults=DEFAULTS, config_dir=self.config_dir)
        assert DEFAULTS == config.config

        config = Config('test.conf', config_dir=self.config_dir)
        assert {} == config.config

    def test_set_get_item(self):
        config = Config('test.conf', config_dir=self.config_dir)
        config['foo'] = 1
        assert config['foo'] == 1
        with pytest.raises(ValueError):
            config.set_item('foo', 'bar')

        config['foo'] = 2
        assert config.get_item('foo') == 2

        config['foo'] = '3'
        assert config.get_item('foo') == 3

        config['unicode'] = 'ВИДЕОФИЛЬМЫ'
        assert config['unicode'] == 'ВИДЕОФИЛЬМЫ'

        config['unicode'] = b'foostring'
        assert not isinstance(config.get_item('unicode'), bytes)

        config._save_timer.cancel()

    def test_set_get_item_none(self):
        config = Config('test.conf', config_dir=self.config_dir)

        config['foo'] = None
        assert config['foo'] is None
        assert isinstance(config['foo'], type(None))

        config['foo'] = 1
        assert config.get('foo') == 1

        config['foo'] = None
        assert config['foo'] is None

        config['bar'] = None
        assert config['bar'] is None

        config['bar'] = None
        assert config['bar'] is None

        config._save_timer.cancel()

    async def test_on_changed_callback(self, mock_callback):
        config = Config('test.conf', config_dir=self.config_dir)
        config.register_change_callback(mock_callback)
        config['foo'] = 1
        assert config['foo'] == 1
        await mock_callback.deferred
        mock_callback.assert_called_once_with('foo', 1)

    async def test_key_function_callback(self, mock_callback):
        config = Config(
            'test.conf', defaults={'foo': 1, 'bar': 1}, config_dir=self.config_dir
        )

        assert config['foo'] == 1
        config.register_set_function('foo', mock_callback)
        await mock_callback.deferred
        mock_callback.assert_called_once_with('foo', 1)

        mock_callback.reset_mock()
        config.register_set_function('bar', mock_callback, apply_now=False)
        mock_callback.assert_not_called()
        config['bar'] = 2
        await mock_callback.deferred
        mock_callback.assert_called_once_with('bar', 2)

    def test_get(self):
        config = Config('test.conf', config_dir=self.config_dir)
        config['foo'] = 1
        assert config.get('foo') == 1
        assert config.get('foobar') is None
        assert config.get('foobar', 2) == 2
        config['foobar'] = 5
        assert config.get('foobar', 2) == 5

    def test_set_log_mask_funcs(self, caplog):
        """Test mask func masks key in log"""
        caplog.set_level(logging.DEBUG)
        config = Config(
            'test.conf',
            config_dir=self.config_dir,
            log_mask_funcs={'hosts': mask_hosts_password},
        )
        config['hosts'] = DEFAULTS['hosts']
        assert isinstance(config['hosts'], list)
        assert 'host1' in caplog.text
        assert 'host2' in caplog.text
        assert 'password1234' not in caplog.text
        assert 'password5678' not in caplog.text
        assert '*' * 10 in caplog.text

    def test_load_log_mask_funcs(self, caplog):
        """Test mask func masks key in log"""
        with open(os.path.join(self.config_dir, 'test.conf'), 'wb') as _file:
            json.dump(DEFAULTS, getwriter('utf8')(_file), **JSON_FORMAT)

        config = Config(
            'test.conf',
            config_dir=self.config_dir,
            log_mask_funcs={'hosts': mask_hosts_password},
        )
        with caplog.at_level(logging.DEBUG):
            config.load(os.path.join(self.config_dir, 'test.conf'))
        assert 'host1' in caplog.text
        assert 'host2' in caplog.text
        assert 'foobar' in caplog.text
        assert 'password1234' not in caplog.text
        assert 'password5678' not in caplog.text
        assert '*' * 10 in caplog.text

    def test_load(self):
        def check_config():
            config = Config('test.conf', config_dir=self.config_dir)

            assert config['string'] == 'foobar'
            assert config['float'] == 0.435
            assert config['password'] == 'abc123*\\[!]?/<>#{@}=|"+$%(^)~'

        # Test opening a previous 1.2 config file of just a json object
        with open(os.path.join(self.config_dir, 'test.conf'), 'wb') as _file:
            json.dump(DEFAULTS, getwriter('utf8')(_file), **JSON_FORMAT)

        check_config()

        # Test opening a previous 1.2 config file of having the format versions
        # as ints
        with open(os.path.join(self.config_dir, 'test.conf'), 'wb') as _file:
            _file.write(b'1\n')
            _file.write(b'1\n')
            json.dump(DEFAULTS, getwriter('utf8')(_file), **JSON_FORMAT)

        check_config()

        # Test the 1.2 config format
        version = {'format': 1, 'file': 1}
        with open(os.path.join(self.config_dir, 'test.conf'), 'wb') as _file:
            json.dump(version, getwriter('utf8')(_file), **JSON_FORMAT)
            json.dump(DEFAULTS, getwriter('utf8')(_file), **JSON_FORMAT)

        check_config()

    def test_save(self):
        config = Config('test.conf', defaults=DEFAULTS, config_dir=self.config_dir)
        # We do this twice because the first time we need to save the file to disk
        # and the second time we do a compare and we should not write
        ret = config.save()
        assert ret
        ret = config.save()
        assert ret

        config['string'] = 'baz'
        config['int'] = 2
        ret = config.save()
        assert ret
        del config

        config = Config('test.conf', defaults=DEFAULTS, config_dir=self.config_dir)
        assert config['string'] == 'baz'
        assert config['int'] == 2

    def test_save_timer(self):
        clock = task.Clock()

        config = Config('test.conf', defaults=DEFAULTS, config_dir=self.config_dir)
        config.callLater = clock.callLater
        config['string'] = 'baz'
        config['int'] = 2
        assert config._save_timer.active()

        # Timeout set for 5 seconds in config, so lets move clock by 5 seconds
        clock.advance(5)

        def check_config(config):
            assert not config._save_timer.active()
            del config
            config = Config('test.conf', defaults=DEFAULTS, config_dir=self.config_dir)
            assert config['string'] == 'baz'
            assert config['int'] == 2

        check_config(config)

    def test_find_json_objects(self):
        s = """{
  "file": 1,
  "format": 1
}{
  "ssl": true,
  "enabled": false,
  "port": 8115
}\n"""

        from deluge.config import find_json_objects

        objects = find_json_objects(s)
        assert len(objects) == 2

    def test_find_json_objects_curly_brace(self):
        """Test with string containing curly brace"""
        s = """{
  "file": 1,
  "format": 1
}{
  "ssl": true,
  "enabled": false,
  "port": 8115,
  "password": "abc{def"
}"""

        from deluge.config import find_json_objects

        objects = find_json_objects(s)
        assert len(objects) == 2

    def test_find_json_objects_double_quote(self):
        """Test with string containing double quote"""
        s = r"""{
  "file": 1,
  "format": 1
}{
  "ssl": true,
  "enabled": false,
  "port": 8115,
  "password": "abc\"def"
}
"""

        from deluge.config import find_json_objects

        objects = find_json_objects(s)
        assert len(objects) == 2
