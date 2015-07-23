from cStringIO import StringIO
import sys
import pypg
from geofdw.exception import CRSError

def crs_to_srid(crs):
  if crs == None:
    return None
  srid = crs.lower().replace('epsg:', '')
  try:
    return int(srid)
  except ValueError as e:
    raise CRSError(crs)

class ArcGridParseError(Exception):
  pass

class ArcGrid():
  def __init__(self, grid, srid = None):
    self.data = []
    self.srid = srid
    self._parse(grid)

  def _parse(self, grid):
    header = {}
    buf = StringIO(grid)

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
          raise ArcGridParseError('Expected %d columns, found %d' % (len(line), header['ncols']))
        self.data.extend(map(float, line))

    self.width = int(header['ncols'])
    self.height = int(header['nrows'])
    self.llx = header['xllcorner']
    self.lly = header['yllcorner']
    self.cellsize = header['cellsize']
    if header.has_key('nodata_value'):
      self.nodata = float(header.get('nodata_value'))
    else:
      self.nodata = None

  def as_pg_raster(self, bbox):
    band = pypg.raster.Band(self.data, self.nodata)
    return pypg.raster.Raster(bbox, self.height, self.width, [band], self.srid)
