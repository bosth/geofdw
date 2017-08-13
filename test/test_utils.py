"""
Test geofdw utils
"""

import unittest
from geofdw.utils import *

class utils(unittest.TestCase):
  def test_crs_to_srid_none(self):
    """
    crs_to_srid converting missing CRS to a SRID
    """
    srid = crs_to_srid(None)
    self.assertEquals(srid, None)

  def test_crs_to_srid_lower(self):
    """
    crs_to_srid converting lower-case CRS to a SRID
    """
    srid = crs_to_srid('epsg:4326')
    self.assertEquals(srid, 4326)

  def test_crs_to_srid_upper(self):
    """
    crs_to_srid converting upper-case CRS to a SRID
    """
    srid = crs_to_srid('EPSG:4326')
    self.assertEquals(srid, 4326)
