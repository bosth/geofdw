from geofdw.base import GeoFDW
from geofdw.exception import MissingOptionError, OptionTypeError, OptionValueError
from geofdw.pg.geometry import Geometry
from shapely.geometry import Point
import random

class RandomPoint(GeoFDW):
  """
  The RandomPoint foreign data wrapper creates a number of random points.
  """
  def __init__(self, options, columns):
    """
    Create the table that will contain the random points. There will only be a
    single column geom of type GEOMETRY(POINT).

    :param dict options: Options passed to the table creation.
      min_x: Minimum value for x (required)
      min_y: Minimum value for y (required)
      max_x: Maximum value for x (required)
      max_y: Maximum value for y (required)
      num: Number of points
      srid: SRID of the points

     :param list columns:
       geom (required)
    """
    self.check_column(columns, 'geom')
    self.min_x = self.get_option(options, 'min_x', option_type=float)
    self.min_y = self.get_option(options, 'min_y', option_type=float)
    self.max_x = self.get_option(options, 'max_x', option_type=float)
    self.max_y = self.get_option(options, 'max_y', option_type=float)
    self.num = self.get_option(options, 'num', required=False, default=1, option_type=int)
    srid = self.get_option(options, 'srid', required=False)

    if self.max_x <= self.min_x or self.max_y <= self.min_y:
      raise OptionValueError('min must be smaller than max')
    super(RandomPoint, self).__init__(options, columns, srid)

  def execute(self, quals, columns):
    for i in range(self.num):
      x = random.uniform(self.min_x, self.max_x)
      y = random.uniform(self.min_y, self.max_y)
      point = Point(x, y)
      geom = Geometry(point, self.srid)
      yield { 'geom' : geom.as_wkb() }
