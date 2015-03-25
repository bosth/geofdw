#!/usr/bin/env python
"""
geofdw
"""

from __future__ import print_function
from setuptools import setup, find_packages
from setuptools.command.test import test as TestCommand
import io
import codecs
import os
import sys

import geofdw

here = os.path.abspath(os.path.dirname(__file__))

def read(*filenames, **kwargs):
  encoding = kwargs.get('encoding', 'utf-8')
  sep = kwargs.get('sep', '\n')
  buf = []
  for filename in filenames:
    with io.open(filename, encoding=encoding) as f:
      buf.append(f.read())
  return sep.join(buf)

long_description = read('README.txt', 'CHANGES.txt')

class PyTest(TestCommand):
  def finalize_options(self):
    TestCommand.finalize_options(self)
    self.test_args = []
    self.test_suite = True

  def run_tests(self):
    import pytest
    errcode = pytest.main(self.test_args)
    sys.exit(errcode)

setup(
    name='geofdw',
    version=geofdw.__version__,
    url='http://github.com/bosth/geofdw',
    license='GPL',
    author='Benjamin Trigona-Harany',
    tests_require=['pytest'],
    cmdclass={'test': PyTest},
    author_email='bosth@alumni.sfu.ca',
    description='',
    long_description=long_description,
    packages=['geofdw'],
    include_package_data=True,
    platforms='any',
    test_suite='test.test_geofdw',
    classifiers = [
    ],
    install_requires = [
      'multicorn>=1.1.0',
      'Shapely>=1.5.0'
      'polyline>=1.1',
      'geopy>=1.9.1',
      'requests>=2.4.0']
    ],
    extras_require = {
      'testing': ['pytest']
    },
    keywords='gis geographical postgis fdw postgresql'
)
