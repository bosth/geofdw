"""
Test randompoint fdw
"""

import unittest

import pypg.geometry
from geofdw.fdw import RandomPoint
from geofdw.exception import MissingOptionError, OptionTypeError, OptionValueError

class RandomPointTestCase(unittest.TestCase):
  def test_missing_option(self):
    """
    fdw.RandomPoint.__init__ missing option
    """
    options = {}
    columns = ['geom']
    self.assertRaises(MissingOptionError, RandomPoint, options, columns)

  def test_bad_option_type(self):
    """
    fdw.RandomPoint.__init__ incorrect option type
    """
    options = {'min_x':'test'}
    columns = ['geom']
    self.assertRaises(OptionTypeError, RandomPoint, options, columns)

  def test_bad_option_value(self):
    """
    fdw.RandomPoint.__init__ incorrect option value
    """
    options = {'min_x':1, 'max_x':0, 'min_y':0, 'max_y':1}
    columns = ['geom']
    self.assertRaises(OptionValueError, RandomPoint, options, columns)

  def test_options(self):
    """
    fdw.RandomPoint.__init__ options
    """
    options = {'min_x':10, 'max_x':20, 'min_y':30, 'max_y':40, 'num': 99, 'srid':4326}
    columns = ['geom']
    fdw = RandomPoint(options, columns)
    self.assertEquals(fdw.min_x, 10)
    self.assertEquals(fdw.max_x, 20)
    self.assertEquals(fdw.min_y, 30)
    self.assertEquals(fdw.max_y, 40)
    self.assertEquals(fdw.num, 99)
    self.assertEquals(fdw.srid, 4326)

  def test_execute(self):
    """
    fdw.RandomPoint.execute check results
    """
    options = {'min_x':10, 'max_x':20, 'min_y':30, 'max_y':40, 'num': 99, 'srid':4326}
    columns = ['geom']
    fdw = RandomPoint(options, columns)
    rows = fdw.execute([], columns)
    for row in rows:
      point, srid = pypg.geometry.postgis.to_shape(row['geom'])
      self.assertTrue(10 <= point.x <= 20)
      self.assertTrue(30 <= point.y <= 40)
