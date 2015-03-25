"""
Test Geometry 
"""

import unittest

from geofdw.pg import Geometry
from geofdw.exception import InvalidGeometryError
from shapely.geometry import Point

class GeometryTestCase(unittest.TestCase):
  def test_missing_shape(self):
    """
    Geometry.__init__ missing shape
    """
    self.assertRaises(InvalidGeometryError, Geometry, None, None)

  def test_from_shape(self):
    """
    Geometry.from_shape load
    """
    point = Point(0, 0)
    geom = Geometry.from_shape(point, 4326)
    self.assertEquals(geom.srid, 4326)
    self.assertTrue(geom.as_shape().equals(point))

  def test_from_shape_nosrid(self):
    """
    Geometry.from_shape load without SRID
    """
    point = Point(0, 0)
    geom = Geometry.from_shape(point)
    self.assertEquals(geom.srid, None)
    #self.assertTrue(geom.equals(point, srid_compare = False))
    self.assertTrue(geom.as_shape().equals(point))

  def test_from_wkb_invalid(self):
    """
    Geometry.from_wkb load invalid WKB
    """
    wkb = '11110008066C00000000000000000'
    self.assertRaises(InvalidGeometryError, Geometry.from_wkb, wkb)

  def test_from_wkb(self):
    """
    Geometry.from_wkb load WKB
    """
    wkb = '0101000020E610000000000000008066C00000000000000000'
    geom = Geometry.from_wkb(wkb)
    self.assertEquals(geom.srid, 4326)
    self.assertTrue(geom.as_shape().equals(Point(-180, 0)))

  def test_from_wkt_invalid(self):
    """
    Geometry.from_wkt load invalid WKT
    """
    wkt = 'LINESTRING(-180 0)'
    self.assertRaises(InvalidGeometryError, Geometry.from_wkt, wkt)

  def test_from_wkt(self):
    """
    Geometry.from_wkt load WKB
    """
    wkt = 'POINT (-180 0)'
    geom = Geometry.from_wkt(wkt, 4326)
    self.assertEquals(geom.srid, 4326)
    self.assertTrue(geom.as_shape().equals(Point(-180, 0)))

  def test_from_ewkt(self):
    """
    Geometry.from_ewkt load EWKT
    """
    ewkt = 'SRID=4326;POINT (-180 0)'
    geom = Geometry.from_ewkt(ewkt)
    self.assertEquals(geom.srid, 4326)
    self.assertTrue(geom.as_shape().equals(Point(-180, 0)))

  def test_from_ewkt_nosrid(self):
    """
    Geometry.from_ewkt load without SRID
    """
    ewkt = 'POINT (-180 0)'
    geom = Geometry.from_ewkt(ewkt)
    self.assertEquals(geom.srid, None)
    self.assertTrue(geom.as_shape().equals(Point(-180, 0)))

  def test_as_ewkt_nosrid(self):
    """
    Geometry.as_ewkt output EWKT without SRID
    """
    ewkt = 'POINT (-180 0)'
    geom = Geometry.from_ewkt(ewkt)
    self.assertEquals(geom.as_ewkt(), ewkt)

  def test_as_ewkt(self):
    """
    Geometry.as_ewkt output EWKT
    """
    ewkt = 'SRID=4326;POINT (-180 0)'
    geom = Geometry.from_ewkt(ewkt)
    self.assertEquals(geom.as_ewkt(), ewkt)

  def test_as_wkt(self):
    """
    Geometry.as_wkt output WKT
    """
    wkt = 'POINT (-180 0)'
    geom = Geometry.from_wkt(wkt)
    self.assertEquals(geom.as_wkt(), wkt)

  def test_bounds(self):
    """
    Geometry.bounds get geometry bounds
    """
    wkb = '01020000000200000000000000000000000000000000000000000000000000F03F000000000000F03F'
    geom = Geometry.from_wkb(wkb)
    self.assertEquals(geom.bounds(), (0.0, 0.0, 1.0, 1.0))

  def test_equals(self):
    """
    Geometry.equals test geometries
    """
    wkb = '0102000020E61000000200000000000000000000000000000000000000000000000000F03F000000000000F03F'
    geom_1 = Geometry.from_wkb(wkb)
    ewkt = 'SRID=4326;LINESTRING(0 0,1 1)'
    geom_2 = Geometry.from_ewkt(ewkt)
    self.assertTrue(geom_1.equals(geom_2))

  def test_equals_nosrid(self):
    """
    Geometry.equals test geometries without SRID
    """
    wkb = '0102000020E61000000200000000000000000000000000000000000000000000000000F03F000000000000F03F'
    geom_1 = Geometry.from_wkb(wkb)
    ewkt = 'LINESTRING(0 0,1 1)'
    geom_2 = Geometry.from_ewkt(ewkt)
    self.assertTrue(geom_1.equals(geom_2, srid_compare = False))

  def test_equals_nosrid(self):
    """
    Geometry.equals test different geometries
    """
    wkb = '0102000020E61000000200000000000000000000000000000000000000000000000000F03F000000000000F03F'
    geom_1 = Geometry.from_wkb(wkb)
    ewkt = 'SRID=3587;LINESTRING(0 0,1 1)'
    geom_2 = Geometry.from_ewkt(ewkt)
    self.assertFalse(geom_1.equals(geom_2))
