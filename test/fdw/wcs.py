"""
Test WCS fdw
"""

import unittest

from multicorn import Qual
from geofdw.fdw import WCS
from pypg import Raster
from geofdw.exception import CRSError, MissingColumnError, MissingOptionError, MissingQueryPredicateError
from requests.exceptions import ConnectionError, Timeout

class WCSTestCase(unittest.TestCase):
  def test_missing_column_raster(self):
    """
    fdw.WCS.__init__ missing raster column
    """
    options = {}
    columns = []
    self.assertRaises(MissingColumnError, WCS, options, columns)

  def test_missing_column_geom(self):
    """
    fdw.WCS.__init__ missing geom column
    """
    options = {}
    columns = ['raster']
    self.assertRaises(MissingColumnError, WCS, options, columns)

  def test_missing_url(self):
    """
    fdw.WCS.__init__ missing url
    """
    options = {}
    columns = ['raster', 'geom']
    self.assertRaises(MissingOptionError, WCS, options, columns)

  def test_missing_layer(self):
    """
    fdw.WCS.__init__ missing layer
    """
    options = {'url' : ''}
    columns = ['raster', 'geom']
    self.assertRaises(MissingOptionError, WCS, options, columns)

  def test_missing_crs(self):
    """
    fdw.WCS.__init__ missing crs
    """
    options = {'url' : '', 'layer' : ''}
    columns = ['raster', 'geom']
    self.assertRaises(MissingOptionError, WCS, options, columns)

  def test_bad_crs(self):
    """
    fdw.WCS.__init__ bad CRS
    """
    options = {'url' : '', 'layer' : '', 'crs' : 'espg:4326'}
    columns = ['raster', 'geom']
    self.assertRaises(CRSError, WCS, options, columns)

  def test_crs(self):
    """
    fdw.WCS.__init__ custom CRS
    """
    options = {'url' : '', 'layer' : '', 'crs' : 'epsg:4326'}
    columns = ['raster', 'geom']
    fdw = WCS(options, columns)
    self.assertEquals(fdw.srid, 4326)

  def test_custom_width(self):
    """
    fdw.WCS.__init__ custom width
    """
    options = {'url' : '', 'layer' : '', 'crs' : 'EPSG:4326', 'width' : '1024'}
    columns = ['raster', 'geom']
    fdw = WCS(options, columns)
    self.assertRegexpMatches(fdw.xml, '<gml:high>1024')

  def test_custom_band(self):
    """
    fdw.WCS.__init__ custom band
    """
    options = {'url' : '', 'layer' : '', 'crs' : 'EPSG:4326', 'band' : '2'}
    columns = ['raster', 'geom']
    fdw = WCS(options, columns)
    self.assertRegexpMatches(fdw.xml, '<singleValue>2</singleValue>')

  def test_geom_predicate_A(self):
    """
    fdw.WCS._get_predicates geom = B
    """
    options = {'url' : '', 'layer' : '', 'crs' : 'EPSG:4326', 'band' : '2'}
    columns = ['raster', 'geom']
    qual = Qual('geom', '=', 'xyz')
    fdw = WCS(options, columns)
    value = fdw._get_predicates([qual])
    self.assertEquals(value, 'xyz')

  def test_geom_predicate_B(self):
    """
    fdw.WCS._get_predicates A = geom
    """
    options = {'url' : '', 'layer' : '', 'crs' : 'EPSG:4326', 'band' : '2'}
    columns = ['raster', 'geom']
    qual = Qual('xyz', '=', 'geom')
    fdw = WCS(options, columns)
    value = fdw._get_predicates([qual])
    self.assertEquals(value, 'xyz')

  def test_geom_predicate_missing(self):
    """
    fdw.WCS.execute missing geom predicate
    """
    options = {'url' : '', 'layer' : '', 'crs' : 'EPSG:4326', 'band' : '2'}
    columns = ['raster', 'geom']
    qual = Qual('xyz', '=', 'xyz')
    fdw = WCS(options, columns)
    self.assertRaises(MissingQueryPredicateError, fdw._get_predicates, [qual])

  def test_no_connect(self):
    """
    fdw.WCS._get_raster bad connection
    """
    options = {'url' : 'http://non-existant-url.net', 'layer' : '', 'crs' : 'EPSG:4326', 'band' : '2'}
    columns = ['raster', 'geom']
    qual = Qual('010100000000000000000000000000000000000000', '=', 'geom')
    fdw = WCS(options, columns)
    result = fdw.execute([qual], columns)
    self.assertListEqual(result, [])
