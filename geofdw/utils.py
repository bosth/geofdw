from multicorn import ForeignDataWrapper, Qual
from multicorn.utils import *
from shapely import geos
import re
from cStringIO import StringIO

class GeoForeignDataWrapper(ForeignDataWrapper):
  def crs_to_srid(self, crs):
    if crs == None:
      return None
    srid = re.sub(re.escape('epsg:'), '', crs, flags=re.I)
    return int(srid)

class GeoVectorForeignDataWrapper(GeoForeignDataWrapper):
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

class GeoRasterForeignDataWrapper(GeoForeignDataWrapper):
  def __init__(self, options, columns, srid = None):
    super(GeoRasterForeignDataWrapper, self).__init__(options, columns)    

  def parse_grid(self, grid):
    print grid
    buf = StringIO(grid)
    header = {}
    data = []
    while True:
      line = buf.readline().split()
      word = line[0].lower()
      if word in ['ncols', 'nrows']:
        header[word] = int(line[1])
      elif word in ['xllcorner', 'yllcorner', 'cellsize', 'nodata_value']:
        header[word] = float(line[1])
      else:
        row = []
        for v in line:
          row.append(float(v))
        if len(row) != header['ncols']:
          raise Exception('Expected %d columns, found %d' % (len(row), header['ncols']))
        data.append(row)
    if len(data) != header['nrows']:
      raise Exception('Expected %d rows, found %d' % (len(data), header['nrows']))

  def grid_to_wkb(self, grid):
    self.parse_grid(grid)
    wkb = bytes()

