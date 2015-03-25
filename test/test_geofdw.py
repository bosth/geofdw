"""
Test basic geofdw
"""

import unittest

from geofdw.base import GeoFDW

class GeoFDWTestCase(unittest.TestCase):
  def test_empty_srid(self):
    """
    GeoFDW adding without SRID
    """
    geofdw = GeoFDW([], {})
    self.assertIsNone(geofdw.srid)

  def test_srid(self):
    """
    GeoFDW adding SRID
    """
    geofdw = GeoFDW([], {}, '4326')
    print type(geofdw.srid)
    self.assertEquals(geofdw.srid, 4326)
