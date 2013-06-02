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
all files that require compilation and `assets.cfg` specified how the files in
`assets` should be compiled.

The simplest possible `assets.cfg` file would look like this::

    [.*]
    cp {asset} {static}

This defines a regular expression ``.*`` which matches any file in assets and
copies the file to the `static` directory. ``{asset}`` will be replaced with
the path to the file in the `assets` directory and ``{static}`` with the
corresponding location within the `static` directory.

In order for this to happen you have to create a :class:`MakeStatic` instance
and pass it your application::

    from flask import Flask
    from flask.ext.makestatic import MakeStatic

    app = Flask(__name__)
    makestatic = MakeStatic(app)

You can then call `:meth:`MakeStatic.watch` which will compile your assets if
any files in your `static` directory are changed. Typically you would do this
before calling :meth:`flask.Flask.run` in a ``if __name__ == '__main__':``
block::

    if __name__ == '__main__':
        makestatic.watch()
        app.run(debug=True)

In production environments you want to compile your static files as part of the
deployment process. This can be achieved by calling the
:meth:`MakeStatic.compile` method, in the app context of the initialized
application::

    with app.app_context():
        makestatic.compile()


API
---

.. module:: flask.ext.makestatic

.. autoclass:: MakeStatic
   :members:

.. autoclass:: RuleMissing
