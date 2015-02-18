"""
:class:`OSRM` is an Open Source Routing Machine foreign data wrapper.
"""

from utils import *
from shapely.geometry import Point, LineString
from shapely import wkb
from polyline.codec import PolylineCodec

import requests

class OSRM(GeoVectorForeignDataWrapper):
  """
  """

  def __init__(self, options, columns):
    """
    Create the table definition based on the provided column names and options.
  
    :param dict options: Options passed to the table creation.
      url: location of the OSRM
  
    :param list columns: Columns the user has specified in PostGIS.
    """
    super(OSRM, self).__init__(options, columns, srid = 4326)    
    zoom = int(options.get('zoom', 14))
    url = options.get('url', 'http://router.project-osrm.org/viaroute')
    self.url_base = '%s?z=%d&output=json&alt=false&instructions=true&' % (url, zoom)

  def execute(self, quals, columns):
    """
    """
    self.source, self.target = self._get_predicates(quals)
    if not self.source or not self.target:
      return []

    url = self._get_url()
    response = requests.get(url).json()

    points = PolylineCodec().decode(response['route_geometry'])
    instructions = response['route_instructions']
    return self._execute(columns, points, instructions)

  def _execute(self, columns, points, instructions):
    for i in range(len(instructions) - 1):
      row = {}
      start = instructions[i][3]
      end = instructions[i+1][3]
      if end - start < 2:
        row['geom'] = self.as_wkb(Point(points[start]))
      else:
        row['geom'] = self.as_wkb(LineString(points[start:end]))

      row['directions'] = instructions[i][0]
      row['name'] = instructions[i][1]
      row['length'] = instructions[i][2]
      row['time'] = instructions[i][4]
      row['direction'] = instructions[i][6]
      row['azimuth'] = instructions[i][7]
      row['source'] = self.as_wkb(self.source)
      row['target'] = self.as_wkb(self.target)
      print row
      yield row

  def _get_predicates(self, quals):
    source = None
    target = None
    for qual in quals:
      if qual.field_name == 'source' and qual.operator == '=':
        source = wkb.loads(qual.value, hex=True)
      elif qual.field_name == 'target' and qual.operator == '=':
        target = wkb.loads(qual.value, hex=True)
    return source, target

  def _get_url(self):
    source = '%f,%f' % (self.source.x, self.source.y)
    target = '%f,%f' % (self.target.x, self.target.y)
    return self.url_base + 'loc=%s&loc=%s' % (source, target)
