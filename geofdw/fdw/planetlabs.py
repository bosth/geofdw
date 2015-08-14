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

    OPERATORS = {'=':'eq', '<':'lt', '<=':'lte', '>':'gt', '>=':'gte'}
    PROPERTIES = {
        'camera.bit_depth': (['='], list, [8, 12]),
        'camera.color_mode': (['='], list, ['RGB', 'Monochromatic']),
        'camera.exposure_time': (['=', '<', '<=', '>', '>='], int), # error with float
        'camera.gain': (['=', '<', '<=', '>', '>='], int), # error with float
        'camera.tdi_pulses': (['=', '<', '<=', '>', '>='], int),
        'cloud_cover.estimated': (['=', '<', '<=', '>', '>='], float),
        'image_statistics.gsd': (['=', '<', '<=', '>', '>='], float),
        'image_statistics.image_quality': (['>='], list, ['test', 'standard', 'target']),
        'image_statistics.snr': (['=', '<', '<=', '>', '>='], float),
        'sat.alt': (['=', '<', '<=', '>', '>='], float),
        'sat.id': (['='], int),
        'sat.lat': (['=', '<', '<=', '>', '>='], float),
        'sat.lng': (['=', '<', '<=', '>', '>='], float),
        'sat.off_nadir': (['=', '<', '<=', '>', '>='], float),
        'sun.altitude': (['=', '<', '<=', '>', '>='], float),
        'sun.azimuth': (['=', '<', '<=', '>', '>='], float),
        'sun.local_time_of_day': (['=', '<', '<=', '>', '>='], float)
    }


    def execute(self, quals, columns):
      """
      Execute the query on the Planet API.

      :param list quals: List of predicates from the WHERE clause of the SQL
      statement. If a geometric predicate is used to filter scenes, the API
      will be used to evaluate the && operator. Certain PostGIS functions,
      notably ST_Intersects, will generate a predicate with the && operator,
      and therefore use of these functions will filter geometries on the remote
      server rather than in Postgres, which is the desired bahaviour. Other
      operators may also be used, but they will not be evaluated on the remote
      server.

      :param list columns: List of columns requested in the SELECT statement.
      """
      aoi, filters = self._get_predicates(quals)
      scenes = self.client.get_scenes_list(intersects=aoi, **filters).get()
      if scenes['count'] > 0:
          for feature in scenes['features']:
              geom = feature['geometry']
              row = {}
              properties = feature['properties']
              for k,v in properties.iteritems():
                  if k in ['camera', 'cloud_cover', 'image_statistics', 'sat', 'sun']:
                      for subk in v.keys():
                          row['%s.%s' % (k, subk)] = v[subk]
                  elif k in ['acquired', 'published']:
                      row[k] = v
              row['geom'] = pypg.geometry.shape.to_postgis(geom, self.srid)
              yield row

    def _get_filter(self, qual):
        if qual.field_name in ['acquired', 'published']:
            if qual.operator in ['=', '<', '<=', '>', '>=']:
                return '%s.%s' % (qual.field_name, self.OPERATORS[qual.operator]), qual.value

        if qual.field_name in self.PROPERTIES:
            attribs = self.PROPERTIES[qual.field_name]
            if qual.operator in attribs[0]:
                if attribs[1] == list:
                    if qual.value in attribs[2]:
                        return '%s.%s' % (qual.field_name, self.OPERATORS[qual.operator]), qual.value
                else:
                        return '%s.%s' % (qual.field_name, self.OPERATORS[qual.operator]), attribs[1](qual.value)
        return None

    def _get_predicates(self, quals):
        shape = None
        filters = {}
        print quals
        for qual in quals:
            if qual.field_name == 'geom':
                if qual.operator in ['&&']:
                    shape, srid = pypg.geometry.postgis.to_shape(qual.value)
            else:
                f = self._get_filter(qual)
                if f:
                    key = f[0]
                    value = f[1]
                    filters[key] = value
        print filters
        if shape:
            if srid != 4326:
                 raise InvalidGeometryError('Planet API only accepts geometries using an SRID of 4326.')
            aoi = pypg.geometry.shape.to_wkt(box(*shape.bounds))
        else:
            aoi = None

        return aoi, filters
