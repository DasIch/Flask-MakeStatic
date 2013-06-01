# coding: utf-8
"""
    flask.ext.makestatic
    ~~~~~~~~~~~~~~~~~~~~~

    :copyright: 2013 by Daniel Neuhäuser
    :license: BSD, see LICENSE.rst for details
"""
import os
import re
import errno
import warnings
import subprocess
from functools import wraps
try:
    from configparser import RawConfigParser, ParsingError
except ImportError:
    from ConfigParser import RawConfigParser, ParsingError

from flask import current_app
from flask.ext.makestatic._compat import iteritems, PY2


def get_rule(filename):
    try:
        matcher, rules = current_app.extensions['MakeStatic']
    except KeyError:
        raise RuntimeError('current application not initialized')
    match = matcher(filename)
    if match:
        return rules[match.lastindex - 1]


def get_static_path(filename):
    return os.path.join(current_app.static_folder, filename)


def get_assets_path():
    return os.path.join(current_app.root_path, 'assets')


def get_asset_path(filename):
    return os.path.join(get_assets_path(), filename)


def compile(rule, asset, static):
    subprocess.check_call(rule.format(asset=asset, static=static), shell=True)


def is_newer(checked, against):
    try:
        against = os.stat(against).st_mtime
    except OSError as error:
        if error.errno == errno.ENOENT:
            against = -1
        else:
            raise
    return os.stat(checked).st_mtime > against


def wrap_send_static_file(app):
    @wraps(app.send_static_file.__func__)
    def send_static_file(self, filename):
        rule = get_rule(filename)
        if rule is not None:
            static = get_static_path(filename)
            asset = get_asset_path(filename)
            try:
                newer = is_newer(asset, static)
            except OSError:
                pass # asset does not exist
            else:
                if newer:
                    compile(rule, asset, static)
        return super(self.__class__, self).send_static_file(filename)
    app.send_static_file = send_static_file.__get__(app, app.__class__)
    app.view_functions['static'] = app.send_static_file


class RuleMissing(Warning):
    """
    Warning that is emitted if a rule cannot be found.
    """


class MakeStatic(object):
    """
    This class provides the extension interface. You can use it by calling it
    directly with a :class:`flask.Flask` instance::

        app = Flask(__name__)
        make_static = MakeStatic(app)

    or by creating an instance and calling :meth:`init_app` later::

        make_static = MakeStatic()

        # somewhere else in the application
        app = Flask(__name__)
        make_static.init_app(app)

    Once initialized :class:`MakeStatic` will parse the `assets.cfg`
    configuration file corresponding to the initialized application and
    replaces :meth:`flask.Flask.send_static_file` with a version that compiles
    assets on demand.

    This is very useful during development and may be a feasable approach even
    on low traffic sites. In production you probably do not want to compile
    assets on demand and instead compile them all at once as part of
    deployment, to do so simply call :meth:`compile`.
    """
    def __init__(self, app=None):
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        """
        Initializes the given :class:`~flask.Flask` instance. Use this if you
        want to use the :class:`MakeStatic` instance before creating a flask
        application.
        """
        with app.open_resource('assets.cfg', 'r') as config_file:
            app.extensions['MakeStatic'] = self.parse_config(config_file)
        wrap_send_static_file(app)

    def parse_config(self, config_file):
        parser = RawConfigParser(allow_no_value=True)
        if PY2:
            parser.readfp(config_file)
        else:
            parser.read_file(config_file)
        config = {}
        for file_regex in parser.sections():
            for rule in parser.options(file_regex):
                if parser.get(file_regex, rule) is not None:
                    raise ParsingError('unexpected value for %r' % file_regex)
                config[file_regex] = rule

        file_regexes = []
        rules = []
        for file_regex, rule in iteritems(config):
            file_regexes.append('(%s)' % file_regex)
            rules.append(rule)
        matcher = re.compile('^%s$' % '|'.join(file_regexes)).match
        return matcher, rules

    def compile(self):
        """
        Compiles all assets to static files in one go.

        This works only when done within an application context of an
        initialized application.

        Emits a :class:`RuleMissing` warning for each file in `assets` for
        which no rule exists.
        """
        assets = get_assets_path()
        for root, _, files in os.walk(assets):
            for file in files:
                file = os.path.join(root, file)
                relative_file = os.path.relpath(file, assets)
                rule = get_rule(relative_file)
                if rule is None:
                    warnings.warn(
                        'cannot find a rule for %s' % relative_file,
                        RuleMissing,
                    )
                else:
                    compile(rule, file, get_static_path(relative_file))


__all__ = ['MakeStatic']
