# coding: utf-8
"""
    flask.ext.makestatic._compat
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    :copyright: 2013 by Daniel Neuhäuser
    :license: BSD, see LICENSE.rst for details
"""
import sys


PY2 = sys.version_info[0] == 2


if PY2:
    def iteritems(d):
        return d.iteritems()

    from cStringIO import StringIO
else:
    def iteritems(d):
        return d.items()

    from io import StringIO


__all__ = ['PY2', 'iteritems', 'StringIO']
