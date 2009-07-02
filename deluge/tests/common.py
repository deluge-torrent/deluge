import tempfile

import deluge.configmanager
import deluge.log

deluge.log.setupLogger()
config_directory = tempfile.mkdtemp()
deluge.configmanager.set_config_dir(config_directory)
