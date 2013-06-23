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

Since 0.2.0 you can also use globbing instead of regular expressions for your
filename patterns, if you set the `MAKESTATIC_FILEPATTERN_FORMAT` configuration
variable in your application configuration to ``'globbing'``.

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


.. _differences:

Differences to other Extensions
-------------------------------

Quite often when discussing Flask-MakeStatic, people ask why they should use
Flask-MakeStatic instead of some other extension or what the differences are.

This resource cannot provide an unbiased answer to that question, so if you
want one, you will have to compare the extensions yourself but I will
nevertheless attempt to provide at least a partial answer and defense for the
design of this extension.

So far I am aware of two other extensions that intend to solve the same problem
as Flask-MakeStatic, these are Flask-Assets_ and Flask-Funnel_.

Unlike Flask-MakeStatic these extensions work by defining so called bundles,
within the code of your application on which filters are applied, which perform
the actual compilation.

In both cases you need to use extension specific code in your templates. In the
case of Flask-Assets_ you even need to define the bundles, made up of your
assets within the code of your application.

Both extensions have more knowledge about the filters you use and how you use
them, this can be convenient and could possibly enable features, that cannot be
provided by Flask-MakeStatic. On the other side this also restricts you, in
your choice of filters. In the case of Flask-Funnel_ as of version 0.1.4 there
is no documented way of adding any filters at all, in the case of Flask-Assets_
you can create your own filters and while this appears to be trivial and well
documented it still requires code specifically for that purpose.

I created Flask-MakeStatic because I think that the frontend of your
application, in which I include static resources, assets, and templates, should
be as independent from your backend as reasonably possible. Flask-Assets_ and
Flask-Funnel_ violate this principle by coupling of front- and backend and
creating restrictions on the frontend beyond what I consider reasonable.

Flask-MakeStatic embraces this principle by providing you with a make inspired
way to compile assets, in a way that integrates well with Flask applications.


.. _Flask-Assets: http://elsdoerfer.name/docs/flask-assets/
.. _Flask-Funnel: http://flask-funnel.readthedocs.org/en/latest/


.. include:: ../CHANGELOG.rst

.. include:: ../CONTRIBUTING.rst

.. include:: ../LICENSE.rst
