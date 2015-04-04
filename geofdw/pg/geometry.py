import shapely.wkb
import shapely.wkt
import re

from geofdw.exception import InvalidGeometryError
from shapely.geometry.base import BaseGeometry
from shapely.geometry import asShape
from shapely.geos import ReadingError
from shapely import geos

class Geometry():
  """
  Represents a PostGIS geometry object that can be imported from or exported to
  a Shapely geometry, WKB or EWKT.
  """
  def __init__(self, shape, srid):
    """
    Note: use one of from_shape(), from_wkb, from_wkt since this might change in future.
    """
    if not issubclass(type(shape), BaseGeometry):
      raise InvalidGeometryError('Geometry can not be None')
    self._shape = shape
    self._set_srid(srid)

  @classmethod
  def from_shape(cls, shape, srid = None):
    """
    Create a Geometry object from a Shapely geometry.
    """
    if not srid:
      srid = geos.lgeos.GEOSGetSRID(shape._geom)
    return cls(asShape(shape), srid)

  @classmethod
  def from_wkb(cls, wkb, srid = None):
    """
    Create a Geometry object from a PostGIS geometry.
    """
    try:
      shape = shapely.wkb.loads(wkb, hex=True)
    except ReadingError as e:
      raise InvalidGeometryError('Invalid WKB can not be loaded')
    if not srid:
      srid = geos.lgeos.GEOSGetSRID(shape._geom)
    return cls(shape, srid)

  @classmethod
  def from_wkt(cls, wkt, srid = None):
    """
    Create a Geometry object from WKT.
    """
    try:
      shape = shapely.wkt.loads(wkt)
    except ReadingError as e:
      raise InvalidGeometryError('Invalid WKT can not be loaded')
    return cls(shape, srid)

  @classmethod
  def from_ewkt(cls, ewkt):
    """
    Create a Geometry object from EWKT.
    """
    if ewkt.count(';'):
      ewkt = ewkt.split(';')
      wkt = ewkt[1]
      srid = re.sub(re.escape('SRID='), '', ewkt[0], flags=re.I)
    else:
      wkt = ewkt
      srid = None
    return cls.from_wkt(wkt, srid)

  def _set_srid(self, srid = None):
    """
    Set the geometry's SRID.
    """
    if srid:
      self.srid = int(srid)
      geos.WKBWriter.defaults['include_srid'] = True
      geos.lgeos.GEOSSetSRID(self._shape._geom, self.srid)
    else:
      self.srid = None

  def as_shape(self):
    """
    Return the geometry as a Shapely geometry.
    """
    return self._shape

  def as_wkb(self):
    """
    Return the geometry as a WKB.
    """
    return self._shape.wkb_hex

  def as_ewkt(self):
    """
    Return the geometry as an EWKT.
    """
    if self.srid:
      return 'SRID=%d;%s' % (self.srid, self._shape.wkt)
    else:
      return self._shape.wkt

  def as_wkt(self):
    """
    Return the geometry as a WKT.
    """
    return self._shape.wkt

  def bounds(self):
    """
    Return the bounds of the geometry.
    """
    return self._shape.bounds

  def equals(self, geom, srid_compare = True):
    """
    Check if two geometries are equal.
    """
    lft_srid = geos.lgeos.GEOSGetSRID(self._shape._geom)
    rgt_srid = geos.lgeos.GEOSGetSRID(geom._shape._geom)
    if srid_compare and lft_srid != rgt_srid:
      return False
    return self._shape.equals(geom._shape)
