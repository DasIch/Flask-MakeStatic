# coding: utf-8
import os
import sys
import atexit
import tempfile
import unittest
from warnings import catch_warnings
from contextlib import closing

from flask import Flask
from werkzeug.exceptions import NotFound

from flask.ext.makestatic import MakeStatic, is_newer, RuleMissing


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

    def test_send_static_file_patch(self):
        app = Flask('working')
        make_static = MakeStatic(app)
        assert make_static # pyflakes...

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

    def test_static_view_patch(self):
        app = Flask('working')
        make_static = MakeStatic(app)
        assert make_static # pyflakes...

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

    def test_compile_uninitialized(self):
        app = Flask('working')
        make_static = MakeStatic()
        with app.app_context():
            try:
                make_static.compile()
            except RuntimeError as error:
                self.assertEqual(error.args[0],
                                 'current application not initialized')
            else:
                assert 0, 'expected RuntimeError'

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


class InternalTestCase(unittest.TestCase):
    def test_is_newer(self):
        a = get_temporary_filename()
        b = get_temporary_filename()
        stat = os.stat(a)
        # bump modified time manually as precision might be as low as 1s and we
        # don't want to sleep for that long
        os.utime(b, (stat.st_atime, stat.st_mtime + 1))

        self.assertTrue(is_newer(b, a))
        self.assertFalse(is_newer(a, a))
        self.assertFalse(is_newer(a, b))

        self.assertTrue(is_newer(a, 'SHOULD_NOT_EXIST'))

        self.assertRaises(OSError, is_newer, 'SHOULD_NOT_EXIST', a)
        self.assertRaises(OSError, is_newer, 'SHOULD_NOT_EXIST', 'ALSO_SHOULD_NOT_EXIST')


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(MakeStaticTestCase))
    suite.addTest(unittest.makeSuite(InternalTestCase))
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='suite')
