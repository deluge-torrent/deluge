from twisted.trial import unittest
from twisted.python.failure import Failure

import common
import os

from deluge.config import Config

DEFAULTS = {"string": "foobar", "int": 1, "float": 0.435, "bool": True, "tuple": (1, 2)}

class ConfigTestCase(unittest.TestCase):
    def setUp(self):
        self.config_dir = common.set_tmp_config_dir()

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
        
        config._save_timer.cancel()

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
        config["string"] = "baz"
        config["int"] = 2
        ret = config.save()
        self.assertTrue(ret)
        del config
        
        config = Config("test.conf", defaults=DEFAULTS, config_dir=self.config_dir)
        self.assertEquals(config["string"], "baz")
        self.assertEquals(config["int"], 2)

    def test_save_timer(self):
        config = Config("test.conf", defaults=DEFAULTS, config_dir=self.config_dir)
        config["string"] = "baz"
        config["int"] = 2
        self.assertTrue(config._save_timer.active())
        
        def check_config(config):
            self.assertTrue(not config._save_timer.active())
            del config
            config = Config("test.conf", defaults=DEFAULTS, config_dir=self.config_dir)
            self.assertEquals(config["string"], "baz")
            self.assertEquals(config["int"], 2)
            
        from twisted.internet.task import deferLater
        from twisted.internet import reactor
        d = deferLater(reactor, 7, check_config, config)
        return d
        
