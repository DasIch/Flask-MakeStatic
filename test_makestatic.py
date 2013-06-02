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
from flask.ext.makestatic.watcher import ThreadedWatcher


TEST_APPS = os.path.join(os.path.dirname(__file__), 'test_apps')
sys.path.insert(0, TEST_APPS)


def get_temporary_filename():
    filename = tempfile.mkstemp()[1]
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


class MakeStaticTestCase(unittest.TestCase):
    def tearDown(self):
        for test_app_dir in os.listdir(TEST_APPS):
            static_dir = os.path.join(TEST_APPS, test_app_dir, 'static')
            if os.path.isdir(static_dir):
                for root, dirs, files in os.walk(static_dir):
                    for file in files:
                        if file == '.gitignore':
                            continue
                        os.remove(os.path.join(root, file))
                    for dir in dirs:
                        os.rmdir(os.path.join(root, dir))

    @contextmanager
    def make_static(self, import_name):
        app = Flask(import_name)
        make_static = MakeStatic(app)
        watcher = make_static.watch()
        try:
            yield app, make_static
        finally:
            watcher.stop()

    def test_send_static_file(self):
        with self.make_static('working') as (app, make_static):
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

    def test_static_view(self):
        with self.make_static('working') as (app, make_static):
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

    def test_compile(self):
        app = Flask('working')
        make_static = MakeStatic(app)
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

    def test_compile_warns_on_missing_rule(self):
        app = Flask('missing_rule')
        make_static = MakeStatic(app)
        with catch_warnings(record=True) as warnings:
            with app.app_context():
                make_static.compile()
        self.assertEqual(len(warnings), 1)
        self.assertTrue(issubclass(warnings[-1].category, RuleMissing))
        self.assertEqual(str(warnings[-1].message),
                         'cannot find a rule for foo.css')


class WatcherTestCase(unittest.TestCase):
    def test(self):
        watcher = ThreadedWatcher()
        added = []
        modified = []
        removed = []
        watcher.file_added.connect(added.append)
        watcher.file_modified.connect(modified.append)
        watcher.file_removed.connect(removed.append)
        directory = get_temporary_directory()
        watcher.add_directory(directory)
        watcher.watch()

        foo = os.path.join(directory, 'foo')
        open(foo, 'w').close()
        time.sleep(0.15) # reasonable amount of reaction time
        self.assertEqual(added, [foo])
        del added[:]
        self.assertEqual(modified, [])
        self.assertEqual(removed, [])

        bump_modification_time(foo)
        time.sleep(0.15)
        self.assertEqual(added, [])
        self.assertEqual(modified, [foo])
        del modified[:]
        self.assertEqual(removed, [])

        os.remove(foo)
        time.sleep(0.15)
        self.assertEqual(added, [])
        self.assertEqual(modified, [])
        self.assertEqual(removed, [foo])
        del removed[:]

        watcher.stop()
        time.sleep(0.15)
        self.assertEqual(threading.active_count(), 1)


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(MakeStaticTestCase))
    suite.addTest(unittest.makeSuite(WatcherTestCase))
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='suite')
