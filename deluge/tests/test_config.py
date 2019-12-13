# -*- coding: utf-8 -*-
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

from __future__ import unicode_literals

import os
from codecs import getwriter

from twisted.internet import task
from twisted.trial import unittest

import deluge.config
from deluge.common import JSON_FORMAT
from deluge.config import Config

from .common import set_tmp_config_dir

DEFAULTS = {
    'string': 'foobar',
    'int': 1,
    'float': 0.435,
    'bool': True,
    'unicode': 'foobar',
    'password': 'abc123*\\[!]?/<>#{@}=|"+$%(^)~',
}


class ConfigTestCase(unittest.TestCase):
    def setUp(self):  # NOQA: N803
        self.config_dir = set_tmp_config_dir()

    def test_init(self):
        config = Config('test.conf', defaults=DEFAULTS, config_dir=self.config_dir)
        self.assertEqual(DEFAULTS, config.config)

        config = Config('test.conf', config_dir=self.config_dir)
        self.assertEqual({}, config.config)

    def test_set_get_item(self):
        config = Config('test.conf', config_dir=self.config_dir)
        config['foo'] = 1
        self.assertEqual(config['foo'], 1)
        self.assertRaises(ValueError, config.set_item, 'foo', 'bar')

        config['foo'] = 2
        self.assertEqual(config.get_item('foo'), 2)

        config['foo'] = '3'
        self.assertEqual(config.get_item('foo'), 3)

        config['unicode'] = 'ВИДЕОФИЛЬМЫ'
        self.assertEqual(config['unicode'], 'ВИДЕОФИЛЬМЫ')

        config['unicode'] = b'foostring'
        self.assertFalse(isinstance(config.get_item('unicode'), bytes))

        config._save_timer.cancel()

    def test_set_get_item_none(self):
        config = Config('test.conf', config_dir=self.config_dir)

        config['foo'] = None
        self.assertIsNone(config['foo'])
        self.assertIsInstance(config['foo'], type(None))

        config['foo'] = 1
        self.assertEqual(config.get('foo'), 1)

        config['foo'] = None
        self.assertIsNone(config['foo'])

        config['bar'] = None
        self.assertIsNone(config['bar'])

        config['bar'] = None
        self.assertIsNone(config['bar'])

        config._save_timer.cancel()

    def test_get(self):
        config = Config('test.conf', config_dir=self.config_dir)
        config['foo'] = 1
        self.assertEqual(config.get('foo'), 1)
        self.assertEqual(config.get('foobar'), None)
        self.assertEqual(config.get('foobar', 2), 2)
        config['foobar'] = 5
        self.assertEqual(config.get('foobar', 2), 5)

    def test_load(self):
        def check_config():
            config = Config('test.conf', config_dir=self.config_dir)

            self.assertEqual(config['string'], 'foobar')
            self.assertEqual(config['float'], 0.435)
            self.assertEqual(config['password'], 'abc123*\\[!]?/<>#{@}=|"+$%(^)~')

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
        self.assertTrue(ret)
        ret = config.save()
        self.assertTrue(ret)

        config['string'] = 'baz'
        config['int'] = 2
        ret = config.save()
        self.assertTrue(ret)
        del config

        config = Config('test.conf', defaults=DEFAULTS, config_dir=self.config_dir)
        self.assertEqual(config['string'], 'baz')
        self.assertEqual(config['int'], 2)

    def test_save_timer(self):
        self.clock = task.Clock()
        deluge.config.callLater = self.clock.callLater

        config = Config('test.conf', defaults=DEFAULTS, config_dir=self.config_dir)
        config['string'] = 'baz'
        config['int'] = 2
        self.assertTrue(config._save_timer.active())

        # Timeout set for 5 seconds in config, so lets move clock by 5 seconds
        self.clock.advance(5)

        def check_config(config):
            self.assertTrue(not config._save_timer.active())
            del config
            config = Config('test.conf', defaults=DEFAULTS, config_dir=self.config_dir)
            self.assertEqual(config['string'], 'baz')
            self.assertEqual(config['int'], 2)

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
        self.assertEqual(len(objects), 2)

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
        self.assertEqual(len(objects), 2)

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
        self.assertEqual(len(objects), 2)
