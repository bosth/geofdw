"""
Test Raster
"""

import unittest

from geofdw.utils import *
from geofdw.pg import PixelType, Band, Raster
from geofdw.exception import ValueBoundsError

class PixelTypeTestCase(unittest.TestCase):
  def test_pixel_type_01(self):
    """
    pg.PixelType.from_data 'f' values
    """
    b = [0.1, 0.2]
    pt = PixelType.from_data(b)
    self.assertEquals(pt.as_struct(), 'f')

  def test_pixel_type_02(self):
    """
    pg.PixelType.from_data 'f' values and 'f' nodata
    """
    b = [1, 2]
    pt = PixelType.from_data(b, 1.1)
    self.assertEquals(pt.as_struct(), 'f')

  def test_pixel_type_03(self):
    """
    pg.PixelType.from_data 'f' values and 'B' nodata
    """
    b = [0.1, 0.2]
    pt = PixelType.from_data(b, 1)
    self.assertEquals(pt.as_struct(), 'f')

  def test_pixel_type_04(self):
    """
    pg.PixelType.from_data 'B' values and 'B' nodata
    """
    b = [1, 2]
    pt = PixelType.from_data(b, 1)
    self.assertEquals(pt.as_struct(), 'B')

  def test_pixel_type_05(self):
    """
    pg.PixelType.from_data positive value outside 'I'
    """
    b = [1, 2**32]
    pt = PixelType.from_data(b, 1)
    self.assertEquals(pt.as_struct(), 'f')

  def test_pixel_type_06(self):
    """
    pg.PixelType.from_data negative value and positive value outside 'i'
    """
    b = [-1, 2**31]
    pt = PixelType.from_data(b, 1)
    self.assertEquals(pt.as_struct(), 'f')

  def test_pixel_type_07(self):
    """
    pg.PixelType.from_data negative value outside 'i'
    """
    b = [0, -2**32]
    pt = PixelType.from_data(b, 1)
    self.assertEquals(pt.as_struct(), 'f')

  def test_pixel_type_as_pg(self):
    """
    pg.PixelType.as_struct check PostGIS type export
    """
    b = [0.1, 0.2]
    pt = PixelType.from_data(b, 1)
    self.assertEquals(pt.as_pg(), 10)

  def test_pixel_type_bounds_error(self):
    """
    pg.PixelType.from_data value exceeds maxiumum
    """
    b = [0, 10**310]
    self.assertRaises(ValueBoundsError, PixelType.from_data, b)

class BandTestCase(unittest.TestCase):
  pass

class RasterTestCase(unittest.TestCase):

  def test_read_arcgrid_1(self):
    """
    pg.Raster test
    """
    b1 = pg.Band([0, 1, 2, 3], 0)
    b2 = pg.Band([0, 1, 2, 3], 0)
    raster = Raster((0, 0, -10, 10), 2, 2, [b1, b2], 4326)
