import struct

from geofdw.exception import ValueBoundsError

class PixelType():
#    PT_8BSI=3,    /* 8-bit signed integer     */
#    PT_8BUI=4,    /* 8-bit unsigned integer   */
#    PT_16BSI=5,   /* 16-bit signed integer    */
#    PT_16BUI=6,   /* 16-bit unsigned integer  */
#    PT_32BSI=7,   /* 32-bit signed integer    */
#    PT_32BUI=8,   /* 32-bit unsigned integer  */
#    PT_32BF=10,   /* 32-bit float             */
#    PT_64BF=11,   /* 64-bit float             */
  TYPES = {'b': (3,  -2**7,  2**7-1),
           'B': (4,   0,     2**8-1),
           'h': (5,  -2**15, 2**15-1),
           'H': (6,   0,     2**16-1),
           'i': (7,  -2**31, 2**31-1),
           'I': (8,   0,     2**32-1),
           'f': (10, -3.402823466e+38, 3.402823466e+38),
           'd': (11, -1.7976931348623158e+308, 1.7976931348623158e+308)
          }

  def __init__(self, struct_type='b'):
      self._struct_type = struct_type

  @classmethod
  def from_data(cls, data, nodata=None):
    val_min = 0
    val_max = 0

    # find min, max and whether floats are necessary
    vals = [nodata] if nodata != None else []
    vals += data
    needs_float = False
    for val in vals:
      if not needs_float and type(val) == float and not val.is_integer():
        needs_float = True
      else:
        val = int(val)
      val_min = min(val_min, val)
      val_max = max(val_max, val)

    # other cases when floats are necessary: 'i' and 'I' are not viable for
    # min and max
    if val_max > PixelType.TYPES.get('I')[2]:
      needs_float = True
    elif val_min <= 0 and val_max > PixelType.TYPES.get('i')[2]:
      needs_float = True
    elif val_min < PixelType.TYPES.get('i')[1]:
      needs_float = True

    # find best type for min and max
    return cls(PixelType._best_type(val_min, val_max, needs_float))

  def as_struct(self):
    return self._struct_type

  def as_pg(self):
    return PixelType.TYPES.get(self._struct_type)[0]

  @staticmethod
  def _good_type(pix_type, val):
    type_info = PixelType.TYPES.get(pix_type)
    type_min = type_info[1]
    type_max = type_info[2]
    return val >= type_min and val <= type_max

  @staticmethod
  def _best_type(val_min, val_max, needs_float=False):
    if needs_float or type(val_min) == float or type(val_max) == float:
      pix_type_opt = ['f', 'd']
    elif val_min < 0:
      pix_type_opt = ['b', 'h', 'i', 'f', 'd']
    else:
      pix_type_opt = ['B', 'H', 'I', 'f', 'd']

    for pix_type in pix_type_opt:
      if PixelType._good_type(pix_type, val_min) and PixelType._good_type(pix_type, val_max):
        return pix_type
    raise ValueBoundsError('Data range (%d, %d) out of bounds' % (val_min, val_max))

class Band():
  def __init__(self, data, nodata=None, pix_type=None):
    self.data = data
    self.nodata = nodata
    if pix_type == None:
      self.pix_type = PixelType.from_data(data, nodata)
    else:
      self.pix_type = pix_type

class Raster():
  def __init__(self, bbox, height, width, bands, srid=None, skewx=0, skewy=0):
    self.bands = bands
    self.srid = srid
    self.width = width
    self.height = height
    self.skewx = skewx
    self.skewy = skewy
    self.ulx = bbox[0]
    self.uly = bbox[3]
    self.scalex = float(bbox[2] - bbox[0]) / self.width
    self.scaley = float(bbox[3] - bbox[1]) / self.height

  def as_wkb(self):
    if self.srid:
      srid = self.srid
    else:
      srid = 0

    # meta data (some unnecessary stuff here)
    byte_list_types = '<bHHddddddiHH'
    byte_list = []
    byte_list.append(1) # endianness
    byte_list.append(0) # version
    byte_list.append(len(self.bands)) # num bands
    byte_list.append(self.scalex) # scale x
    byte_list.append(self.scaley) # scale y
    byte_list.append(self.ulx) # upper left x
    byte_list.append(self.uly) # upper left y
    byte_list.append(self.skewx) # skew x
    byte_list.append(self.skewy) # skey y
    byte_list.append(srid) # SRID
    byte_list.append(self.width) # width
    byte_list.append(self.height) # height
    # band meta data
    for band in self.bands:
      pg_type = band.pix_type.as_pg()
      st_type = band.pix_type.as_struct()
      byte = 0
      byte += pg_type << 0 # type
      byte += 0 << 4 # reserved bit
      byte += 0 << 5 # is no data
      if not band.nodata == None:
        byte += 1 << 6 # has no data
      byte += 0 << 7 # is offdb
      byte_list_types += 'B%c%d%c' % (st_type, len(band.data), st_type)
      byte_list.append(byte)
      if band.nodata == None:
        byte_list.append(0)
      else:
        byte_list.append(band.nodata)

      # band data
      for val in band.data:
        byte_list.append(val)

    wkb = struct.pack(byte_list_types, *byte_list)
    return wkb.encode('hex')
