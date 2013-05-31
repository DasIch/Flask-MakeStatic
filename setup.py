# coding: utf-8
"""
Flask-MakeStatic
================

Flask-MakeStatic provides a simple YAML based configuration to compile assets.
"""
from setuptools import setup


setup(
    name='Flask-MakeStatic',
    version='0.1.0-dev',
    url='https://github.com/DasIch/Flask-MakeStatic',
    license='BSD',
    author='Daniel Neuhäuser',
    author_email='ich@danielneuhaeuser.de',
    description='Make for your flask app assets',
    long_description=__doc__,
    packages=['flask_makestatic'],
    zip_safe=False,
    include_package_data=True,
    platforms='any',
    install_requires=[
        'Flask>=0.9',
        'PyYAML>=3.10'
    ],
    test_suite='test_makestatic.suite',
    classifiers=[
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ]
)
