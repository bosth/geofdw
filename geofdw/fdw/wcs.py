"""
:class:`WCS` is a WebCoverageService foreign data wrapper.
"""

from geofdw.base import GeoFDW
from geofdw.utils import ArcGrid, crs_to_srid
from geofdw.exception import MissingQueryPredicateError
import pypg
import requests

XML = """<?xml version="1.0" encoding="UTF-8"?>
<GetCoverage version="1.0.0" service="WCS" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns="http://www.opengis.net/wcs" xmlns:ows="http://www.opengis.net/ows/1.1" xmlns:gml="http://www.opengis.net/gml" xmlns:ogc="http://www.opengis.net/ogc" xsi:schemaLocation="http://www.opengis.net/wcs http://schemas.opengis.net/wcs/1.0.0/getCoverage.xsd">
  <sourceCoverage>$LAYER</sourceCoverage>
  <domainSubset>
    <spatialSubset>
      <gml:Envelope srsName="$CRS">
        <gml:pos>$MINX $MINY</gml:pos>
        <gml:pos>$MAXX $MAXY</gml:pos>
      </gml:Envelope>
      <gml:Grid dimension="2">
        <gml:limits>
          <gml:GridEnvelope>
            <gml:low>0 0</gml:low>
            <gml:high>$WIDTH $HEIGHT</gml:high>
          </gml:GridEnvelope>
        </gml:limits>
        <gml:axisName>x</gml:axisName>
        <gml:axisName>y</gml:axisName>
      </gml:Grid>
    </spatialSubset>
  </domainSubset>
  <rangeSubset>
    <axisSubset name="Band">
    <singleValue>$BAND</singleValue>
    </axisSubset>
  </rangeSubset>
  <output>
    <crs>$CRS</crs>
    <format>ArcGrid</format>
  </output>
</GetCoverage>
"""

class WCS(GeoFDW):
  def __init__(self, options, columns):
    super(WCS, self).__init__(options, columns)
    self.check_columns(['raster', 'geom'])
    self.url = self.get_option('url')
    layer = self.get_option('layer')
    crs = self.get_option('crs')
    self.srid = crs_to_srid(crs)
    width = self.get_option('width', required=False, default='256')
    height = self.get_option('height', required=False, default='256')
    band = self.get_option('band', required=False, default='1')
    self.xml = XML.replace('$LAYER', layer).replace('$CRS', crs).replace('$HEIGHT', height).replace('$WIDTH', width).replace('$BAND', band)
    self.headers = {'content-type': 'text/xml', 'Accept-Encoding': 'text' }
    self.get_request_options()

  def execute(self, quals, columns):
    bbox = self._get_predicates(quals)
    return self._get_raster(bbox)

  def _get_raster(self, bbox):
    shape, srid = pypg.geometry.postgis.to_shape(bbox)
    bounds = shape.bounds
    xml = self.xml.replace('$MINX', str(bounds[0])).replace('$MINY', str(bounds[1])).replace('$MAXX', str(bounds[2])).replace('$MAXY', str(bounds[3]))
    try:
      response = requests.post(self.url, headers=self.headers, data=xml, auth=self.auth, verify=self.verify)
    except requests.exceptions.ConnectionError as e:
      self.log('WCS FDW: unable to connect to %s' % self.url)
      return []
    except requests.exceptions.Timeout as e: #pragma: no cover
      self.log('WCS FDW: timeout connecting to %s' % self.url)
      return []

    if response.status_code == 200:
      grid = ArcGrid(response.text, self.srid)
      rast = grid.as_pg_raster(bounds)
      return [ { 'rast' : rast.ewkb(), 'geom' : bbox } ] # add geom
    else:
      return None

  def _get_predicates(self, quals):
    for qual in quals:
      if qual.field_name == 'geom' and qual.operator in ['=', '~=']:
        return qual.value
      elif qual.value == 'geom' and qual.operator in ['=', '~=']:
        return qual.field_name
    raise MissingQueryPredicateError('Query predicate with "geom" column is required')
