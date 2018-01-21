#!/usr/bin/env python
"""
geofdw
"""

import os
import sys
from setuptools import setup, find_packages
from setuptools.command.test import test as TestCommand
from geofdw._version import __version__

def readme():
    with open("README.rst") as f:
        return f.read()

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
    name="geofdw",
    version=__version__,
    url="http://github.com/bosth/geofdw",
    license="GNU GPLv3",
    author="Benjamin Trigona-Harany",
    tests_require=["pytest"],
    cmdclass={"test": PyTest},
    author_email="bosth@alumni.sfu.ca",
    description="Foreign Data Wrappers for PostGIS",
    long_description=readme(),
    packages=["geofdw"],
    include_package_data=True,
    platforms="any",
    test_suite="test.geofdw",
    classifiers = [
    ],
    install_requires = [
      "multicorn>=1.1.0",
      "geopy>=1.9.1",
      "requests>=2.4.0",
      "plpygis>=0.0.3"
    ],
    extras_require = {
      'testing': ['pytest']
    },
    keywords='gis geographical postgis fdw postgresql'
)
