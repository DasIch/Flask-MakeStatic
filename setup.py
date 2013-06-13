# coding: utf-8
import os

from setuptools import setup


def get_version():
    # We can't import flask.ext.makestatic because that would require all
    # dependencies to be installed.
    init_path = os.path.join(
        os.path.dirname(__file__), 'flask_makestatic', '__init__.py'
    )
    with open(init_path) as init_file:
        for line in init_file:
            if line.startswith('__version__'):
                return line.split('=')[1].replace("'", '').strip()
        raise ValueError('__version__ not found in %s' % init_path)


def get_long_description():
    with open(os.path.join(os.path.dirname(__file__), 'README.rst')) as readme:
        return readme.read()


setup(
    name='Flask-MakeStatic',
    version=get_version(),
    url='https://github.com/DasIch/Flask-MakeStatic',
    license='BSD',
    author='Daniel Neuhäuser',
    author_email='ich@danielneuhaeuser.de',
    description='Make for your flask app assets',
    long_description=get_long_description(),
    packages=['flask_makestatic'],
    zip_safe=False,
    include_package_data=True,
    platforms='any',
    install_requires=['Flask>=0.10'],
    test_suite='test_makestatic.suite',
    classifiers=[
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ]
)
