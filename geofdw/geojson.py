"""
:class:`GeoJSON` is a GeoJSON foreign data wrapper.
"""

from utils import *
from shapely.geometry import shape
import requests

class GeoJSON(GeoVectorForeignDataWrapper):
  """
  The GeoJSON foreign data wrapper can read the contents of an online GeoJSON
  file. The following column will exist in the table: geom GEOMETRY. Additional
  columns may be specified.

  Since column names in PostgreSQL are usually lowercase, so the wrapper will
  attempt case-insensitive matching between the column names and the attribute
  names in the GeoJSON file.

  Note that the geometry will use the SRID 4326 (WGS84) as specified by the
  GeoJSON standard. If you think you know better the SRID can be overridden
  with a table option (remember, you are *casting* the values to a new CRS, not
  tranforming them). The GeoJSON foreign data wrapper will *not* attempt to
  parse any CRS defined in the GeoJSON file itself.
  """

  def __init__(self, options, columns):
    """
    Create the table definition based on the provided column names and options.
  
    :param dict options: Options passed to the table creation.
      url: location of the GeoJSON file (required)
      srid: custom SRID that overrides the 4326 default
  
    :param list columns: Columns the user has specified in PostGIS.
    """
    self.url = options.get('url')
    srid = options.get('srid', 4326)
    super(GeoJSON, self).__init__(options, columns, srid = srid)    

  def execute(self, quals, columns):
    """
    Execute the query by reading the GeoJSON file and returning the contents
    based on the selected columns.

    :param list quals: List of predicates from the WHERE clause of the SQL
    statement. All filtering will happen in PostgreSQL rather than in the
    foreign data wrapper.
    
    :param list columns: List of columns requested in the SELECT statement.
    """
    try:
      response = requests.get(self.url)
    except requests.exceptions.InvalidURL as e:
      log_to_postgres('GeoJSON FDW: invalid URL %s' % self.url, WARNING)
      return []
    except requests.exceptions.ConnectionError as e:
      log_to_postgres('GeoJSON FDW: unable to connect to %s' % self.url, WARNING)
      return []
    except requests.exceptions.Timeout as e:
      log_to_postgres('GeoJSON FDW: timeout connecting to %s' % self.url, WARNING)
      return []

    return self._execute(response.json()['features'], columns)

  def _execute(self, features, columns):
    if 'geom' in columns:
      columns.remove('geom')
      with_geom = True
    else:
      with_geom = False

    for feat in features:
      row = {}
      if with_geom:
        row['geom'] = self.as_wkb(shape(feat['geometry']))

      properties = feat['properties']
      for p in properties.keys():
        for col in columns:
          if col == p or col == p.lower():
            row[col] = properties.get(p)
            break

      yield row
