#!/usr/bin/env python
"""
geofdw
"""

from setuptools import setup, find_packages

REQUIRES = [
]

setup(
    name='geofdw',
    version=0.1,
    description='',
    license='',
    url='',
    long_description='',
    author='Benjamin Trigona-Harany',
    author_email='bosth@alumni.sfu.ca',

    packages=find_packages(),
    install_requires = [
      'multicorn'
    ],
    extras_require = {
    },
    keywords='gis geographical postgis fdw postgresql'
)
