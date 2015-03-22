from shapely import geos
import shapely.wkb
import shapely.wkt
import re

class Geometry():
  def __init__(self, shape, srid = None):
    self._shape = shape
    self.set_srid(srid)

  @classmethod
  def from_wkb(cls, wkb):
    shape = shapely.wkb.loads(wkb, hex=True)
    srid = geos.lgeos.GEOSGetSRID(shape._geom)
    return cls(shape, srid)

  @classmethod
  def from_wkt(cls, wkt):
    if wkt.count(';'):
      ewkt = wkt.split(';')
      wkt = ewkt[1]
      srid = re.sub(re.escape('SRID='), '', ewkt[0], flags=re.I)
    else:
      srid = None
    shape = shapely.wkt.loads(wkt)
    return cls(shape, srid)

  def set_srid(self, srid = None):
    if srid:
      self.srid = int(srid)
      geos.WKBWriter.defaults['include_srid'] = True
      geos.lgeos.GEOSSetSRID(self._shape._geom, self.srid)
    else:
      self.srid = None

  def as_shape(self):
    return self._shape

  def as_wkb(self):
    # TODO: make writing ewkb optional (?)
    return self._shape.wkb_hex

  def as_wkt(self, ewkt = True):
    if self.srid and ewkt:
      return 'SRID=%d;%s' % (self.srid, self._shape.wkt)
    else:
      return self._shape.wkt

  def bounds(self):
    return self._shape.bounds
