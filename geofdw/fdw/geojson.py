"""
:class:`GeoJSON` is a GeoJSON foreign data wrapper.
"""

from geofdw.base import GeoFDW
from geofdw.exception import MissingColumnError, MissingOptionError, OptionTypeError
from plpygis import Geometry
import json
import requests


class GeoJSON(GeoFDW):
    """
    The GeoJSON foreign data wrapper can read the contents of an online GeoJSON
    file. The following column will exist in the table: geom GEOMETRY.
    Additional columns may be specified.

    Since column names in PostgreSQL are usually lowercase, so the wrapper will
    attempt case-insensitive matching between the column names and the
    attribute names in the GeoJSON file.

    Note that the geometry will use the SRID 4326 as specified by the GeoJSON
    standard. If you think you know better the SRID can be overridden with a
    table option (remember, you are *casting* the values to a new CRS, not
    transforming them). The GeoJSON foreign data wrapper will *not* attempt to
    parse any CRS defined in the GeoJSON file itself.
    """
    def __init__(self, options, columns):
        """
        Create the table definition based on the provided column names and
        options.

        :param dict options: Options passed to the table creation.
            url: location of the GeoJSON file (required)
            srid: custom SRID that overrides the 4326 default
            verify: set to false to ignore invalid SSL certificates
            user: user name for authentication
            pass: password for authentication

        :param list columns: Columns the user has specified in PostGIS.
            geom (required)
        """
        super(GeoJSON, self).__init__(options, columns)
        self.check_columns(["geom"])
        self.url = self.get_option("url")
        self.srid = self.get_option("srid", required=False, default=4326,
                                    option_type=int)
        self.get_request_options()

    def execute(self, quals, columns):
        """
        Execute the query by reading the GeoJSON file and returning the
        contents based on the selected columns.

        :param list quals: List of predicates from the WHERE clause of the SQL
        statement. All filtering will happen in PostgreSQL rather than in the
        foreign data wrapper.

        :param list columns: List of columns requested in the SELECT statement.
        """
        try:
            response = requests.get(self.url, auth=self.auth,
                                    verify=self.verify)
        except requests.exceptions.ConnectionError as e:
            self.log("GeoJSON FDW: unable to connect to %s" % self.url)
            return []
        except requests.exceptions.Timeout as e:  #pragma: no cover
            self.log("GeoJSON FDW: timeout connecting to %s" % self.url)
            return []

        try:
            data = response.json()
        except ValueError as e:
            self.log("GeoJSON FDW: invalid JSON")
            return []
        try:
            features = data["features"]
        except KeyError as e:
            self.log("GeoJSON FDW: invalid GeoJSON")
            return []
        return self._execute(features, columns)

    def _execute(self, features, columns):
        if "geom" in columns:
            columns.remove("geom")
            use_geom = True
        else:
            use_geom = False
        for feat in features:
            row = {}
            if use_geom:
                gj = feat["geometry"]
                geom = Geometry.from_geojson(gj, srid=self.srid)
                row["geom"] = geom.wkb

            properties = feat["properties"]
            for p in properties.keys():
                for col in columns:
                    if col == p or col == p.lower():
                        row[col] = properties.get(p)
                        break
            yield row
