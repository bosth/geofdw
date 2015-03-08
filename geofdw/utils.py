from multicorn import ForeignDataWrapper, Qual
from multicorn.utils import *
from shapely import geos
from cStringIO import StringIO
import re
import struct
import sys

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

class ArcGrid():
  def __init__(self, srid = None):
    self.data = []
    self.data_type = None
    self.data_min = sys.float_info.max
    self.data_max = sys.float_info.min
    self.srid = srid

  def parse(self, grid):
    header = {}
    buf = StringIO(grid)
    self.data_type = int

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
          num = float(v)
          if num < self.data_min:
            self.data_min = num
          elif num > self.data_max:
            self.data_max = num
          self.data.append(num)
          if self.data_type == int and not num.is_integer():
            self.data_type = float

    self.width = header['ncols']
    self.height = header['nrows']
    self.nodata = header.has_key('nodata_value')
    if self.nodata:
      self.nodata_val = float(header.get('nodata_value'))
      if self.nodata_val < self.data_min:
        self.data_min = self.nodata_val
      elif self.nodata_val > self.data_max:
        self.data_max = self.nodata_val
      if not self.nodata_val.is_integer():
        self.data_type = float

  def best_data_type(self):
    if self.data_type == int:
      if self.data_min < 0:
        if self.data_min >= -2**31 and self.data_max <= 2**31-1:
          return ('<i', 7) # PG: 32SI
      else:
        if self.data_max <= 2**32-1:
          return ('<I', 8) # PG: 32UI
    self.data_type = float
    return ('<d', 11) # PG: 64BF

  def to_wkb(self, grid, bbox):
    scalex = float(bbox[2] - bbox[0]) / self.width
    scaley = float(bbox[3] - bbox[1]) / self.height
    if self.srid:
      srid = self.srid
    else:
      srid = 0
    struct_data_type, pg_data_type  = self.best_data_type()

    # meta data (some unnecessary stuff here)
    wkb = ''
    wkb += struct.pack('<b', 1) # endianness
    wkb += struct.pack('<H', 0) # version
    wkb += struct.pack('<H', 1) # num bands
    wkb += struct.pack('<d', scalex) # scale x
    wkb += struct.pack('<d', scaley) # scale y
    wkb += struct.pack('<d', bbox[0]) # upper left x
    wkb += struct.pack('<d', bbox[3]) # upper left y
    wkb += struct.pack('<d', 0) # skew x
    wkb += struct.pack('<d', 0) # skey y
    wkb += struct.pack('<i', srid) # SRID
    wkb += struct.pack('<H', self.width) # width
    wkb += struct.pack('<H', self.height) # height

    # band meta data
    band  = 0
    band += pg_data_type << 0 # pixel type (see rt_api.h)
    band +=  0 << 4 # reserved bit
    band +=  0 << 5 # is no data
    band +=  1 << 6 if self.nodata else 0 # has no data
    band += 0 << 7 # is offdb
    wkb += struct.pack('<B', band)
    wkb += struct.pack(struct_data_type, self.data_type(self.nodata_val) if self.nodata else 0)

    # band data
    for val in self.data:
      wkb += struct.pack(struct_data_type, self.data_type(val))

    return wkb.encode('hex')
