Flask-MakeStatic
================

.. currentmodule:: flask.ext.makestatic

Flask-MakeStatic is an extension for Flask_ that adds support for compilation
of static files such as sass_ or coffeescript_ files.

.. _Flask: http://flask.pocoo.org/
.. _sass: http://sass-lang.com/
.. _coffeescript: http://coffeescript.org/

In order to use it you simply create an `assets` directory and an `assets.cfg`
file in the same directory as your `static` directory. `assets` should contain
all files that require compilation and `assets.cfg` specifies how the files in
`assets` should be compiled.

The simplest possible `assets.cfg` file would look like this::

    [.*]
    cp {asset} {static}

This defines a regular expression ``.*`` which matches any file in assets and
copies the file to the `static` directory. ``{asset}`` will be replaced with
the path to the file in the `assets` directory and ``{static}`` with the
corresponding location within the `static` directory.

As you can see the syntax is kind of like an ini file. You have sections which
match files in your assets directory followed by one or more commands that are
executed when a matched file is compiled.

Within these commands several substitutions are available, which you can use
with the `.format()` string formatting syntax:

============= =============================================================
`asset`       The absolute path to matched asset.
`static`      The absolute path to the corresponding location in the static
              directory.
`static_dir`  The absolute path to the static directory.
`static_base` Like `static` but without the file extension.
============= =============================================================

In order to compile your assets you have to first create a :class:`MakeStatic`
instance, this should be familiar if you have used other flask extensions::

    from flask import Flask
    from flask.ext.makestatic import MakeStatic

    app = Flask(__name__)
    makestatic = MakeStatic(app)

First of all you are probably concerned about development. During development
you do not want to manually recompile all the time, so what you should do is
call :meth:`MakeStatic.watch` before calling :meth:`flask.Flask.run`::

    if __name__ == '__main__':
        makestatic.watch()
        app.run(debug=True)

This will compile your assets whenever a change is detected.

In production environments using :meth:`MakeStatic.watch` is not a good idea
because it starts a new thread to look for changes and has to compile all
assets at least once. This costs performance and may unnecessarily compile your
assets in environments using multiple workers.

Instead what you want to do, is compile your assets during your deployment
process. You can do this by calling :meth:`MakeStatic.compile`.


API
---

.. module:: flask.ext.makestatic

.. autoclass:: MakeStatic
   :members:

.. autoclass:: RuleMissing


Changelog
---------

.. include:: ../CHANGELOG.rst


License
-------

.. include:: ../LICENSE.rst
