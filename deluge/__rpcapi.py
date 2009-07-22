from new import classobj
from deluge.core.core import Core
from deluge.core.daemon import Daemon

class RpcApi:
    pass

def scan_for_methods(obj):
    methods = {
        '__doc__': 'Methods available in %s' % obj.__name__.lower()
    }
    for d in dir(obj):
        if not hasattr(getattr(obj,d), '_rpcserver_export'):
            continue
        methods[d] = getattr(obj, d)
    cobj = classobj(obj.__name__.lower(), (object,), methods)
    setattr(RpcApi, obj.__name__.lower(), cobj)

scan_for_methods(Core)
scan_for_methods(Daemon)