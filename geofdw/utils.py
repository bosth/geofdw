from multicorn import ForeignDataWrapper, Qual
from multicorn.utils import *
from shapely import geos

class GeoVectorForeignDataWrapper(ForeignDataWrapper):
  def __init__(self, options, columns, srid = None):
    super(GeoVectorForeignDataWrapper, self).__init__(options, columns)    
    self.use_srid(srid)

  def use_srid(self, srid):
    if srid:
      self.srid = int(srid)
      geos.WKBWriter.defaults['include_srid'] = True
    else:
      self.srid = None

  def as_wkb(self, feature):
    if self.srid:
       geos.lgeos.GEOSSetSRID(feature._geom, self.srid)
    return feature.wkb_hex

class GeoRasterForeignDataWrapper(ForeignDataWrapper):
  def __init__(self, options, columns, srid = None):
    super(GeoRasterForeignDataWrapper, self).__init__(options, columns)    
