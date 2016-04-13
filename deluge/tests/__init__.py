# Increase open file descriptor limit to allow tests to run
# without getting error: what():  epoll: Too many open files
from __future__ import print_function

try:
    import resource
except ImportError:  # Does not exist on Windows
    pass
else:
    try:
        resource.setrlimit(resource.RLIMIT_NOFILE, (65536, 65536))
    except (ValueError, resource.error) as ex:
        print("Failed to raise file descriptor limit:", ex)
