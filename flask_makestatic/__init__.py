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

from flask.ext.makestatic.watcher import ThreadedWatcher


__version__ = '0.1.0'
__version_info__ = (0, 1, 0)


_section_re = re.compile(r"\[(?P<file_re>[^\]]+)\]")
_command_re = re.compile(r'\s*(?P<command>.*?)\s*$')


class RuleMissing(Warning):
    """
    Warning that is emitted if a rule cannot be found.
    """


class ParsingError(Exception):
    def __init__(self, message, line, lineno):
        Exception.__init__(self, message, line, lineno)
        self.message = message
        self.line = line
        self.lineno = lineno


class _ConfigParser(object):
    def __init__(self, file):
        self.file = file
        self.lines = list(self.stripped_comments(enumerate(file, start=1)))

    def stripped_comments(self, lines):
        for lineno, line in lines:
            if '#' in line:
                comment_start = line.index('#')
                line = line[:comment_start].rstrip()
                if not line:
                    continue
            elif not line.strip():
                continue
            yield lineno, line

    def next_line(self):
        return self.lines.pop(0)

    def parse_rule(self):
        try:
            lineno, line = self.next_line()
        except IndexError:
            return
        match = _section_re.match(line)
        if match is None:
            raise ParsingError('expected new rule', line, lineno)
        regex = match.group('file_re')
        commands = []
        insert = False
        while True:
            try:
                lineno, line = self.next_line()
            except IndexError:
                break
            if _section_re.match(line):
                insert = True
                break
            commands.append(line.strip())
        if insert:
            self.lines.insert(0, (lineno, line))
        return regex, commands

    def parse(self):
        while True:
            result = self.parse_rule()
            if result is None:
                break
            yield result


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
        file_regexes = []
        rulesets = []
        for file_regex, rules in _ConfigParser(config_file).parse():
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

        When run in a process started by the reloader, this does nothing to
        prevent the start of an unnecessary second watcher.

        :param sleep: The amount of time in seconds that should be slept
                      between checks for changes, may be ignored.
        """
        if os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
            # We are running in the Werkzeug reloader, which runs the setup
            # code twice (don't ask) which means we are called twice. This
            # means that the Watcher is also created twice and we compile all
            # assets twice. That is annoying to say the least, so we just
            # return and do nothing.
            return
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
