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

        self.directory_added = Signal()
        self.directory_modified = Signal()
        self.directory_removed = Signal()

        self._stopped = False

    def _listdir(self, directory):
        return set(os.path.join(directory, f) for f in os.listdir(directory))

    def add_file(self, file):
        with self._lock:
            self.files[file] = os.stat(file).st_mtime

    def add_directory(self, directory, ignore_contained=True):
        with self._lock:
            paths = self._listdir(directory)
            if ignore_contained:
                self.directories[directory] = paths
            else:
                self.directories[directory] = set()
            for path in paths:
                if os.path.isfile(path):
                    self.add_file(path)
                elif os.path.isdir(path):
                    self.add_directory(path, ignore_contained=ignore_contained)

    def stop(self):
        self._stopped = True

    def watch(self, sleep=0.1):
        while not self._stopped:
            with self._lock:
                new_directories = []
                removed_directories = []
                for directory, seen in iteritems(self.directories):
                    try:
                        current = self._listdir(directory)
                    except OSError as error:
                        if error.errno == errno.ENOENT:
                            self.directory_removed.send(directory)
                            removed_directories.append(directory)
                        else:
                            raise
                    else:
                        for path in seen ^ current:
                            self.directory_modified.send(directory)
                            if path in current:
                                if os.path.isfile(path):
                                    self.add_file(path)
                                    self.file_added.send(path)
                                elif os.path.isdir(path):
                                    new_directories.append(path)
                                    self.directory_added.send(path)
                            else:
                                if os.path.isfile(path):
                                    self.file_removed.send(path)
                                    self.files.pop(path)
                                elif os.path.isdir(path):
                                    self.directory_removed.send(path)
                        self.directories[directory] = current
                for directory in new_directories:
                    self.add_directory(directory, ignore_contained=False)
                for directory in removed_directories:
                    del self.directories[directory]
                removed_files = []
                for file, last_known_modified_time in iteritems(self.files):
                    try:
                        modified_time = os.stat(file).st_mtime
                    except OSError as error:
                        if error.errno == errno.ENOENT:
                            self.file_removed.send(file)
                            removed_files.append(file)
                        else:
                            raise
                    else:
                        if modified_time > last_known_modified_time:
                            self.files[file] = modified_time
                            self.file_modified.send(file)
                            directory = os.path.dirname(file)
                            if directory in self.directories:
                                self.directory_modified.send(directory)
                for file in removed_files:
                    del self.files[file]
                time.sleep(sleep)


class ThreadingMixin(object):
    def watch(self, sleep=0.1):
        thread = threading.Thread(target=super(ThreadingMixin, self).watch,
                                  kwargs=dict(sleep=sleep))
        thread.daemon = True
        thread.start()


class ThreadedWatcher(ThreadingMixin, Watcher):
    pass
