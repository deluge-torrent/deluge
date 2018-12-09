# Increase open file descriptor limit to allow tests to run
# without getting error: what():  epoll: Too many open files
from __future__ import print_function, unicode_literals

from deluge.i18n import setup_translation

try:
    import resource
except ImportError:  # Does not exist on Windows
    pass
else:
    try:
        resource.setrlimit(resource.RLIMIT_NOFILE, (65536, 65536))
    except (ValueError, resource.error) as ex:
        error = 'Failed to raise file descriptor limit: %s' % ex
        # print(error)

# Initialize gettext
setup_translation()
