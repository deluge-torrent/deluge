# -*- coding: utf-8 -*-

import os

from twisted.internet import task
from twisted.trial import unittest

import deluge.config
from deluge.config import Config

from .common import set_tmp_config_dir

DEFAULTS = {"string": "foobar", "int": 1, "float": 0.435, "bool": True, "unicode": u"foobar"}


class ConfigTestCase(unittest.TestCase):
    def setUp(self):  # NOQA
        self.config_dir = set_tmp_config_dir()

    def test_init(self):
        config = Config("test.conf", defaults=DEFAULTS, config_dir=self.config_dir)
        self.assertEquals(DEFAULTS, config.config)

        config = Config("test.conf", config_dir=self.config_dir)
        self.assertEquals({}, config.config)

    def test_set_get_item(self):
        config = Config("test.conf", config_dir=self.config_dir)
        config["foo"] = 1
        self.assertEquals(config["foo"], 1)
        self.assertRaises(ValueError, config.set_item, "foo", "bar")

        config["foo"] = 2
        self.assertEquals(config.get_item("foo"), 2)

        config["foo"] = "3"
        self.assertEquals(config.get_item("foo"), 3)

        config["unicode"] = u"ВИДЕОФИЛЬМЫ"
        self.assertEquals(config["unicode"], u"ВИДЕОФИЛЬМЫ")

        config["unicode"] = "foostring"
        self.assertTrue(isinstance(config.get_item("unicode"), unicode))

        config._save_timer.cancel()

    def test_set_get_item_none(self):
        config = Config("test.conf", config_dir=self.config_dir)

        config["foo"] = None
        self.assertIsNone(config["foo"])
        self.assertIsInstance(config["foo"], type(None))

        config["foo"] = 1
        self.assertEquals(config.get("foo"), 1)

        config["foo"] = None
        self.assertIsNone(config["foo"])

        config["bar"] = None
        self.assertIsNone(config["bar"])

        config["bar"] = None
        self.assertIsNone(config["bar"])

        config._save_timer.cancel()

    def test_get(self):
        config = Config("test.conf", config_dir=self.config_dir)
        config["foo"] = 1
        self.assertEquals(config.get("foo"), 1)
        self.assertEquals(config.get("foobar"), None)
        self.assertEquals(config.get("foobar", 2), 2)
        config["foobar"] = 5
        self.assertEquals(config.get("foobar", 2), 5)

    def test_load(self):
        def check_config():
            config = Config("test.conf", config_dir=self.config_dir)

            self.assertEquals(config["string"], "foobar")
            self.assertEquals(config["float"], 0.435)

        # Test loading an old config from 1.1.x
        import pickle
        pickle.dump(DEFAULTS, open(os.path.join(self.config_dir, "test.conf"), "wb"))

        check_config()

        # Test opening a previous 1.2 config file of just a json object
        import json
        json.dump(DEFAULTS, open(os.path.join(self.config_dir, "test.conf"), "wb"), indent=2)

        check_config()

        # Test opening a previous 1.2 config file of having the format versions
        # as ints
        f = open(os.path.join(self.config_dir, "test.conf"), "wb")
        f.write(str(1) + "\n")
        f.write(str(1) + "\n")
        json.dump(DEFAULTS, f, indent=2)
        f.close()

        check_config()

        # Test the 1.2 config format
        v = {"format": 1, "file": 1}
        f = open(os.path.join(self.config_dir, "test.conf"), "wb")
        json.dump(v, f, indent=2)
        json.dump(DEFAULTS, f, indent=2)
        f.close()

        check_config()

    def test_save(self):
        config = Config("test.conf", defaults=DEFAULTS, config_dir=self.config_dir)
        # We do this twice because the first time we need to save the file to disk
        # and the second time we do a compare and we should not write
        ret = config.save()
        self.assertTrue(ret)
        ret = config.save()
        self.assertTrue(ret)

        config["string"] = "baz"
        config["int"] = 2
        ret = config.save()
        self.assertTrue(ret)
        del config

        config = Config("test.conf", defaults=DEFAULTS, config_dir=self.config_dir)
        self.assertEquals(config["string"], "baz")
        self.assertEquals(config["int"], 2)

    def test_save_timer(self):
        self.clock = task.Clock()
        deluge.config.callLater = self.clock.callLater

        config = Config("test.conf", defaults=DEFAULTS, config_dir=self.config_dir)
        config["string"] = "baz"
        config["int"] = 2
        self.assertTrue(config._save_timer.active())

        # Timeout set for 5 seconds in config, so lets move clock by 5 seconds
        self.clock.advance(5)

        def check_config(config):
            self.assertTrue(not config._save_timer.active())
            del config
            config = Config("test.conf", defaults=DEFAULTS, config_dir=self.config_dir)
            self.assertEquals(config["string"], "baz")
            self.assertEquals(config["int"], 2)

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
        self.assertEquals(len(objects), 2)
