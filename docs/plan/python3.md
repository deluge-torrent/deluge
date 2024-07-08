# Python 3 Port

This page provides more detailed information on porting to Python 3 started in ticket [#1328](https://dev.deluge-torrent.org/ticket/1328).

The current consensus is that the core and common files should be prepared for a future Twisted release with full Python 3 support and UI's worked on at a later date.

## References

It is best to read these other documents on Python 3 porting

[Django](https://docs.djangoproject.com/en/dev/topics/python3/)
[https://wiki.ubuntu.com/Python/3](https://wiki.ubuntu.com/Python/3)
[https://twistedmatrix.com/trac/wiki/Plan/Python3](https://twistedmatrix.com/trac/wiki/Plan/Python3)

## Twisted
Deluge relies on all dependant packages supporting Python 3 with Twisted being the most crucial and support is just about complete: [Twisted Python 3 Plan](https://twistedmatrix.com/trac/wiki/Plan/Python3).

Another option for Twisted is to remove the use of it in favour of Python 3's [asyncio](https://docs.python.org/dev/library/asyncio.html).  This would, of course, remove backwards compatibility with Python 2 and require a lot of work to port to asyncio, but could be worthwhile in the end.

## 2to3

Using [python-future](http://python-future.org/) is the best option to convert the code.

## Required changes

* Magic Method `__cmp__` in `common.py` replaced with `__lt__`
* `iteritems()` where needed replace with try/except: http://python3porting.com/differences.html#dictionary-methods

## Future Imports

 `from `__future__` import unicode_literals`::
    Likely to be applied to all files to ensure byte, Unicode string separation

 `from `__future__` import division` *and* `from `__future__` import print_function`::
    Added to files where required

 `from `__future__` import absolute_import`::
    Should not be required if the imports are properly set up. See: http://python3porting.com/differences.html#imports

## Compatibility Module

It will be easier and simpler to use either `future` or `six` (see [py-future](http://python-future.org/faq.html#what-is-the-relationship-between-future-and-six) docs) to write compatible code.


