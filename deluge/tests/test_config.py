#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

import os
from codecs import getwriter

import pytest
from twisted.internet import task

from deluge.common import JSON_FORMAT
from deluge.config import Config

DEFAULTS = {
    'string': 'foobar',
    'int': 1,
    'float': 0.435,
    'bool': True,
    'unicode': 'foobar',
    'password': 'abc123*\\[!]?/<>#{@}=|"+$%(^)~',
}


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

    def test_get(self):
        config = Config('test.conf', config_dir=self.config_dir)
        config['foo'] = 1
        assert config.get('foo') == 1
        assert config.get('foobar') is None
        assert config.get('foobar', 2) == 2
        config['foobar'] = 5
        assert config.get('foobar', 2) == 5

    def test_load(self):
        def check_config():
            config = Config('test.conf', config_dir=self.config_dir)

            assert config['string'] == 'foobar'
            assert config['float'] == 0.435
            assert config['password'] == 'abc123*\\[!]?/<>#{@}=|"+$%(^)~'

        # Test opening a previous 1.2 config file of just a json object
        import json

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
