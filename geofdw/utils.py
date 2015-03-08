from multicorn import ForeignDataWrapper, Qual
from multicorn.utils import *
from shapely import geos
from cStringIO import StringIO
import re
import struct

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

  def parse_arcgrid(self, grid):
    buf = StringIO(grid)
    header = {}
    data = []
    while True:
      line = buf.readline().split()
      if not line:
        break
      word = line[0].lower()
      if word in ['ncols', 'nrows']:
        header[word] = int(line[1])
      elif word in ['xllcorner', 'yllcorner', 'cellsize', 'nodata_value']:
        header[word] = float(line[1])
      else:
        if len(line) != header['ncols']:
          raise Exception('Expected %d columns, found %d' % (len(v), header['ncols']))
        for v in line:
          data.append(float(v))
    return (header, data)

  def arcgrid_to_wkb(self, grid, bbox):
    header, data = self.parse_arcgrid(grid)
    width = header['ncols']
    height = header['nrows']
    scalex = float(bbox[2] - bbox[0]) / width
    scaley = float(bbox[3] - bbox[1]) / height

    wkb = ''

    # meta data
    wkb += struct.pack('<b', 1) # endianness
    wkb += struct.pack('<H', 0) # version
    wkb += struct.pack('<H', 1) # num bands
    wkb += struct.pack('<d', scalex) # scale x
    wkb += struct.pack('<d', scaley) # scale y
    wkb += struct.pack('<d', bbox[0]) # upper left x
    wkb += struct.pack('<d', bbox[3]) # upper left y
    wkb += struct.pack('<d', 0) # upper left x
    wkb += struct.pack('<d', 0) # upper left y
    wkb += struct.pack('<i', self.srid) # SRID
    wkb += struct.pack('<H', width) # width
    wkb += struct.pack('<H', height) # height

    # band meta data
    band  = 0
    band += 11 << 0 # pixel type (hardcoded to 64-bit floating point) TODO: select best type
    band +=  0 << 4 # reserved bit
    band +=  0 << 5 # is no data
    if header['nodata_value']:
      band +=  1 << 6 # has no data
    else:
      band +=  0 << 6 # has no data
    band +=  1 << 7 # is offdb
    wkb += struct.pack('<B', band)

    # band data
    for val in data:
      wkb += struct.pack('<d', val)

    return wkb.encode('hex')
