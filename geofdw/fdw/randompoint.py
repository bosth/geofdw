from geofdw.base import GeoFDW
from geofdw.exception import MissingOptionError, OptionTypeError, OptionValueError
from geofdw.pg.geometry import Geometry
from shapely.geometry import Point
import random

class RandomPoint(GeoFDW):
  """
  The RandomPoint foreign data wrapper creates a certain number of random points.
  """
  def __init__(self, options, columns):
    """
    Create the table that will contain the random points. There will only be a
    single column geom of type GEOMETRY(POINT).

    :param dict options: Options passed to the table creation.
      min_x: Minimum value for x
      min_y: Minimum value for y
      max_x: Maximum value for x
      max_y: Maximum value for y
      num: Number of points (optional)
      srid: SRID of the points (optional)
    """
    try:
      self.min_x = float(options['min_x'])
      self.min_y = float(options['min_y'])
      self.max_x = float(options['max_x'])
      self.max_y = float(options['max_y'])
      self.num = int(options.get('num', 1))
    except KeyError as e:
      raise MissingOptionError(e)
    except ValueError as e:
      raise OptionTypeError(e)
    if self.max_x <= self.min_x or self.max_y <= self.min_y:
      raise OptionValueError('min must be smaller than max')
    srid = options.get('srid', None)
    super(RandomPoint, self).__init__(options, columns, srid)

  def execute(self, quals, columns):
    for i in range(self.num):
      x = random.uniform(self.min_x, self.max_x)
      y = random.uniform(self.min_y, self.max_y)
      point = Point(x, y)
      geom = Geometry(point, self.srid)
      yield { 'geom' : geom.as_wkb() }
