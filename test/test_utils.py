"""
Test geofdw utils
"""

import unittest

from geofdw.utils import *

class utils(unittest.TestCase):
  grid_text_1 = """NCOLS 8
NROWS 4
XLLCORNER 30.0
YLLCORNER 30.0
CELLSIZE 1.0
NODATA_VALUE -9999
1441.0 1360.0 1348.0 1295.0 1362.0 1352.0 1340.0 1335.0
1464.0 1404.0 1409.0 1380.0 1372.0 1399.0 1336.0 1286.0
1419.0 1430.0 1434.0 1405.0 1409.0 1433.0 1335.0 1418.0
1455.0 1570.0 1488.0 1437.0 1413.0 1457.0 1330.0 1478.0
"""

  grid_text_2 = """NCOLS 4
NROWS 8
XLLCORNER -30.0
YLLCORNER 0.0
CELLSIZE 1.5
1441.0 1360.0 1348.0 1295.0
1362.0 1352.0 1340.0 1335.0
1464.0 1404.0 1409.0 1380.0
1372.0 1399.0 1336.0 1286.0
1419.0 1430.0 1434.0 1405.0
1409.0 1433.0 1335.0 1418.0
1455.0 1570.0 1488.0 1437.0
1413.0 1457.0 1330.0 1478.0
"""

  grid_text_3 = """NCOLS 10
NROWS 1
XLLCORNER 0.0
YLLCORNER 0.0
CELLSIZE 1.0
1441.0 1360.0 1348.0 1295.0
"""

  def test_crs_to_srid_none(self):
    """
    crs_to_srid converting missing CRS to a SRID
    """
    srid = crs_to_srid(None)
    self.assertEquals(srid, None)


  def test_crs_to_srid_lower(self):
    """
    crs_to_srid converting lower-case CRS to a SRID
    """
    srid = crs_to_srid('epsg:4326')
    self.assertEquals(srid, 4326)

  def test_crs_to_srid_upper(self):
    """
    crs_to_srid converting upper-case CRS to a SRID
    """
    srid = crs_to_srid('EPSG:4326')
    self.assertEquals(srid, 4326)

  def test_read_arcgrid_1(self):
    """
    ArcGrid parsing file with nodata and SRID
    """
    grid = ArcGrid(self.grid_text_1, 4326)
    self.assertEquals(grid.width, 8)
    self.assertEquals(grid.height, 4)
    self.assertEquals(grid.llx, 30.0)
    self.assertEquals(grid.lly, 30.0)
    self.assertEquals(grid.cellsize, 1.0)
    self.assertEquals(grid.nodata, -9999)
    self.assertEquals(len(grid.data), 32)
    self.assertEquals(grid.srid, 4326)

  def test_read_arcgrid_2(self):
    """
    ArcGrid parsing file without nodata and SRID
    """
    grid = ArcGrid(self.grid_text_2)
    self.assertEquals(grid.width, 4)
    self.assertEquals(grid.height, 8)
    self.assertEquals(grid.llx, -30.0)
    self.assertEquals(grid.lly, 0.0)
    self.assertEquals(grid.cellsize, 1.5)
    self.assertEquals(grid.nodata, None)
    self.assertEquals(len(grid.data), 32)
    self.assertEquals(grid.srid, None)

  def test_read_arcgrid_3(self):
    """
    ArcGrid parsing invalid file
    """
    self.assertRaises(ArcGridParseError, ArcGrid, self.grid_text_3)

  def test_to_pg_raster(self):
    """
    ArcGrid exporting to PostGIS raster
    """
    grid = ArcGrid(self.grid_text_1, 4326)
    raster = grid.as_pg_raster((30, 30, 38, 34))
    self.assertEquals(grid.srid, raster.srid)
    self.assertEquals(grid.width, raster.width)
    self.assertEquals(grid.height, raster.height)
    self.assertEquals(grid.llx, raster.ulx)
    self.assertNotEqual(grid.lly, raster.uly)
    self.assertEquals(len(raster.bands), 1)
