"""
:class:`PlanetScenes` is a foreign data wrappers for the Planet Labs imagery.
"""

from geofdw.base import *
from geofdw.exception import InvalidGeometryError, QueryPredicateError
from planet import api
from shapely.geometry import box
import json
import geopy
import pypg

class PlanetScenes(GeoFDW):
    """
    The PlanetScenes foreign data wrapper retrieves a list of scenes and their
    metadata. The following columns are supported in the table: id INTEGER,
    strip_id NUMERIC, geom GEOMETRY(POLYGON, 4326), acquired TIMESTAMP WITH
    TIME ZONE, camera JSON, image_statistics JSON, links JSON, sat JSON, sun
    JSON.

    NOTE: Due to a limitation in Multicorn quals, JSON queries (i.e.
    "camera->>'gain' > 50") are not passed to the Planet API. Could break out
    the JSON keys as individual columns.
    """
    def __init__(self, options, columns):
        super(PlanetScenes, self).__init__(options, columns, srid=4326)
        api_key = self.get_option('api_key', required=True)
        self.client = api.Client(api_key=api_key)

    def execute(self, quals, columns):
      """
      Execute the query on the Planet API.

      :param list quals: List of predicates from the WHERE clause of the SQL
      statement. If a geometric predicate is used to filter scenes, the API
      will be used to evaluate the && operator. Other predicates may be added,
      but they will be evaluated in PostgreSQL and not on the remote server.

      :param list columns: List of columns requested in the SELECT statement.
      """
      aoi, filters = self._get_predicates(quals)
      print aoi
      print filters
      scenes = self.client.get_scenes_list(intersects=aoi, **filters).get()
      if scenes['count'] > 0:
          print 'count',scenes['count']
          for feature in scenes['features']:
              geom = feature['geometry']
              row = {}
              for k,v in feature['properties'].iteritems():
                  row[k] = json.dumps(v)
              row['geom'] = pypg.geometry.shape.to_postgis(geom, self.srid)
              yield row

    def _execute(self, columns):
        return []

    def _get_predicates(self, quals):
        shape = None
        filters = {}
        print quals
        for qual in quals:
            if qual.field_name == 'geom':
                if qual.operator in ['&&']:
                    shape, srid = pypg.geometry.postgis.to_shape(qual.value)
            elif qual.value == 'geom':
                if qual.operator in ['&&']:
                    shape, srid = pypg.geometry.postgis.to_shape(qual.field_name)
            elif qual.field_name == 'acquired':
                if qual.operator == '<':
                    filters['acquired.lt'] = qual.value
                elif qual.operator == '<=':
                    filters['acquired.lte'] = qual.value
                elif qual.operator == '>':
                    filters['acquired.gt'] = qual.value
                elif qual.operator == '>=':
                    filters['acquired.gte'] = qual.value
            elif qual.value == 'acquired':
                if qual.operator == '<':
                    filters['acquired.gt'] = qual.field_name
                elif qual.operator == '<=':
                    filters['acquired.gte'] = qual.field_name
                elif qual.operator == '>':
                    filters['acquired.lt'] = qual.field_name
                elif qual.operator == '>=':
                    filters['acquired.lte'] = qual.field_name

        if shape:
            if srid != 4326:
                 raise InvalidGeometryError('Planet API only accepts geometries using an SRID of 4326.')
            aoi = pypg.geometry.shape.to_geojson(box(*shape.bounds))
        else:
            aoi = None

        return json.dumps(aoi), filters
