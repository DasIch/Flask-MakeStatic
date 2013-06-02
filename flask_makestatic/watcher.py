# coding: utf-8
"""
    flask.ext.makestatic.watcher
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    :copyright: 2013 by Daniel Neuhäuser
    :license: BSD, see LICENSE.rst for details
"""
import os
import time
import errno
import threading

from flask.ext.makestatic._compat import iteritems


class Signal(object):
    def __init__(self):
        self.listeners = []

    def send(self, *args, **kwargs):
        for listener in self.listeners:
            listener(*args, **kwargs)

    def connect(self, function):
        self.listeners.append(function)
        return function


class Watcher(object):
    def __init__(self):
        self.files = {}
        self.directories = {}
        self._lock = threading.RLock()

        self.file_added = Signal()
        self.file_modified = Signal()
        self.file_removed = Signal()

        self._stopped = False

    def _listdir(self, directory):
        return set(os.path.join(directory, f) for f in os.listdir(directory))

    def add_file(self, file):
        with self._lock:
            self.files[file] = os.stat(file).st_mtime

    def add_directory(self, directory):
        with self._lock:
            self.directories[directory] = files = self._listdir(directory)
            for file in files:
                self.add_file(file)

    def stop(self):
        self._stopped = True

    def watch(self):
        while not self._stopped:
            with self._lock:
                for directory, seen_files in iteritems(self.directories):
                    current_files = self._listdir(directory)
                    for file in seen_files ^ current_files:
                        if file in current_files:
                            self.add_file(file)
                            self.file_added.send(file)
                        else:
                            self.file_removed.send(file)
                            self.files.pop(file)
                    self.directories[directory] = current_files
                for file, last_known_modified_time in iteritems(self.files):
                    try:
                        modified_time = os.stat(file).st_mtime
                    except OSError as error:
                        if error.errno == errno.ENOENT:
                            self.file_removed.send(file)
                        raise
                    else:
                        if modified_time > last_known_modified_time:
                            self.files[file] = modified_time
                            self.file_modified.send(file)
                time.sleep(0.1)


class ThreadingMixin(object):
    def watch(self):
        thread = threading.Thread(target=super(ThreadingMixin, self).watch)
        thread.daemon = True
        thread.start()


class ThreadedWatcher(ThreadingMixin, Watcher):
    pass
