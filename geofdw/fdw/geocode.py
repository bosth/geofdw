"""
:class:`FGeocode` and `RGeocode` are foreign data wrappers for the geopy
geocoding module.
"""

from geofdw.base import *
import geopy
from plpygis import Geometry, Point


class _Geocode(GeoFDW):
    def __init__(self, options, columns):
        super(_Geocode, self).__init__(options, columns, srid=4326)
        self.service = options.get("service", "googlev3")
        geocoder = geopy.get_geocoder_for_service(self.service)
        if geocoder == geopy.geocoders.googlev3.GoogleV3:
            api_key = options.get("api_key")
            self.geocoder = geocoder(api_key=api_key)
        elif geocoder == geopy.geocoders.arcgis.ArcGIS:
            username = options.get("username")
            password = options.get("password")
            self.geocoder = geocoder(username=username, password=password)
        else:
            self.geocoder = geocoder()

    def get_path_keys(self):
        """
        Query planner helper.
        """
        return [("rank", 1), ("geom", 1), ("address", 1)]


class FGeocode(_Geocode):
    """
    The FGeocode foreign data wrapper can do forward geocoding using a number
    of online services. The following columns may exist in the table: query
    TEXT, rank INTEGER, geom GEOMETRY(POINTZ, 4326), address TEXT.

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
            api_key: API key for GoogleV3 (optional)
            username: user name for ArcGIS (optional)
            password: password for ArcGIS (optional)

        :param list columns: Columns the user has specified in PostGIS.
        """
        super(FGeocode, self).__init__(options, columns)

    def execute(self, quals, columns):
        """
        Execute the query on the geocoder.

        :param list quals: List of predicates from the WHERE clause of the SQL
        statement. The geocoder expects that one of these predicates will be of
        the form "query = 'Helsinki, Finland". Optionally, a bounding polygon
        can be used to influence the geocoder if it is supported; the following
        formats are recognised (and treated equivalently):

                geom && ST_GeomFromText('POLYGON(...)')
                ST_GeomFromText('POLYGON(...)') && geom
                geom @ ST_GeomFromText('POLYGON(...)')
                ST_GeomFromText('POLYGON(...)') ~ geom

            Other predicates may be added, but they will be evaluated in
            PostgreSQL and not here.

        :param list columns: List of columns requested in the SELECT statement.
        """
        query, bounds = self._get_predicates(quals)

        if query:
            return self._execute(columns, query, bounds)
        else:
            return []

    def _execute(self, columns, query, bounds=None):
        rank = 0
        col_geom = "geom" in columns
        col_addr = "address" in columns
        col_query = "query" in columns
        locations = self._get_locations(query, bounds)

        if locations:
            for location in locations:
                rank = rank + 1
                row = {"rank": rank}
                if col_geom:
                    geom = Point((location.longitude, location.latitude,
                                  location.altitude), srid=self.srid)
                    row["geom"] = geom
                if col_addr:
                    row["address"] = location.address
                if col_query:
                    row["query"] = query
                yield row

    def _get_predicates(self, quals):
        query = None
        bounds = None
        for qual in quals:
            if qual.field_name == "query" and qual.operator == "=":
                query = qual.value

            # note A ~ B is transformed into B @ A
            if qual.field_name == "geom" and qual.operator in ["&&", "@"]:
                bounds = Geometry(qual.value).bounds
            elif qual.value == "geom" and qual.operator == "&&":
                bounds = Geometry(qual.field_name).bounds

        return query, bounds

    def _get_locations(self, query, bounds):
        log_to_postgres("Geocode (%s): running query '%s' with bounds = %s" %
                        (self.service, query, str(bounds)), DEBUG)
        if bounds and self.service == "googlev3":
            return self.geocoder.geocode(query, False, bounds=(bounds[1], bounds[0], bounds[3], bounds[2]))
        else:
            return self.geocoder.geocode(query, False)


class RGeocode(_Geocode):
    """
    The RGeocode foreign data wrapper can do reverse geocoding using a number
    of online services. The following columns may exist in the table: query
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
            api_key: API key for GoogleV3 (optional)
            username: user name for ArcGIS (optional)
            password: password for ArcGIS (optional)

        :param list columns: Columns the user has specified in PostGIS.
        """
        super(RGeocode, self).__init__(options, columns)

    def execute(self, quals, columns):
        """
        Execute the query on the geocoder.

        :param list quals: List of predicates from the WHERE clause of the SQL
        statement. The geocoder expects that one of these predicates will be of
        the form "query = ST_MakePoint(0, 52)"

            Other predicates may be added, but they will be evaluated in
            PostgreSQL and not here.

        :param list columns: List of columns requested in the SELECT statement.
        """

        query = self._get_predicates(quals)
        if query:
            return self._execute(columns, query)
        else:
            return []

    def _execute(self, columns, query):
        rank = 0
        col_geom = "geom" in columns
        col_addr = "address" in columns
        col_query = "query" in columns
        locations = self._get_locations(query)

        for location in locations:
            rank = rank + 1
            row = {"rank": rank}
            if col_geom:
                geom = Point((location.longitude, location.latitude,
                              location.altitude), srid=self.srid)
                row["geom"] = geom
            if col_addr:
                row["address"] = location.address
            if col_query:
                row["query"] = query.wkb
            yield row

    def _get_predicates(self, quals):
        for qual in quals:
            if qual.field_name == "query" and qual.operator == "=":
                return Geometry(qual.value)
        return None

    def _get_locations(self, query):
        log_to_postgres("GeocodeR (%s): running query '%s'" % (self.service,
                                                               query), DEBUG)
        return self.geocoder.reverse([query.x, query.y])
