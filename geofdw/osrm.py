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
  The OSRM foreign data wrapper can generate driving directions using an Open
  Source Routing Machine server.

  Note that all geometries will use SRID 4326.
  """

  def __init__(self, options, columns):
    """
    Create the table definition based on the provided column names and options.
    The source and target columns are required to get any meaningful results
    from a query.
  
    :param dict options: Options passed to the table creation.
      url: location of the OSRM. Defaults to the community's instance.
      zoom: default zoom level. Defaults to 14.
  
    :param list columns: Columns the user has specified in PostGIS.
      geom GEOMETRY(GEOMETERY, 4326): line or point representing a segment in the route
      name TEXT: name of a way
      turn INTEGER: turn istructions (0: no turn; 1: go straight; etc)
      length INTEGER: travel distance (m)
      time INTEGER: travel time (s)
      azimuth FLOAT
      source GEOMETRY(POINT, 4326): source point of route
      target GEOMETRY(POINT, 4326): target point of route
    """
    super(OSRM, self).__init__(options, columns, srid = 4326)    
    zoom = int(options.get('zoom', 14))
    url = options.get('url', 'http://router.project-osrm.org/viaroute')
    self.url_base = '%s?z=%d&output=json&alt=false&instructions=true&' % (url, zoom)

  def execute(self, quals, columns):
    """
    Execute the query on the OSRM server, returning the optimal routing between
    two points.

    :param list quals: List of predicates from the WHERE clause of the SQL
    statement. The OSRM expects two points, a starting location (the 'source'
    column) and a destination (the 'target' column). Both points must use SRID
    4326:

      source = ST_SetSRID(ST_MakePoint(51.64070,-121.29703), 4326) AND 
      target = ST_SetSRID(ST_MakePoint(49.28924,-123.01752), 4326)

      Other predicates may be added, but they will be evaluated in PostgreSQL
      and not here and they will only have the effect of removing segments of
      the optimal route not influencing the overall route search.

    :param list columns: List of columns requested in the SELECT statement.
    Generally, there is no need to request the 'source' and 'target' columns
    when querying the OSRM FDW.
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

      if 'geom' in columns:
        if end - start < 2:
          row['geom'] = self.as_wkb(Point(points[start]))
        else:
          row['geom'] = self.as_wkb(LineString(points[start:end]))
      if 'turn' in columns: 
        row['turn'] = instructions[i][0]
      if 'name' in columns: 
        row['name'] = instructions[i][1]
      if 'length' in columns: 
        row['length'] = instructions[i][2]
      if 'time' in columns: 
        row['time'] = instructions[i][4]
      if 'azimuth' in columns: 
        row['azimuth'] = instructions[i][7]
      if 'source' in columns: 
        row['source'] = self.as_wkb(self.source)
      if 'target' in columns: 
        row['target'] = self.as_wkb(self.target)
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
