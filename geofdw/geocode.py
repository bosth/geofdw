"""
:class:`FGeocode` and `RGeocode` are foreign data wrappers for the geopy
geocoding module.
"""

from utils import *
from shapely.geometry import Point
from shapely import wkb
import geopy

class _Geocode(GeoVectorForeignDataWrapper):
  def __init__(self, options, columns):
    super(_Geocode, self).__init__(options, columns, srid = 4326)    
    self.service = options.get('service', 'googlev3')
    self.geocoder = geopy.get_geocoder_for_service(self.service)()

  def get_path_keys(self):
    """
    Query planner helper.
    """
    return [ ('rank', 1), ('geom', 1), ('address', 1) ]

class FGeocode(_Geocode):
  """
  The FGeocode foreign data wrapper can do forward geocoding using a number of
  online services. The following columns may exist in the table: query TEXT,
  rank INTEGER, geom GEOMETRY(POINTZ, 4326), address TEXT.

  Note that the geometry will be a 3d point with SRID 4326. At present, no
  supported geocoder returns a useful elevation (the GoogleV3 geocoder, for
  example, returns a static elevation of 0).
  """

  def __init__(self, options, columns):
    """
    Create the table that uses GoogleV3 by default or one of the following
    named geocoders: ArcGIS; GoogleV3; Nominatim.

    :param dict options: Options passed to the table creation.
      service: 'arcgis', 'googlev3', 'nominatim'

    :param list columns: Columns the user has specified in PostGIS.
    """
    super(FGeocode, self).__init__(options, columns)

  def execute(self, quals, columns):
    """
    Execute the query on the geocoder.

    :param list quals: List of predicates from the WHERE clause of the SQL
    statement. The geocoder expects that one of these predicates will be of the
    form "query = 'Helsinki, Finland". Optionally, a bounding polygon can be
    used to influence the geocoder if it is supported; the following formats
    are recognised (and treated equivalently):

        geom && ST_GeomFromText('POLYGON(...)')
        ST_GeomFromText('POLYGON(...)') && geom
        geom @ ST_GeomFromText('POLYGON(...)')
        ST_GeomFromText('POLYGON(...)') ~ geom 

      Other predicates may be added, but they will be evaluated in PostgreSQL
      and not here.

    :param list columns: List of columns requested in the SELECT statement.
    """
    query, bounds = self._get_predicates(quals)

    if query:
      return self._execute(columns, query, bounds)
    else:
      return []

  def _execute(self, columns, query, bounds = None):
    rank = 0
    col_geom = 'geom' in columns
    col_addr = 'address' in columns
    col_query = 'query' in columns
    locations = self._get_locations(query, bounds)

    for location in locations:
      rank = rank + 1
      row = { 'rank' : rank }
      if col_geom:
        row['geom'] = self.as_wkb(Point(location.latitude, location.longitude, location.altitude))
      if col_addr:
        row['address'] = location.address
      if col_query:
        row['query'] = query
      yield row


  def _get_predicates(self, quals):
    query = None
    bounds = None
    for qual in quals:
      if qual.field_name == 'query' and qual.operator == '=':
        query = qual.value

      if qual.field_name == 'geom' and qual.operator in ['&&', '@']: # note A ~ B is transformed into B @ A
        bounds = wkb.loads(qual.value, hex=True).bounds
      elif qual.value == 'geom' and qual.operator == '&&':
        bounds = wkb.loads(qual.field_name, hex=True).bounds

    return query, bounds

  def _get_locations(self, query, bounds):
    log_to_postgres('Geocode (%s): running query "%s" with bounds = %s' % (self.service, query, str(bounds)), DEBUG)
    if bounds and self.service == 'googlev3':
      return self.geocoder.geocode(query, False, bounds = bounds)
    else:
      return self.geocoder.geocode(query, False)

class RGeocode(_Geocode):
  """
  The RGeocode foreign data wrapper can do reverse geocoding using a number of
  online services. The following columns may exist in the table: query
  GEOMETRY(POINT, 4326), rank INTEGER, geom GEOMETRY(POINTZ, 4326), address
  TEXT.

  Note that the geometry will be a 3d point with SRID 4326. At present, no
  supported geocoder returns a useful elevation (the GoogleV3 geocoder, for
  example, returns a static elevation of 0).
  """

  def __init__(self, options, columns):
    """
    Create the table that uses GoogleV3 by default or one of the following
    named geocoders: ArcGIS; GoogleV3; Nominatim.

    :param dict options: Options passed to the table creation.
      service: 'arcgis', 'googlev3', 'nominatim'

    :param list columns: Columns the user has specified in PostGIS.
    """
    super(RGeocode, self).__init__(options, columns)

  def execute(self, quals, columns):
    """
    Execute the query on the geocoder.

    :param list quals: List of predicates from the WHERE clause of the SQL
    statement. The geocoder expects that one of these predicates will be of the
    form "query = ST_MakePoint(52, 0)"

      Other predicates may be added, but they will be evaluated in PostgreSQL
      and not here.

    :param list columns: List of columns requested in the SELECT statement.
    """

    query = self._get_predicates(quals)
    if query:
      print 'executing'
      return self._execute(columns, query)
    else:
      return []

  def _execute(self, columns, query):
    rank = 0
    col_geom = 'geom' in columns
    col_addr = 'address' in columns
    col_query = 'query' in columns
    locations = self._get_locations(query)

    for location in locations:
      rank = rank + 1
      row = { 'rank' : rank }
      if col_geom:
        row['geom'] = self.as_wkb(Point(location.latitude, location.longitude, location.altitude))
      if col_addr:
        row['address'] = location.address
      if col_query:
        row['query'] = self.as_wkb(query)
      yield row


  def _get_predicates(self, quals):
    for qual in quals:
      if qual.field_name == 'query' and qual.operator == '=':
        return wkb.loads(qual.value, hex=True)

    return None

  def _get_locations(self, query):
    log_to_postgres('GeocodeR (%s): running query "%s"' % (self.service, query.wkt), DEBUG)
    return self.geocoder.reverse([query.x, query.y])
