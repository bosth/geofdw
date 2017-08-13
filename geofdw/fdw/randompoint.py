from geofdw.base import GeoFDW
from geofdw.exception import OptionValueError
from plpygis import Point
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
    super(RandomPoint, self).__init__(options, columns)
    self.check_columns(["geom"])
    self.min_x = self.get_option("min_x", option_type=float)
    self.min_y = self.get_option("min_y", option_type=float)
    self.max_x = self.get_option("max_x", option_type=float)
    self.max_y = self.get_option("max_y", option_type=float)
    self.num = self.get_option("num", required=False, default=1, option_type=int)
    self.srid = self.get_option("srid", required=False, option_type=int)

    if self.max_x <= self.min_x or self.max_y <= self.min_y:
      raise OptionValueError("min must be smaller than max")

  def execute(self, quals, columns):
    for i in range(self.num):
      x = random.uniform(self.min_x, self.max_x)
      y = random.uniform(self.min_y, self.max_y)
      point = Point((x, y), srid=self.srid)
      yield { "geom" : point }
