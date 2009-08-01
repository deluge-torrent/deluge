from twisted.trial import unittest
from twisted.python.failure import Failure

import common

from deluge.config import Config

class ConfigTestCase(unittest.TestCase):
    def test_init(self):
        defaults = {"string": "foobar", "int": 1, "float": 0.435, "bool": True, "tuple": (1, 2)}
        
        config = Config("test.conf", defaults=defaults, config_dir=".")
        self.assertEquals(defaults, config.config)
        
        config = Config("test.conf", config_dir=".")
        self.assertEquals({}, config.config)
    
    def test_set_get_item(self):
        config = Config("test.conf", config_dir=".")
        config["foo"] = 1
        self.assertEquals(config["foo"], 1)
        self.assertRaises(ValueError, config.set_item, "foo", "bar")
        config["foo"] = 2
        self.assertEquals(config.get_item("foo"), 2)
        
        config._save_timer.cancel()

    def test_load(self):
        d = {"string": "foobar", "int": 1, "float": 0.435, "bool": True, "tuple": (1, 2)}

        def check_config():
            config = Config("test.conf", config_dir=".")
            
            self.assertEquals(config["string"], "foobar")
            self.assertEquals(config["float"], 0.435)
                
        # Test loading an old config from 1.1.x
        import pickle
        pickle.dump(d, open("test.conf", "wb"))
        
        check_config()
                
        # Test opening a previous 1.2 config file of just a json object
        import json
        json.dump(d, open("test.conf", "wb"), indent=2)

        check_config()
        
        # Test opening a previous 1.2 config file of having the format versions
        # as ints
        f = open("test.conf", "wb")
        f.write(str(1) + "\n")
        f.write(str(1) + "\n")
        json.dump(d, f, indent=2)
        f.close()
        
        check_config()
        
        # Test the 1.2 config format
        v = {"format": 1, "file": 1}
        f = open("test.conf", "wb")
        json.dump(v, f, indent=2)
        json.dump(d, f, indent=2)
        f.close()
        
        check_config()
