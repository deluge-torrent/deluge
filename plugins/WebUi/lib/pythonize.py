"""
some dbus to python type conversions
-decorator for interface
-wrapper class for proxy
"""
def pythonize(var):
    """translates dbus types back to basic python  types."""
    if isinstance(var, list):
        return [pythonize(value) for value in var]
    if isinstance(var, tuple):
        return tuple([pythonize(value) for value in var])
    if isinstance(var, dict):
        return dict(
        [(pythonize(key), pythonize(value)) for key, value in var.iteritems()]
        )

    for klass in [unicode, str, bool, int, float, long]:
        if isinstance(var,klass):
            return klass(var)
    return var

def pythonize_call(func):
    def deco(*args,**kwargs):
        return pythonize(func(*args, **kwargs))
    return deco

def pythonize_interface(func):
    def deco(*args, **kwargs):
        args = pythonize(args)
        kwargs = pythonize(kwargs)
        return func(*args, **kwargs)
    return deco

class PythonizeProxy(object):
    def __init__(self,proxy):
        self.proxy = proxy
    def __getattr__(self, key):
        return pythonize_call(getattr(self.proxy, key))
