Contributing
------------

If you want to contribute to Flask-MakeStatic, fork the repository_ and create
a local clone. Once you have done that, you should create a virtual environment
in whichever manner you prefer. Having acticated the virtual environment you
can install all tools that are useful in the development using::

    $ make dev

Now you should take a look at ``make help``. If you run that command, you will
see a list of useful commands you can issue with a small description of what
each one does.

If you make any changes to the code you should run ``make test-all`` before
committing to ensure that your changes do not break anything on any of the
supported Python versions and that the documentation builds successfully.

Running ``make test-all`` requires you to have installed the CPython
implementations of all supported Python versions and PyPy. If you have not
installed them already, you can do so quite easily using Homebrew_ on OS X.

If everything passes, commit your changes and make a pull request to `master`,
if you introduced a new feature or make a pull request to the maintenance
branch of the currently maintained version if you fixed a bug. Eventually
someone will review your pull request and hopefully merge it.

.. _repository: https://github.com/DasIch/Flask-MakeStatic
.. _Homebrew: http://mxcl.github.io/homebrew/
