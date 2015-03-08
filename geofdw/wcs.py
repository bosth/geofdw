"""
:class:`WCS` is a WebCoverageService foreign data wrapper.
"""

from utils import *
from shapely import wkb
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

class WCS(GeoRasterForeignDataWrapper):
  def __init__(self, options, columns):
    super(WCS, self).__init__(options, columns)    
    version = options.get('version', '1.0.0')
    layer = options.get('layer')
    width = str(options.get('width', 256))
    height = str(options.get('height', 256))
    band = str(options.get('band', 1))
    self.crs = options.get('crs')
    self.srid = self.crs_to_srid(self.crs)
    self.xml = XML.replace('$LAYER', layer).replace('$CRS', self.crs).replace('$HEIGHT', height).replace('$WIDTH', width).replace('$BAND', band)
    self.url = options.get('url')
    self.headers = {'content-type': 'text/xml', 'Accept-Encoding': 'text' }

# can estimate this
#  def get_path_keys(self):
#    """
#    Query planner helper.
#    """
#    return [ ('rast', 1) ]

  def execute(self, quals, columns):
    bbox = self._get_predicates(quals)
    if bbox:
      return self._get_raster(bbox)
    else:
      return None

  def _get_raster(self, bbox):
    bounds = wkb.loads(bbox, hex=True).bounds
    xml = self.xml.replace('$MINX', str(bounds[0])).replace('$MINY', str(bounds[1])).replace('$MAXX', str(bounds[2])).replace('$MAXY', str(bounds[3]))
    req = requests.post(self.url, headers=self.headers, data=xml)
    if req.status_code == 200:
      grid = ArcGrid(self.srid)
      grid.parse(req.text)
      rast = grid.to_wkb(grid, bounds)
      return [ { 'rast' : rast, 'geom' : bbox } ] # add geom
    else:
      return None

  def _get_predicates(self, quals):
    for qual in quals:
      if qual.field_name == 'geom' and qual.operator in ['=', '~=']:
        return qual.value
      elif qual.value == 'geom' and qual.operator in ['=', '~=']:
        return qual.field_name
    return None
