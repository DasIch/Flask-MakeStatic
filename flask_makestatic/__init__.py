# coding: utf-8
"""
    flask.ext.makestatic
    ~~~~~~~~~~~~~~~~~~~~~

    :copyright: 2013 by Daniel Neuhäuser
    :license: BSD, see LICENSE.rst for details
"""
import os
import re
import warnings
import subprocess
try:
    from configparser import RawConfigParser, ParsingError
except ImportError:
    from ConfigParser import RawConfigParser, ParsingError

from flask.ext.makestatic._compat import iteritems, PY2
from flask.ext.makestatic.watcher import ThreadedWatcher


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

    Once initialized :class:`MakeStatic` will parse the `assets.cfg`
    configuration file corresponding to the initialized application.
    """
    def __init__(self, app):
        self.app = app

        with self.app.open_resource('assets.cfg', 'r') as config_file:
            self.matcher, self.rulesets = self.parse_config(config_file)

    @property
    def assets_folder(self):
        return os.path.join(self.app.root_path, 'assets')

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
                config.setdefault(file_regex, []).append(rule)

        file_regexes = []
        rulesets = []
        for file_regex, rules in iteritems(config):
            file_regexes.append('(%s)' % file_regex)
            rulesets.append(rules)
        matcher = re.compile('^%s$' % '|'.join(file_regexes)).match
        return matcher, rulesets

    def get_rules(self, filename):
        match = self.matcher(filename)
        if match:
            return self.rulesets[match.lastindex - 1]

    def watch(self, sleep=0.1):
        """
        Starts a daemon thread that watches the `static` directory for changes
        and compiles the files that do change.

        Returns a :class:`ThreadedWatcher`, if you want to turn of watching you
        can call :meth:`ThreadedWatcher.stop`.

        :param sleep: The amount of time in seconds that should be slept
                      between checks for changes, may be ignored.
        """
        watcher = ThreadedWatcher()
        @watcher.file_added.connect
        def on_file_added(filename):
            print(
                u'Flask-MakeStatic: detected new asset %s, compiling' %
                os.path.relpath(filename, self.assets_folder)
            )
            self.compile_asset(filename)
        @watcher.file_modified.connect
        def on_file_modified(filename):
            print(
                u'Flask-MakeStatic: detected change in %s, compiling' %
                os.path.relpath(filename, self.assets_folder)
            )
            self.compile_asset(filename)
        watcher.add_directory(self.assets_folder)
        watcher.watch(sleep=sleep)
        self.compile() # initial compile
        return watcher

    def compile(self):
        """
        Compiles all assets to static files in one go.

        This works only when done within an application context of an
        initialized application.

        Emits a :class:`RuleMissing` warning for each file in `assets` for
        which no rule exists.
        """
        for root, _, files in os.walk(self.assets_folder):
            for file in files:
                self.compile_asset(os.path.join(root, file))

    def compile_asset(self, filename):
        relative_filename = os.path.relpath(filename, self.assets_folder)
        rules = self.get_rules(relative_filename)
        if rules is None:
            warnings.warn(
                'cannot find a rule for %s' % relative_filename,
                RuleMissing,
            )
        else:
            static = os.path.join(self.app.static_folder, relative_filename)
            static_base = os.path.splitext(static)[0]
            for rule in rules:
                subprocess.check_call(
                    rule.format(
                        asset=filename,
                        static=static,
                        static_dir=self.app.static_folder,
                        static_base=static_base
                    ),
                    shell=True
                )


__all__ = ['MakeStatic']
