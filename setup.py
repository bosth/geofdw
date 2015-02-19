#!/usr/bin/env python
"""
geofdw
"""

from setuptools import setup

setup(
    name='geofdw',
    version=0.1,
    description='',
    license='',
    url='',
    long_description='',
    author='Benjamin Trigona-Harany',
    author_email='bosth@alumni.sfu.ca',

    packages=['geofdw'],
    install_requires = [
      'multicorn',
      'Shapely'
    ],
    extras_require = {
      'OSRM': ['polyline>=1.1'],
      'Geocode': ['geopy>=1.9.1'],
      'GeoJSON': ['requests>=2.4.3']
    },
    keywords='gis geographical postgis fdw postgresql'
)
