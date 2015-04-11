"""
Test basic geofdw
"""

import unittest

from geofdw.base import GeoFDW

class GeoFDWTestCase(unittest.TestCase):
  def test_init(self):
    """
    GeoFDW
    """
    fdw = GeoFDW({}, ['geom'])
    self.assertListEqual(fdw.columns, ['geom'])
