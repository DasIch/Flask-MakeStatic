Flask-MakeStatic
================

.. currentmodule:: flask.ext.makestatic

Flask-MakeStatic is an extension for Flask_ that adds support for compilation
of static files such as sass_ or coffeescript_ files.

.. _Flask: http://flask.pocoo.org/
.. _sass: http://sass-lang.com/
.. _coffeescript: http://coffeescript.org/

In order to use it you simply create an `assets` directory and an `assets.yaml`
file in the same directory as your `static` directory. `assets` should contain
all files that require compilation and `assets.yaml` specified how the files in
`assets` should be compiled.

The simplest possible `assets.yaml` file would look like this::

    .*: cp {asset} {static}

This defines a regular expression ``.*`` which matches any file in assets and
copies the file to the `static` directory. ``{asset}`` will be replaced with
the path to the file in the `assets` directory and ``{static}`` with the
corresponding location within the `static` directory

In order for this to happen you have to create a :class:`MakeStatic` instance
and pass it your application::

    from flask import Flask
    from flask.ext.makestatic import MakeStatic

    app = Flask(__name__)
    makestatic = MakeStatic(app)

:class:`MakeStatic` wraps and replaces :meth:`~flask.Flask.send_static_file`
and the static view of the flask application, to seamlessly compile assets when
a request to a static file is made.  In order to avoid unnecessary
compilations, compiled assets are cached in the `static` directory.

In production environments you do not usually let flask serve static files nor
should you. In this scenario you want to compile your static files as part of
the deployment process. This can be achieved by calling the
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
