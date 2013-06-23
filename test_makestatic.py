# coding: utf-8
import os
import sys
import time
import atexit
import shutil
import tempfile
import unittest
import threading
from warnings import catch_warnings
from contextlib import closing, contextmanager

from flask import Flask
from werkzeug.exceptions import NotFound

from flask.ext.makestatic import MakeStatic, RuleMissing
from flask.ext.makestatic._compat import StringIO
from flask.ext.makestatic.watcher import ThreadedWatcher


TEST_APPS = os.path.join(os.path.dirname(__file__), 'test_apps')
sys.path.insert(0, TEST_APPS)


def get_temporary_filename(directory=None):
    filename = tempfile.mkstemp(dir=directory)[1]
    @atexit.register
    def remove_file():
        try:
            os.remove(filename)
        except EnvironmentError:
            pass
    return filename


def get_temporary_directory():
    directory = tempfile.mkdtemp()
    @atexit.register
    def remove_directory():
        try:
            shutil.rmtree(directory)
        except EnvironmentError:
            pass
    return directory


def bump_modification_time(path):
    stat = os.stat(path)
    os.utime(path, (stat.st_atime, stat.st_mtime + 1))


@contextmanager
def catch_stdout():
    old_stdout = sys.stdout
    sys.stdout = rv = StringIO()
    try:
        yield rv
    finally:
        sys.stdout = old_stdout


class MakeStaticTestCase(unittest.TestCase):
    def tearDown(self):
        for test_app_dir in os.listdir(TEST_APPS):
            static_dir = os.path.join(TEST_APPS, test_app_dir, 'static')
            if os.path.isdir(static_dir):
                for root, dirs, files in os.walk(static_dir, topdown=False):
                    for file in files:
                        if file == '.gitignore':
                            continue
                        os.remove(os.path.join(root, file))
                    for dir in dirs:
                        os.rmdir(os.path.join(root, dir))

    @contextmanager
    def make_static(self, import_name, config=None):
        app = Flask(import_name)
        if config is not None:
            app.config.update(config)
        make_static = MakeStatic(app)
        watcher = make_static.watch(sleep=0.01)
        try:
            yield app, make_static
        finally:
            watcher.stop()

    @contextmanager
    def make_static_in_app_context(self, import_name, config=None):
        app = Flask(import_name)
        if config is not None:
            app.config.update(config)
        make_static = MakeStatic()
        make_static.init_app(app)
        with app.app_context():
            watcher = make_static.watch(sleep=0.01)
            try:
                yield app, make_static
            finally:
                watcher.stop()

    def get_watcher_contexts(self, import_name, config=None):
        yield self.make_static(import_name, config)
        yield self.make_static_in_app_context(import_name, config)

    def test_send_static_file(self):
        for context in self.get_watcher_contexts('working'):
            with context as (app, make_static):
                with app.test_request_context():
                    with closing(app.send_static_file('foo')) as response:
                        self.assertEqual(response.status_code, 200)

                    with closing(app.send_static_file('spam')) as response:
                        self.assertEqual(response.status_code, 200)

                    with closing(app.send_static_file('bar')) as response:
                        self.assertEqual(response.status_code, 200)
                        response.direct_passthrough = False
                        self.assertEqual(response.data, b'abc\ndef\n')

                    self.assertRaises(NotFound, app.send_static_file, 'baz')

                    with closing(app.send_static_file('eggs.css')) as response:
                        self.assertEqual(response.status_code, 200)

                    with catch_warnings(record=True): # silence RuleMissing warning
                        with catch_stdout() as stdout:
                            filename = os.path.basename(get_temporary_filename(
                                directory=make_static.assets_folder
                            ))
                            time.sleep(0.05)

                    self.assertEqual(
                        stdout.getvalue(),
                        'Flask-MakeStatic: detected new asset %s, compiling\n' %
                        filename
                    )

                    self.assertRaises(NotFound, app.send_static_file, filename)

                    with catch_stdout() as stdout:
                        bump_modification_time(
                            os.path.join(make_static.assets_folder, 'foo')
                        )
                        time.sleep(0.05)

                    self.assertEqual(
                        stdout.getvalue(),
                        'Flask-MakeStatic: detected change in foo, compiling\n'
                    )

                    with closing(app.send_static_file('foo')) as response:
                        self.assertEqual(response.status_code, 200)

    def test_send_static_file_globbing(self):
        config = {'MAKESTATIC_FILEPATTERN_FORMAT': 'globbing'}
        for context in self.get_watcher_contexts('working_globbing', config):
            with context as (app, make_static):
                with app.test_request_context():
                    with closing(app.send_static_file('foo')) as response:
                        self.assertEqual(response.status_code, 200)

                    with closing(app.send_static_file('spam')) as response:
                        self.assertEqual(response.status_code, 200)

                    with closing(app.send_static_file('bar')) as response:
                        self.assertEqual(response.status_code, 200)
                        response.direct_passthrough = False
                        self.assertEqual(response.data, b'abc\ndef\n')

                    self.assertRaises(NotFound, app.send_static_file, 'baz')

                    with closing(app.send_static_file('eggs.css')) as response:
                        self.assertEqual(response.status_code, 200)

                    with catch_warnings(record=True): # silence RuleMissing warning
                        with catch_stdout() as stdout:
                            filename = os.path.basename(get_temporary_filename(
                                directory=make_static.assets_folder
                            ))
                            time.sleep(0.05)

                    self.assertEqual(
                        stdout.getvalue(),
                        'Flask-MakeStatic: detected new asset %s, compiling\n' %
                        filename
                    )

                    self.assertRaises(NotFound, app.send_static_file, filename)

                    with catch_stdout() as stdout:
                        bump_modification_time(
                            os.path.join(make_static.assets_folder, 'foo')
                        )
                        time.sleep(0.05)

                    self.assertEqual(
                        stdout.getvalue(),
                        'Flask-MakeStatic: detected change in foo, compiling\n'
                    )

                    with closing(app.send_static_file('foo')) as response:
                        self.assertEqual(response.status_code, 200)

    def test_static_view(self):
        for context in self.get_watcher_contexts('working'):
            with context as (app, make_static):
                client = app.test_client()
                with closing(client.get('/static/foo')) as response:
                    self.assertEqual(response.status_code, 200)

                with closing(client.get('/static/spam')) as response:
                    self.assertEqual(response.status_code, 200)

                with closing(client.get('/static/bar')) as response:
                    self.assertEqual(response.status_code, 200)
                    self.assertEqual(response.data, b'abc\ndef\n')

                with closing(client.get('/static/baz')) as response:
                    self.assertEqual(response.status_code, 404)

                with closing(client.get('/static/eggs.css')) as response:
                    self.assertEqual(response.status_code, 200)

                with catch_warnings(record=True): # silence RuleMissing warning
                    with catch_stdout() as stdout:
                        filename = os.path.basename(get_temporary_filename(
                            directory=make_static.assets_folder
                        ))
                        time.sleep(0.05)

                self.assertEqual(
                    stdout.getvalue(),
                    'Flask-MakeStatic: detected new asset %s, compiling\n' %
                    filename
                )

                with closing(client.get('/static/' + filename)) as response:
                    self.assertEqual(response.status_code, 404)

                with catch_stdout() as stdout:
                    bump_modification_time(
                        os.path.join(make_static.assets_folder, 'foo')
                    )
                    time.sleep(0.05)

                self.assertEqual(
                    stdout.getvalue(),
                    'Flask-MakeStatic: detected change in foo, compiling\n'
                )

                with closing(client.get('/static/foo')) as response:
                    self.assertEqual(response.status_code, 200)

    def test_static_view_globbing(self):
        config = {'MAKESTATIC_FILEPATTERN_FORMAT': 'globbing'}
        for context in self.get_watcher_contexts('working_globbing', config):
            with context as (app, make_static):
                client = app.test_client()
                with closing(client.get('/static/foo')) as response:
                    self.assertEqual(response.status_code, 200)

                with closing(client.get('/static/spam')) as response:
                    self.assertEqual(response.status_code, 200)

                with closing(client.get('/static/bar')) as response:
                    self.assertEqual(response.status_code, 200)
                    self.assertEqual(response.data, b'abc\ndef\n')

                with closing(client.get('/static/baz')) as response:
                    self.assertEqual(response.status_code, 404)

                with closing(client.get('/static/eggs.css')) as response:
                    self.assertEqual(response.status_code, 200)

                with catch_warnings(record=True): # silence RuleMissing warning
                    with catch_stdout() as stdout:
                        filename = os.path.basename(get_temporary_filename(
                            directory=make_static.assets_folder
                        ))
                        time.sleep(0.05)

                self.assertEqual(
                    stdout.getvalue(),
                    'Flask-MakeStatic: detected new asset %s, compiling\n' %
                    filename
                )

                with closing(client.get('/static/' + filename)) as response:
                    self.assertEqual(response.status_code, 404)

                with catch_stdout() as stdout:
                    bump_modification_time(
                        os.path.join(make_static.assets_folder, 'foo')
                    )
                    time.sleep(0.05)

                self.assertEqual(
                    stdout.getvalue(),
                    'Flask-MakeStatic: detected change in foo, compiling\n'
                )

                with closing(client.get('/static/foo')) as response:
                    self.assertEqual(response.status_code, 200)

    def test_compile(self):
        app = Flask('working')
        make_static = MakeStatic(app)
        make_static.compile()

        # ensure that app is not patched and assets are not compiled on demand
        app = Flask('working')
        client = app.test_client()
        with closing(client.get('/static/foo')) as response:
            self.assertEqual(response.status_code, 200)

        with closing(client.get('/static/spam')) as response:
            self.assertEqual(response.status_code, 200)

        with closing(client.get('/static/bar')) as response:
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.data, b'abc\ndef\n')

        with closing(client.get('/static/eggs.css')) as response:
            self.assertEqual(response.status_code, 200)

    def test_compile_in_app_context(self):
        app = Flask('working')
        make_static = MakeStatic()
        make_static.init_app(app)
        with app.app_context():
            make_static.compile()

        # ensure that app is not patched and assets are not compiled on demand
        app = Flask('working')
        client = app.test_client()
        with closing(client.get('/static/foo')) as response:
            self.assertEqual(response.status_code, 200)

        with closing(client.get('/static/spam')) as response:
            self.assertEqual(response.status_code, 200)

        with closing(client.get('/static/bar')) as response:
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.data, b'abc\ndef\n')

        with closing(client.get('/static/eggs.css')) as response:
            self.assertEqual(response.status_code, 200)

    def test_compile_globbing(self):
        app = Flask('working_globbing')
        app.config['MAKESTATIC_FILEPATTERN_FORMAT'] = 'globbing'
        make_static = MakeStatic(app)
        make_static.compile()

        # ensure that app is not patched and assets are not compiled on demand
        app = Flask('working_globbing')
        client = app.test_client()
        with closing(client.get('/static/foo')) as response:
            self.assertEqual(response.status_code, 200)

        with closing(client.get('/static/spam')) as response:
            self.assertEqual(response.status_code, 200)

        with closing(client.get('/static/bar')) as response:
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.data, b'abc\ndef\n')

        with closing(client.get('/static/eggs.css')) as response:
            self.assertEqual(response.status_code, 200)

    def test_compile_warns_on_missing_rule(self):
        app = Flask('missing_rule')
        make_static = MakeStatic(app)
        with catch_warnings(record=True) as warnings:
            make_static.compile()
        self.assertEqual(len(warnings), 1)
        self.assertTrue(issubclass(warnings[-1].category, RuleMissing))
        self.assertEqual(str(warnings[-1].message),
                         'cannot find a rule for foo.css')

    def test_compile_factory_pattern_without_app_context(self):
        app = Flask('working')
        make_static = MakeStatic()
        make_static.init_app(app)
        self.assertRaises(RuntimeError, make_static.compile)


class WatcherTestCase(unittest.TestCase):
    def assert_(self, **kwargs):
        self.assertEqual(self.added_files, kwargs.pop('added_files', []))
        del self.added_files[:]
        self.assertEqual(self.modified_files, kwargs.pop('modified_files', []))
        del self.modified_files[:]
        self.assertEqual(self.removed_files, kwargs.pop('removed_files', []))
        del self.removed_files[:]
        self.assertEqual(self.added_directories,
                         kwargs.pop('added_directories', []))
        del self.added_directories[:]
        self.assertEqual(self.modified_directories,
                         kwargs.pop('modified_directories', []))
        del self.modified_directories[:]
        self.assertEqual(self.removed_directories,
                         kwargs.pop('removed_directories', []))
        del self.removed_directories[:]

        if kwargs:
            raise TypeError(
                'unexpected keyword argument: %s' % kwargs.popitem()[0]
            )

    def test(self):
        watcher = ThreadedWatcher()
        self.added_files = []
        self.modified_files = []
        self.removed_files = []
        self.added_directories = []
        self.modified_directories = []
        self.removed_directories = []
        watcher.file_added.connect(self.added_files.append)
        watcher.file_modified.connect(self.modified_files.append)
        watcher.file_removed.connect(self.removed_files.append)
        watcher.directory_added.connect(self.added_directories.append)
        watcher.directory_modified.connect(self.modified_directories.append)
        watcher.directory_removed.connect(self.removed_directories.append)

        directory = get_temporary_directory()
        watcher.add_directory(directory)
        watcher.watch(sleep=0.01)

        foo = os.path.join(directory, 'foo')
        open(foo, 'w').close()
        time.sleep(0.05) # reasonable amount of reaction time
        self.assert_(added_files=[foo], modified_directories=[directory])

        bump_modification_time(foo)
        time.sleep(0.05)
        self.assert_(modified_files=[foo], modified_directories=[directory])

        os.remove(foo)
        time.sleep(0.05)
        self.assert_(removed_files=[foo], modified_directories=[directory])

        bar = os.path.join(directory, 'bar')
        os.mkdir(bar)
        time.sleep(0.05)
        self.assert_(added_directories=[bar], modified_directories=[directory])

        baz = os.path.join(bar, 'baz')
        open(baz, 'w').close()
        time.sleep(0.05)
        self.assert_(added_files=[baz], modified_directories=[bar])

        bump_modification_time(baz)
        time.sleep(0.05)
        self.assert_(modified_files=[baz], modified_directories=[bar])

        os.remove(baz)
        time.sleep(0.05)
        self.assert_(removed_files=[baz], modified_directories=[bar])

        os.rmdir(bar)
        time.sleep(0.05)
        self.assert_(removed_directories=[bar],
                     modified_directories=[directory])

        watcher.stop()
        time.sleep(0.05)
        self.assertEqual(threading.active_count(), 1)


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(MakeStaticTestCase))
    suite.addTest(unittest.makeSuite(WatcherTestCase))
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='suite')
