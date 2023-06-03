"""
:class:`OpenSky` is a foreign data wrapper for the OpenSky website.
"""

from geofdw.base import *
import geopy
from plpygis import Geometry, Point, LineString
import os
from datetime import datetime, timezone
from dateutil import parser
from requests import Session
from requests.auth import HTTPBasicAuth
from requests.exceptions import JSONDecodeError
OSURL = "https://opensky-network.org/api"

CATEGORY = {
    0  : "No information at all",
    1  : "No ADS-B Emitter Category Information",
    2  : "Light (< 15500 lbs)",
    3  : "Small (15500 to 75000 lbs)",
    4  : "Large (75000 to 300000 lbs)",
    5  : "High Vortex Large (aircraft such as B-757)",
    6  : "Heavy (> 300000 lbs)",
    7  : "High Performance (> 5g acceleration and 400 kts)",
    8  : "Rotorcraft",
    9  : "Glider / sailplane",
    10 : "Lighter-than-air",
    11 : "Parachutist / Skydiver",
    12 : "Ultralight / hang-glider / paraglider",
    13 : "Reserved",
    14 : "Unmanned Aerial Vehicle",
    15 : "Space / Trans-atmospheric vehicle",
    16 : "Surface Vehicle – Emergency Vehicle",
    17 : "Surface Vehicle – Service Vehicle",
    18 : "Point Obstacle (includes tethered balloons)",
    19 : "Cluster Obstacle",
    20 : "Line Obstacle"
}

class _OpenSky(GeoFDW):
    def __init__(self, options, columns):
        super(_OpenSky, self).__init__(options, columns, srid=4326)
        osuser = options.get("osuser", os.getenv("OPENSKY_USER"))
        ospass = options.get("ospass", os.getenv("OPENSKY_PASS"))
        self.opensky = Session()
        if osuser and ospass:
            self.opensky.auth = HTTPBasicAuth(osuser, ospass)


class StateVector(_OpenSky):
    """
    """

    def __init__(self, options, columns):
        """
        Create a table containing aircraft and their current state.

        :param dict options: Options passed to the table creation.
            osuser: OpenSky user name
            ospass: OpenSky password

        :param list columns: Columns the user has specified in PostGIS.
            geom [POINTZ]: position of the airplane
            icao24 [TEXT]: the transponder address
            time [TIMESTAMP] 
            callsign [TEXT]
            origin_country [TEXT]
            baro_altitude [FLOAT]: barometric altitude
            velocity [FLOAT]: measured in m/s
            true_track [FLOAT]: degrees clockwise from north
            vertical_rate [FLOAT]: measured in m/s
            squakw [TEXT]: transponder code
            spi [BOOLEAN]: whether flight status has a special purpose indicator
            on_ground [BOOLEAN]
            position_source [INTEGER]: 0=ADS-B, 1=ASTERIX, 2=MLAT, 3=FLARM
            category [INTEGER]: aircraft category
            category_text [TEXT]: aircraft category (description)
        """
        super(StateVector, self).__init__(options, columns)

    def execute(self, quals, columns):
        """
        Execute the query.

        :param list quals: List of predicates from the WHERE clause of the SQL
        statement. The API accepts a time (TIMESTAMP) or a icao24 (TEXT) identifier. A
        bounding polygon can also be used to influence the geocoder if it is
        supported; the following formats are recognised (and treated
        equivalently):

                geom && ST_GeomFromText('POLYGON(...)')
                ST_GeomFromText('POLYGON(...)') && geom
                geom @ ST_GeomFromText('POLYGON(...)')
                ST_GeomFromText('POLYGON(...)') ~ geom

            Other predicates may be added, but they will be evaluated in
            PostgreSQL and not server-side.

        :param list columns: List of columns requested in the SELECT statement.
        """
        time, epoch, icao24, bounds = self._get_predicates(quals)
        return self._execute(columns, time, epoch, icao24, bounds)

    def _get_predicates(self, quals):
        time = None
        epoch = None
        icao24 = None
        bounds = None
        log_to_postgres("QUAL {}".format(quals), INFO)
        for qual in quals:
            if qual.field_name == "time" and qual.operator == "=":
                time = qual.value.replace(tzinfo=timezone.utc)
                epoch = int(qual.value.replace(tzinfo=timezone.utc).timestamp())
            if qual.field_name == "icao24":
                if qual.operator == "=":
                    icao24 = qual.value
                elif qual.operator == ("=", True):
                    icao24 = qual.value

            # note A ~ B is transformed into B @ A
            if qual.field_name == "geom" and qual.operator in ["&&", "@"]:
                bounds = Geometry(qual.value).bounds
            elif qual.value == "geom" and qual.operator == "&&":
                bounds = Geometry(qual.field_name).bounds
        return time, epoch, icao24, bounds

    def _execute(self, columns, time, epoch, icao24, bounds=None):
        if "category" in columns:
            category = True
        else:
            category = False

        row = {}
        states = self._get_states(epoch, icao24, bounds, category=category)
        if not states: return []

        for state in states:
            row["icao24"] = state[0]
            if time:
                row["time"] = time.isoformat()
            else:
                row["time"] = datetime.utcfromtimestamp(state[4])
            if state[5] is not None and state[6] is not None:
                if state[7] is None:
                    geom = Point((state[5], state[6]), srid=self.srid)
                else:
                    geom = Point((state[5], state[6], state[13]), srid=self.srid)
                row["geom"] = geom
            row["callsign"] = state[1]
            row["origin_country"] = state[2]
            row["on_ground"] = state[8]
            row["velocity"] = state[9]
            row["true_track"] = state[10]
            row["vertical_rate"] = state[11]
            row["squawk"] = state[14]
            row["spi"] = state[15]
            row["position_source"] = state[16]
            if category:
                row["category"] = state[17]
                row["category_text"] = CATEGORY.get(state[17], None)
            yield row

    def _get_states(self, epoch, icao24, bounds, category):
        params = {}
        if category:
            params["extended"] = 1
        if bounds:
            params["lomin"] = bounds[0]
            params["lomax"] = bounds[1]
            params["lamin"] = bounds[2]
            params["lamax"] = bounds[3]
        if epoch:
            params["time"] = epoch
        if icao24:
            params["icao24"] = icao24

        response = self.opensky.get(f"{OSURL}/states/all", params=params)
        try: 
            json = response.json()
            log_to_postgres("OPENSKY {}".format(response.url), INFO)
        except JSONDecodeError as e:
            log_to_postgres("OPENSKY {}".format(response.text), ERROR)
            raise e
        return json.get("states")

    def get_path_keys(self):
        """
        Query planner helper.
        """
        return [("geom", 100), ("time", 10), ("icao24", 1)]
