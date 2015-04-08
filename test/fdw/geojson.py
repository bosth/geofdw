"""
Test GeoJSON fdw
"""

import unittest

from geofdw.fdw import GeoJSON
from geofdw.pg import Geometry
from geofdw.exception import MissingColumnError, MissingOptionError, OptionTypeError

class GeoJSONTestCase(unittest.TestCase):

  EXAMPLE = 'https://raw.githubusercontent.com/colemanm/hurricanes/master/fl_2004_hurricanes.geojson'
  def test_missing_url(self):
    """
    GeoJSON.__init__ missing url
    """
    options = {}
    columns = ['geom']
    self.assertRaises(MissingOptionError, GeoJSON, options, columns)

  def test_missing_geom_column(self):
    """
    GeoJSON.__init__ missing geometry column
    """
    options = {'url' : self.EXAMPLE}
    columns = []
    self.assertRaises(MissingColumnError, GeoJSON, options, columns)

  def test_srid(self):
    """
    GeoJSON.__init__ set custom SRID
    """
    options = {'url' : self.EXAMPLE, 'srid' : '900913'}
    columns = ['geom']
    fdw = GeoJSON(options, columns)
    self.assertEquals(fdw.srid, 900913)

  def test_invalid_srid(self):
    """
    GeoJSON.__init__ set invalid SRID
    """
    options = {'url' : self.EXAMPLE, 'srid' : 'EPSG:900913'}
    columns = ['geom']
    self.assertRaises(OptionTypeError, GeoJSON, options, columns)

  def test_verify_ssl(self):
    """
    GeoJSON.__init__ enable SSL verify
    """
    options = {'url' : self.EXAMPLE, 'verify' : 'true'}
    columns = ['geom']
    fdw = GeoJSON(options, columns)
    self.assertEquals(fdw.verify, True)

  def test_no_verify_ssl(self):
    """
    GeoJSON.__init__ disable SSL verify
    """
    options = {'url' : self.EXAMPLE, 'verify' : 'false'}
    columns = ['geom']
    fdw = GeoJSON(options, columns)
    self.assertEquals(fdw.verify, False)

  def test_authentication(self):
    """
    GeoJSON.__init__ use authentication
    """
    options = {'url' : self.EXAMPLE, 'user' : 'name', 'pass' : 'secret'}
    columns = ['geom']
    fdw = GeoJSON(options, columns)
    self.assertEquals(fdw.auth, ('name', 'secret'))

  def test_no_authentication(self):
    """
    GeoJSON.__init__ disable authentication
    """
    options = {'url' : self.EXAMPLE}
    columns = ['geom']
    fdw = GeoJSON(options, columns)
    self.assertEquals(fdw.auth, None)

  def test_execute_bad_url(self):
    """
    GeoJSON.execute non-existant URL
    """
    options = {'url' : 'http://d.xyz'}
    columns = ['geom']
    fdw = GeoJSON(options, columns)
    rows = fdw.execute([], columns)
    self.assertListEqual(rows, [])

  def test_not_json(self):
    """
    GeoJSON.execute receive non-JSON response
    """
    options = {'url' : 'http://raw.githubusercontent.com'}
    columns = ['geom']
    fdw = GeoJSON(options, columns)
    rows = fdw.execute([], columns)
    self.assertListEqual(rows, [])

  def test_not_geojson(self):
    """
    GeoJSON.execute receive non-GeoJSON response
    """
    options = {'url' : 'https://raw.githubusercontent.com/fge/sample-json-schemas/master/json-home/json-home.json'}
    columns = ['geom']
    fdw = GeoJSON(options, columns)
    rows = fdw.execute([], columns)
    self.assertListEqual(rows, [])

  def test_geojson(self):
    """
    GeoJSON.execute receive GeoJSON response
    """
    options = {'url' : self.EXAMPLE}
    columns = ['geom']
    fdw = GeoJSON(options, columns)
    rows = fdw.execute([], columns)
    for row in rows:
      self.assertIsInstance(row['geom'], str)

  def test_geojson_attribute(self):
    """
    GeoJSON.execute receive GeoJSON response with non-spatial attribute
    """
    options = {'url' : self.EXAMPLE}
    columns = ['geom', 'NAME']
    fdw = GeoJSON(options, columns)
    rows = fdw.execute([], columns)
    for row in rows:
      self.assertIn(row['NAME'], ['Alex', 'Bonnie', 'Charley', 'Danielle', 'Earl', 'Frances', 'Gaston', 'Hermine', 'Ivan', 'Tropical Depression 2', 'Tropical Depression 10', 'Jeanne', 'Karl', 'Lisa', 'Matthew', 'Nicole', 'Otto'])
